# Three Independent Python Projects with REST API Integration

Three complete, separately runnable Python web applications built with **FastAPI + Streamlit + SQLAlchemy + SQLite** for the academic project team below. Each application has its own backend, dashboard, database, tests, configuration, and README. They communicate **only** through authenticated JSON over HTTP.

| Project | Owner | Registration No. | Application |
|---|---|---|---|
| Person A | **Sachien N** | **23MID0255** | Smart Expense Categorization and Budget Manager |
| Person B | **Shravan N A** | **23MID0445** | Smart Subscription Manager |
| Person C | **HARIHARAN S** | **23MID0182** | Smart Home Electricity Monitoring and TNEB Bill Verification System |

> No database file is shared between projects. Person B and Person C remain fully functional when Person A is offline. The electricity project never claims that TNEB/TANGEDCO issued an incorrect bill.

---

## 1. Folder tree

```text
Three_Person_Python_Projects/
├── README.md
├── INTEGRATION.md
├── requirements-all.txt
├── pytest.ini
├── run_all.py
│
├── person_a_sachien_n_23MID0255/
│   ├── app.py                      # Streamlit entry point
│   ├── api.py                      # FastAPI application
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── errors.py
│   ├── services/
│   │   ├── category_service.py
│   │   ├── expense_service.py
│   │   ├── budget_service.py
│   │   ├── report_service.py
│   │   ├── csv_service.py
│   │   ├── integration_service.py
│   │   └── common.py
│   ├── ui/
│   │   ├── api_client.py
│   │   └── dashboard.py
│   ├── tests/                      # 16 tests
│   ├── data/person_a.db            # created on first API start
│   ├── .streamlit/config.toml
│   ├── requirements.txt
│   ├── .env / .env.example
│   └── README.md
│
├── person_b_shravan_n_a_23MID0445/
│   ├── app.py
│   ├── api.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── errors.py
│   ├── services/
│   │   ├── billing.py
│   │   ├── subscription_service.py
│   │   ├── payment_service.py
│   │   ├── renewal_service.py
│   │   ├── integration_service.py
│   │   └── common.py
│   ├── ui/
│   │   ├── api_client.py
│   │   └── dashboard.py
│   ├── tests/                      # 13 tests
│   ├── data/person_b.db
│   ├── .streamlit/config.toml
│   ├── requirements.txt
│   ├── .env / .env.example
│   └── README.md
│
├── person_c_hariharan_s_23MID0182/
│   ├── app.py
│   ├── api.py
│   ├── seed_demo.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── errors.py
│   ├── services/
│   │   ├── socket_service.py
│   │   ├── reading_service.py
│   │   ├── tariff_service.py
│   │   ├── cost_service.py
│   │   ├── bill_service.py
│   │   ├── bill_comparison_service.py
│   │   ├── historical_analysis_service.py
│   │   ├── expense_service.py
│   │   ├── integration_service.py
│   │   ├── demo_service.py
│   │   ├── common.py
│   │   └── adapters/             # manual / simulated / future vendor contract
│   ├── ui/
│   │   ├── api_client.py
│   │   └── dashboard.py
│   ├── tests/                      # 16 tests
│   ├── data/person_c.db
│   ├── .streamlit/config.toml
│   ├── requirements.txt
│   ├── .env / .env.example
│   └── README.md
│
└── integration_tests/              # 9 live cross-project tests
    ├── conftest.py
    ├── test_integration.py
    └── test_offline_safety.py
```

Generated folders such as `.venv/`, `__pycache__/`, `.pytest_cache/` and the SQLite files are intentionally not part of the source tree listing.

---

## 2. Architecture

