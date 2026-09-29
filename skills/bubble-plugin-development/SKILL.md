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

## Buildprint workspace routing

Every Buildprint workspace has its own local CLI profile. Resolve the target
app from the plugin repo's `AGENTS.md` and select its profile on **every**
call with `BUILDPRINT_PROFILE`:

| Profile | Workspace | Apps |
| --- | --- | --- |
| `ricowtf` | rico.wtf | `tiptap-plugin` |
| `defacto` | Defacto | `mm-137` |

```sh
BUILDPRINT_PROFILE=ricowtf buildprint project list
BUILDPRINT_PROFILE=ricowtf "$skill_dir/scripts/check-setup" --live "$PWD"
```

Every plugin uses two rico.wtf apps unless its `AGENTS.md` says otherwise:

- `tiptap-plugin` — development app and every plugin's test app. Setting it
  as the test app adds the plugin's Testing version (`<plugin_id>_dev` in the
  app JSON); develop and verify changes here on a feature branch.
- `nocode-to-knowcode` — publicly accessible demo pages. They run released
  versions; update them when a release changes what they show.
  **Buildprint cannot read or change this app** (it is on Bubble's free
  plan). Change it only in the Bubble editor; see
  [Public demo pages](#public-demo-pages).

The active profile in `~/.buildprint/auth.json` is shared by every session on
the machine. Never run `buildprint profile switch`, `buildprint link`, or
`buildprint profile create`, and never override `HOME`. If `buildprint profile
list` lacks the profile you need, stop and ask the user to create it.

## Public demo pages

Small edits to `nocode-to-knowcode` (text, links, page settings, a redirect
workflow) go straight into its Bubble editor in the browser.

Build new demo sections in `tiptap-plugin`, then copy them over:

1. Build each section as one group on a `tiptap-plugin` feature branch with
   Buildprint, and verify it there with real clicks and typing.
2. Open both editors in the same browser. Right-click the group →
   **Copy with workflows**, then paste it into the target
   `nocode-to-knowcode` page.
3. Verify the public page in run mode with real clicks.

Design sections so the paste is clean:

- Build demo sections with the released install, not the Testing one. The
  Testing install's elements reference `<plugin_id>_dev`, which does not
  exist in `nocode-to-knowcode`. The released install (`<plugin_id>`) comes
  from a normal Marketplace install or from authorizing the app in the
  plugin's settings; `tiptap-plugin` needs it alongside the Testing install,
  and `nocode-to-knowcode` needs it too.
- Use only features in the released plugin version.
- Depend only on what already exists in `nocode-to-knowcode`: no new
  app-wide styles, option sets, or data types. If a section needs a data
  type, create it in `nocode-to-knowcode` first so the pasted workflows
  find it.
- Keep workflows inside the group; page-level workflows are left behind.

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
BUILDPRINT_PROFILE=<profile> buildprint branch create <app> <issue>-<slug> --from test
BUILDPRINT_PROFILE=<profile> buildprint project clone <app> --branch <issue>-<slug> --dir <workspace-root>
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
