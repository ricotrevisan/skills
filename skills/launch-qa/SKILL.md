---
name: launch-qa
description: Pre-launch QA — five first-time-user personas walk the app in real browsers; rank what they hit, fix it, rerun.
disable-model-invocation: true
---

# Launch QA

You are the **launch QA lead**. Five subagents each play one first-time user and walk the app from landing page to first success in a real browser. You merge what they hit, fix it in one pass, and rerun all five to prove it. You own the merge and the fixes; the personas only report.

A **friction moment** is any point where a persona gets confused, stuck, or annoyed — each one gets a screenshot.

## 1. Pin the run

Record before dispatching anything:

- **Target URL** — local or staging. The breaker submits junk and the skeptic creates accounts, so a production URL needs the user's explicit go-ahead.
- **First success** — the one observable outcome that means a new user got value (e.g. "first project created and visible on the dashboard"). Infer it from the app's onboarding and confirm it with the user if it is ambiguous.
- **Accounts** — how a persona signs up: fresh email aliases, a test mailbox, seeded invite codes, test-mode payment cards. Every persona starts logged out with a fresh identity.
- **Browser** — the host's browser policy decides the tool (collaborative preview, browserq, Playwright, …). Each persona needs its own isolated session. Confirm the tool can set a 375px viewport and throttle the network; if throttling is unavailable, the mobile persona runs at 375px and reports the gap.
- **Artifacts dir** — `launch-qa/<YYYY-MM-DD>/round-<n>/<persona>/`, outside committed source unless the user asks otherwise.

**Exit:** all five values written down.

## 2. Dispatch the five personas

Read [`persona-brief.md`](persona-brief.md). Start five subagents in parallel, one per persona, each with fresh context. Each prompt is self-contained: the shared brief, that persona's section only, plus the run values from step 1 and the round number.

**Exit:** five friction logs returned, each ending in `reached first success` or `quit at <step>`.

## 3. Merge and rank

Collapse friction moments across personas into **issues** by root cause, not by symptom: "the CTA says *Get started* on landing but *Create workspace* on signup" is one issue even if three personas describe it three ways. Open the screenshots — the logs are claims, the screenshots are evidence.

Rank issues by how many personas hit them (5 → 1). Break ties by worst outcome: quit > stuck > confused > annoyed. Write the ranked list to `launch-qa/<date>/issues.md`:

| # | Issue | Hit by | Worst outcome | Evidence | Root cause | Fix |
|---|---|---|---|---|---|---|

**Exit:** every friction moment from every log maps to exactly one issue row.

## 4. Fix in one pass

Fix every issue in the list in a single pass, then run the project's tests. Some issues are product decisions rather than bugs — pricing, legal copy, whether a step should exist at all. Mark those `needs decision`, state the options, and leave them for the user instead of inventing policy.

**Exit:** every row is `fixed` (with the change that fixed it) or `needs decision`; tests pass.

## 5. Rerun all five

Repeat step 2 as round 2 with fresh identities and sessions, adding the round-1 issues each persona hit to that persona's prompt so it checks them explicitly. All five rerun, including personas that hit nothing — a fix can break someone else's path.

New friction from round 2 goes through steps 3–5 again. A persona that quit in round 1 must reach first success in round 2.

**Exit:** all five personas reach first success, and every `fixed` row has a round-2 screenshot showing the fixed state.

## Report

Lead with the verdict: launch-ready, or what blocks it. Then the ranked issue table with before/after screenshots, the `needs decision` items with their options, and any persona constraint the browser could not emulate.
