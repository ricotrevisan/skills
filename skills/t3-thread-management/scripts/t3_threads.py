#!/usr/bin/env python3
"""Start T3 threads using CLI auth and the local orchestration API."""
import argparse
import datetime
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def discover_cli(base, explicit=None):
    candidates = [Path(explicit).expanduser()] if explicit else []
    if not explicit:
        if found := shutil.which('t3'):
            candidates.append(Path(found))
        candidates += sorted((base / 'runtime/versions').glob('*/node_modules/.bin/t3'),
                             key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        if path.is_file():
            if path.suffix in ('.mjs', '.js'):
                return ['node', str(path)]
            if os.access(path, os.X_OK):
                return [str(path)]
    raise ValueError('No CLI found. Supply --cli with an installed t3 or built bin.mjs.')


class Client:
    def __init__(self, base, cli=None):
        runtime = json.loads((base / 'userdata/server-runtime.json').read_text())
        self.origin = runtime['origin'].rstrip('/')
        parsed = urllib.parse.urlsplit(self.origin)
        host = parsed.hostname
        try:
            loopback = host == 'localhost' or ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = False
        if (not loopback or parsed.scheme not in ('http', 'https') or
                parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path):
            raise ValueError('Runtime origin must be a loopback HTTP(S) origin.')
        result = subprocess.run(discover_cli(base, cli) + [
            'auth', 'session', 'issue', '--base-dir', str(base), '--ttl', '5m',
            '--label', 't3-thread-management', '--token-only'],
            text=True, capture_output=True, timeout=30)
        if result.returncode or not result.stdout.strip():
            raise ValueError('CLI authentication failed. Check the selected CLI and auth session issue --help.')
        self.token = result.stdout.strip()
        self.opener = urllib.request.build_opener(NoRedirect())

    def api(self, path, data=None):
        req = urllib.request.Request(self.origin + path,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            with self.opener.open(req, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'T3 HTTP {error.code}; inspect receipt/status before retrying.') from None

    def snapshot(self):
        return self.api('/api/orchestration/snapshot')

    def dispatch(self, command):
        return self.api('/api/orchestration/dispatch', command)


def thread_status(snapshot, tid):
    thread = next((t for t in snapshot['threads'] if t['id'] == tid), None)
    if thread is None:
        return {'id': tid, 'found': False}
    return {key: thread.get(key) for key in
            ('id', 'projectId', 'title', 'branch', 'worktreePath', 'session', 'latestTurn')}


def start(client, args):
    workspace = str(Path(args.workspace).expanduser().resolve(strict=True))
    if not Path(workspace).is_dir():
        raise ValueError('Workspace must be a directory.')
    worktree = str(Path(args.worktree).expanduser().resolve(strict=True)) if args.worktree else None
    if bool(worktree) != bool(args.branch):
        raise ValueError('Supply --branch and --worktree together.')
    prompt = Path(args.prompt_file).read_text(encoding='utf-8')
    if not prompt.strip() or not args.title.strip():
        raise ValueError('Prompt and title must be nonempty.')
    request = dict(workspace=workspace, worktree=worktree, branch=args.branch,
                   title=args.title, source=args.source_thread, prompt=prompt)
    fingerprint = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    receipt = Path(args.receipt).expanduser()
    snapshot = client.snapshot()
    if receipt.exists():
        saved = json.loads(receipt.read_text())
        if saved['fingerprint'] != fingerprint:
            raise ValueError('Receipt belongs to a different request. Inspect it before proceeding.')
        return {'receipt': saved, 'thread': thread_status(snapshot, saved['threadId']),
                'note': 'Existing receipt: no writes performed. Inspect status before any recovery.'}
    source = next(t for t in snapshot['threads'] if t['id'] == args.source_thread)
    project = next((p for p in snapshot['projects'] if
                    p['workspaceRoot'] == workspace and not p.get('deletedAt')), None)
    pid = project['id'] if project else str(uuid.uuid4())
    if any(t['projectId'] == pid and t['title'] == args.title and not t.get('deletedAt')
           for t in snapshot['threads']):
        raise ValueError('A thread with this project/title exists. Inspect before starting more work.')
    saved = dict(fingerprint=fingerprint, projectId=pid, threadId=str(uuid.uuid4()),
                 messageId=str(uuid.uuid4()), stage='prepared',
                 commandIds={key: str(uuid.uuid4()) for key in ('project', 'thread', 'start')})
    # Exclusive creation prevents concurrent invocations sharing a receipt.
    with receipt.open('x', encoding='utf-8') as f:
        json.dump(saved, f, indent=2)
    def dispatch(stage, body):
        body['commandId'] = saved['commandIds'][stage]
        client.dispatch(body)
        saved['stage'] = stage + '-accepted'
        temporary = receipt.with_name(receipt.name + '.tmp')
        temporary.write_text(json.dumps(saved, indent=2))
        temporary.replace(receipt)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    if not project:
        dispatch('project', dict(type='project.create', projectId=pid,
                 title=Path(workspace).name, workspaceRoot=workspace, createdAt=now))
    settings = {key: source[key] for key in ('modelSelection', 'runtimeMode')}
    dispatch('thread', dict(type='thread.create', threadId=saved['threadId'], projectId=pid,
             title=args.title, branch=args.branch, worktreePath=worktree,
             interactionMode='default', createdAt=now, **settings))
    dispatch('start', dict(type='thread.turn.start', threadId=saved['threadId'],
             message=dict(messageId=saved['messageId'], role='user', text=prompt, attachments=[]),
             interactionMode='default', createdAt=now, **settings))
    return {'receipt': saved, 'thread': thread_status(client.snapshot(), saved['threadId'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-dir', default=os.environ.get('T3CODE_HOME', '~/.t3'))
    parser.add_argument('--cli', help='Installed t3 executable or built bin.mjs')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inspect')
    status = commands.add_parser('status')
    status.add_argument('--thread-id', required=True)
    create = commands.add_parser('start')
    for name in ('source-thread', 'workspace', 'title', 'prompt-file', 'receipt'):
        create.add_argument('--' + name, required=True)
    create.add_argument('--branch')
    create.add_argument('--worktree')
    args = parser.parse_args()
    client = Client(Path(args.base_dir).expanduser().resolve(), args.cli)
    if args.command == 'start':
        result = start(client, args)
    elif args.command == 'status':
        result = thread_status(client.snapshot(), args.thread_id)
    else:
        snapshot = client.snapshot()
        result = dict(origin=client.origin,
            projects=[{k: p.get(k) for k in ('id', 'title', 'workspaceRoot')}
                      for p in snapshot['projects'] if not p.get('deletedAt')],
            threads=[{k: t.get(k) for k in ('id', 'projectId', 'title')}
                     for t in snapshot['threads'] if not t.get('deletedAt') and not t.get('archivedAt')])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, StopIteration, KeyError, subprocess.SubprocessError) as error:
        print(f'Error: {error or "Source thread or required API field not found."}', file=sys.stderr)
        sys.exit(1)
