#!/usr/bin/env python3
"""Keep a Linear issue truthful while an autonomous agent works on it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

MARKER_PREFIX = "<!-- linear-ticket-workflow:"
REVIEW_RE = re.compile(r"\b(review|verification|qa|testing)\b", re.I)
BLOCKED_RE = re.compile(r"\b(blocked|waiting|paused)\b", re.I)


class LinearError(RuntimeError):
    pass


def run(command: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, input=input_text, text=True, capture_output=True, check=False)


@dataclass
class Transport:
    mode: str = "auto"
    host: str = "lab"
    slug: str = "linear"
    account: str | None = None

    def _local_available(self) -> bool:
        return shutil.which("loggie") is not None

    def call(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.account:
            raise LinearError(
                "no Loggie account configured; set loggieAccount in .linear-ticket.json "
                "or pass --loggie-account"
            )
        body = json.dumps(payload, separators=(",", ":"))
        loggie_command = ["loggie-account", self.account, "call", self.slug, "POST", "/", "-b", body]
        if self.mode == "local" or (self.mode == "auto" and self._local_available()):
            command = loggie_command
        elif self.mode in {"auto", "ssh"}:
            remote = " ".join(
                shlex.quote(part)
                for part in loggie_command
            )
            command = ["ssh", "-o", "BatchMode=yes", self.host, remote]
        else:
            raise LinearError(f"unsupported transport: {self.mode}")

        result = run(command)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise LinearError(f"Loggie call failed ({result.returncode}): {detail}")
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise LinearError(f"Loggie returned non-JSON output: {result.stdout[:300]!r}") from exc

        # Loggie normally returns the upstream GraphQL body directly, but tolerate a
        # single common response wrapper without guessing through arbitrary shapes.
        if isinstance(response, dict) and "body" in response and not ({"data", "errors"} & response.keys()):
            wrapped = response["body"]
            if isinstance(wrapped, str):
                response = json.loads(wrapped)
            elif isinstance(wrapped, dict):
                response = wrapped

        if not isinstance(response, dict):
            raise LinearError("Linear response was not a JSON object")
        if response.get("errors"):
            raise LinearError("Linear GraphQL error: " + json.dumps(response["errors"], ensure_ascii=False))
        return response


def graphql(transport: Transport, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    response = transport.call({"query": query, "variables": variables})
    data = response.get("data")
    if not isinstance(data, dict):
        raise LinearError("Linear response did not contain data")
    return data


ISSUE_QUERY = """
query IssueForAgent($id: String!) {
  organization { name }
  issue(id: $id) {
    id identifier title url
    state { id name type }
    project { id name }
    team { id key name states { nodes { id name type position } } }
    comments(first: 100) { nodes { id body } }
  }
}
"""

UPDATE_QUERY = """
mutation UpdateAgentIssue($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue { id identifier state { id name type } }
  }
}
"""

COMMENT_QUERY = """
mutation CommentOnAgentIssue($input: CommentCreateInput!) {
  commentCreate(input: $input) { success comment { id body } }
}
"""


def fetch_issue(transport: Transport, issue_id: str) -> dict[str, Any]:
    data = graphql(transport, ISSUE_QUERY, {"id": issue_id})
    issue = data.get("issue")
    if not isinstance(issue, dict):
        raise LinearError(f"Linear issue not found: {issue_id}")
    issue["organization"] = data.get("organization")
    return issue


def find_config(start: pathlib.Path | None = None) -> tuple[pathlib.Path | None, dict[str, Any]]:
    current = (start or pathlib.Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / ".linear-ticket.json"
        if candidate.is_file():
            try:
                value = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise LinearError(f"invalid {candidate}: {exc}") from exc
            if not isinstance(value, dict):
                raise LinearError(f"invalid {candidate}: expected a JSON object")
            return candidate, value
        if (directory / ".git").exists():
            break
    return None, {}


def validate_routing(issue: dict[str, Any], config: dict[str, Any], config_path: pathlib.Path | None) -> None:
    source = str(config_path) if config_path else "routing configuration"
    expected_workspace = config.get("linearWorkspace")
    actual_workspace = (issue.get("organization") or {}).get("name")
    if expected_workspace and actual_workspace != expected_workspace:
        raise LinearError(
            f"{source} expects Linear workspace {expected_workspace!r}, "
            f"but {issue['identifier']} resolved in {actual_workspace!r}"
        )
    expected_project = config.get("linearProject")
    actual_project = (issue.get("project") or {}).get("name")
    if expected_project and actual_project != expected_project:
        raise LinearError(
            f"{source} expects Linear project {expected_project!r}, "
            f"but {issue['identifier']} belongs to {actual_project!r}"
        )


def choose_state(issue: dict[str, Any], event: str) -> dict[str, Any] | None:
    states = issue["team"]["states"]["nodes"]
    if event == "start":
        candidates = [state for state in states if state["type"] == "started" and not REVIEW_RE.search(state["name"])]
        return sorted(candidates, key=lambda state: state.get("position", 9999))[0] if candidates else None
    if event == "review":
        candidates = [state for state in states if state["type"] == "started" and REVIEW_RE.search(state["name"])]
        return sorted(candidates, key=lambda state: state.get("position", 9999))[0] if candidates else None
    if event == "block":
        candidates = [state for state in states if state["type"] == "started" and BLOCKED_RE.search(state["name"])]
        return sorted(candidates, key=lambda state: state.get("position", 9999))[0] if candidates else None
    if event == "done":
        candidates = [state for state in states if state["type"] == "completed"]
        return sorted(candidates, key=lambda state: state.get("position", 9999))[0] if candidates else None
    raise LinearError(f"unknown event: {event}")


def marker(event: str, fields: list[str]) -> str:
    digest = hashlib.sha256("\0".join([event, *fields]).encode()).hexdigest()[:16]
    return f"{MARKER_PREFIX}{event}:{digest} -->"


def build_comment(args: argparse.Namespace) -> tuple[str | None, str | None]:
    if args.event == "start":
        details = [value for value in [f"T3 thread: {args.thread}" if args.thread else None, f"Branch: `{args.branch}`" if args.branch else None] if value]
        if not details:
            return None, None
        text = "Agent started work.\n\n" + "\n".join(f"- {value}" for value in details)
        token = marker("start", [args.thread or "", args.branch or ""])
    elif args.event == "review":
        text = f"Implementation is ready for review.\n\n- PR: {args.pr}"
        token = marker("review", [args.pr])
    elif args.event == "block":
        text = f"Agent is blocked.\n\n{args.message}"
        token = marker("block", [args.message])
    elif args.event == "done":
        details = [f"Evidence: {args.evidence}"]
        if args.pr:
            details.insert(0, f"PR: {args.pr}")
        text = "Work is complete.\n\n" + "\n".join(f"- {value}" for value in details)
        token = marker("done", [args.pr or "", args.evidence])
    else:
        return None, None
    return f"{text}\n\n{token}", token


def update_state(transport: Transport, issue: dict[str, Any], state: dict[str, Any]) -> None:
    if issue["state"]["id"] == state["id"]:
        return
    result = graphql(transport, UPDATE_QUERY, {"id": issue["id"], "input": {"stateId": state["id"]}})["issueUpdate"]
    if not result.get("success"):
        raise LinearError("Linear reported an unsuccessful issue update")


def add_comment(transport: Transport, issue: dict[str, Any], body: str | None, token: str | None) -> bool:
    if not body or not token:
        return False
    if any(token in (comment.get("body") or "") for comment in issue["comments"]["nodes"]):
        return False
    result = graphql(transport, COMMENT_QUERY, {"input": {"issueId": issue["id"], "body": body}})["commentCreate"]
    if not result.get("success"):
        raise LinearError("Linear reported an unsuccessful comment creation")
    return True


def parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("issue", help="Linear identifier or issue UUID, for example DEF-123")
    common.add_argument("--transport", choices=["auto", "local", "ssh"], default=os.getenv("LINEAR_TICKET_TRANSPORT", "auto"))
    common.add_argument("--loggie-host", default=os.getenv("LINEAR_TICKET_LOGGIE_HOST", "lab"))
    common.add_argument("--slug", default=os.getenv("LINEAR_TICKET_LOGGIE_SLUG", "linear"))
    common.add_argument("--loggie-account", help="Loggie account alias, normally configured by .linear-ticket.json")
    common.add_argument("--dry-run", action="store_true", help="Resolve and print the transition without writing")
    common.add_argument("--allow-reopen", action="store_true", help="Explicitly allow moving a completed/canceled issue back into active work")

    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="event", required=True)
    start = sub.add_parser("start", parents=[common], help="Move to the first active-work state")
    start.add_argument("--thread", help="T3 thread URL or ID")
    start.add_argument("--branch", help="Git branch")
    review = sub.add_parser("review", parents=[common], help="Move to an existing review state and comment")
    review.add_argument("--pr", required=True, help="Pull request URL")
    block = sub.add_parser("block", parents=[common], help="Use an existing blocked state if present and comment")
    block.add_argument("--message", required=True, help="Concrete blocker and required action")
    done = sub.add_parser("done", parents=[common], help="Move to completed after explicit evidence")
    done.add_argument("--pr", help="Merged pull request URL, when applicable")
    done.add_argument("--evidence", required=True, help="Why the ticket is actually complete, including tests/merge evidence")
    status = sub.add_parser("status", parents=[common], help="Read the issue without changing it")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config_path, config = find_config()
        account = args.loggie_account or os.getenv("LINEAR_TICKET_LOGGIE_ACCOUNT") or config.get("loggieAccount")
        transport = Transport(args.transport, args.loggie_host, args.slug, account)
        issue = fetch_issue(transport, args.issue)
        validate_routing(issue, config, config_path)
        if args.event == "status":
            print(json.dumps({"identifier": issue["identifier"], "title": issue["title"], "state": issue["state"], "workspace": (issue.get("organization") or {}).get("name"), "project": (issue.get("project") or {}).get("name"), "loggieAccount": account, "config": str(config_path) if config_path else None, "url": issue["url"]}, indent=2))
            return 0

        if args.event in {"start", "review", "block"} and issue["state"]["type"] in {"completed", "canceled"} and not args.allow_reopen:
            raise LinearError(
                f"refusing to reopen {issue['identifier']} from {issue['state']['name']!r}; "
                "pass --allow-reopen only when the ticket was explicitly reopened"
            )

        state = choose_state(issue, args.event)
        # Review and block are optional workflow refinements. Without a matching
        # state, keep the current truthful active state and still add the comment.
        if not state and args.event in {"review", "block"}:
            state = issue["state"]
        if not state:
            raise LinearError(f"No suitable {args.event!r} workflow state exists for team {issue['team']['key']}")

        body, token = build_comment(args)
        plan = {"issue": issue["identifier"], "from": issue["state"]["name"], "to": state["name"], "comment": body}
        if args.dry_run:
            print(json.dumps(plan, indent=2))
            return 0

        update_state(transport, issue, state)
        commented = add_comment(transport, issue, body, token)
        verified = fetch_issue(transport, args.issue)
        if verified["state"]["id"] != state["id"]:
            raise LinearError(f"verification failed: expected state {state['name']!r}, got {verified['state']['name']!r}")
        if token and commented and not any(token in (comment.get("body") or "") for comment in verified["comments"]["nodes"]):
            raise LinearError("verification failed: lifecycle comment was not found after creation")

        print(json.dumps({"identifier": verified["identifier"], "state": verified["state"]["name"], "commented": commented, "url": verified["url"]}, indent=2))
        return 0
    except (LinearError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"linear-ticket: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
