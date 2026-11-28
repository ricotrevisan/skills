---
name: council
description: Trigger this if the user says 'council'.
---

# Council

Overrides Theo's `council` in tstack. Same process, with four default members (Claude Opus, GPT Sol, Deepseek, and Antigravity Neon).

Before an audit, address outstanding PR comments, fix known issues, and run
relevant checks. Give council the updated implementation; do not defer known
fixes until reviews return. If the user wants to discard the implementation
and explore new ideas, skip fixes to code being replaced.

## Members

Bring in delegates, one per row, at high reasoning effort. In T3 `delegate_task`, omit `runtimeMode` so delegates inherit `full-access` and never prompt for approvals; never pass `runtimeMode: "approval-required"`. If the user names members, use those.

| Member | T3 `delegate_task` target |
| --- | --- |
| Claude Opus | `claudeAgent`, latest Opus, `effort: high` |
| GPT Sol | `acpRegistry_primeagent` (`prime-agent`), latest `codex-lb` Sol, `thought_level: high` |
| Deepseek | `pi`, `opencode-go/deepseek-v4.1-flash`, `thinking: high` |
| Antigravity Neon | `antigravity`, `gemini-4-neon`, `thought_level: high` |

Resolve exact model ids with `orchestrator_capabilities`, then start all four in parallel with `delegate_task`. Elsewhere, use the harness's subagent tools.

If a member is unavailable, report it instead of substituting another model. Known fallbacks for the same model:

- `claudeAgent` not authenticated: ask the user to run `claude auth login` on that host, or run Opus through Pi (`pi`, `claude-bridge/claude-opus-5-5`).
- `prime-agent` (`acpRegistry_primeagent`) unavailable or missing `codex-lb`: run GPT Sol through Pi (`pi`, latest `codex-lb` Sol, `thinking: high`).

## Running it

Give each delegate the request and relevant context. For review or feedback, keep their work read-only via the task prompt and `role: "review"`, never via `runtimeMode: "approval-required"`. Collect their responses and summarize the useful findings, disagreements, and recommended next steps.

Do not wait idle. When a result arrives, check its findings against the code at once and decide what to fix while the other delegates run. Do not edit files while a delegate still reviews the same checkout. If the user marks a delegate as non-blocking, do not wait for it; treat a late result as feedback and do not record its score.

For a code review, ask each delegate for a score out of 10. Count each full review pass as one round. A fresh review after fixes starts a new round. A narrow re-check of one fix by the member who raised it is a re-check, not a round.

Set a blocker bar in the brief: a blocker breaks the flow, loses data, or publishes something the user didn't say. Tell members which polish is already deferred to a ticket, so they don't raise it again.

## Results

If the work ends in a pull request, put the results in the PR description, before the model and harness line at the end:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Claude Opus | 7/10 | 9/10 |
| GPT Sol | 8/10 | 10/10 |
| Deepseek | 7/10 | 9/10 |
| Antigravity Neon | 8/10 | 9/10 |
```

If a delegate gives no score, write `no score`. Do not invent one. If the PR is open, edit the description; do not post a comment for this. If there is no PR, put the same results in the final reply only.

If you agree with their recommendations, make the changes and request a fresh review after. Continue until all delegates are satisfied.

Do not let repeated reviews result in scope creep. It is your job to fight to keep scope limited.
