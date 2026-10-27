# Smart Subscription Manager

**Owner:** Shravan N A · **Registration No.: 23MID0445**

A standalone application for recurring services: billing cycles, expected costs, renewal dates, reminders, actual payment history, CSV export, and an authenticated REST push of subscription expense data to Person A.

---

## Features

- Subscription CRUD with service, category, amount, currency, cycle, start date, next renewal, payment method, status and notes.
- Weekly, monthly, quarterly, yearly and custom day-interval billing.
- Active, paused, cancelled and expired statuses.
- Correct annual/monthly equivalents for each cycle, clearly distinguished from actual payments.
- Upcoming renewals, overdue renewals and persisted configurable reminders.
- Actual payment history with idempotency keys and duplicate prevention.
- Search, filter, sort, CSV export.
- Plotly charts for category mix, cycle counts and renewal horizon.
- Authenticated Person B → Person A sync; local data is never lost when Person A is offline.
- Explicit statements that no payment provider integration exists and no payment is processed automatically.
- Owner/project information page.

## Architecture

```text
Streamlit dashboard (ui/) ──HTTP/JSON──► FastAPI (api.py) ──SQLAlchemy──► data/person_b.db
                                                  │
                                                  └── authenticated push ──► Person A :8001
```

The dashboard uses only the HTTP API. Project B has no import of, or connection to, Person A's database.

## Setup

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_b_subscription_manager"
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # already present in this workspace
```

`.env` variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/person_b.db` | Own database |
| `API_BASE_URL` | `http://127.0.0.1:8002` | Dashboard → API |
| `PERSON_A_API_URL` | `http://127.0.0.1:8001` | Sync destination |
| `PERSON_A_SYNC_API_KEY` | dev key | Must match A's `PERSON_B_SYNC_API_KEY` |
| `INTEGRATION_TIMEOUT_SECONDS` | `5` | Outbound timeout |
| `INTEGRATION_RETRIES` | `2` | Transient retries |
| `UPCOMING_DAYS` | `30` | Default renewal horizon |
| `CORS_ORIGINS` | local Streamlit origin | Allowed dashboard origins |

## Run

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8002
python -m streamlit run app.py --server.port 8502
```

Dashboard: http://127.0.0.1:8502  
API docs: http://127.0.0.1:8002/docs  
Health: http://127.0.0.1:8002/health

## Billing mathematics

| Cycle | Annual projection | Monthly equivalent |
|---|---|---|
| Weekly | amount × 52 | annual ÷ 12 |
| Monthly | amount × 12 | annual ÷ 12 |
| Quarterly | amount × 4 | annual ÷ 12 |
| Yearly | amount | annual ÷ 12 |
| Custom every N days | amount × 365 ÷ N | annual ÷ 12 |

Results are rounded half-up to two decimals. Renewal dates use anchor-preserving calendar arithmetic for monthly/quarterly/yearly cycles (e.g. 31 Jan → 29 Feb in a leap year → 31 Mar). Monthly equivalents are **estimates**, not actual payments.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health and owner identity |
| GET | `/project-info` | Project metadata |
| GET | `/meta/categories` | Suggested category labels |
| GET | `/subscriptions` | Search/filter/sort all subscriptions |
| POST | `/subscriptions` | Create subscription |
| GET | `/subscriptions/{id}` | Subscription detail |
| PUT | `/subscriptions/{id}` | Update subscription or status |
| DELETE | `/subscriptions/{id}` | Delete subscription and related local records |
| GET | `/subscriptions/summary` | Counts, projections, category/cycle summaries |
| GET | `/subscriptions/upcoming?days=30` | Upcoming + overdue renewals + reminders |
| POST | `/subscriptions/{id}/advance-renewal` | Move next renewal one interval |
| GET | `/subscriptions/payments` | Actual payment history |
| POST | `/subscriptions/payments` | Record an actual payment (idempotent) |
| DELETE | `/subscriptions/payments/{id}` | Delete a payment record |
| POST | `/subscriptions/reminders/refresh` | Create reminders due inside each reminder window |
| GET | `/subscriptions/reminders` | Pending reminders |
| POST | `/subscriptions/reminders/{id}/dismiss` | Dismiss a reminder |
| GET | `/subscriptions/export.csv` | CSV export |
| GET | `/integrations/person-a/status` | Push state and optional live health |
| GET | `/integrations/person-a/payload` | Documented payload for Person A pulls (**key required**) |
| POST | `/integrations/person-a/sync` | Authenticated push to Person A (**key required**) |

Integration endpoints require `X-API-Key`.

## Integrations

- Push trigger: `POST /integrations/person-a/sync?period=YYYY-MM`.
- Stable external record ID: `sub:<subscription_id>:<YYYY-MM>`.
- Active subscriptions only. If an actual payment exists for the period, its amount and `is_estimate=false` are sent; otherwise the monthly-equivalent recurring share is sent as `is_estimate=true`.
- A failed push records `integration_sync_state`, keeps all local data, and returns HTTP 503. Retry from the dashboard or API.
- The last successful sync timestamp is preserved separately from the last attempt.
- Full schema and examples: root [INTEGRATION.md](../INTEGRATION.md).

Example payload lookups:

```powershell
Invoke-RestMethod "http://127.0.0.1:8002/subscriptions/summary"
Invoke-RestMethod "http://127.0.0.1:8002/integrations/person-a/payload" -Headers @{"X-API-Key"="dev-person-b-to-a-key"}
```

## Data model

- `subscriptions` — recurring service configuration and renewal state.
- `subscription_payments` — manually recorded actual payments; unique idempotency key and one payment per subscription/billing period.
- `renewal_reminders` — persisted pending/dismissed reminders, unique per subscription + renewal date.
- `integration_sync_state` — latest attempt/success, safe error, HTTP status and record count.

Database file: `data/person_b.db`.

## Tests

```powershell
python -m pytest -q
```

Verified result: **13 passed**.

Covered: health/identity, creation, all billing intervals and projections, month-end renewal arithmetic, validation, status changes/search/filter, upcoming/overdue, reminders, payment idempotency, duplicate period prevention, future/currency validation, summary, CSV export, payload generation without secrets, and offline push failure preserving local data.

## Known limitations

- Single-user local application; no login.
- No payment provider; actual payments are user-entered facts only.
- One payment per subscription per billing period in this scope; split payments are not modeled.
- Expected monthly/yearly values are estimates and are not prorated for mid-month starts.
- Multi-currency data is stored per subscription; dashboard headline projections are INR-only with no FX conversion.
- Reminders are created when “Refresh reminders” is used (or via the API), not by a background scheduler.
- No Alembic migrations; recreate the SQLite file for incompatible schema changes.
- Default development key is local-only.
