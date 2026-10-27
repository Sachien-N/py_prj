# Smart Expense Categorization and Budget Manager

**Owner:** Sachien N · **Registration No.: 23MID0255**

A standalone personal-finance web application with a FastAPI backend, Streamlit dashboard, and its own SQLite database. It records expenses/refunds, applies configurable keyword categorization, tracks overall/category budgets, produces monthly reports, imports/exports CSV, and imports subscription/electricity expenses from Person B and Person C over authenticated REST.

---

## Features

- Expense/refund CRUD with amount, date, merchant, category, payment method, description, currency and transaction type.
- Configurable categories with merchant keywords, priority, colour and active state.
- Rule-based automatic categorization; explicit categories override the rule.
- Refund records linked to original expenses, with total-refund validation and net-spending calculations.
- Overall monthly budgets and category budgets with usage, remaining balance and exceeded alerts.
- Date-range filtering, search, transaction history, category summaries and monthly reports.
- Plotly charts for category share, six-month trend, budget vs actual, and daily/monthly spending.
- Validated CSV import (atomic: invalid file imports nothing) and safe CSV export.
- Authenticated B→A subscription expense import and C→A electricity expense import.
- Deduplication by `(source_app, external_id)`; repeated syncs update rather than duplicate.
- Graceful offline handling: failed sync returns 503, records safe failure state, preserves the last successful timestamp, and never fabricates external data.
- Explicit owner/project information page.

## Architecture

```text
Streamlit dashboard (ui/) ──HTTP/JSON──► FastAPI (api.py) ──SQLAlchemy──► data/person_a.db
                                                ▲
                          X-API-Key JSON pushes │
                          Person B / Person C ───┘
```

- The UI never imports the ORM and never opens SQLite directly.
- Services contain business logic and calculations; API routes handle HTTP/auth/validation.
- Monetary values use `Decimal`/`Numeric(14,2)` and serialize as two-decimal strings.
- SQLite foreign keys are enabled with `PRAGMA foreign_keys=ON`.

## Setup

From the workspace root (assuming the shared venv is active):

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_a_expense_manager"
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # already present in this workspace
```

Configuration (`.env`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/person_a.db` | Own database |
| `API_BASE_URL` | `http://127.0.0.1:8001` | Dashboard → API |
| `PERSON_B_API_URL` | `http://127.0.0.1:8002` | Pull subscription data |
| `PERSON_C_API_URL` | `http://127.0.0.1:8003` | Pull electricity data |
| `PERSON_B_SYNC_API_KEY` | dev key | Must match B's `PERSON_A_SYNC_API_KEY` |
| `PERSON_C_SYNC_API_KEY` | dev key | Must match C's `PERSON_A_SYNC_API_KEY` |
| `INTEGRATION_TIMEOUT_SECONDS` | `5` | Outbound timeout |
| `INTEGRATION_RETRIES` | `2` | Transient retries |
| `CORS_ORIGINS` | local Streamlit origin | Allowed dashboard origins |

## Run

Two terminals from this directory:

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8001
python -m streamlit run app.py --server.port 8501
```

Dashboard: http://127.0.0.1:8501  
API docs: http://127.0.0.1:8001/docs  
Health: http://127.0.0.1:8001/health

The database and default categories are created on first API start.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health and owner identity |
| GET | `/project-info` | Project metadata |
| GET | `/categories` | List categories (`include_inactive`) |
| POST | `/categories` | Create category |
| PUT | `/categories/{id}` | Update category |
| DELETE | `/categories/{id}` | Delete unused category |
| GET | `/expenses` | Filter by dates/category/search/type/source |
| POST | `/expenses` | Create expense or refund |
| GET | `/expenses/{id}` | Expense detail |
| PUT | `/expenses/{id}` | Update local expense |
| DELETE | `/expenses/{id}` | Delete local expense |
| GET | `/expenses/summary` | Totals, categories, payments, sources |
| GET | `/expenses/export.csv` | Filtered CSV export |
| POST | `/expenses/import/csv` | Validated atomic CSV import |
| GET | `/budgets?month=YYYY-MM` | Budget overview with usage |
| POST | `/budgets` | Create overall/category budget |
| PUT | `/budgets/{id}` | Update budget |
| DELETE | `/budgets/{id}` | Delete budget |
| GET | `/reports/monthly?month=YYYY-MM&months=6` | Monthly report and trend |
| GET | `/integrations/status` | Local sync state and optional live health |
| POST | `/integrations/subscriptions/sync` | Accept B push; empty body pulls from B |
| POST | `/integrations/electricity/sync` | Accept C push; empty body pulls from C |

Integration endpoints require `X-API-Key`. OpenAPI docs contain the full schemas.

## Business rules

- **Net spending** = expense records − refund records. Refund amounts are positive but reduce net spending.
- A refund may reference an original expense; refunds cannot exceed the original amount or change currency.
- If no category is supplied and auto-categorization is enabled, the longest matching keyword wins; ties break by category priority then name. No match → `Miscellaneous`.
- Imported external rows are read-only in Person A. Change them at the source.
- Budget “spent” is net spending in the month for the budget scope. If an overall budget exists it is used for the dashboard headline; otherwise category budgets are summed.
- Multi-currency rows are stored, but top-level totals are for the requested currency (default INR); no FX conversion is invented.

## CSV import format

Required headers: `date`, `amount`, `merchant`. Optional: `category`, `payment_method`, `description`, `transaction_type`, `currency`.

```csv
date,amount,merchant,category,payment_method,description,transaction_type,currency
2026-10-01,100.00,Metro card,Transport,upi,Commute,expense,INR
2026-10-02,450.00,Apollo pharmacy,,card,Medicines,expense,INR
```

- UTF-8 (with or without BOM), maximum 2 MB and 5,000 rows.
- Invalid rows return HTTP 422 with row-level messages and **no rows are inserted**.
- Export protects text cells from spreadsheet formula injection.

## Integration

See the root [INTEGRATION.md](../INTEGRATION.md) for full payloads. Example B→A request:

```python
import requests
requests.post(
    "http://127.0.0.1:8001/integrations/subscriptions/sync",
    headers={"X-API-Key": "dev-person-b-to-a-key"},
    json=payload,
    timeout=10,
)
```

Person A accepts either a pushed payload or, with an empty body, pulls from the configured Person B/C URL. External records are keyed by `source_app + external_id` and upserted.

Example imported lookup:

```powershell
Invoke-RestMethod "http://127.0.0.1:8001/expenses?source_app=person_b"
Invoke-RestMethod "http://127.0.0.1:8001/integrations/status?check_remote=true"
```

## Data model

`categories` → `expenses` and `budgets`; external imports additionally create `imported_external_expenses` audit rows. `integration_sync_state` stores last attempt/success, safe error and counts per source. Indexes cover dates, status and practical lookups; unique constraints protect category names and external IDs.

Database file: `data/person_a.db`.

## Tests

```powershell
python -m pytest -q
```

Verified result: **16 passed**.

Tests cover API/health identity, CRUD, validation, auto-categorization/override, refund cap and net calculation, filters, budgets (usage/remaining/exceeded/duplicates), monthly report aggregation, CSV validation/atomicity/export, auth, idempotent imports, wrong key, malformed payloads, and offline pull failure without fabricated rows.

## Known limitations

- Single-user local app; no login/multi-tenant isolation.
- Default development API keys are stored in `.env` for local demonstration.
- No FX conversion; headline budgets are INR.
- Imported data must be corrected at its source.
- No Alembic migrations; schema changes in this academic scope require recreating the SQLite file.
- Streamlit pages were exercised headlessly; no exhaustive multi-browser visual testing.
