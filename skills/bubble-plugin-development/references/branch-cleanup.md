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

The bundled `scripts/delete-bubble-branch.js` is a Tiptap-specific fallback for
Bubble versions where the CLI exposes no deletion command. It drives the Bubble
editor with a fixed 1700×1050 viewport, hard-coded app/login details, and a few
coordinate clicks. Inspect the script before every use and prefer a supported
Buildprint or Bubble operation when one exists.

After explicit deletion approval:

```sh
skill_dir="${AGENT_SKILL_DIR:-$HOME/.agents/skills/bubble-plugin-development}"
node "$skill_dir/scripts/delete-bubble-branch.js" <exact-branch-name>
```

Requirements:

- `BUBBLE_COOKIE` is set without being printed.
- Playwright and its Chromium build are already installed.
- The Bubble editor layout still matches the helper's expected viewport.

Treat “not listed” as ambiguous until you separately verify the app and branch
selector. Completion requires confirming that the exact branch no longer
appears and that the intended destination branch still contains the merged
changes.
