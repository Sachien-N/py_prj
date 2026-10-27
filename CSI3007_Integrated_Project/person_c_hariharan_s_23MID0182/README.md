# Smart Home Electricity Monitoring and TNEB Electricity Bill Verification System

**Owner:** HARIHARAN S · **Registration No.: 23MID0182**

A standalone electricity-monitoring application that records manual or simulated smart-socket readings, computes interval energy, applies configurable progressive Tamil Nadu-style tariff configurations, compares estimates with actual bills, and investigates discrepancies with six months of evidence.

> **Important:** the bundled tariff is an illustrative demonstration configuration, **not an official TNEB/TANGEDCO tariff**. Every calculated cost is an estimate. The project never asserts that a utility bill is incorrect. Socket readings may not cover the whole household.

---

## Features

- Smart-socket/appliance registration with rated power, location, active status and adapter type.
- Manual readings, deterministic simulation, and clearly labelled demo data.
- Modular adapter contract for future vendor APIs/MQTT (`services/adapters/`); no hardware integration is claimed.
- Reading validation: timezone required, no future timestamps, duplicate timestamps rejected, out-of-order readings accepted and flagged, above-rated power stored with a quality flag.
- Energy calculation from intervals:
  `energy (kWh) = previous power (W) × observed duration (h) ÷ 1000`.
- Intervals longer than `MAX_READING_GAP_HOURS` are excluded and explicitly reported; missing data is never filled with invented energy.
- Daily/monthly/by-socket/billing-period aggregation with temporal data coverage.
- Configurable effective-dated tariff configurations with progressive slabs and fixed, per-unit and percentage components.
- Actual bill capture and validated CSV import.
- Bill comparison: actual vs estimate, unit/cost/percentage deviation, configurable tolerance, zero handling.
- Six-month evidence analysis distinguishing **observed facts** from **possible explanations**, with missing-data warnings.
- Plotly charts, CSV/JSON exports, demo generation.
- Electricity expense records for Person A, actual bills first, otherwise clearly marked estimates.
- Functions fully when Person A is offline.

## Architecture

```text
Streamlit dashboard (ui/) ──HTTP/JSON──► FastAPI (api.py) ──SQLAlchemy──► data/person_c.db
                                                  │
                                                  └── authenticated push ──► Person A :8001
```

- The UI never opens the database.
- `services/tariff_service.py` is independent of the UI and unit-tested.
- The six-month analysis reuses the same aggregation and tariff services.
- Timezone: readings are stored as naive UTC and grouped into local calendar dates using `TIMEZONE` (default `Asia/Kolkata`).

## Setup

```powershell
cd "D:\Documents\New folder\Three_Person_Python_Projects\person_c_smart_electricity"
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # already present in this workspace
```

`.env` variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/person_c.db` | Own database |
| `API_BASE_URL` | `http://127.0.0.1:8003` | Dashboard → API |
| `TIMEZONE` | `Asia/Kolkata` | Local calendar grouping |
| `PERSON_A_API_URL` | `http://127.0.0.1:8001` | Sync destination |
| `PERSON_A_SYNC_API_KEY` | dev key | Must match A's `PERSON_C_SYNC_API_KEY` |
| `INTEGRATION_TIMEOUT_SECONDS` | `5` | Outbound timeout |
| `INTEGRATION_RETRIES` | `2` | Transient retries |
| `DISCREPANCY_TOLERANCE_PERCENT` | `10` | Default comparison tolerance |
| `MAX_READING_GAP_HOURS` | `4` | Longer intervals become reported missing data |
| `CORS_ORIGINS` | local Streamlit origin | Allowed dashboard origins |

## Run

```powershell
python -m uvicorn api:app --host 127.0.0.1 --port 8003
python -m streamlit run app.py --server.port 8503
```

Dashboard: http://127.0.0.1:8503  
API docs: http://127.0.0.1:8003/docs  
Health: http://127.0.0.1:8003/health

On first start the database is created and the **demo tariff** is seeded. It is flagged `is_verified=false` and its source text explicitly says it is not an official tariff order.

## Tariff engine

A tariff configuration contains:

- Name, billing category, currency, effective-from and optional effective-to.
- Source, source URL, verification flag, notes.
- Ordered progressive slabs. Slabs must start at 0 and be contiguous; only the final slab may be unbounded.
- Optional components:
  - `fixed_monthly` — added once per estimate,
  - `per_unit` — applied to all units,
  - `percent_of_energy` — percentage of the energy charge.

Calculation:

```text
units_in_slab = min(total_units, slab_upper) - slab_lower
energy_charge = Σ(units_in_slab × rate)
components    = fixed + per_unit×units + percentage×energy_charge
total_cost    = energy_charge + components
```

Every result includes:
- selected tariff ID/name/effective date/source/verified flag,
- slab breakdown and component breakdown,
- `is_estimate: true`,
- warnings/assumptions, including that fixed components are not prorated and the tariff may be unverified.

A new effective-dated tariff should be created for rate changes; old configurations are left intact for audit.

## Reading and aggregation model

