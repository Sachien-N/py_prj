# Data Flow

## 1. Normal operation (every dashboard read)

```text
Browser ──► Streamlit dashboard ──► ui/api_client.py ──HTTP──► own FastAPI
                                                                      │
                                                              SQLAlchemy (own DB) ◄─┘
```

Every number a user sees was fetched live from that project's API at request
time. The dashboards never read SQLite files and never cache cross-project
data invisibly: imported rows show their producer (`source_app`) and whether
they are estimates.

## 2. Person B → Person A (subscription expenses)

```text
┌─────────────── Person B :8002 ───────────────┐      ┌────────────── Person A :8001 ──────────────┐
│ Integrations page → "Push to Person A"       │      │                                            │
│   1. build_expense_payload()                 │      │                                            │
│      (subscriptions × payments this cycle)   │      │                                            │
│   2. POST /integrations/subscriptions/sync   ├─HTTP─►│ 3. verify X-API-Key (PERSON_B_SYNC_API_KEY)│
│      X-API-Key: dev-person-b-to-a-key        │      │ 4. Pydantic validates full payload (422?)  │
│   6. store sync result (success/failure)     │◄─200─┤ 5. upsert expenses by (source_app,         │
└──────────────────────────────────────────────┘      │    external_id); bump integration state    │
                                                      └────────────────────────────────────────────┘
```

Failure path: connection error / non-200 → B records `status: failure` with
timestamp and shows it honestly; nothing is half-imported in A (validation
runs before the first row is written).

## 3. Person C → Person A (electricity expenses)

Same shape as §2 but the payload is monthly electricity expense summaries
(actual bill months and estimated months from readings), produced by C's
`expense_service.build_person_a_payload()`. Months without readings and
without a bill are **omitted** and reported in `summary.warnings`. Actual
TNEB bill months carry `is_estimate: false`; estimated months are labelled
`is_estimate: true`.

## 4. Pull fallback (A-initiated)

`POST /integrations/subscriptions/sync` (or `/electricity/sync`) with an
**empty body** makes A fetch `GET {PERSON_*_API_URL}/integrations/person-a/
payload` with the pair key. This is a convenience path — it does not update
B's/C's own sync state; their push endpoints remain the primary flow.

## 5. Launcher / gateway flows (operational, not business data)

```text
start_all.py ──spawn──► uvicorn ×3 APIs ──spawn──► uvicorn gateway :8000
                    └─spawn──► streamlit ×3 dashboards
gateway ──GET /health /_stcore/health──► every service (registry + probes)
```

The gateway only reads status endpoints; it never touches project databases.

## 6. What flows where — summary table

| Data | Produced by | Consumed by | Transport | Storage after import |
|---|---|---|---|---|
| Subscription expense summaries | B `subscription_service` | A | HTTPS/HTTP POST + key | A's `expenses` (`source_app='person_b'`) |
| Electricity expense summaries | C `expense_service` | A | HTTPS/HTTP POST + key | A's `expenses` (`source_app='person_c'`) |
| Sync status | every integration service | own dashboard Integrations page | internal (own DB) | `integration_sync_state` |
| Service health | all 7 services | gateway / launcher | HTTP GET | none (display only) |
