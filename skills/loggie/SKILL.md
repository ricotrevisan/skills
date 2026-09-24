---
name: loggie
description: Access connected services through the Loggie CLI. Use when the user mentions Loggie, or when a task needs an external service integration that is not available through the session's tools; check Loggie's live catalog before concluding access is unavailable.
---

## Loggie account routing

Before any Loggie discovery or call, read `~/.loggie/ACCOUNTS.md` and use `~/.local/bin/loggie-account personal ...` for rico.wtf/personal work or `~/.local/bin/loggie-account work ...` for MocharyMethod/Defacto. Apply that account prefix to every `loggie` example below. Profile names can repeat across accounts; keep the account and connection paired.

# Loggie

Loggie is available through the shell as `loggie` (fallback: `~/.local/bin/loggie`), even when no Loggie MCP tools appear in the session. It proxies authenticated requests to connected services.

## Discover and call

1. Run `loggie setup` to obtain the current profile, integration slugs, account labels, readiness, permissions, and routing instructions. Use this live catalog rather than a saved integration list.
2. Select the integration matching the user's intended service and account. Similar services can have multiple slugs. Resolve the account from task context; ask only if the remaining ambiguity affects the requested action. A pending integration is not ready to use.
3. Discover the relevant endpoints and inspect the chosen endpoint's parameters before constructing a request:

   ```bash
   loggie discover <slug> --search <term> --limit 10
   loggie discover <slug> --endpoint <path> --method GET
   ```

   For GraphQL, use `--graphql-type query` (or `mutation`) with `--operation <name>` to inspect an operation. Use `loggie discover --help` for filtering and pagination options.
4. Call the discovered method and path through Loggie:

   ```bash
   loggie call <slug> GET <path> --query 'limit=10'
   loggie call <slug> POST <path> --body '{"field":"value"}'
   ```

   These are syntax templates; substitute discovered paths, parameters, and values. Follow discovery's path conventions rather than guessing API prefixes. Use `loggie call --help` for multipart forms, binary uploads, and headers. Read endpoint details on demand instead of loading every integration's schema.

## Authentication and failures

- Use the selected account's saved credential. `loggie-account <account> status` reports its profile and auth source. If authentication is missing, use the named credential setup in `~/.loggie/ACCOUNTS.md`; preserve the existing default login and keep keys out of output.
- Route Loggie integration traffic through its proxy, as instructed by setup. The CLI handles this; direct HTTP access uses `/api/proxy/{integrationSlug}/{path}` with the Loggie `x-api-key` header.
- Inspect proxy errors, including `details.upstream_body` when present. Refresh setup or endpoint discovery when errors suggest stale routing or permissions. For sandbox network failures, use the environment's normal escalation mechanism.
- Read/write permissions describe technical access, not user authorization. Stay within the requested task. Before retrying a write after an uncertain response, check whether it succeeded or use endpoint-supported idempotency.

Use service-specific workflow guidance when it adds account conventions or operational context; obtain endpoint syntax from live discovery.
