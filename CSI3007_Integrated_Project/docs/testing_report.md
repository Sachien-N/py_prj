# Testing Report

**Environment:** Linux (Ubuntu), Python 3.12.15, pinned requirements from
`requirements.txt` installed in a fresh virtual environment.
**Date:** 2026-10-26. Every result below was produced by actually running the
commands; nothing is extrapolated.

## 1. Archive reconstruction verification

| Check | Result |
|---|---|
| ZIP integrity of 4 outer archives (`unzip -t`) | ✅ 4/4 OK |
| ZIP integrity of all 11 inner parts (`unzip -t`) | ✅ 11/11 OK |
| All 11 parts present (Part_01–Part_11) | ✅ confirmed, none missing |
| Reconstruction mapping complete | ✅ 110/110 files placed, 0 missing sources |
| Python syntax of reconstructed tree (`py_compile`) | ✅ all files compile |
| Test counts vs original root README (A16/B13/C16) | ✅ 16 / 13 / 16 passed |

## 2. Per-project test suites (pytest, isolated venv)

| Suite | Result |
|---|---|
| `person_a_sachien_n_23MID0255/tests` (expenses, budgets, reports, CSV, integrations) | ✅ **16 passed** |
| `person_b_shravan_n_a_23MID0445/tests` (subscriptions, payments, billing, push integration) | ✅ **13 passed** |
| `person_c_hariharan_s_23MID0182/tests` (readings, tariffs, bills, analysis, exports, demo) | ✅ **16 passed** |

## 3. Live cross-project integration tests (`integration_tests/`, 9 tests)

Spawns the three real FastAPI servers on ports 8011–8013 with temporary
databases and exercises the authenticated exchanges:

| Check | Result |
|---|---|
| B → A push authenticated, idempotent import | ✅ |
| C → A push authenticated, idempotent import | ✅ |
| Pull fallback (A fetches producer payload) | ✅ |
| Wrong key rejected (401), invalid payload rejected (422) | ✅ |
| Producer offline → honest 503, **no partial import**, local data preserved | ✅ |
| B/C remain fully functional while A is offline | ✅ |
| **Total** | ✅ **9 passed** |

## 4. Repository-level suite (`tests/`, 32 tests)

| Group | What it validates | Result |
|---|---|---|
| `test_individual_projects.py` | Runs each per-project suite in a subprocess; ownership files/README identity; design-system theme modules per project; integrated layout; registry ↔ folder consistency | ✅ passed |
| `test_api_integration.py` | Each FastAPI app exposes the documented routes in its OpenAPI schema; `/health` documented; sync endpoints declare `X-API-Key` | ✅ passed |
| `test_data_exchange.py` | Pair keys match across `.env.example` templates; unique ports 8001–8003; payload schemas carry `source_app`/`external_id`; each project owns its DB path; no real secrets in templates | ✅ passed |
| `test_end_to_end.py` | Live B→A exchange on ports 8021–8023 with temp DBs: 401 unauthenticated, import + idempotent re-push, A's status reflects success, C's payload endpoint answers | ✅ passed |
| **Total** | | ✅ **32 passed** |

## 5. Integrated launcher smoke test (real run, then stopped cleanly)

`python start_all.py` — observed behaviour:

- ✅ Starts 3 APIs → gateway → 3 dashboards; waits for each health check.
- ✅ Gateway `GET /health` → healthy; `GET /services` → **7/7 reachable**.
- ✅ Landing page served with all three owners, registration numbers and
  design systems labelled.
- ✅ All three Streamlit dashboards answer `/_stcore/health` → `ok`.
- ✅ **Live exchange B→A:** push accepted (`records_imported: 1`), row stored
  in A with `source_app: person_b`; identical re-push → `records_imported: 0,
  records_updated: 1` (idempotent).
- ✅ **Live exchange C→A:** electricity expenses imported (`records_imported: 1`).
- ✅ Unauthenticated push → `401`.
- ✅ `Ctrl+C`/SIGTERM stops all children; all ports verified free afterwards.
- ✅ Port-conflict guard exits with a clear message and offset suggestion
  (verified once while a service was still shutting down).

## 6. UI / design-system verification

- ✅ Each dashboard imports its own `ui/theme.py` (`Claymorphism`,
  `Glassmorphism`, `Neumorphism` constants asserted by tests) and applies it
  after `set_page_config`.
- ✅ Each `.streamlit/config.toml` palette harmonises with its design system
  (A violet-on-pastel, B indigo glass, C amber-on-grey).
- ✅ Streamlit server + page HTML served for all three dashboards.
- ⚠️ Not performed: pixel-level visual review in real browsers (the delivery
  environment is headless). The CSS targets standard Streamlit DOM nodes;
  if a Streamlit update renames a node, the theme degrades gracefully to
  the palette in `config.toml`.

## 7. Not run / not verifiable here (honest list)

- Browser-based manual exploration of every Streamlit page (headless
  environment) — covered indirectly by API tests + HTML/health probes.
- Windows PowerShell and macOS script execution — scripts are written for
  those platforms and syntax-checked, but executed only on Linux; review
  `docs/windows_setup.md` / `docs/macos_setup.md` on the target OS.
- Real TNEB bill verification against a genuine electricity bill — the
  feature is exercised with clearly-labelled demo/sample bills only.
- Cross-computer (LAN) integration — documented (firewall + LAN IP steps)
  but requires a second machine to execute.
- Performance/load testing — out of scope for the coursework demo.

## 8. Known fixed issues discovered during testing

1. Two test files had been placed in the wrong project during reconstruction
   (`test_integration_exports.py` → C, `test_billing.py` → B) — detected by
   import errors, corrected, all suites green afterwards.
2. `integration/health_checks.py` initially read non-existent registry
   fields for `/services` — fixed and re-verified (7/7 reachable).
3. The launcher now pins each service's `DATABASE_URL` to its own project
   folder so a stray machine-wide `DATABASE_URL` environment variable cannot
   redirect a project to a foreign database (observed in the delivery
   sandbox; defensive fix, original project code untouched).
