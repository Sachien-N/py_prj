# Integration Architecture

## Roles

| Component | Runs on | Responsibility |
|---|---|---|
| Person applications (API + UI ×3) | 8001–8003, 8501–8503 | Own their data and business logic; expose documented REST endpoints |
| Integration gateway (`integration/api_gateway.py`) | 8000 | Landing page, `/services` live status, `/projects` ownership summary |
| Launcher (`start_all.py`) | — | Start/stop the seven processes in dependency order with health checks |
| `integration/service_registry.py` | — | Single source of truth: ports, owners, design systems, project folders |
| `integration/health_checks.py` | — | Real HTTP probes with timeouts; reports actual errors, never guesses |

## What "integrated" means here

1. **One command starts everything** — `python start_all.py` starts the three
   APIs, waits for their `/health`, starts the gateway and the three
   dashboards, and prints a URL table. `Ctrl+C` stops all of them.
2. **One landing page** — the gateway on <http://127.0.0.1:8000> labels every
   application with its owner, registration number and design system, and
   links to each dashboard and OpenAPI doc page.
3. **Documented data flows** — B→A and C→A authenticated pushes (see
   `api_contracts.md`); nothing else moves between projects.
4. **Honest observability** — `GET /services` probes every service and
   returns per-service `reachable`/`error`; the landing page displays the
   live counts.

## What integration deliberately does NOT do

- No merged or shared database; no cross-project SQL access.
- No business logic in the gateway; it cannot modify expenses, subscriptions
  or readings.
- No fabricated data: if Person B is offline, Person A's dashboard shows the
  actual failure state (503 + last failure timestamp), not stale demo data.

## Failure isolation

| Scenario | Behaviour |
|---|---|
| Person B offline | A's subscription-integration page shows "unavailable"; A's own expense features work; B's dashboard is unaffected for its local features |
| Person C offline | Same pattern for electricity expenses |
| Person A offline | B and C can still push? No — pushes target A, so B/C mark their sync as failed with an honest status; all local B/C features keep working |
| Gateway not started | Nothing breaks: applications exchange data directly; the landing page is optional |
| Port conflict | Launcher detects occupied ports before starting and exits with the list; `--port-offset 100` shifts every port |

## Port allocation and offsets

Default ports: gateway 8000, A 8001/8501, B 8002/8502, C 8003/8503.
`start_all.py --port-offset N` adds N to every application port (the
gateway keeps 8000 unless overridden via `GATEWAY_PORT`). When projects run
on different machines, set each project's `PERSON_*_API_URL` to the LAN
address of the peer (e.g. `http://192.168.1.23:8001`) — see
`troubleshooting.md` for the cross-computer checklist.
