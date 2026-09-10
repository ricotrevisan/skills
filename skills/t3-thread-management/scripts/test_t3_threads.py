import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from t3_threads import run_remote, start


class FakeClient:
    def __init__(self, fail=None):
        self.data = {'projects': [], 'threads': [{
            'id': 'source', 'projectId': 'other', 'title': 'Source',
            'modelSelection': {'provider': 'codex', 'model': 'inherited'},
            'runtimeMode': 'full-access'}]}
        self.calls = []
        self.fail = fail

    def snapshot(self):
        return copy.deepcopy(self.data)

    def dispatch(self, command):
        self.calls.append(command)
        if command['type'] == 'project.create':
            self.data['projects'].append({'id': command['projectId'],
                'workspaceRoot': command['workspaceRoot']})
        elif command['type'] == 'thread.create':
            self.data['threads'].append({**command, 'id': command['threadId']})
        else:
            thread = next(t for t in self.data['threads'] if t['id'] == command['threadId'])
            thread['session'] = {'status': 'running', 'activeTurnId': 'turn'}
        if command['type'] == self.fail:
            raise TimeoutError('Response lost after write')
        return {'sequence': len(self.calls)}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        prompt = root / 'task.txt'
        prompt.write_text('Build the harness. Preserve the existing checkout.')
        self.args = argparse.Namespace(workspace=str(root), worktree=None, branch=None,
            prompt_file=str(prompt), receipt=str(root / 'receipt.json'),
            title='Build harness', source_thread='source')

    def test_creates_project_then_thread_then_turn_and_inherits_settings(self):
        client = FakeClient()
        result = start(client, self.args)
        self.assertEqual([c['type'] for c in client.calls],
            ['project.create', 'thread.create', 'thread.turn.start'])
        self.assertEqual(client.calls[-1]['modelSelection'], client.data['threads'][0]['modelSelection'])
        self.assertEqual(client.calls[-1]['message']['text'], Path(self.args.prompt_file).read_text())
        self.assertEqual(result['thread']['session']['status'], 'running')
        start(client, self.args)
        self.assertEqual(len(client.calls), 3)

    def test_lost_response_never_replays_mutation(self):
        for stage in ['project.create', 'thread.create', 'thread.turn.start']:
            with self.subTest(stage=stage):
                self.args.receipt = str(Path(self.temp.name) / (stage + '.json'))
                client = FakeClient(fail=stage)
                with self.assertRaises(TimeoutError):
                    start(client, self.args)
                count = len(client.calls)
                start(client, self.args)
                self.assertEqual(len(client.calls), count)

    def test_reuses_project_and_attaches_worktree(self):
        client = FakeClient()
        client.data['projects'] = [{'id': 'existing', 'workspaceRoot': self.args.workspace}]
        self.args.worktree = self.args.workspace
        self.args.branch = 'test/harness'
        result = start(client, self.args)
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(result['thread']['projectId'], 'existing')
        self.assertEqual(result['thread']['worktreePath'], self.args.worktree)

    def test_duplicate_title_and_changed_receipt_are_rejected(self):
        client = FakeClient()
        start(client, self.args)
        original = self.args.receipt
        self.args.receipt = str(Path(self.temp.name) / 'another.json')
        with self.assertRaisesRegex(ValueError, 'thread.*exists'):
            start(client, self.args)
        self.args.receipt = original
        self.args.title = 'Different work'
        with self.assertRaisesRegex(ValueError, 'different request'):
            start(client, self.args)
        self.assertEqual(len(client.calls), 3)

    def test_invalid_worktree_pair_does_not_write(self):
        client = FakeClient()
        self.args.branch = 'test/harness'
        with self.assertRaisesRegex(ValueError, 'together'):
            start(client, self.args)
        self.assertEqual(client.calls, [])

    def remote_args(self):
        return argparse.Namespace(**vars(self.args), host='office', base_dir=None,
            cli=None, node=None, allow_non_loopback=False, command='start', prompt=None)

    def test_remote_transfer_preserves_prompt_and_target_paths_without_shell_interpolation(self):
        args = self.remote_args()
        text = "say 'hello'\n$(touch /tmp/unwanted) `whoami` $HOME"
        Path(args.prompt_file).write_text(text)
        args.workspace = '/remote/project with spaces'
        args.receipt = '/remote/receipt.json'
        with patch('t3_threads.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, '{"ok": true}', '')
            self.assertEqual(run_remote(args), {'ok': True})
        command = run.call_args.args[0]
        self.assertEqual(command[-2], 'office')
        self.assertIn('BatchMode=yes', command)
        self.assertNotIn(text, ' '.join(command))
        payload = json.loads(run.call_args.kwargs['input'])
        remote = payload['args']
        self.assertEqual(remote[remote.index('--prompt') + 1], text)
        self.assertIn('/remote/project with spaces', remote)
        self.assertIn('/remote/receipt.json', remote)
        self.assertNotIn('--host', remote)
        self.assertNotIn('--base-dir', remote)
        self.assertNotIn('--prompt-file', remote)
        # Execute the actual SSH loader locally with harmless code to verify that
        # its stdin protocol preserves arguments without interpreting task text.
        payload['code'] = 'import json,sys; print(json.dumps(sys.argv[1:]))'
        out = subprocess.run(command[-1], shell=True, input=json.dumps(payload),
                             text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(out.stdout), remote)

    def test_remote_inline_prompt_and_destination_overrides(self):
        args = self.remote_args()
        args.prompt_file = None
        args.prompt = 'say hello'
        args.base_dir = '/Users/rico/.t3code'
        args.cli = '/remote/bin.ts'
        args.node = '/remote/node'
        args.allow_non_loopback = True
        with patch('t3_threads.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, '{}', '')
            run_remote(args)
        remote = json.loads(run.call_args.kwargs['input'])['args']
        self.assertEqual(remote[:7], ['--base-dir', args.base_dir, '--cli', args.cli,
                                     '--node', args.node, '--allow-non-loopback'])
        self.assertEqual(remote[-2:], ['--prompt', 'say hello'])

    def test_remote_ssh_failure_propagates_without_retry(self):
        with patch('t3_threads.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([], 255, '', 'Connection closed')
            with self.assertRaisesRegex(RuntimeError, 'inspect the destination'):
                run_remote(self.remote_args())
            self.assertEqual(run.call_count, 1)

    def test_remote_rejects_option_as_host(self):
        args = self.remote_args()
        args.host = '-oProxyCommand=bad'
        with patch('t3_threads.subprocess.run') as run:
            with self.assertRaises(ValueError):
                run_remote(args)
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
