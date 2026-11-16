# Personal Google connections (Loggie `personal`)

Account: rico.trevisan@gmail.com. Prefix every call with `~/.local/bin/loggie-account personal`.

| Slug | API | Path prefix (as discovered) | Smoke test |
| --- | --- | --- | --- |
| `google-mail-calendar-personal` | Gmail v1 | `/gmail/v1/...` | `GET /gmail/v1/users/me/profile` |
| | Calendar v3 | none: `/users/me/calendarList`, `/calendars/{id}/events` | `GET /users/me/calendarList` |
| `google-drive-docs-personal` | Drive v3 | none: `/files`, `/about` | `GET /about --query 'fields=user'` |
| | Sheets v4 | `/v4/spreadsheets/...` | |
| | Docs v1, Slides v1 | `/v1/documents/...`, `/v1/presentations/...` | |

- Each connection sends each API to its own Google host through Loggie endpoint groups. Use the paths discovery lists; don't add host prefixes.
- Specs come from APIs.guru: `https://api.apis.guru/v2/specs/googleapis.com/<api>/<version>/openapi.yaml`. To add an API (Tasks, People), add its spec to the matching connection through `loggie-admin`, then propose a routing group for its host. Scopes are fixed at creation, so a new scope needs re-authorization.
- OAuth client: Google Cloud project `loggie-514908`, Web client "Loggie rico.wtf", redirect `https://app.loggie.ai/connections/new`. The consent screen is published but unverified. If Google rejects tokens, re-authorize in Loggie or submit the app for verification.
- Gmail scope is `gmail.modify`: read, label, draft, send; no permanent delete. Sending mail, or changing events or files, is a write: confirm with Rico first.
