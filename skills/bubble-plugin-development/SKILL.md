---
name: bubble-plugin-development
description: Use when working in a Bubble.io plugin repo (~/bubble-plugins/*) that uses Pled for plugin sync and Buildprint for the dev app. Covers the Pled workflow, the two-code-piles layout, secure keys, renderer bundle builds, branching, and how to verify changes against the real Bubble UI.
---

# Bubble plugin development

Workflow for Bubble.io plugin repos that use **Pled** (plugin source sync to
Bubble) and **Buildprint** (dev app hosting and branching). Each plugin repo's
`AGENTS.md` holds the plugin-specific facts (app name, demo page, login,
renderer details); this skill holds the shared workflow. Read the repo's
`AGENTS.md` first.

## Two code piles

- `src/` — decoded Bubble plugin source. Pled uploads this. Never hand-edit
  anything outside `src/` and expect it to reach Bubble.
- `lib/` — separately built runtime bundle (renderer, Tiptap runtime, etc.),
  versioned and uploaded on release.

## Pled (plugin sync)

`BUBBLE_COOKIE` is already in the shell. Never write it to the repo.

```sh
pled status
pled pull      # first, if status says "No baseline"
pled push
pled watch     # auto-push src/ changes
```

- If `pled status` reports a divergence, inspect both sides and choose the
  safe direction. Preserve intentional local changes.
- In `src/elements/*/initialize.js` / `update.js`, omit Bubble's outer
  `function(...)` — Pled adds it. Do not wrap the file yourself.
- Signatures: `initialize.js` → `instance`, `context`; `update.js` →
  `instance`, `properties`, `context`.
- `secure` shared keys are server-only. Elements never see them.

## Runtime bundle (lib)

- Respect the pinned Node version (`lib/.node-version` where present).
- Build from `lib/`: `npm ci`, then build/test per the repo.
- Release flow: copy the bundle to a **unique versioned filename**, then
  `pled upload`, then update the element's `headers.html` (or equivalent) to
  the new CDN URL before pushing the plugin. Never upload a stale or generic
  filename.

## Dev app (Buildprint)

The plugin points at a Buildprint-hosted Bubble app as its test app. See the
repo's `AGENTS.md` for the app name, login, and demo page.

For new work on a ticket, create a branch (short name, include the issue
number):

```sh
# ticket: 33: implement Pie Chart element
buildprint branch create <app> 33-pie-chart --from test
buildprint project clone <app> --branch 33-pie-chart --dir /home/rico/<dir>
cd /home/rico/<dir>/33-pie-chart
# edit pages, then:
buildprint apply
```

- Bubble allows **9 branch copies under `test`** (`test` + 9; 10 app
  versions in total) — warn when approaching the limit.
- Share links look like
  `https://<user>:<pass>@<app>.bubbleapps.io/version-<id>/<page>`; Bubble
  assigns `<id>` when the branch is created.
- Create as many dev pages as needed. When done: merge the branch into main,
  delete dev pages you created, and remove the branch.
- **Clean up after yourself.** Finishing a ticket means: merge the work,
  delete the Bubble branch (via the Bubble editor if no CLI command exists),
  delete the dev pages you created, and remove the local branch workspace
  (e.g. `~/tiptap-plugin/<branch>/`). Never leave spent branches, pages, or
  local workspaces behind.

## Verifying changes

- **No Playwright MCP. No `TEST_URL`.** Open the real run-mode demo URL in
  browser preview tools, or use `buildprint screenshot` against it.
- **Do not fake clicks with injected JavaScript.** Bubble click states do not
  update from synthetic events. Click the real UI.
- The browser may ignore URL credentials and show a login popup — that is
  expected.

## Demo page

Keep a demo page that shows off the plugin: simple user-facing language,
written for a medior Bubble developer. If the plugin points at the marketplace
version, the demo reflects the published version, not local changes.
