import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import t3_threads as t3

PROVIDERS = [
    {'instanceId': 'codex', 'driver': 'codex', 'enabled': True, 'status': 'ready', 'models': [
        {'slug': 'gpt-6-astra', 'capabilities': {'optionDescriptors': [
            {'id': 'reasoningEffort', 'type': 'select', 'options': [{'id': 'low'}, {'id': 'medium'}]},
            {'id': 'fastMode', 'type': 'boolean'}]}}]},
    {'instanceId': 'grok', 'driver': 'grok', 'enabled': False, 'status': 'disabled', 'models': []},
    {'instanceId': 'acp', 'driver': 'acpRegistry', 'enabled': True, 'status': 'ready', 'models': []},
]
PROJECTS = [
    {'id': 'p1', 'title': 'devops', 'workspaceRoot': '/home/rico/devops'},
    {'id': 'p2', 'title': 'dup', 'workspaceRoot': '/a'},
    {'id': 'p3', 'title': 'dup', 'workspaceRoot': '/b'},
    {'id': 'p4', 'title': 'gone', 'workspaceRoot': '/c', 'deletedAt': '2026-01-01'},
]


def ns(**kw):
    base = dict(worktree_from=None, existing_worktree=None, branch=None, no_origin=False)
    base.update(kw)
    return argparse.Namespace(**base)


class PureTests(unittest.TestCase):
    def test_command_id_is_stable_and_required(self):
        self.assertEqual(t3.command_id('discord-1'), t3.command_id(' discord-1 '))
        self.assertNotEqual(t3.command_id('discord-1'), t3.command_id('discord-2'))
        with self.assertRaises(ValueError):
            t3.command_id('  ')

    def test_resolve_project(self):
        self.assertEqual(t3.resolve_project(PROJECTS, 'devops')['id'], 'p1')
        self.assertEqual(t3.resolve_project(PROJECTS, 'p1')['id'], 'p1')
        self.assertEqual(t3.resolve_project(PROJECTS, '/home/rico/devops')['id'], 'p1')
        for ref in ('dup', 'gone', 'missing'):
            with self.assertRaises(ValueError):
                t3.resolve_project(PROJECTS, ref)

    def test_parse_options(self):
        self.assertEqual(t3.parse_options(['reasoningEffort=low']), [{'id': 'reasoningEffort', 'value': 'low'}])
        with self.assertRaises(ValueError):
            t3.parse_options(['noequals'])

    def test_validate_selection(self):
        sel = t3.validate_selection(PROVIDERS, 'codex', 'gpt-6-astra',
                                    t3.parse_options(['reasoningEffort=medium', 'fastMode=true']))
        self.assertEqual(sel, {'instanceId': 'codex', 'model': 'gpt-6-astra', 'options': [
            {'id': 'reasoningEffort', 'value': 'medium'}, {'id': 'fastMode', 'value': True}]})
        self.assertNotIn('options', t3.validate_selection(PROVIDERS, 'codex', 'gpt-6-astra', []))
        # Providers without a model list (ACP before first session) accept any slug.
        self.assertEqual(t3.validate_selection(PROVIDERS, 'acp', 'anything', [])['model'], 'anything')
        bad = [('nope', 'gpt-6-astra', []), ('grok', 'grok-build', []), ('codex', 'gpt-0', []),
               ('codex', 'gpt-6-astra', [{'id': 'reasoningEffort', 'value': 'ultra'}]),
               ('codex', 'gpt-6-astra', [{'id': 'serviceTier', 'value': 'default'}]),
               ('codex', 'gpt-6-astra', [{'id': 'fastMode', 'value': 'yes'}])]
        for args in bad:
            with self.assertRaises(ValueError, msg=args):
                t3.validate_selection(PROVIDERS, *args)

    def test_workspace_strategy(self):
        self.assertEqual(t3.workspace_strategy(ns()), {'type': 'root'})
        self.assertEqual(t3.workspace_strategy(ns(worktree_from='main', branch='t3code/x')),
                         {'type': 'worktree', 'baseRef': 'main', 'startFromOrigin': True, 'branch': 't3code/x'})
        self.assertFalse(t3.workspace_strategy(ns(worktree_from='main', no_origin=True))['startFromOrigin'])
        self.assertEqual(t3.workspace_strategy(ns(existing_worktree='/w')),
                         {'type': 'existing_worktree', 'worktreePath': '/w'})
        with self.assertRaises(ValueError):
            t3.workspace_strategy(ns(worktree_from='main', existing_worktree='/w'))

    def test_summarize_and_started(self):
        projection = {'thread': {'id': 't', 'title': 'T', 'branch': 'b'},
                      'runs': [{'status': 'completed', 'startedAt': 'x', 'completedAt': 'y'}],
                      'messages': [{'role': 'user', 'text': 'hi'}, {'role': 'assistant', 'text': 'hello'}]}
        s = t3.summarize(projection)
        self.assertEqual((s['threadId'], s['lastAssistantMessage'], s['run']['status']), ('t', 'hello', 'completed'))
        self.assertTrue(t3.started(s))
        self.assertFalse(t3.started(t3.summarize({'thread': {}, 'runs': [], 'messages': []})))
        self.assertFalse(t3.started({'run': {'status': 'waiting', 'startedAt': None}}))

    def test_setup_scripts_only_for_new_worktrees(self):
        project = {'scripts': [
            {'name': 'dev', 'command': 'mix phx.server', 'runOnWorktreeCreate': False},
            {'name': 'setup', 'command': 'mix setup', 'async': True, 'runOnWorktreeCreate': True},
            {'name': 'second', 'command': 'never runs', 'runOnWorktreeCreate': True}]}
        self.assertEqual(t3.setup_scripts(project, {'type': 'worktree', 'baseRef': 'main'}),
                         [{'name': 'setup', 'command': 'mix setup', 'async': True}])
        self.assertEqual(t3.setup_scripts(project, {'type': 'root'}), [])
        self.assertEqual(t3.setup_scripts({}, {'type': 'worktree'}), [])

    def test_check_origin(self):
        t3.check_origin('http://127.0.0.1:3773', False)
        t3.check_origin('http://100.124.111.25:8789', True)
        for origin, allow in (('http://100.124.111.25:8789', False), ('http://127.0.0.1:3773/x', True),
                              ('ftp://127.0.0.1', True)):
            with self.assertRaises(ValueError, msg=origin):
                t3.check_origin(origin, allow)


