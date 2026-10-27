# Integration Layer

This folder contains the **coordination layer only**. The three applications
stay independently owned: their databases, business logic, and configuration
are never merged.

| Module | Purpose |
|---|---|
| `service_registry.py` | Single source of truth for all runnable services (ports, owners, design systems). |
| `health_checks.py` | Real availability probes with configurable timeouts; reports actual errors. |
| `api_gateway.py` | FastAPI app on port **8000**: landing page (`/`), `/health`, `/services`, `/projects`, `/registry`. |

## Running the gateway alone

```bash
# from the repository root
python -m uvicorn integration.api_gateway:app --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000> for the central landing page.

## What the gateway does NOT do

- It does not access any project's SQLite database.
- It does not proxy business requests between projects.
- It does not fabricate status: if a service is down, `/services` says so and
  includes the underlying connection error.

## How the applications actually integrate

Permitted data flows (all authenticated with per-pair `X-API-Key` headers,
validated JSON schemas, timeouts and retries):

| Flow | Producer | Consumer | Trigger |
|---|---|---|---|
| Subscription expenses | Person B (port 8002) | Person A (port 8001) | B pushes `POST /integrations/subscriptions/sync` |
| Electricity expenses | Person C (port 8003) | Person A (port 8001) | C pushes `POST /integrations/electricity/sync` |
| Manual pull | Person A | B and C | A fetches documented JSON payloads |

See `docs/api_contracts.md` for exact request/response schemas and
`docs/data_flow.md` for sequence diagrams.
