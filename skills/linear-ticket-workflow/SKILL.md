---
name: linear-ticket-workflow
description: Keep a Linear ticket's status truthful while an autonomous coding agent works on it. Use whenever a T3Code or other coding-agent task is tied to a Linear issue.
---

# Linear ticket workflow

When the task names a Linear issue, treat that issue as part of the execution contract. Update it as work changes state; do not leave the board stale and do not mark an agent turn as completed work.

Use the bundled `scripts/linear-ticket` command. It calls Linear through the repository's explicitly configured Loggie account, verifies every write by reading the issue back, and deduplicates lifecycle comments. If Loggie is not installed locally, the default `auto` transport uses `ssh lab`; override with `--transport` or `LINEAR_TICKET_TRANSPORT` when needed.

## Repository routing

Every repository that uses Linear must contain `.linear-ticket.json` at its Git root:

```json
{
  "loggieAccount": "work",
  "linearWorkspace": "MocharyMethod",
  "linearProject": "Defacto"
}
```

`loggieAccount` is required and selects credentials through `loggie-account`. `linearWorkspace` and `linearProject` are optional but strongly recommended safety checks: the command refuses to update a ticket that resolves to a different workspace or project. The CLI searches from the current directory up to the Git root and fails closed when no account is configured. `--loggie-account` is an explicit one-off override, not a substitute for repository configuration.

Also document the same policy in `AGENTS.md`, including the exact Loggie account alias, Linear workspace/project, and instruction to use this skill. Repositories whose canonical tracker is GitHub must not receive `.linear-ticket.json` or Linear lifecycle instructions.

## Lifecycle

### Start actual implementation

As soon as investigation becomes active implementation, move the issue to the team's first ordinary `started` state:

```bash
<skill-dir>/scripts/linear-ticket start DEF-123 \
  --thread '<T3 thread URL or ID>' \
  --branch '<branch>'
```

Do not set In Progress merely because a thread or worktree was created. The agent must have actually started the ticket. The CLI refuses to revive completed or canceled tickets unless `--allow-reopen` is passed after an explicit reopening decision.

### Ready for review

After focused checks pass and a PR exists:

```bash
<skill-dir>/scripts/linear-ticket review DEF-123 --pr '<PR URL>'
```

The command uses an existing started-state whose name contains Review, Verification, QA, or Testing. If the team has no such state, it leaves the current state unchanged and adds the PR comment. Never invent workflow states.

### Blocked

When progress requires a human decision, unavailable credential, failing external dependency, or another concrete intervention:

```bash
<skill-dir>/scripts/linear-ticket block DEF-123 \
  --message 'Exact blocker and the action needed to unblock it.'
```

The command uses an existing blocked/waiting/paused started-state when available; otherwise it keeps the current state and comments. Do not use “blocked” for ordinary debugging or work the agent can continue itself.

### Done

Only mark completed when the ticket's real completion boundary has been met:

```bash
<skill-dir>/scripts/linear-ticket done DEF-123 \
  --pr '<merged PR URL>' \
  --evidence 'PR merged; focused and full checks passed; runtime verified.'
```

`--evidence` is mandatory. An agent turn ending, code being committed, or a PR merely being opened is not Done. If the repository convention says merged is complete, wait for merge. If deployment or production verification is explicitly part of the ticket, wait for that too.

### Inspect without writing

```bash
<skill-dir>/scripts/linear-ticket status DEF-123
<skill-dir>/scripts/linear-ticket start DEF-123 --dry-run
```

## Operating rules

1. Preserve the exact Linear identifier from the task. Do not infer a different issue from branch names or prose.
2. Run lifecycle updates from the repository so `.linear-ticket.json` is discovered. `lab` uses `loggie-account` locally; hosts without Loggie may use the verified SSH fallback to `lab`.
3. Never create states, change assignment, alter priority, or rewrite the issue description as part of lifecycle tracking.
4. Use one concise blocker or evidence comment, not progress-journal spam. Identical retries are idempotent.
5. If a Linear update fails, report it as a task-tracking failure. Do not claim the ticket was updated.
6. Status updates do not expand authorization. Merge, deployment, infrastructure mutation, and unrelated scope still require their normal approval.
7. When handing work to another agent, include the issue identifier and tell it this skill applies. Structured metadata is preferable to making the receiving agent scrape an identifier from prose.

## Installation

The containing skills repository is intended to be symlinked into the agent client's shared skill directory. Ensure this directory is linked as `~/.agents/skills/linear-ticket-workflow` on every T3Code host. The scripts require Python 3, `ssh` for remote fallback, and either local Loggie access or SSH access to a host with the `linear` Loggie integration.
