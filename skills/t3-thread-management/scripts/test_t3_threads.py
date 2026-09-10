import argparse
import copy
from pathlib import Path
import tempfile
import unittest

from t3_threads import start


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


if __name__ == '__main__':
    unittest.main()
