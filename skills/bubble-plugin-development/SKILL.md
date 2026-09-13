---
name: bubble-plugin-development
description: Develop, debug, test, and release Bubble.io plugins in `~/bubble-plugins/*` using Pled for plugin source and Buildprint for the dev app. Use for plugin elements or actions, renderer bundles, Bubble branches, demo pages, and preview verification.
---

# Bubble plugin development

Use this workflow for Bubble plugin repos that pair **Pled** with a
Buildprint-hosted development app. Read the target repo's `AGENTS.md` first;
it owns the plugin id, app name, demo page, login, build commands, and any
renderer-specific rules. This skill owns the shared operating procedure.

The workflow requires Bash, Node.js/npm, Pled, Buildprint CLI,
`BUBBLE_COOKIE`, and a plugin repo with `AGENTS.md`.

## Preflight

Run the bundled preflight from the plugin repo before relying on the toolchain:

```sh
skill_dir="${AGENT_SKILL_DIR:-$HOME/.agents/skills/bubble-plugin-development}"
"$skill_dir/scripts/check-setup" "$PWD"
```

Use `--live` when a task needs Bubble access. It adds read-only `pled status`
and `buildprint project list` probes. A passing local preflight is not proof of
remote access; a passing live preflight is.

If preflight fails, report each missing command, credential, or repo marker.
Set up only what the user asked to change. Never print `BUBBLE_COOKIE`, copy it
into a repo, or expose Buildprint authentication files.

## Sources of truth

- `src/` is decoded Bubble plugin source. Pled uploads it.
- `lib/` is a separately built runtime bundle when the plugin has one.
- The development app is a test surface, not a substitute for fixing shared
  plugin behavior in `src/` or `lib/`.
- The repo's `AGENTS.md` resolves plugin-specific facts. Stop if its app name
  does not exactly match the Buildprint project you intend to use.

In `src/elements/*/initialize.js` and `update.js`, omit Bubble's outer
`function(...)`; Pled adds it. The decoded signatures are:

- `initialize.js`: `instance`, `context`
- `update.js`: `instance`, `properties`, `context`

Bubble `secure` shared keys are server-only; element code never receives them.

## Git PR routing and release boundaries

For plugin source changes that need a GitHub PR, or requests to open, babysit,
ship through, or resume that PR, read [pr-shepherd](../pr-shepherd/SKILL.md).
It owns Git PR creation, review/CI polling, evidence-based fixes or questions,
guarded Git merge, and task-owned Git cleanup. Opening a PR starts that loop;
it does not finish the task.

Scoped ship-through-PR intent can authorize the eventual **Git merge** once its
gates pass; opening a PR alone cannot. **Git merge is not Pled push/upload,
Bubble branch merge, plugin release, or a live deployment.** It does not replace
this skill's external-change authorization, real-preview verification, or
immediate confirmations. If Git merge triggers a Bubble/live release, obtain
that release's required authorization before merging Git.

The immediate-confirmation rules below remain in force for Bubble merges,
releases, branch deletion, and direct changes to `test` or `live`, even when
the Git PR is approved and its merge was authorized earlier. Follow stricter
repository instructions as well.

## Change workflow

1. Inspect `AGENTS.md`, `git status`, `pled status`, and the relevant source
   before editing. If Pled reports divergence, understand both sides and
   preserve intentional local and remote work.
2. For development-app changes, use a short dedicated Bubble branch derived
   from `test`. Never edit `test` or `live` directly. Bubble allows nine branch
   copies under `test`; check capacity before creating one.
3. Change plugin behavior in `src/`. Change a separately bundled runtime in
   `lib/`, respecting its pinned Node version and repo-specific build commands.
4. Run the narrow tests first, then the repo's full relevant build/test suite.
5. When a runtime bundle changed, create a uniquely versioned asset, upload it,
   update the plugin header to that exact URL, and push the plugin only after
   the user has authorized the external changes.
6. Apply development-app changes through Buildprint only after checking the
   target branch and creating a savepoint or equivalent rollback point.
7. Verify the exact Bubble branch in real run mode. Use real pointer/keyboard
   interaction; synthetic JavaScript events do not prove Bubble click states.

Typical branch setup:

```sh
buildprint branch create <app> <issue>-<slug> --from test
buildprint project clone <app> --branch <issue>-<slug> --dir <workspace-root>
```

Treat `pled pull`, `pled push`, `pled upload`, `buildprint branch create`,
`buildprint apply`, Bubble/platform merges, releases, and branch deletion as
mutations. Verify the exact target and rollback before each. Feature-branch
work that is plainly inside an implementation request needs no extra
confirmation; Pled push/upload still needs the external-change authorization
above. Bubble/platform merges, releases, branch deletion, and any direct change
to `test` or `live` require explicit confirmation immediately before they run.
Git PR merge and task-owned Git cleanup use the scoped-consent rules in
[pr-shepherd](../pr-shepherd/SKILL.md), without bypassing these platform gates.

## Verification and completion

A plugin task is complete only when all applicable checks pass:

- The code diff contains only intended plugin, bundle, or dev-app changes.
- Relevant tests and builds pass.
- After any approved push, `pled status` reports the expected remote state.
- Buildprint changes exist on the intended feature branch and its diff is
  understood.
- The affected behavior was exercised in the exact branch's real preview,
  including the failure case that motivated the change.
- The final response names the tested branch/version and returns its exact
  preview URL, preserving its path and query string.
- Merge and cleanup happen only when the user requested them. Then remove only
  task-created branches, demo pages, and local workspaces, and verify removal.

When creating or substantially redesigning a demo page, read
[references/demo-page.md](references/demo-page.md). When the user asks to merge
or remove a Bubble branch, read
[references/branch-cleanup.md](references/branch-cleanup.md) before acting.