```text
                  authenticated JSON over HTTP
  ┌────────────────────────┐        B → A        ┌────────────────────────┐
  │ Person B               │  X-API-Key header   │ Person A               │
  │ Subscription Manager   ├────────────────────►│ Expense Manager        │
  │ FastAPI :8002          │                     │ FastAPI :8001          │
  │ Streamlit :8502        │                     │ Streamlit :8501        │
  │ data/person_b.db       │                     │ data/person_a.db       │
  └────────────────────────┘                     │                        │
             ▲                                   │ Imported external      │
             │ manual browser use                │ expenses + sync state  │
             │                                   │                        │
  ┌────────────────────────┐        C → A        │                        │
  │ Person C               │  X-API-Key header   │                        │
  │ Electricity Monitoring ├────────────────────►│                        │
  │ FastAPI :8003          │                     │                        │
  │ Streamlit :8503        │                     └────────────────────────┘
  │ data/person_c.db       │
  └────────────────────────┘
```

- **No shared code at runtime, no shared database, no direct cross-database query.**
- Person A can also *pull* the documented payloads with `POST /integrations/.../sync` and an empty body.
- Person B sends monthly recurring-cost shares (estimated) or recorded actual payment amounts, never claiming that a payment was processed automatically.
- Person C sends actual bills where available, otherwise clearly marked tariff estimates, and never invents a missing month.

See [INTEGRATION.md](INTEGRATION.md) for exact authentication, payload schemas, idempotency and failure behaviour.

For a three-computer deployment (Person A on Windows, Person B and Person C on separate macOS systems), use [RUN_GUIDE_A_WINDOWS_BC_MACOS.txt](RUN_GUIDE_A_WINDOWS_BC_MACOS.txt).

---

## 3. Prerequisites

- **Python 3.11 or newer** (verified here with Python 3.13.5 on Windows).
- Windows PowerShell (commands below) or an equivalent shell.
- Internet access only for the one-time dependency installation.
- No Node.js, JavaScript/TypeScript application code, PHP, Java or other language is used. Streamlit's small bundled browser UI is Python-driven.

The verification environment uses this workspace:

```text
Workspace: D:\Documents\New folder
Projects:  D:\Documents\New folder\Three_Person_Python_Projects
Venv:      D:\Documents\New folder\.venv
```

### Install dependencies (exact commands)

```powershell
cd "D:\Documents\New folder"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r "Three_Person_Python_Projects\requirements-all.txt"
```

Each project has its own identical pinned `requirements.txt` if you prefer installing per project:

```powershell
python -m pip install -r "Three_Person_Python_Projects\person_a_sachien_n_23MID0255\requirements.txt"
python -m pip install -r "Three_Person_Python_Projects\person_b_shravan_n_a_23MID0445\requirements.txt"
python -m pip install -r "Three_Person_Python_Projects\person_c_hariharan_s_23MID0182\requirements.txt"
```

Create working environment files (they are already present in this workspace):

```powershell
Copy-Item "Three_Person_Python_Projects\person_a_sachien_n_23MID0255\.env.example" "Three_Person_Python_Projects\person_a_sachien_n_23MID0255\.env"
Copy-Item "Three_Person_Python_Projects\person_b_shravan_n_a_23MID0445\.env.example" "Three_Person_Python_Projects\person_b_shravan_n_a_23MID0445\.env"
Copy-Item "Three_Person_Python_Projects\person_c_hariharan_s_23MID0182\.env.example" "Three_Person_Python_Projects\person_c_hariharan_s_23MID0182\.env"
```

The development API keys in the examples default to matching values. Replace them before any shared or non-local use.

---

## 4. Start all six services with one command

```powershell
cd "D:\Documents\New folder"
.\.venv\Scripts\Activate.ps1
cd "Three_Person_Python_Projects"
python run_all.py
```

URLs printed by the launcher:

| Service | URL |
|---|---|
| Person A dashboard | http://127.0.0.1:8501 |
| Person A API + Swagger | http://127.0.0.1:8001 · http://127.0.0.1:8001/docs |
| Person B dashboard | http://127.0.0.1:8502 |
| Person B API + Swagger | http://127.0.0.1:8002 · http://127.0.0.1:8002/docs |
| Person C dashboard | http://127.0.0.1:8503 |
| Person C API + Swagger | http://127.0.0.1:8003 · http://127.0.0.1:8003/docs |

### If a suggested port is already in use

