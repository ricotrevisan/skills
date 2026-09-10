# Direct CLI/API example

The native CLI can open a new desktop thread:

```bash
npx t3@latest app /user/rico/imaginary_project
```

Then submit `say hello` in the thread. The directory must exist on the same
machine as the desktop app. This command has no prompt flag and does not submit
that text itself. On a headless server, use the orchestration API instead.

## Submit the prompt without the helper

This standalone Bash example uses the native CLI for authentication and project
registration, and curl/jq for the supported API. Run it on the destination server
with a compatible T3 CLI and running server. It creates the requested directory,
registers it if necessary, then creates a thread and submits exactly `say hello`.
Replace `SOURCE_THREAD` with a thread on that same server whose model/runtime
settings you intend to inherit. Adjust `T3` and `T3_BASE` for that installation.

```bash
set -euo pipefail
T3=(npx --yes t3@latest)
T3_BASE="${T3CODE_HOME:-$HOME/.t3}"
SOURCE_THREAD='<source-thread-id>'
PROJECT='/user/rico/imaginary_project'
ORIGIN=$(jq -r .origin "$T3_BASE/userdata/server-runtime.json")
TOKEN=$("${T3[@]}" auth session issue --base-dir "$T3_BASE" \
  --ttl 5m --label greeting --token-only)
trap 'unset TOKEN' EXIT
# Keep the token out of curl's process arguments; do not enable shell tracing.
api() {
  curl --fail-with-body --silent --show-error \
    --config <(printf 'header = "Authorization: Bearer %s"\n' "$TOKEN") \
    --header 'Content-Type: application/json' "$@"
}
mkdir -p "$PROJECT"
SNAPSHOT=$(api "$ORIGIN/api/orchestration/snapshot")
if ! jq -e --arg p "$PROJECT" \
  '.projects[] | select(.workspaceRoot == $p and .deletedAt == null)' \
  <<< "$SNAPSHOT" >/dev/null; then
  "${T3[@]}" project add --base-dir "$T3_BASE" "$PROJECT"
fi
SNAPSHOT=$(api "$ORIGIN/api/orchestration/snapshot")
THREAD=$(python3 -c 'import uuid; print(uuid.uuid4())')
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# Write the exact request before sending it. Keep this file if the response is lost.
REQUEST=$(mktemp)
jq -e --arg source "$SOURCE_THREAD" --arg p "$PROJECT" \
  --arg id "$THREAD" --arg now "$NOW" '
  (.threads[] | select(.id == $source)) as $s |
  (.projects[] | select(.workspaceRoot == $p and .deletedAt == null)) as $p |
  {type:"thread.turn.start", commandId:($id+"-start"), threadId:$id,
   message:{messageId:($id+"-message"),role:"user",text:"say hello",attachments:[]},
   modelSelection:$s.modelSelection, runtimeMode:$s.runtimeMode,
   interactionMode:"default", createdAt:$now,
   bootstrap:{createThread:{projectId:$p.id,title:"Greeting",
     modelSelection:$s.modelSelection,runtimeMode:$s.runtimeMode,
     interactionMode:"default",branch:null,worktreePath:null,createdAt:$now}}}
' <<< "$SNAPSHOT" > "$REQUEST"
printf 'Thread: %s\nSaved request: %s\n' "$THREAD" "$REQUEST"
api --data-binary "@$REQUEST" "$ORIGIN/api/orchestration/dispatch"
api "$ORIGIN/api/orchestration/snapshot" |
  jq --arg id "$THREAD" '.threads[] | select(.id == $id) | {id,title,session,latestTurn}'
```

A newly accepted turn may still be pending. Repeat the final snapshot/status query
to verify it started. After a lost response, query this saved thread ID before
resubmitting anything; do not rerun the whole example to generate a different ID.
Use the helper when you want persistent duplicate protection and SSH transport.
