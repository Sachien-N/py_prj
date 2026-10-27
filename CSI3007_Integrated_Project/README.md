# CSI3007 Integrated Project — Three Independent Python Applications

**Course:** CSI3007 · Advanced Python Programming
**Deliverable:** one repository, three independently owned projects, verified API integration.

> **Ownership statement.** The three applications below are *individually
> owned* coursework projects. They are **not** a jointly developed team app.
> Each keeps its own database, business logic, UI and tests; the applications
> exchange only permitted data through documented, key-authenticated REST
> APIs. Names and registration numbers are reproduced exactly as they appear
> in each project's own source files.

| Identity | Owner | Registration No. | Application | Design system | Ports (API / UI) |
|---|---|---|---|---|---|
| Person A | **Sachien N** | **23MID0255** | Smart Expense Categorization and Budget Manager | **Claymorphism** | 8001 / 8501 |
| Person B | **Shravan N A** | **23MID0445** | Smart Subscription Manager | **Glassmorphism** | 8002 / 8502 |
| Person C | **Hariharan S** | **23MID0182** | Smart Home Electricity Monitoring and TNEB Bill Verification System | **Neumorphism** | 8003 / 8503 |

## What was delivered from the uploaded archives

The uploads arrived as four nested ZIP archives (`Upload_Part_01..04.zip`)
containing the eleven original parts (`Part_01.zip` … `Part_11.zip`), plus a
`Three_Person_Python_Projects.zip`. Inspection findings (full detail in
[`docs/input_inventory.md`](docs/input_inventory.md)):

- All eleven parts were **valid, independent ZIPs created with directory
  paths stripped** — the project tree was reconstructed *from file contents*
  (database names, class names, docstrings, ports, owner evidence).
- ~98 % of the archive bytes were a bundled Python virtual environment;
  this is intentionally not copied — `requirements.txt` recreates it.
- The original source tree, the three SQLite databases and the original root
  documentation were **fully recovered: 110 files, 0 missing**.
- The `Three_Person_Python_Projects.zip` upload is a *previously modified*
  variant of the same projects (uniform refactor with `auth.py`, earlier
  timestamps); the parts tree is newer and richer, so it is authoritative.
- Functional validation: per-project suites **16 / 13 / 16 passed** (exactly
  the counts documented in the original README) and **9/9** live
  cross-project integration tests passed.

## The three applications

### Person A — Sachien N (23MID0255) · Claymorphism
Tracks expenses with auto-categorisation, budgets with progress bars,
monthly/category reports and CSV export, plus an **Integrations** page that
receives subscription expenses from Person B and electricity expenses from
Person C. The dashboard uses a soft, tactile clay look: pastel palette,
rounded layered cards, pill buttons — readable and never toy-like.

### Person B — Shravan N A (23MID0445) · Glassmorphism
Manages recurring services: billing cycles, projected monthly/annual costs,
renewal reminders, payment history, CSV export, and an authenticated push of
subscription expenses to Person A. The dashboard uses restrained frosted-glass
panels over a controlled indigo gradient — translucent but readable.

### Person C — Hariharan S (23MID0182) · Neumorphism
Records manual or simulated smart-socket readings, computes interval energy,
applies configurable progressive TNEB-style tariffs, compares estimates with
actual bills and investigates discrepancies with six months of evidence. The
system verifies bills and never claims the utility issued an incorrect bill.
The dashboard uses soft raised/inset surfaces on a single-tone grey canvas
with clear control states. Demo data is always labelled `SIMULATED`.

## Repository structure

```text
CSI3007_Integrated_Project/
├── README.md                        ← this file
├── requirements.txt                 ← pinned dependencies (identical stack)
├── pytest.ini                       ← runs tests/ and integration_tests/
├── .gitignore · .env.example
├── start_all.py                     ← integrated launcher (7 services)
├── run_all.py                       ← original launcher (6 services, no gateway)
├── person_a_sachien_n_23MID0255/    ← complete original application (A)
├── person_b_shravan_n_a_23MID0445/  ← complete original application (B)
├── person_c_hariharan_s_23MID0182/  ← complete original application (C)
├── integration/                     ← api_gateway.py · service_registry.py · health_checks.py
├── shared/                          ← config.py · logging_config.py · exceptions.py
├── scripts/                         ← setup/start for Windows PowerShell & macOS shell
├── integration_tests/               ← 9 live cross-project tests
├── tests/                           ← repository-level test suite
└── docs/                            ← 13 documents incl. originals in docs/original/
```