`run_all.py` detects occupied ports and refuses to start. Use a coordinated offset; the launcher rewires all API base URLs automatically:

```powershell
python run_all.py --port-offset 100
```

That produces APIs at **8101/8102/8103** and dashboards at **8601/8602/8603**. During verification, an unrelated process was already listening on port 8001 in this environment, so the smoke test was performed with `--port-offset 100`.

Press **Ctrl+C** to stop all six child processes cleanly. The launcher prints the manual commands on exit.

---

## 5. Start each project independently

All commands assume the virtual environment is activated. Use **three terminals** for a complete system, or start only the project you need.

### Person A — Expense Manager

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_a_sachien_n_23MID0255"
python -m uvicorn api:app --host 127.0.0.1 --port 8001
# second terminal
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_a_sachien_n_23MID0255"
python -m streamlit run app.py --server.port 8501
```

### Person B — Subscription Manager

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_b_shravan_n_a_23MID0445"
python -m uvicorn api:app --host 127.0.0.1 --port 8002
# second terminal
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_b_shravan_n_a_23MID0445"
python -m streamlit run app.py --server.port 8502
```

### Person C — Electricity Monitoring

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_c_hariharan_s_23MID0182"
python -m uvicorn api:app --host 127.0.0.1 --port 8003
# second terminal
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_c_hariharan_s_23MID0182"
python -m streamlit run app.py --server.port 8503
```

The database file is created automatically and seeded with default categories (A) or a clearly-labelled illustrative tariff (C) on first API start.

---

## 6. Databases

| Project | SQLite file | Main tables |
|---|---|---|
| Person A | `person_a_sachien_n_23MID0255/data/person_a.db` | `expenses`, `categories`, `budgets`, `imported_external_expenses`, `integration_sync_state` |
| Person B | `person_b_shravan_n_a_23MID0445/data/person_b.db` | `subscriptions`, `subscription_payments`, `renewal_reminders`, `integration_sync_state` |
| Person C | `person_c_hariharan_s_23MID0182/data/person_c.db` | `sockets`, `electricity_readings`, `tariff_configs`, `tariff_slabs`, `tariff_components`, `electricity_bills`, `bill_comparisons`, `integration_sync_state` |

The database URLs are configured independently in each `.env`:

```dotenv
DATABASE_URL=sqlite:///./data/person_a.db
DATABASE_URL=sqlite:///./data/person_b.db
DATABASE_URL=sqlite:///./data/person_c.db
```

The automated tests override `DATABASE_URL` with temporary test databases and never use the demonstration files.

The three delivered demo databases are initialised and contain demonstration records: Person A has local expenses/budgets plus imported subscription/electricity records, Person B has sample subscriptions/payments/reminders, and Person C has clearly-labelled simulated sockets/readings/bills and comparisons. Delete the `.db` files (with the APIs stopped) for a completely empty first run.

Reset a demonstration database (only when you intentionally want to erase that project's data):

```powershell
# Stop the relevant API first.
Remove-Item "person_a_sachien_n_23MID0255\data\person_a.db"
Remove-Item "person_b_shravan_n_a_23MID0445\data\person_b.db"
Remove-Item "person_c_hariharan_s_23MID0182\data\person_c.db"
```

---

## 7. Configuration

Each project loads its own `.env` (`python-dotenv`, existing environment variables take precedence). Important variables:

| Variable | Project | Purpose |
|---|---|---|
| `DATABASE_URL` | A/B/C | Independent SQLite URL |
| `API_BASE_URL` | A/B/C | URL used by that project's Streamlit dashboard |
| `PERSON_B_API_URL` | A | Where A pulls subscription data |
| `PERSON_C_API_URL` | A | Where A pulls electricity data |
| `PERSON_A_API_URL` | B/C | Destination for sync pushes |
| `PERSON_B_SYNC_API_KEY` | A | Must equal `PERSON_A_SYNC_API_KEY` in B |
| `PERSON_C_SYNC_API_KEY` | A | Must equal `PERSON_A_SYNC_API_KEY` in C |
| `INTEGRATION_TIMEOUT_SECONDS` | A/B/C | Outbound HTTP timeout (default 5) |
| `INTEGRATION_RETRIES` | A/B/C | Transient retry count (default 2) |
| `TIMEZONE` | C | Local calendar timezone (default `Asia/Kolkata`) |
| `DISCREPANCY_TOLERANCE_PERCENT` | C | Default bill-deviation tolerance (default 10) |
| `MAX_READING_GAP_HOURS` | C | Longer intervals are excluded and reported (default 4) |

No production secrets are embedded in code. The checked-in development keys are explicitly local-only.

---

## 8. Tests — commands and actual results

Run each project's suite from that project's directory, then the cross-project suite from the root.

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_a_sachien_n_23MID0255"
python -m pytest -q

cd "..\person_b_shravan_n_a_23MID0445"
python -m pytest -q

cd "..\person_c_hariharan_s_23MID0182"
python -m pytest -q

cd ".."
python -m pytest -q
```