- Duplicate `(socket_id, reading_at)` → HTTP 409.
- Out-of-order timestamps are accepted, stored, and recalculated in sorted order.
- Timestamp must be timezone-aware and no more than 5 minutes in the future.
- Power must be non-negative; above the socket's rated power is stored with `quality_flag=above_rated_power`.
- Intervals are clipped to local day/month boundaries and split at midnight.
- Coverage is the union of observed reading intervals, not an assumption of continuous household monitoring.
- A missing day/month has `energy_kwh: null` and a warning; it is not rendered as a fabricated zero.

## Comparison and six-month rule

```text
unit_deviation = actual billed units - estimated units
cost_deviation = actual bill amount - estimated cost
percentage_deviation = cost_deviation ÷ estimated cost × 100
```

- If estimated cost is zero: percentage is `null` when actual cost is non-zero, with an explicit explanation; both zero gives 0%.
- `exceeds_tolerance = abs(percentage) > tolerance`, or a non-zero cost deviation when the percentage is undefined.
- A comparison requires at least one usable reading interval; otherwise HTTP 422 is returned and no estimate is invented.
- When tolerance is exceeded, the preceding six calendar months are analysed:
  - usable readings and recorded bills are listed separately,
  - missing months and coverage below 95% are flagged,
  - current daily usage is compared with the historical median (0.70–1.30 ratio band),
  - non-calendar billing periods are flagged,
  - repeated same-direction estimation differences are counted,
  - **observed facts** and **possible explanations** are returned separately,
  - insufficient history is explicitly reported.
- The report never claims a TNEB/TANGEDCO error.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health + owner identity |
| GET | `/project-info` | Metadata/limitations |
| GET | `/sockets` | List sockets |
| POST | `/sockets` | Create socket |
| GET | `/sockets/{id}` | Socket detail |
| PUT | `/sockets/{id}` | Update socket |
| DELETE | `/sockets/{id}` | Delete socket and readings |
| POST | `/sockets/readings` | Add a validated reading |
| GET | `/sockets/readings` | Recent readings (`socket_id`, `limit`) |
| DELETE | `/sockets/readings/{id}` | Delete reading |
| POST | `/sockets/{id}/simulate?days=&interval_minutes=` | Generate labelled simulated readings |
| GET | `/sockets/{id}/readings` | Readings for one socket |
| GET | `/consumption/daily` | Daily energy/coverage |
| GET | `/consumption/monthly` | Monthly energy/coverage |
| GET | `/consumption/by-socket` | Per-socket totals |
| GET | `/consumption/estimate` | Tariff-based cost estimate for a period |
| GET | `/consumption/monthly-costs` | Monthly tariff estimates |
| GET | `/tariffs` | List tariff configurations |
| POST | `/tariffs` | Create a tariff version |
| GET | `/tariffs/{id}` | Tariff detail |
| PUT | `/tariffs/{id}` | Update metadata/verification/active state |
| GET | `/bills` | List bills |
| POST | `/bills` | Record an actual bill |
| GET | `/bills/{id}` | Bill detail |
| DELETE | `/bills/{id}` | Delete bill and comparison |
| POST | `/bills/import/csv` | Validated bill CSV import |
| GET | `/bills/compare/{bill_id}` | Compute/persist comparison; optional tolerance/tariff |
| GET | `/analysis/six-months?bill_id=` | Six-month evidence analysis |
| GET | `/expenses/electricity` | Monthly actual/estimated expense records |
| GET | `/exports/consumption.csv` | Daily consumption CSV |
| GET | `/exports/bill-comparisons.csv` | Comparison history CSV |
| POST | `/demo/seed` | Generate labelled simulated data |
| GET | `/integrations/person-a/status` | Sync state and optional live health |
| GET | `/integrations/person-a/payload` | Payload for A pulls (**key required**) |
| POST | `/integrations/person-a/sync` | Push to Person A (**key required**) |

## Simulated demo data

From the dashboard: **Integrations → Simulated demonstration data**, or:

```powershell
python seed_demo.py --months 6 --force
```

Demo data:
- 3 sockets with `is_demo=true`,
- hourly `is_simulated=true` readings,
- six simulated bills with source `SIMULATED DEMO — not a real TNEB bill`,
- every demo record visibly labelled simulated.

`--force` deletes only demo-flagged sockets and demo-reference bills, then regenerates.

## Tests

```powershell
python -m pytest -q
```

Verified result: **16 passed**.

Covered: socket CRUD/duplicate validation, timezone/future/duplicate/out-of-order readings, formula-based daily/monthly/by-socket aggregation, long-gap exclusion, progressive tariff calculation and components, tariff validation/listing, bill comparison and tolerance, no-reading rejection, six-month facts/explanations/insufficient-history behaviour, bill CSV import/export, expense records and payload auth, integration failure preserving data, demo labels, and simulated reading generation.

## Known limitations

- No physical smart plug, vendor cloud API, or MQTT broker is implemented. Only manual, simulated and a future adapter contract exist.
- The seeded Tamil Nadu tariff is illustrative and unverified; users must configure and verify official rates and charges.
- Socket coverage cannot establish whole-house consumption.
- Energy uses the previous reading's power across each interval; power changes between readings are not captured. Long gaps are excluded rather than interpolated.
- Fixed tariff components are applied once per estimate, not prorated.
- Utility billing periods may not match calendar months; the analysis normalizes but cannot fully resolve meter-reading timing.
- No login; local single-user academic scope.
- No Alembic migrations; an incompatible schema change requires recreating the SQLite database.
- Default development integration key is local-only.
