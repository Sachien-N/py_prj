# API Contracts

Every application publishes an interactive OpenAPI page at
`http://127.0.0.1:{port}/docs`. This document summarises the endpoints that
matter for the integration demo and the repository-level contract tests
(`tests/test_api_integration.py` enforces them).

Authentication for cross-project calls uses a per-pair `X-API-Key` header.
Development keys (placeholders, replaceable in each `.env`):

| Pair | Header used by | Development value |
|---|---|---|
| B → A | B pushing to A | `dev-person-b-to-a-key` |
| C → A | C pushing to A | `dev-person-c-to-a-key` |

## Person A — Smart Expense API (port 8001)

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness (`{"status": "healthy"}`) |
| `POST /expenses`, `GET /expenses`, `PATCH /expenses/{id}`, `DELETE /expenses/{id}` | Local expense CRUD (supports `?source_app=` filter for imported rows) |
| `GET /expenses/report`, `GET /expenses/export.csv` | Aggregated reports and CSV export |
| `POST /categories`, `GET /categories`, `PATCH/DELETE /categories/{id}` | Category management |
| `POST /budgets`, `GET /budgets`, `PATCH/DELETE /budgets/{id}` | Budget management with progress data |
| `POST /integrations/subscriptions/sync` | **Receives** Person B's subscription expenses (key: B→A). Empty body = pull from B instead |
| `POST /integrations/electricity/sync` | **Receives** Person C's electricity expenses (key: C→A). Empty body = pull from C instead |
| `GET /integrations/status` | Per-source sync state: last success/failure, items received |

### B→A payload (abridged)

```json
{
  "source_app": "person_b",
  "generated_at": "2026-10-20T10:00:00",
  "billing_period": "2026-10",
  "summary": {"active_subscriptions": 1},
  "expense_records": [{
      "source_app": "person_b",
      "external_id": "sub:1:2026-10",
      "service_name": "Netflix",
      "category": "Entertainment",
      "amount": "499.00",
      "currency": "INR",
      "billing_period": "2026-10",
      "billing_date": "2026-10-15",
      "record_updated_at": "2026-10-20T10:00:00",
      "is_estimate": true,
      "description": "Expected monthly subscription cost"
  }]
}
```

Success: `200 {"records_imported": 1, "records_updated": 0, "status": "success", ...}`.
Repeating the identical payload yields `records_imported: 0,
records_updated: 1` — the import is **idempotent** on
`(source_app, external_id)`; `record_updated_at` decides whether a newer
version replaces an older one.

## Person B — Smart Subscription API (port 8002)

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness |
| `POST/GET/PATCH/DELETE /subscriptions` | Subscription CRUD (cycles: weekly…custom N days) |
| `POST/GET/DELETE /payments` | Payment history |
| `GET /renewals/upcoming` | Renewal calendar (`UPCOMING_DAYS` window) |
| `GET /subscriptions/export.csv` | CSV export |
| `POST /integrations/person-a/sync` | **Pushes** expenses to A; returns A's response verbatim plus local sync state |
| `GET /integrations/person-a/payload` | **Serves** the payload A pulls (key required) |
| `GET /integrations/person-a/status` | Last push result — honest success/failure with timestamps |

## Person C — Smart Electricity API (port 8003)

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness |
| `POST/GET/PATCH/DELETE /sockets` | Smart-socket registry |
| `POST /sockets/{id}/readings`, `GET /sockets/{id}/readings` | Manual readings; `POST /sockets/{id}/simulate` generates clearly-labelled simulated data |
| `POST/GET /tariffs`, `.../components` | Progressive TNEB-style tariff configuration |
| `POST /bills`, `GET /bills`, `POST /bills/{id}/verify` | Actual bill registration and TNEB bill verification with discrepancy analysis |
| `GET /bills/{id}/evidence` | Six-month evidence trail for a discrepancy investigation |
| `GET /expenses/electricity` | Monthly electricity expenses (actual + estimated) in Person A's payload shape |
| `POST /demo/seed` | Demo data — every record flagged `SIMULATED` |
| `POST /integrations/person-a/sync`, `GET /integrations/person-a/payload`, `GET /integrations/person-a/status` | Push to / serve for / status of the A integration |

## Gateway (port 8000)

| Method & path | Purpose |
|---|---|
| `GET /` | Landing page (owners, design systems, live status snippet) |
| `GET /health` | Gateway liveness |
| `GET /services` | Live probe of all seven registered services |
| `GET /projects` | Ownership/titles/design-system summary |
| `GET /registry` | Machine-readable registry |

## Error and timeout behaviour (all projects)

- Invalid payloads → `422` with Pydantic's field-level details.
- Wrong/missing `X-API-Key` → `401`; keys never appear in responses or logs.
- Producer unreachable during a pull → `503` with `details.status =
  "failure"`; **no partial imports** (local data untouched) and the failure
  is recorded in the integration status of the requester.
- HTTP client timeouts: `INTEGRATION_TIMEOUT_SECONDS` (default 5) with
  `INTEGRATION_RETRIES` (default 2).
