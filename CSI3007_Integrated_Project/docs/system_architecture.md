# System Architecture

## High-level view

```text
                        ┌────────────────────────────────┐
                        │   Integration Gateway :8000    │
                        │  landing page / services / health │
                        └───────────────┬────────────────┘
                                        │ status probes only (HTTP)
     ┌──────────────────────┬───────────┴──────────┬──────────────────────┐
     │                      │                      │                      │
┌─────────────┐   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ Person A    │   │ Person A UI │        │ Person B UI │        │ Person C UI │
│ API  :8001  │   │  :8501      │        │  :8502      │        │  :8503      │
│ FastAPI     │   │ Streamlit   │        │ Streamlit   │        │ Streamlit   │
│ SQLAlchemy  │   │ Claymorphism│        │ Glassmorph. │        │ Neumorphism │
└──────┬──────┘   └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
       │                 │                       │                      │
┌──────┴──────┐   ┌──────┴────────┐      ┌──────┴──────┐        ┌──────┴──────┐
│ person_a.db │   │ ui/api_client │      │ ui/api_client│       │ ui/api_client│
│ (SQLite)    │◄──┤  HTTP only    │      │  HTTP only   │       │  HTTP only   │
└─────────────┘   └───────────────┘      └──────────────┘       └──────────────┘

Data exchange (X-API-Key authenticated, JSON only):
  Person B :8002 ──POST /integrations/subscriptions/sync──► Person A :8001
  Person C :8003 ──POST /integrations/electricity/sync───► Person A :8001
```

## Technology stack (identical stack, independent deployments)

Every project independently uses:

- **FastAPI 0.120** — REST API with Pydantic 2.12 validation and OpenAPI docs.
- **SQLAlchemy 2.0** — ORM over SQLite; tables created on API start-up.
- **Streamlit 1.65** — dashboard frontend; all data access via the project's
  own REST API (`ui/api_client.py`), never direct DB access.
- **Plotly 7.1 / pandas / numpy** — charts and tabular analysis.
- **pytest 8.4** — per-project suites plus live cross-project tests.

## Per-application layering

```text
app.py                 Streamlit entry point (calls ui.dashboard.main)
api.py                 FastAPI routes, auth dependency, error mapping
config.py              env-driven Settings (ports, URLs, keys, CORS)
database.py            engine/session lifecycle, init_db()
models.py              SQLAlchemy ORM models
schemas.py             Pydantic request/response contracts
services/              business logic (one module per capability)
services/common.py     small per-project formatting/period helpers
ui/api_client.py       typed HTTP client for the project's own API
ui/theme.py            design-system CSS (Clay/Glass/Neu)  [added in integration]
ui/dashboard.py        Streamlit pages (Overview, features, Integrations…)
tests/                 pytest suite against the API (httpx TestClient)
data/*.db              the project's own SQLite database
```

## Design decisions preserved from the originals

1. **UI talks only to its own API.** Dashboards never import `models` or
   `database`; swapping the backend behind the API would not touch the UI.
2. **No shared database, no shared process.** The launcher starts seven
   independent processes; each with its own working directory and `.env`.
3. **Fail honestly.** Integration pages show real sync status (success /
   failure with timestamps) and never fabricate success.
4. **Idempotent imports.** A deduplicates incoming records on
   `(source_app, external_id)`, so retries are safe.
