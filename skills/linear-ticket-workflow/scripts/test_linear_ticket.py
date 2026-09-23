#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

MODULE_PATH = pathlib.Path(__file__).with_name("linear_ticket.py")
spec = importlib.util.spec_from_file_location("linear_ticket", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"could not load {MODULE_PATH}")
linear_ticket = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = linear_ticket
spec.loader.exec_module(linear_ticket)


def issue(state_name="Todo", state_type="unstarted"):
    return {
        "id": "issue-1",
        "identifier": "DEF-123",
        "title": "Test",
        "url": "https://linear.app/x/issue/DEF-123",
        "state": {"id": "current", "name": state_name, "type": state_type},
        "team": {
            "id": "team-1",
            "key": "DEF",
            "states": {"nodes": [
                {"id": "progress", "name": "In Progress", "type": "started", "position": 1},
                {"id": "review", "name": "In Review", "type": "started", "position": 2},
                {"id": "done", "name": "Done", "type": "completed", "position": 3},
            ]},
        },
        "comments": {"nodes": []},
    }


class StateSelectionTests(unittest.TestCase):
    def test_start_avoids_review_state(self):
        self.assertEqual(linear_ticket.choose_state(issue(), "start")["id"], "progress")

    def test_review_uses_existing_review_state(self):
        self.assertEqual(linear_ticket.choose_state(issue(), "review")["id"], "review")

    def test_block_is_optional(self):
        self.assertIsNone(linear_ticket.choose_state(issue(), "block"))

    def test_done_uses_completed_state(self):
        self.assertEqual(linear_ticket.choose_state(issue(), "done")["id"], "done")


class CommentTests(unittest.TestCase):
    def test_done_requires_evidence_at_parse_time(self):
        with self.assertRaises(SystemExit):
            linear_ticket.parser().parse_args(["done", "DEF-123"])

    def test_marker_is_stable(self):
        first = linear_ticket.marker("review", ["https://example/pr/1"])
        second = linear_ticket.marker("review", ["https://example/pr/1"])
        self.assertEqual(first, second)

    def test_duplicate_comment_is_skipped(self):
        token = linear_ticket.marker("review", ["pr"])
        current = issue()
        current["comments"]["nodes"] = [{"body": f"already there {token}"}]
        self.assertFalse(linear_ticket.add_comment(object(), current, "body", token))


class TransportTests(unittest.TestCase):
    @patch.object(linear_ticket.shutil, "which", return_value=None)
    @patch.object(linear_ticket, "run")
    def test_auto_uses_ssh_fallback(self, mocked_run, _mocked_which):
        mocked_run.return_value.returncode = 0
        mocked_run.return_value.stdout = '{"data":{"ok":true}}'
        mocked_run.return_value.stderr = ""
        result = linear_ticket.Transport(mode="auto", host="lab").call({"query": "query { ok }"})
        self.assertEqual(result["data"]["ok"], True)
        command = mocked_run.call_args.args[0]
        self.assertEqual(command[:4], ["ssh", "-o", "BatchMode=yes", "lab"])


if __name__ == "__main__":
    unittest.main()