class RemoteTests(unittest.TestCase):
    def test_remote_forwards_args_and_inlines_prompt_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp, 'task.txt')
            task.write_text("quote ' $(rm -rf /) \n line2", encoding='utf-8')
            argv = ['--host', 'office', '--base-dir', '~/.t3code', '--allow-non-loopback', 'start',
                    '--project', 'devops', '--title', 'T', '--request-id', 'r1', '--prompt-file', str(task),
                    '--provider', 'codex', '--model', 'gpt-6-astra']
            args = t3.build_parser().parse_args(argv)
            seen = {}

            def fake_run(cmd, input, **kw):
                seen['cmd'], seen['payload'] = cmd, json.loads(input)
                return type('R', (), {'returncode': 0, 'stdout': '{"ok": true}', 'stderr': ''})()

            with patch('subprocess.run', fake_run):
                self.assertEqual(t3.run_remote(args, argv), {'ok': True})
        forwarded = seen['payload']['args']
        self.assertNotIn('--host', forwarded)
        self.assertNotIn('--prompt-file', forwarded)
        self.assertEqual(forwarded[forwarded.index('--prompt') + 1], task.read_text() if task.exists() else
                         "quote ' $(rm -rf /) \n line2")
        self.assertEqual(seen['cmd'][:6], ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '--'])
        self.assertEqual(seen['cmd'][6], 'office')
        self.assertNotIn('rm -rf', seen['cmd'][7])

    def test_rejects_ssh_options_as_host(self):
        argv = ['--host=-oProxyCommand=x', 'inspect']
        with self.assertRaises(ValueError):
            t3.run_remote(t3.build_parser().parse_args(argv), argv)


if __name__ == '__main__':
    unittest.main()
