---
name: t3-thread-management
description: Start, check, or find T3 Code threads on lab, office, or this machine through the server's V2 orchestration API. Use when the user asks to start a T3 session, hand work to another server, split work across T3 threads, or check a thread's status.
---

# T3 thread management

T3 Code 0.1.0 servers run orchestration protocol 2. One server call,
`orchestration.launchThread`, creates the thread, prepares its workspace (root,
an existing worktree, or a new worktree from a base ref), and sends the first
message. The bundled helper wraps it: standard-library Python 3.9+, auth from the
destination's own `t3` CLI (five-minute token, `orchestration:read` +
`orchestration:operate`), WebSocket RPC for writes, HTTP for reads.

Run `scripts/t3_threads.py --help` (and `<subcommand> --help`) for flags. Global
options precede the subcommand.

## Servers

| Target | Invocation prefix |
| --- | --- |
| this machine | `t3_threads.py` (base `~/.t3`) |
| lab | `t3_threads.py --host lab` |
| office (Mac mini) | `t3_threads.py --host office --base-dir '~/.t3code' --allow-non-loopback` |

`--host` streams the helper to `python3` on the destination over SSH; auth is
issued and used there. Paths in `--existing-worktree` and `--project` (when a
path) are destination paths; `--prompt-file` is read locally and sent as text.

## Launch

1. **Prompt file.** Write a UTF-8 task file: objective, source paths, scope,
   applicable instructions, verification, deliverables. Carry forward the user's
   actual authorization; a new thread gains no merge/deploy permission. Include
   needed facts; history is not copied.
2. **Request ID.** Choose a stable ID per requested thread (originating message
   or task). The helper derives the server `commandId` from it, so re-sending the
   same request returns the same thread with `"resumed": true` and starts nothing
   new. Keep it for every retry and status check.
3. **Inspect.** `inspect --models` lists provider instances with status, model
   slugs, and option values. Pick a `ready` provider. Use those exact slugs and
   option ids (Codex `reasoningEffort`/`serviceTier`, Claude `effort`, Pi `thinking`,
   ACP agents report their own). `--source-thread` inherits model and runtime mode instead.
4. **Dry run.** `start ... --dry-run` resolves the project (id, exact title, or
   workspace root; `--add-project` registers a missing path) and validates the
   selection against the live server. Fix every error it reports.
   `setupScriptsThatWillRun` shows the project's first `runOnWorktreeCreate`
   script: the server runs it in a new worktree with no further approval. Review each
   command (and any script it calls) before launching; if one is unsafe for the
   task, use the project root or an existing worktree instead and say so.
5. **Start.** Same arguments without `--dry-run`. Workspace: default is the
   project root; `--worktree-from main --branch t3code/<task>` has the server
   fetch and create the worktree from `origin/main` (`--worktree-from default`
   uses origin's default branch; `--no-origin` for the local ref); `--existing-worktree PATH` attaches one. Defaults: `--runtime-mode
   full-access`, `--interaction-mode default`, `--wait started`.
6. **Verify.** Done when the output shows `waitSatisfied: true` and a run with
   `startedAt` (or `--wait completed` and a terminal run status), plus the
   expected `branch`/`worktreePath`. Report server, project, title, thread ID,
   branch/worktree, and run state. If the wait timed out, say so and poll
   `status --thread-id`.

For an empty thread (phone handoff), use `--no-message`; workspace setup is still
performed by the server.

## Continue or stop a thread

- `send --thread-id ID --request-id R --prompt-file F` queues a follow-up after any
  running turn and waits like `start`. `--provider/--model/--option` switch the model
  for that turn. Use a new request ID per message.
- `interrupt --thread-id ID` stops the running turn; `--hold-queue` also holds queued
  messages (T3's Stop button). The next `send` releases the queue.

## Recovery

- Timeout, SSH drop, or unclear outcome: read `status` before re-sending a `send`;
  re-run the identical `start` (same request ID). `resumed: true` means it had landed; read `status`.
- `Provider ... is error/disabled`: the provider needs attention in Settings →
  Providers on that server. Report it; choose another provider only if the user
  agrees.
- `WebSocket upgrade refused ... 426`: the server is not on protocol 2.
- Smoke tests: `delete --thread-id` removes the thread only. Remove its worktree
  and branch with `git worktree remove` / `git branch -D` after confirming they
  hold no changes.

Find past threads with `search --query` (message text). Wire-level details for
writing another client are in [references/protocol.md](references/protocol.md).
