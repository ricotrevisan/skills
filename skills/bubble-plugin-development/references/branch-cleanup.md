# Bubble branch cleanup

Branch merge and deletion are destructive external changes. Resolve the exact
app, source branch, destination branch, and task-created resources first. Ask
for confirmation immediately before the merge or deletion unless the user has
just authorized those exact targets.

## Before cleanup

1. Verify the feature branch diff and real preview.
2. Record the branch name and Bubble-assigned version id.
3. Create or identify a rollback/savepoint when the platform supports it.
4. Confirm that no other active task uses the branch or its demo pages.

Use Buildprint's supported merge command when available. Do not assume merge
permission from an earlier request to edit or test.

## Tiptap branch deletion helper

The bundled `scripts/delete-bubble-branch.sh` is a fallback for Bubble versions
where the CLI exposes no deletion command. It drives the Bubble editor through
`browserq` (Chrome, 1700×1050 viewport) using the `BUBBLE_COOKIE` editor login,
which it pipes to `browserq cookies import`. It clicks the branch row by exact
text, opens the branch's `…` menu by coordinates, and proceeds only if the menu
shows the branch's Buildprint ID and the dialog names the branch. Inspect the
script before every use and prefer a supported Buildprint or Bubble operation
when one exists.

Rehearse first, then delete after explicit approval:

```sh
skill_dir="${AGENT_SKILL_DIR:-$HOME/.agents/skills/bubble-plugin-development}"
"$skill_dir/scripts/delete-bubble-branch.sh" --dry-run <exact-branch-name>
"$skill_dir/scripts/delete-bubble-branch.sh" <exact-branch-name>
```

`--dry-run` stops at the confirmation dialog and closes it. Opening a branch in
the editor (including in a dry run) updates its "Updated" time in Bubble. The
app defaults to `tiptap-plugin` (`BUBBLE_APP`, `BUILDPRINT_PROFILE=ricowtf`).
Screenshots are printed as browserq artifact paths.

Requirements:

- `BUBBLE_COOKIE` is set without being printed.
- `browserq` is running on this machine and the Buildprint CLI can list the
  app's branches.
- The Bubble editor layout still matches the helper (`…` menu at 276,66);
  the ID check stops it if the layout drifts.

The helper reports success only when `buildprint branch list` no longer lists
the branch.
Treat “not listed” as ambiguous until you separately verify the app and branch
selector. Completion requires confirming that the exact branch no longer
appears and that the intended destination branch still contains the merged
changes.
