# Continuity

The pause, resume, and handover rules for a PR loop that outlives one session.
[Main workflow](../SKILL.md) carries the three rules that apply on every run; this
file carries the checkpoint fields and the watcher mechanics.

## Checkpoint

Persist a task-local checkpoint at creation and after every transition: repository
and PR, canonical worktree, owner/lease, scope and consent source, head/base,
feedback versions, dispositions and open questions, CI/review receipt URLs and
status, round count, quiet-window start, last successful poll, next wakeup,
blocker, and watcher handle. Keep credentials out of checkpoints and public
receipts.

## Watcher

One tracked, bounded background watcher with completion notification covers a
short wait. For continuation across session exit or restart, find the host's
supported durable scheduler or resumable job system and its real API and docs;
configure a bounded run or deadline and a notification destination. Persist and
read back its handle, enabled state, schedule, and checkpoint/resume entry point
before saying the PR is being watched. This skill installs no such system.

With no durable mechanism available: state that unattended watching is
unavailable, save the checkpoint, and give the user the exact PR and checkpoint
location needed to resume. An untracked detached agent, an unbounded sleep loop,
and a chat promise are all non-durable. Pause and notify on questions, revocation,
escalation, or an exhausted watcher budget instead of polling forever.

## Resume

Acquire single-writer ownership and confirm the previous owner stopped or
explicitly transferred its lease. If ownership cannot be established, stay
read-only. Refresh all GitHub state and consent before acting. Discard cached
readiness after an unobserved gap and restart the quiet window. Reconcile prior
replies, pushes, merge attempts, and watcher handles before retrying, so no action
runs twice. On cancellation or verified completion, stop the task's watch and read
back its stopped state.
