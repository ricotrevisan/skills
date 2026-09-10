---
name: t3-thread-management
description: Create and start T3Code threads with task handoffs and isolated worktrees, or check their status, using the local server and CLI authentication. Use when the user asks to start a new T3 session or split work across T3 threads.
---

# T3 thread management

T3 threads can be started on a headless server: obtain short-lived authentication
with the T3 CLI, then call the running server's orchestration API. A missing MCP
thread tool or `t3` executable on PATH does not establish that access is unavailable.
`t3 app <path>` instead talks to a desktop app on the same machine; its failure
does not rule out the headless route.

## Prepare the handoff

1. Use the user's requested repository. Read its instructions and inspect Git
   status. For concurrent work on an existing repo, fetch the intended base and
   create a dedicated branch/worktree. Preserve other checkouts. For a new project,
   create the requested directory; the receiving agent can initialize the repo.
2. Write a UTF-8 prompt file containing the concrete objective, source/reference
   paths, assigned worktree and branch, scope ownership, applicable instructions,
   verification requirements, and expected deliverables. Carry forward the user's
   actual authorization; a new thread gains no additional merge/release permissions.
3. Select the source T3 thread ID from the current context or the helper's
   `inspect` output. The helper inherits its model selection and runtime mode.
   This does not copy conversation history: include needed facts in the prompt.

## Create and verify

Use the bundled standard-library Python helper. It discovers the server from
`~/.t3/userdata/server-runtime.json` and checks PATH and `~/.t3/runtime/versions/`
for a CLI. Override `--base-dir` or `--cli` when necessary; a built source checkout
can be invoked with `--cli /path/to/apps/server/dist/bin.mjs`.

```bash
python3 <skill-dir>/scripts/t3_threads.py inspect

python3 <skill-dir>/scripts/t3_threads.py start \
  --source-thread <current-thread-id> \
  --workspace /absolute/project/root \
  --title 'Concrete task title' \
  --prompt-file /absolute/task.txt \
  --receipt /absolute/task-thread.json

python3 <skill-dir>/scripts/t3_threads.py status --thread-id <new-thread-id>
```

For an existing project with a separate worktree, supply the original project root
as `--workspace`, plus `--branch <branch>` and `--worktree /absolute/worktree`.
The helper attaches an already prepared worktree; it does not create branches.

Use one receipt per requested thread. It records IDs and completed dispatch stages,
never credentials. Re-running the same request with that receipt reads status
without submitting another turn. A changed request with the same receipt fails.

After dispatch, check status until there is evidence of a started turn (a running
session, an active turn ID, or a completed turn/message). An accepted command alone
is not proof that the agent started. Report the project, thread title/ID, worktree,
and observed status. If startup remains pending or fails, report it accurately.

## Failure recovery

- Authentication stays in memory and expires after five minutes. The helper sends
  it only to the loopback origin in the runtime file, with redirects disabled.
- After a timeout or error, inspect the receipt and server status. Keep the same
  IDs; do not delete the receipt and blindly retry. If creation/start did not land,
  inspect the current API contract before explicitly resuming that stage.
- On CLI/schema mismatch, check the installed CLI's `--help` and local T3 source:
  `apps/server/src/cli/project.ts`, `packages/contracts/src/`, and orchestration
  routes. The successful flow is project.create (if missing), thread.create, then
  thread.turn.start through `/api/orchestration/dispatch`; read state through
  `/api/orchestration/snapshot`. Use the live API for writes, not SQLite edits.
- If the helper finds an existing active thread with the same project and title,
  inspect it before choosing reuse or a distinct title. Never start duplicate work
  merely to recover from an uncertain response.

Creating, starting, or steering a thread must be within the user's requested work.
Use this workflow for actual T3 sessions; ordinary in-turn subagents are a separate
capability.
