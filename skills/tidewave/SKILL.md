---
name: tidewave
description: Use Tidewave MCP tools (project_eval, get_logs, browser_eval, execute_sql_query, get_docs, get_source_location, get_ecto_schemas) against a running Phoenix dev server. Load before calling any Tidewave tool for runtime introspection, log reading, SQL, or driving the app in a real browser. Assumes tidewave >= 0.8.
---

# Tidewave MCP (0.8+)

Tidewave runs inside the Phoenix dev server, MCP endpoint at `/tidewave/mcp`.
Tools only work while that server is up.

## Two rules that prevent most failures

1. **Never guess tool names.** Registered names vary by client (`tidewave_project_eval`,
   `mcp__tidewave__project_eval`, ...). List the server's tools first.
2. **Never guess the `browser` API.** Call `browser_eval` with `{action: "help"}` once
   per conversation and treat its output as the entire API. Anything not in it does not
   exist — past guesses that all failed: `browser.visit`, `browser.goto`,
   `browser.getById`, Playwright-style `page` objects, passing strings to `browser.eval`.

## browser_eval

Action-based: `{action: "help" | "new-session" | "eval", sid: "...", args: {code: "..."}}`.
`help` returns the API and the active session id; pass that as `sid` to `eval`.
`new-session` opens another session (same browser window if you pass a `sid`) — useful
for multi-tab scenarios like presence.

Essentials the help enforces:

- Top-level code runs in an isolated context, NOT on the page. Only `browser.eval(fn)`
  runs on the page. Pass a function, never a string. `console.log` results — never return.
- The function cannot see outer variables; pass elements via the locators argument.
- Navigate/reload with `browser.reload(path)`.
- Snapshot-first: `browser.snapshot()` → `browser.getBySnapshotRef(ref)` →
  `browser.click`/`browser.fill`. Don't grope with `textContent`/`innerHTML`.
- No code comments in the code you send.
- Read source code first; use the browser only to fill gaps or preview changes.

## Failure triage

| Symptom | Meaning | Do |
|---|---|---|
| "Browser is not connected ... manual user retry" | No browser tab with Tidewave connected | Stop. Ask the user to open the app in the browser. Do not retry. |
| ECONNREFUSED / fetch failed / 000 | Dev server is down | Start the server yourself. No MCP tool can revive a dead BEAM. |
| "Blocked a frame ... cross-origin" | Browser session's origin ≠ app origin (scheme/port drift, e.g. after a restart) | Don't retry unchanged. Re-check which origin the session uses (`help` shows it) and align. |

## project_eval

- Args: `code` (required), `arguments` (list, available in code as `arguments`),
  `timeout` (default 30s). IEx helpers work, e.g. `exports(Module)`.
- Returns both stdout and the result — `IO.inspect` freely.
- Sigil trap: `~s(...)` around code containing `)` (e.g. `Date.now()`) closes the sigil
  early. Use heredocs (`~s"""`) or `"` strings.
- Prefer it over shelling out to `mix run`/`iex` — it's the live app state.

## The rest

- `get_logs`: `tail` required; filter with `grep` (case-insensitive regex) and `level`.
  Excludes log lines caused by your own tool calls.
- `get_source_location` / `get_docs`: take `Module`, `Module.fun`, or `Module.fun/arity`
  (`c:` prefix for callbacks). Prefer over grepping the file system when you know the name.
- `execute_sql_query`: raw SQL through the app's repo.
- `get_ecto_schemas`: no args; lists schema modules + file paths.
- `search_package_docs` no longer exists (moved to the Hex CLI in 0.6).
