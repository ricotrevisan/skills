# Software factory — background

Source: Steve Sewell (Builder.io), YouTube talk on "self-improving software"
(https://www.youtube.com/watch?v=pNmfMi-yjZk), watched 2026-09-24 via Gemini
full-duration analysis. Paraphrased notes; model names from the analysis
may be imprecise.

## The shape he describes

- **Scheduled slash-command stages** run by a coding agent host on a timer:
  collect (every few hours), babysit own PR, review open PRs, ship,
  watchdog (~4×/day), lookback (weekly/monthly over 30 days).
- **Intake**: Slack support, GitHub issues, Sentry, analytics, logs. Collect
  asks reporters for missing detail (URL, timestamp) and re-evaluates on reply.
- **Policy file** decides autonomous vs human: clear and verifiable →
  worktree, reproduce, fix, verify (tests, browser, screenshots), open PR;
  ambiguous or security-sensitive → human.
- **Approval policy** allows auto-merge only for low-risk classes; the rest
  wait for a human.
- **Model routing**: cheap models for volume work, a stronger model for
  oversight (watchdog, lookback), and an orchestrator told to delegate.
- **Runner**: a dedicated always-on machine instead of cloud runners, because
  full verification needs real browser sessions, keys, and local context;
  notifications when a human must authenticate.

## His prerequisites

1. Monorepo — one place for apps, frameworks, and agent skills.
2. Strong telemetry and end-to-end tests — verification quality caps
   factory quality.
3. Beta vs production split — internal beta updates on every merge;
   production cuts over once a day.

## His adoption order

Dry-run collect locally → tune policy until you agree with its picks →
PRs with mandatory human merge → schedule collect/review → add watchdog and
lookback.

## Takeaways worth keeping

- The engineer's job shifts to designing and tuning the loop.
- The factory is only as good as its verification; invest there first.
- Autonomy is per-stage and earned; start propose-only.