Each project folder keeps its complete original architecture:

```text
app.py · api.py · config.py · database.py · models.py · schemas.py · errors.py
services/ (business logic) · ui/ (dashboard + api_client + theme)
tests/ · data/person_x.db · .streamlit/config.toml · .env.example · README.md
```

## Architecture and API integration

```text
Browser ─► Streamlit UI ─HTTP─► own FastAPI ─SQLAlchemy─► own SQLite
Person B :8002 ──POST /integrations/subscriptions/sync (X-API-Key)──► Person A :8001
Person C :8003 ──POST /integrations/electricity/sync  (X-API-Key)──► Person A :8001
Gateway :8000 ── health probes only ──► all seven services (real status)
```

- Dashboards talk **only** to their own API (typed HTTP client, no DB access).
- Imports into A are **idempotent** on `(source_app, external_id)`; retries
  update instead of duplicating.
- Failures are honest: unreachable peers produce `503` + recorded failure —
  no fake success, no fabricated data.
- Contracts: [`docs/api_contracts.md`](docs/api_contracts.md) ·
  flows: [`docs/data_flow.md`](docs/data_flow.md) ·
  architecture: [`docs/system_architecture.md`](docs/system_architecture.md),
  [`docs/integration_architecture.md`](docs/integration_architecture.md).

## Quick start (Windows 10/11 PowerShell)

```powershell
cd C:\path\to\CSI3007_Integrated_Project
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1   # one-time
.\.venv\Scripts\python.exe start_all.py                              # integrated
```

## Quick start (macOS Terminal)

```bash
cd /path/to/CSI3007_Integrated_Project
bash scripts/setup_macos.sh          # one-time
.venv/bin/python start_all.py        # integrated
```

Then open the **landing page** <http://127.0.0.1:8000> and the three
dashboards (8501 Claymorphism · 8502 Glassmorphism · 8503 Neumorphism).
Stop everything with `Ctrl+C`.

## Independent execution (each project alone)

```bash
cd person_a_sachien_n_23MID0255      # or person_b… / person_c…
../.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8001   # A's API
../.venv/bin/python -m streamlit run app.py --server.port 8501        # A's UI
```

(Windows: `..\.venv\Scripts\python.exe`. B uses 8002/8502, C uses 8003/8503.)
A project runs standalone; only its integration features need a peer online.
More options: `--port-offset`, `--no-gateway`, original `run_all.py` — see
[`docs/installation_guide.md`](docs/installation_guide.md).

## Tests

```bash
python -m pytest tests/ -q              # repository-level (runs per-project suites too)
python -m pytest integration_tests/ -q  # 9 live cross-project tests
cd person_b_shravan_n_a_23MID0445 && python -m pytest tests/ -q   # one suite
```

Latest verified results: **A 16 ✓ · B 13 ✓ · C 16 ✓ · integration 9 ✓** —
see [`docs/testing_report.md`](docs/testing_report.md) for scope and the
honest not-run list.

## Troubleshooting & known limitations

Port conflicts (`--port-offset 100`), firewall rules for cross-computer
demos, `externally-managed-environment` pip errors, and the full honest
limitations list live in
[`docs/troubleshooting.md`](docs/troubleshooting.md). Highlights: one process
per project (no production web-farm claims), the gateway monitors but never
proxies business data, and the sync keys shipped are coursework placeholders
— change them in `.env` before any real deployment.

## Documentation index

`docs/` — project_overview · individual_project_ownership · input_inventory
(archive reconstruction evidence) · system_architecture ·
integration_architecture · api_contracts · database_design · data_flow ·
installation_guide · windows_setup · macos_setup · testing_report ·
troubleshooting · `original/` (the recovered original root documentation).
