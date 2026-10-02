---
name: browserq
description: Browser automation on lab through the browserq admission queue. Use whenever a task needs a browser session (open, snapshot, extract, click, screenshot) or a choice between Chrome and Lightpanda.
---

Run all browser automation through browserq: `agent-browser` runs only as `browserq exec <job> -- <command>`. browserq leases one browser session at a time from a shared, capped pool and runs the commands inside it. One lease covers the whole session, so hold it across all your steps and release it promptly.

## Steps

1. **Pick the engine.** Run `browserq route <workflow>` with one of `public-read`, `visual`, `authenticated`, `interactive`, `unknown`. Only `public-read` (public pages, no login, read-only navigation and text/DOM extraction) may use `lightpanda`; everything else uses `chrome`, the default. Done when you have one engine.
2. **Lease a session.**
   ```bash
   JOB=$(browserq --agent "$AGENT" start --engine chrome --wait 2m) || exit $?
   trap 'browserq --agent "$AGENT" close "$JOB"' EXIT
   ```
   `$AGENT` is a stable name for your task (e.g. the worktree name). Queue progress goes to stderr; the job id is the only stdout line. Done when `$JOB` holds a `bq-…` id.
3. **Drive it.** `browserq --agent "$AGENT" exec "$JOB" -- <agent-browser command>`, for example `open https://example.com/`, `snapshot -i`, `get text h1`, `click @e3`, `screenshot page.png`. Run commands one at a time; a second concurrent command in the same session is refused as busy. Add `--timeout 90s` before `--` for slow pages.
4. **Check Lightpanda output.** If a `lightpanda` session returns missing or wrong content and you have run only read-only commands, switch with `JOB=$(browserq --agent "$AGENT" fallback "$JOB")` and repeat your read-only steps in the fresh Chrome session. Fallback is refused once you clicked, typed, filled, pressed keys, evaluated JS or reloaded.
5. **Release.** `browserq --agent "$AGENT" close "$JOB"` as soon as the browser work is finished. Done when it prints `closed`.

## Reference

**What browserq owns.** It chooses the engine binary, the session, the profile, the config and the browser endpoint, so passing `--session`, `--cdp`, `--profile`, `--engine`, `--config`, `connect`, `close`, cookies/state/auth commands, `file:` URLs or screenshot paths with directories is rejected (exit 65, reason on stderr). Text arguments starting with `-` are rejected too, because agent-browser would parse them as options. Screenshots take a plain file name and land in browserq's artifact directory; the path is printed on stderr.

**Exit codes.**

| code | meaning | what to do |
|---|---|---|
| 0 / other | agent-browser's own result | read its output |
| 124 | command deadline hit; browser-side effect unknown | inspect page state (`get url`, `snapshot`) before repeating anything that mutates |
| 137 | killed because the session closed or hit its lifetime | start a new session |
| 65 | request rejected (passthrough rule or fallback not allowed) | change the command |
| 66 | no such session for you, or it was closed (reason shown) | start a new session |
| 75 | queue full, queue wait elapsed, session busy, or not yet admitted | wait and retry later; do not spin |
| 69 | daemon not reachable or engine not configured | report it; do not run `agent-browser` directly |
| 74 | close could not verify cleanup; capacity stays reserved | report it to the operator |

**Lifetimes.** Idle sessions are closed after the configured idle timeout and every session has an absolute lifetime (`browserq status` shows `IDLE` and `LEFT` seconds). Nothing is retried or replayed for you after a timeout, kill or daemon restart.

**Lightpanda limits seen in the pilot.** Navigation, `snapshot`, `read`, `get`, `eval` worked on probe pages. Its screenshots ignore page CSS layout and render CJK text as boxes, so screenshots and visual checks belong on Chrome.
