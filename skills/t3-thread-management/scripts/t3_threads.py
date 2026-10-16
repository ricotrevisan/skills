#!/usr/bin/env python3
"""Launch and inspect T3 Code threads through a running server's V2 orchestration API.

Standard library only (Python 3.9+), so `--host` can stream it to another machine.
Auth is a five-minute bearer session issued by the destination's own t3 CLI.
"""
import argparse
import base64
import glob
import ipaddress
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

PROTOCOL = '2'
SCOPES = ('orchestration:read', 'orchestration:operate')
REQUEST_NAMESPACE = uuid.UUID('6f1d3c2e-8a4b-4f3e-9c1d-2b7a5e0f9d11')
TERMINAL_RUN_STATES = ('completed', 'failed', 'interrupted', 'cancelled', 'error')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def discover_cli(base, explicit=None, node='node'):
    """Return argv for the destination's t3 CLI."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    else:
        found = shutil.which('t3')
        if found:
            candidates.append(Path(found))
        # npm installs: the native binary needs no Node on PATH (office over SSH).
        candidates += [Path(p) for p in sorted(glob.glob(os.path.expanduser(
            '~/.local/lib/node_modules/t3/node_modules/@t3code/t3-*/t3')))]
        candidates += sorted((base / 'runtime/versions').glob('*/t3'),
                             key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        if path.is_file():
            if path.suffix in ('.mjs', '.js'):
                return [node, str(path)]
            if os.access(str(path), os.X_OK):
                return [str(path)]
    raise ValueError('No t3 CLI found. Supply --cli with an installed t3 executable.')


def check_origin(origin, allow_non_loopback):
    parsed = urllib.parse.urlsplit(origin)
    host = parsed.hostname
    try:
        loopback = host == 'localhost' or ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = False
    if (not host or parsed.scheme not in ('http', 'https') or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ('', '/')):
        raise ValueError('Runtime origin must be a plain HTTP(S) origin.')
    if not loopback and not allow_non_loopback:
        raise ValueError('Runtime origin is not loopback. For a verified server bound to its own '
                         'LAN/Tailnet address (office), pass --allow-non-loopback.')
    return parsed


class Client:
    def __init__(self, base, cli=None, node='node', allow_non_loopback=False):
        runtime_file = base / 'userdata/server-runtime.json'
        if not runtime_file.exists():
            raise ValueError(f'{runtime_file} not found: no running server for this base dir. '
                             'Pass --base-dir (office uses ~/.t3code).')
        self.origin = json.loads(runtime_file.read_text())['origin'].rstrip('/')
        self.parsed = check_origin(self.origin, allow_non_loopback)
        argv = discover_cli(base, cli, node) + [
            'auth', 'session', 'issue', '--base-dir', str(base), '--ttl', '5m',
            '--label', 't3-thread-management', '--token-only']
        for scope in SCOPES:
            argv += ['--scope', scope]
        result = subprocess.run(argv, text=True, capture_output=True, timeout=60)
        if result.returncode or not result.stdout.strip():
            raise ValueError('CLI authentication failed: ' + (result.stderr.strip() or 'no token'))
        self.token = result.stdout.strip()
        self.opener = urllib.request.build_opener(NoRedirect())
        self.sock = None
        self.buf = b''
        self.next_id = 1

    # --- HTTP (reads)
    def http(self, path):
        req = urllib.request.Request(self.origin + path, headers={
            'Authorization': 'Bearer ' + self.token, 'x-t3-orchestration-protocol': PROTOCOL})
        try:
            with self.opener.open(req, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'T3 HTTP {error.code} for {path}') from None

    def shell(self):
        return self.http('/api/orchestration/shell')

    def projection(self, thread_id):
        return self.http('/api/orchestration/threads/' + urllib.parse.quote(thread_id, safe=''))['projection']

    # --- WebSocket RPC (writes and server queries)
    def _connect(self):
        port = self.parsed.port or (443 if self.parsed.scheme == 'https' else 80)
        sock = socket.create_connection((self.parsed.hostname, port), timeout=120)
        if self.parsed.scheme == 'https':
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=self.parsed.hostname)
        key = base64.b64encode(os.urandom(16)).decode()
        sock.sendall((f'GET /ws?orchestrationProtocol={PROTOCOL} HTTP/1.1\r\n'
                      f'Host: {self.parsed.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                      f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n'
                      f'Authorization: Bearer {self.token}\r\n\r\n').encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError('WebSocket upgrade closed without a response.')
            buf += chunk
        head, self.buf = buf.split(b'\r\n\r\n', 1)
        status = head.split(b'\r\n')[0].decode(errors='replace')
        if ' 101 ' not in status:
            raise RuntimeError('WebSocket upgrade refused: ' + status + ' '
                               + self.buf.decode(errors='replace')[:300])
        self.sock = sock

    def _send_frame(self, opcode, data):
        mask = os.urandom(4)
        n = len(data)
        if n < 126:
            header = bytes([0x80 | opcode, 0x80 | n])
        elif n < 65536:
            header = bytes([0x80 | opcode, 0x80 | 126]) + struct.pack('>H', n)
        else:
            header = bytes([0x80 | opcode, 0x80 | 127]) + struct.pack('>Q', n)
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise RuntimeError('WebSocket closed by server.')
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _messages(self):
        data = b''
        while True:
            b0, b1 = self._exact(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack('>H', self._exact(2))[0]
            elif n == 127:
                n = struct.unpack('>Q', self._exact(8))[0]
            payload = self._exact(n)
            opcode = b0 & 0x0F
            if opcode == 0x9:
                self._send_frame(0xA, payload)
                continue
            if opcode == 0xA:
                continue
            if opcode == 0x8:
                raise RuntimeError('WebSocket closed: ' + payload[2:].decode(errors='replace'))
            data += payload
            if b0 & 0x80:
                decoded = json.loads(data)
                return decoded if isinstance(decoded, list) else [decoded]

    def rpc(self, tag, payload):
        """One Effect-RPC request over JSON frames; returns the success value or raises."""
        if self.sock is None:
            self._connect()
        request_id = str(self.next_id)
        self.next_id += 1
        self._send_frame(0x1, json.dumps({'_tag': 'Request', 'id': request_id, 'tag': tag,
                                          'payload': payload, 'headers': []}).encode())
        while True:
            for message in self._messages():
                if message.get('_tag') == 'Ping':
                    self._send_frame(0x1, b'{"_tag":"Pong"}')
                    continue
                if message.get('requestId') != request_id:
                    continue
                if message.get('_tag') == 'Exit':
                    exit_ = message['exit']
                    if exit_.get('_tag') == 'Success':
                        return exit_.get('value')
                    raise RuntimeError(f'{tag} failed: ' + json.dumps(exit_.get('cause', exit_))[:1500])
                if message.get('_tag') == 'Defect':
                    raise RuntimeError(f'{tag} defect: ' + json.dumps(message.get('defect'))[:1500])

    def close(self):
        if self.sock is not None:
            try:
                self._send_frame(0x8, struct.pack('>H', 1000))
                self.sock.close()
            except OSError:
                pass
            self.sock = None


# --- pure helpers (unit tested)

def command_id(request_id):
    """Stable command ID: re-sending the same request returns the same thread (resumed)."""
    if not request_id or not request_id.strip():
        raise ValueError('A nonempty --request-id is required.')
    return str(uuid.uuid5(REQUEST_NAMESPACE, request_id.strip()))


def resolve_project(projects, ref):
    ref = ref.strip()
    root = str(Path(ref).expanduser()) if ref.startswith(('/', '~')) else None
    matches = [p for p in projects if not p.get('deletedAt') and
               (p['id'] == ref or p.get('title') == ref or (root and p.get('workspaceRoot') == root))]
    if len(matches) != 1:
        found = ', '.join(f"{p.get('title')} ({p.get('workspaceRoot')})" for p in matches) or 'none'
        raise ValueError(f'Project {ref!r} must match exactly one project; matched: {found}.')
    return matches[0]


def parse_options(pairs):
    options = []
    for pair in pairs or []:
        key, sep, value = pair.partition('=')
        if not sep or not key.strip():
            raise ValueError(f'--option expects id=value, got {pair!r}.')
        options.append({'id': key.strip(), 'value': value.strip()})
    return options


def validate_selection(providers, instance_id, model, options):
    """Check provider/model/options against the live server.getConfig descriptors."""
    provider = next((p for p in providers if p.get('instanceId') == instance_id), None)
    if provider is None:
        raise ValueError(f'Provider instance {instance_id!r} not on this server; available: '
                         + ', '.join(p.get('instanceId', '?') for p in providers) + '.')
    if not provider.get('enabled') or provider.get('status') != 'ready':
        raise ValueError(f"Provider {instance_id!r} is {provider.get('status')} "
                         f"(enabled={provider.get('enabled')}); fix it in Settings > Providers.")
    models = provider.get('models') or []
    descriptor = next((m for m in models if m.get('slug') == model), None)
    if models and descriptor is None:
        raise ValueError(f'Model {model!r} not offered by {instance_id!r}; e.g. '
                         + ', '.join(m['slug'] for m in models[:8]) + '.')
    known = {d['id']: d for d in ((descriptor or {}).get('capabilities') or {}).get('optionDescriptors', [])}
    for option in options:
        d = known.get(option['id'])
        if d is None:
            raise ValueError(f"Option {option['id']!r} not supported by {instance_id}/{model}; "
                             f"supported: {', '.join(known) or 'none'}.")
        allowed = [o['id'] for o in d.get('options', [])]
        if d.get('type') == 'boolean':
            if option['value'] not in ('true', 'false'):
                raise ValueError(f"Option {option['id']!r} expects true or false.")
            option['value'] = option['value'] == 'true'
        elif allowed and option['value'] not in allowed:
            raise ValueError(f"Option {option['id']}={option['value']!r} invalid; allowed: {', '.join(allowed)}.")
    return {'instanceId': instance_id, 'model': model, **({'options': options} if options else {})}


def workspace_strategy(args):
    if args.worktree_from and args.existing_worktree:
        raise ValueError('Use either --worktree-from or --existing-worktree.')
    branch = {'branch': args.branch} if args.branch else {}
    if args.worktree_from:
        return {'type': 'worktree', 'baseRef': args.worktree_from,
                'startFromOrigin': not args.no_origin, **branch}
    if args.existing_worktree:
        return {'type': 'existing_worktree', 'worktreePath': args.existing_worktree, **branch}
    return {'type': 'root', **branch}


def setup_scripts(project, strategy):
    """The script the server runs unprompted when launchThread creates a worktree (first match only)."""
    if strategy.get('type') != 'worktree':
        return []
    first = next((s for s in project.get('scripts') or [] if s.get('runOnWorktreeCreate')), None)
    return [{k: first.get(k) for k in ('name', 'command', 'async')}] if first else []


def summarize(projection):
    thread = projection.get('thread') or {}
    runs = projection.get('runs') or []
    run = runs[-1] if runs else {}
    messages = [m for m in projection.get('messages') or [] if m.get('role') == 'assistant']
    last = (messages[-1].get('text') or '') if messages else ''
    return {
        'threadId': thread.get('id'), 'title': thread.get('title'), 'projectId': thread.get('projectId'),
        'modelSelection': thread.get('modelSelection'), 'runtimeMode': thread.get('runtimeMode'),
        'interactionMode': thread.get('interactionMode'), 'branch': thread.get('branch'),
        'worktreePath': thread.get('worktreePath'),
        'run': {k: run.get(k) for k in ('status', 'startedAt', 'completedAt', 'error')} if run else None,
        'lastAssistantMessage': last[:500],
    }


def started(summary):
    run = summary.get('run') or {}
    return bool(run.get('startedAt')) or run.get('status') in TERMINAL_RUN_STATES


# --- commands

def cmd_inspect(client, args):
    shell = client.shell()
    config = client.rpc('server.getConfig', {})
    providers = []
    for p in config.get('providers', []):
        entry = {k: p.get(k) for k in ('instanceId', 'driver', 'enabled', 'status')}
        models = p.get('models') or []
        entry['models'] = [m['slug'] for m in models] if args.models else len(models)
        if args.models:
            entry['options'] = {m['slug']: {d['id']: [o['id'] for o in d.get('options', [])] or d.get('type')
                                            for d in (m.get('capabilities') or {}).get('optionDescriptors', [])}
                                for m in models}
        providers.append(entry)
    return {'origin': client.origin, 'providers': providers,
            'projects': [{k: p.get(k) for k in ('id', 'title', 'workspaceRoot')}
                         for p in shell['projects'] if not p.get('deletedAt')],
            'activeThreads': len([t for t in shell['threads'] if not t.get('archivedAt')])}


def cmd_search(client, args):
    return client.rpc('orchestration.searchThreads', {'query': args.query})


def cmd_status(client, args):
    return summarize(client.projection(args.thread_id))


def cmd_delete(client, args):
    client.rpc('orchestration.dispatchCommand', {'type': 'thread.delete', 'commandId': str(uuid.uuid4()),
                                                 'threadId': args.thread_id})
    return {'deleted': args.thread_id, 'note': 'Worktree and branch are left on disk.'}


def cmd_start(client, args, base):
    if not args.title.strip():
        raise ValueError('--title must be nonempty.')
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding='utf-8')
    else:
        prompt = args.prompt
    if prompt is not None and not prompt.strip():
        raise ValueError('Prompt is empty; use --no-message for an empty thread.')
    shell = client.shell()
    try:
        project = resolve_project(shell['projects'], args.project)
    except ValueError:
        if not args.add_project:
            raise
        root = str(Path(args.project).expanduser().resolve(strict=True))
        subprocess.run(discover_cli(base, args.cli, args.node or 'node') + [
            'project', 'add', '--base-dir', str(base), root], check=True, capture_output=True, timeout=60)
        project = resolve_project(client.shell()['projects'], root)
    if args.source_thread:
        source = client.projection(args.source_thread)['thread']
        selection = source['modelSelection']
        runtime_mode = args.runtime_mode or source.get('runtimeMode')
    else:
        if not args.provider or not args.model:
            raise ValueError('Supply --provider and --model, or --source-thread to inherit them.')
        providers = client.rpc('server.getConfig', {}).get('providers', [])
        selection = validate_selection(providers, args.provider, args.model, parse_options(args.option))
        runtime_mode = args.runtime_mode
    payload = {
        'commandId': command_id(args.request_id), 'creationSource': 'server',
        'projectId': project['id'], 'title': args.title.strip(), 'modelSelection': selection,
        'runtimeMode': runtime_mode or 'full-access', 'interactionMode': args.interaction_mode,
        'workspaceStrategy': workspace_strategy(args),
    }
    if prompt is not None:
        payload['initialMessage'] = {'text': prompt, 'attachments': []}
    if args.dry_run:
        return {'dryRun': True, 'project': {k: project.get(k) for k in ('id', 'title', 'workspaceRoot')},
                'setupScriptsThatWillRun': setup_scripts(project, payload['workspaceStrategy']),
                'payload': {**payload, 'initialMessage': {'chars': len(prompt or '')}}}
    result = client.rpc('orchestration.launchThread', payload)
    thread_id = result['threadId']
    summary = summarize(result['projection'])
    deadline = time.time() + args.timeout
    while args.wait != 'none' and prompt is not None and time.time() < deadline:
        if args.wait == 'started' and started(summary):
            break
        if args.wait == 'completed' and (summary.get('run') or {}).get('status') in TERMINAL_RUN_STATES:
            break
        time.sleep(3)
        summary = summarize(client.projection(thread_id))
    return {'resumed': result.get('resumed'), 'commandId': payload['commandId'], **summary,
            'waitSatisfied': args.wait == 'none' or prompt is None or (
                started(summary) if args.wait == 'started'
                else (summary.get('run') or {}).get('status') in TERMINAL_RUN_STATES)}


# --- SSH transport

def run_remote(args, argv):
    """Stream this file and the arguments over SSH; auth stays on the destination."""
    if not args.host or args.host.startswith('-') or any(c.isspace() for c in args.host):
        raise ValueError('Use an SSH host alias or user@host, not SSH options.')
    forwarded = []
    skip = False
    for i, item in enumerate(argv):
        if skip:
            skip = False
            continue
        if item == '--host':
            skip = True
            continue
        if item.startswith('--host='):
            continue
        if item == '--prompt-file':
            forwarded += ['--prompt', Path(argv[i + 1]).read_text(encoding='utf-8')]
            skip = True
            continue
        forwarded.append(item)
    # Only this constant loader is interpreted by the remote shell; all input travels as JSON on stdin.
    loader = ('import json,sys; p=json.load(sys.stdin); sys.argv=["t3_threads.py"]+p["args"]; '
              'exec(compile(p["code"],"t3_threads.py","exec"),{"__name__":"__main__"})')
    payload = json.dumps({'code': Path(__file__).read_text(), 'args': forwarded})
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '--', args.host,
                             'python3 -c ' + shlex.quote(loader)],
                            input=payload, text=True, capture_output=True, timeout=args.timeout + 120)
    if result.returncode:
        raise RuntimeError('Remote invocation failed; check status with the same --request-id before '
                           'retrying.\n' + result.stderr.strip())
    return json.loads(result.stdout)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--host', help='SSH destination (lab, office); runs there with its own auth')
    parser.add_argument('--base-dir', help='T3 data dir on the destination (default $T3CODE_HOME or ~/.t3; office: ~/.t3code)')
    parser.add_argument('--cli', help='t3 executable on the destination')
    parser.add_argument('--node', help='Node for a .mjs/.js CLI')
    parser.add_argument('--allow-non-loopback', action='store_true',
                        help="Use the runtime file's LAN/Tailnet origin (office)")
    parser.add_argument('--timeout', type=int, default=180, help='Seconds to wait for --wait (default 180)')
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect', help='Providers, models and projects on the server')
    inspect.add_argument('--models', action='store_true', help='List model slugs and option values')
    search = commands.add_parser('search', help='Full-text search over thread messages')
    search.add_argument('--query', required=True)
    status = commands.add_parser('status', help='Run state and last reply of a thread')
    status.add_argument('--thread-id', required=True)
    delete = commands.add_parser('delete', help='Delete a thread (e.g. a smoke test); leaves its worktree')
    delete.add_argument('--thread-id', required=True)
    start = commands.add_parser('start', help='Create a thread and send its first message')
    start.add_argument('--project', required=True, help='Project id, exact title, or workspace root')
    start.add_argument('--add-project', action='store_true', help='Register --project path if missing')
    start.add_argument('--title', required=True)
    start.add_argument('--request-id', required=True,
                       help='Stable per task; retries with the same id return the same thread')
    message = start.add_mutually_exclusive_group(required=True)
    message.add_argument('--prompt-file', help='UTF-8 task file on the invoking machine')
    message.add_argument('--prompt', help='Inline task text')
    message.add_argument('--no-message', action='store_true', help='Empty thread (e.g. iPhone handoff)')
    start.add_argument('--source-thread', help='Inherit model selection and runtime mode from this thread')
    start.add_argument('--provider', help='Provider instance id from inspect (codex, claudeAgent, pi, ...)')
    start.add_argument('--model', help='Model slug from inspect --models')
    start.add_argument('--option', action='append', help='Model option id=value, repeatable')
    start.add_argument('--runtime-mode', choices=['approval-required', 'auto-accept-edits', 'auto', 'full-access'])
    start.add_argument('--interaction-mode', choices=['default', 'plan'], default='default')
    start.add_argument('--worktree-from', metavar='REF', help='Server creates a new worktree from REF')
    start.add_argument('--no-origin', action='store_true', help='With --worktree-from: use local REF, not origin/REF')
    start.add_argument('--existing-worktree', metavar='PATH', help='Attach an existing worktree')
    start.add_argument('--branch', help='Branch name for the worktree/root')
    start.add_argument('--wait', choices=['none', 'started', 'completed'], default='started')
    start.add_argument('--dry-run', action='store_true', help='Resolve and validate; send nothing')
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(argv)
    if args.host:
        print(json.dumps(run_remote(args, argv), indent=2))
        return
    base = Path(args.base_dir or os.environ.get('T3CODE_HOME') or '~/.t3').expanduser().resolve()
    client = Client(base, args.cli, args.node or 'node', args.allow_non_loopback)
    try:
        if args.command == 'start':
            result = cmd_start(client, args, base)
        else:
            result = {'inspect': cmd_inspect, 'search': cmd_search, 'status': cmd_status,
                      'delete': cmd_delete}[args.command](client, args)
    finally:
        client.close()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        sys.exit(1)