Latest executed results (after the final code changes):

| Suite | Result | Coverage focus |
|---|---|---|
| Person A | **16 passed** | CRUD, validation, refunds, budgets, monthly reports, CSV atomic import/export, auth, dedup, remote failure |
| Person B | **13 passed** | cycle projections, renewals, statuses, payment idempotency, reminders, payload generation, offline safety |
| Person C | **16 passed** | energy intervals, reading validation, gaps, tariff slabs/components, bill comparison, six-month analysis, exports, offline safety |
| Cross-project | **9 passed** | live B→A, C→A, API keys, invalid payloads, A pull, health, database separation, currency/date consistency, A-offline preservation |

The integration suite starts real Uvicorn processes on temporary databases (ports 8011–8013) and shuts them down afterwards. The A-offline test starts an isolated Person B instance pointed at an unreachable Person A.

Dashboard verification: all pages of all three Streamlit apps were executed headlessly with `streamlit.testing.v1.AppTest`; real form submissions were exercised for Person A expenses, Person B subscriptions, Person C sockets, Person C bill comparison, Person C six-month analysis, and Person C tariff creation. The six Streamlit servers were also health-checked through the launcher. This is not a substitute for a full cross-browser visual review.

---

## 9. Integration examples

Full schemas and examples are in [INTEGRATION.md](INTEGRATION.md). Short examples:

### Person B → Person A push

```http
POST http://127.0.0.1:8001/integrations/subscriptions/sync
X-API-Key: dev-person-b-to-a-key
Content-Type: application/json

{
  "source_app": "person_b",
  "generated_at": "2026-10-21T10:05:00",
  "billing_period": "2026-10",
  "summary": {"active_subscriptions": 1},
  "expense_records": [
    {
      "source_app": "person_b",
      "external_id": "sub:1:2026-10",
      "subscription_id": 1,
      "service_name": "Netflix",
      "category": "Entertainment",
      "amount": "499.00",
      "currency": "INR",
      "billing_period": "2026-10",
      "billing_date": "2026-10-15",
      "record_updated_at": "2026-10-21T10:05:00",
      "is_estimate": true,
      "description": "Estimated monthly recurring share"
    }
  ]
}
```

Typical success response:

```json
{
  "source": "person_b",
  "status": "success",
  "billing_period": "2026-10",
  "records_received": 1,
  "records_imported": 1,
  "records_updated": 0,
  "message": "Subscription expenses imported idempotently"
}
```

### Person C → Person A push

```http
POST http://127.0.0.1:8001/integrations/electricity/sync
X-API-Key: dev-person-c-to-a-key
Content-Type: application/json

{
  "source_app": "person_c",
  "generated_at": "2026-10-21T10:05:00",
  "summary": {"records": 1, "actual_records": 1},
  "expense_records": [
    {
      "source_app": "person_c",
      "external_id": "electricity:2026-09",
      "period": "2026-09",
      "billing_date": "2026-09-30",
      "expense_amount": "2840.50",
      "currency": "INR",
      "units": "312.00",
      "is_estimate": false,
      "description": "Actual electricity bill",
      "record_updated_at": "2026-10-01T09:00:00",
      "data_coverage_pct": "96.40"
    }
  ]
}
```

