---
name: t3-thread-management
description: Create and start T3Code threads locally or on another server over SSH, with task handoffs and isolated worktrees, or check their status. Use when the user asks to start a new T3 session, hand work to another server, or split work across T3 threads.
---

# T3 thread management

T3 threads can be started on a headless server: obtain short-lived authentication
with the T3 CLI, then call the running server's orchestration API. A missing MCP
thread tool or `t3` executable on PATH does not establish that access is unavailable.
`t3 app <path>` instead talks to a desktop app on the same machine; its failure
does not rule out the headless route.
For a direct CLI/API example without the helper, read
[references/direct-api.md](references/direct-api.md). The native CLI has no prompt
submission subcommand; do not invent a `t3 --prompt` or `t3 session create` flag.

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
Use `--node /path/to/node` if Node is absent from PATH. These connection options
precede the `inspect`, `start`, or `status` subcommand.

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

For a short task, replace `--prompt-file` with `--prompt 'say hello'`.

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

## Another server over SSH

Put `--host office` before the subcommand. The helper streams its code and the
prompt over SSH to Python 3 on the destination; no remote skill installation is
required. SSH uses batch mode and the existing host-key policy. Configure SSH
access when necessary rather than disabling host verification.

```bash
python3 <skill-dir>/scripts/t3_threads.py --host office inspect
python3 <skill-dir>/scripts/t3_threads.py --host office start \
  --source-thread <office-thread-id> \
  --workspace /path/on/office/project \
  --title 'Greeting' --prompt 'say hello' \
  --receipt /path/on/office/greeting-thread.json
```

`--prompt-file` is read on the invoking machine and sent as text. Workspace,
worktree, receipt, CLI, Node and base-directory paths belong to the destination.
The destination uses its own T3CODE_HOME/default when `--base-dir` is omitted;
the invoking machine's environment is not forwarded. Source thread IDs must exist
on the destination: choose one from its `inspect` output. Authentication is issued
and used there; tokens never travel back in the SSH payload or result.

Prepare branches/worktrees on the destination before starting. The helper does
not transfer repositories or uncommitted files. Describe needed files in the
handoff and explicitly transfer them within the user's scope.

An SSH disconnect can occur after a successful API write. The receipt lives on
the destination; re-run with the same host, request and receipt to inspect it.
Use `--host office status --thread-id <id>` to verify startup.

If a machine uses a different layout, inspect its launcher/runtime file and pass
the actual `--base-dir`, `--cli` and `--node`. Some servers bind only to a LAN or
Tailnet IP. After verifying that the destination owns the runtime file's address,
pass `--allow-non-loopback`; it uses that configured origin with redirects disabled.

## Failure recovery

- Authentication stays in memory and expires after five minutes. The helper uses
  the loopback runtime origin by default, with redirects disabled. The explicit
  non-loopback override is for a verified destination-owned server address.
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
