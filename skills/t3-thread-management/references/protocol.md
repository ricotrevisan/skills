# T3 Code V2 orchestration protocol (0.1.0)

Read when the helper lacks an operation you need. Verified against 0.1.0 on
2026-10-16; the server bundle (`apps/server/dist/binCli-*.mjs`) is the source of
truth for schemas.

## Auth

`t3 auth session issue --base-dir <base> --ttl 5m --token-only --scope ...`
prints a bearer token. Scope names: `t3 auth session issue --help`. The server's
origin is `origin` in `<base>/userdata/server-runtime.json`.

## HTTP (reads)

Headers: `Authorization: Bearer <token>`, `x-t3-orchestration-protocol: 2`.

- `GET /api/orchestration/shell` — `{projects, threads, archivedThreads, snapshotSequence}`.
- `GET /api/orchestration/threads/<urlencoded id>` — `{projection: {thread, runs, messages, ...}}`.
  Also `/bounded`, `/transcript`, `/history?cursor=`.
- `GET /api/projects`, `POST /api/projects/mutate`.

The V1 routes `/api/orchestration/dispatch` and `/api/orchestration/snapshot` are
gone (404 / web app HTML).

## WebSocket RPC (writes)

`GET /ws?orchestrationProtocol=2` with the bearer header (or `?wsTicket=` from
`POST /api/auth/websocket-ticket`). Older clients get HTTP 426
`orchestration_protocol_incompatible`.

Effect RPC, one JSON message (or array) per text frame:

```json
{"_tag":"Request","id":"1","tag":"orchestration.launchThread","payload":{...},"headers":[]}
{"_tag":"Exit","requestId":"1","exit":{"_tag":"Success","value":{...}}}
```

Failures arrive as `exit._tag: "Failure"` with `cause`, or `_tag: "Defect"`.
Answer `{"_tag":"Ping"}` with `{"_tag":"Pong"}`. Streams (`subscribe*`) send
`Chunk` messages and expect `{"_tag":"Ack","requestId":...}`.

Useful methods: `server.getConfig` (providers, models, option descriptors),
`orchestration.launchThread`, `orchestration.dispatchCommand` (V2 commands such
as `thread.archive`, `thread.delete`, `thread.model-selection.set`; each takes
`commandId` + `threadId`), `orchestration.searchThreads` (`{query}`),
`orchestration.getThreadProjection`.

## `orchestration.launchThread` payload

```json
{
  "commandId": "<uuid; same id => same thread, resumed: true>",
  "creationSource": "server",
  "projectId": "<from shell>",
  "title": "Task title",
  "modelSelection": {"instanceId": "codex", "model": "gpt-6-astra",
                     "options": [{"id": "reasoningEffort", "value": "medium"}]},
  "runtimeMode": "approval-required | auto-accept-edits | auto | full-access",
  "interactionMode": "default | plan",
  "workspaceStrategy": {"type": "root"}
                     | {"type": "existing_worktree", "worktreePath": "/abs"}
                     | {"type": "worktree", "baseRef": "main", "branch": "t3code/x", "startFromOrigin": true},
  "initialMessage": {"text": "...", "attachments": []}
}
```

Result: `{threadId, projection, resumed}`. A run's `status` moves through
`waiting` to `completed`; `startedAt` marks provider startup.