Repeated requests with the same `external_id` update the existing Person A expense and never insert a duplicate.

---

## 10. Demonstration data

- **Person A:** add expenses, refunds and budgets from the dashboard; import a CSV; use the Integrations page to pull from B/C when they are running.
- **Person B:** add subscriptions, record actual payments, refresh renewal reminders.
- **Person C:** generate clearly-labelled simulated data in **Integrations → Simulated demonstration data** or run:

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_c_hariharan_s_23MID0182"
python seed_demo.py --months 6 --force
```

Every generated socket, reading and bill is marked as simulated or demo. The seeded tariff is explicitly **not** an official TNEB tariff.

---

## 11. Security notes

- Integration endpoints require `X-API-Key`; comparison uses constant-time `hmac.compare_digest`.
- Keys are read from environment variables / `.env`; responses never include keys.
- Pydantic constrains amounts, dates, strings, periods and payload shapes. Totals are computed by the backend.
- SQLAlchemy ORM parameter binding is used throughout.
- CSV uploads are extension/content-type checked and size-limited (2 MB for A and C).
- Generic error handlers avoid exposing stack traces and secrets to users.
- CORS is restricted to the local dashboard origins.
- No user login is implemented, so this is a **single-user local academic application**, not a multi-tenant deployment.
- Development keys must be changed before sharing the application.

---

## 12. Known limitations (honest list)

1. **No physical smart-plug, vendor API or MQTT integration.** Person C implements manual readings, simulation, and a documented adapter interface for future hardware.
2. **No official TNEB/TANGEDCO tariff is bundled.** The seeded tariff is illustrative and unverified; users must configure and verify current rates, slabs, fixed charges, duties and effective dates.
3. **Socket coverage is partial by nature.** Energy results cover monitored sockets only. Temporal data coverage is reported; it is not whole-house coverage.
4. **No payment provider.** Person B records actual payments manually and never claims a payment was processed automatically.
5. **Single currency headline totals.** APIs store currency; Person A/B dashboards show INR headline totals and do not perform FX conversion.
6. **One actual payment per subscription per billing period** in Person B, which prevents duplicate external requests but does not model split payments.
7. **No user authentication or role-based access** in the dashboards.
8. **Person C's fixed monthly tariff components are applied once per estimate**, not prorated by days; this is documented in each estimate.
9. **The six-month analysis is evidence-based but not conclusive.** It never asserts that a utility bill is incorrect.
10. **Browser rendering** was smoke-tested headlessly, not exhaustively across Chrome/Firefox/Edge.
11. **Development secrets** are stored in local `.env` files and are only appropriate for local use.
12. **No migrations framework.** Tables are created with `Base.metadata.create_all`; schema changes for this academic scope require recreating the SQLite file or adding a small migration script.

---

## 13. Troubleshooting

| Symptom | Fix |
|---|---|
| Dashboard says API offline | Start that project's Uvicorn process and check `API_BASE_URL` in its `.env`. |
| Port already in use | Stop the other process or use `python run_all.py --port-offset 100`. |
| Integration returns 401 | Keys on sender and receiver do not match. Check both `.env` files. |
| Integration returns 503 | The destination API is offline or timed out. Local sender data is preserved; retry when it is back. |
| C comparison says no usable readings | Add readings that span the billing period; intervals longer than `MAX_READING_GAP_HOURS` are excluded. |
| C says no active tariff | Add a tariff effective for the bill's end date and make it active. |
| A dashboard shows no integrated data | Run B/C sync from their dashboards or A's Integrations page while the other APIs are online. |
| Non-ASCII characters look garbled in Windows console | This is a console encoding issue; browser/JSON responses are UTF-8. Set `PYTHONIOENCODING=utf-8` if needed. |
| Tests leave temporary files | Each suite uses separate temporary databases in its `tests/` folder and the integration suite uses a system temp directory. |
