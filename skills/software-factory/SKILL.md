---
name: software-factory
description: Assess whether a project can run as a "software factory" (agents that take tickets/errors through fix, verification, review, and release on a schedule) and design a staged rollout for it. Use when asked whether a project is ready for autonomous agent development, to design an agent pipeline from Linear/issue intake to deploy, or to add/tune a factory stage (collect, fix, gate, promote, watchdog, lookback).
---

# Software factory

A software factory is a scheduled loop of agents that turns intake (tickets,
errors, feedback) into verified, reviewed, released changes. Humans design
the loop, set policy, and own the judgment gates; agents do the volume.
Background and source → [reference.md](reference.md).

This is a design-and-assessment skill. It does not install a scheduler or
grant merge/deploy authority. Discover the project's actual tools before
proposing a stage, and follow the project's AGENTS.md/CLAUDE.md safety rules.

## 1. Assess readiness (read-only)

Inspect the project and fill this table with evidence (paths, commands, run
history), not assumptions. Each row is a prerequisite for the stages it names.

| Capability | Question | Needed by |
| --- | --- | --- |
| Intake | Where do tickets, errors, feedback land? Can an agent read and comment there? | Collect |
| Isolation | Can an agent get its own workspace (git worktree, app branch) without touching others? | Fix |
| Isolated data | Can concurrent agents test without sharing mutable fixtures/DB rows? | Parallel fixes |
| Verification | What automated checks prove a change works? What do they *not* cover? | Fix, Gate |
| Check reliability | Recent pass/fail history on unchanged revisions; runner vs app failures | Gate |
| Change review | Can a human see a readable diff and evidence (screenshots, recordings)? | Review |
| Promotion | Is there a staging → prod path, scriptable, with a revision pin and rollback? | Promote |
| Observability | Error tracking, logs, analytics an agent can query after release | Collect, Lookback |
| Runner host | An always-on machine with the browsers, sessions, and secrets the checks need | All scheduled stages |

Verdict per stage: **ready**, **ready with limits** (state them), or
**blocked by** (the missing row). Green checks only mean "passed what is
covered" — always list uncovered critical journeys next to any gate.

## 2. Choose stages and autonomy

Stages, in adoption order. Each can run at *propose* (writes a plan/comment
only), *act with human gate*, or *autonomous*.

1. **Collect/triage** — pull new intake, dedupe, ask reporters for missing
   repro detail, classify against the policy.
2. **Fix** — in an isolated workspace: reproduce, write the failing
   regression check, fix, verify, attach evidence, hand off for review.
3. **Review babysit** — respond to review comments and failing checks on the
   agent's own change until green (see `pr-shepherd` for git projects).
4. **Gate & promote** — on human approval: integrate into staging, run the
   gate, promote to production if green, smoke-check, report.
5. **Watchdog** — a few times a day, find stalled or abandoned work and
   nudge or escalate it. Use a stronger model than the workers.
6. **Lookback** — weekly/monthly, mine 30 days of intake and escapes for
   recurring failures and brittle areas; propose systemic fixes and new tests.

Rules that hold at every autonomy level:

- The **human judgment gate stays before production** until the gate has a
  track record (see step 4). Moving it later is an explicit, recorded decision.
- **Never retry until green.** A failed check blocks; preserve evidence,
  classify app vs fixture vs runner, then rerun the whole gate.
- **Pin revisions.** Test the exact snapshot you promote; if it moved, retest.
- **One writer per ticket/workspace/fixture.** Serialize anything shared.
- Route security-sensitive, data-migrating, billing, auth, and ambiguous
  tickets to a human regardless of policy.

## 3. Design the ticket state machine

Put the loop where the team already works. For a Linear-driven project:

| Linear state | Owner | Factory action |
| --- | --- | --- |
| Todo / Triage (factory label) | Factory | Collect: clarify or accept per policy |
| In Progress | Factory | Fix in isolated workspace; regression check first |
| In Review | Human | Reviews diff + evidence; approves by moving on, or comments back |
| Staging / Ready to ship | Factory | Integrate → gate → promote (per autonomy level) |
| Done | Factory | After production smoke + report link |
| Blocked / Needs human | Human | Any failed gate, conflict, or policy exit |

Every transition the factory makes carries a comment: what ran, the pinned
revision, the evidence path, and what is *not* covered. Failures move the
ticket to Blocked with the reason instead of silently retrying.

Batching: if staging promotes everything merged so far (not just this
ticket), promotion must re-gate the combined revision and name every ticket
it ships.

## 4. Write the policy file

Keep policy in the repo (e.g. `factory/policy.yaml`) so it is reviewed like
code. Minimum fields:

```yaml
intake:            # sources, labels/filters, polling interval
accept_when:       # repro possible, area covered by checks, size limit
human_only:        # areas/labels always routed to a human
verification:      # commands, required evidence, per-area extra checks
promotion:
  staging: human   # human | factory
  production: human
  requires: [gate_passed, revision_pinned, evidence_reviewed]
limits:            # max concurrent fixes, max changes per day, stop conditions
notify:            # where blocked/needs-human pings go
```

## 5. Roll out

1. **Dry run**: run collect by hand; compare its choices with yours; tune
   policy until you agree.
2. **Propose-only fixes**: agent writes plans and failing checks, no changes.
3. **Fixes to In Review**: agent changes code in isolation; humans merge/promote.
4. **Scheduled**: cron/host scheduler runs collect and fix.
5. **Factory-run promotion** — only after the gate has a clean record (e.g.
   N consecutive unchanged-revision gates with no runner failures, critical
   journeys covered) and a rollback path is tested.
6. Add watchdog, then lookback.

Advance one step at a time; record the decision and the evidence for it.

## 6. Output

Deliver: the readiness table with evidence, the per-stage verdicts, the
proposed state machine and policy draft, the rollout step to start at, and
the concrete gaps (with owners/tickets) blocking the next step.
