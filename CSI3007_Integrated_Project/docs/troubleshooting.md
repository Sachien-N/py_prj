# Troubleshooting and Known Limitations

## Port problems

| Symptom | Cause | Fix |
|---|---|---|
| Launcher exits: "These ports are already in use: …" | A previous run or another app holds a port | Stop the other app, or `python start_all.py --port-offset 100` |
| Dashboard URL opens but blank / connection refused | Streamlit still starting | Wait a few seconds; launcher waits up to 90 s for UI health |
| Find who holds a port | — | Windows: `netstat -ano | findstr :8001` → `taskkill /PID <pid> /F` · macOS: `lsof -iTCP:8001 -sTCP:LISTEN` → `kill -9 <pid>` |

## Dependency problems

| Symptom | Cause | Fix |
|---|---|---|
| `Missing dependency: …` from the launcher | Commands run with system Python, not `.venv` | Use `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (macOS), or re-run the setup script |
| `error: externally-managed-environment` from pip | PEP 668 system Python (common on Homebrew/Linux) | Create/use the venv as above — never `--break-system-packages` |
| Wheel install fails on old Python | Python < 3.11 | Install Python 3.11+ (the pins target 3.11–3.13) |

## Cross-computer (LAN) integration

| Symptom | Cause | Fix |
|---|---|---|
| A cannot pull from B/C, connection refused | Peer API not started, or URL still `127.0.0.1` | Set `PERSON_B_API_URL` / `PERSON_C_API_URL` (and A's URL on B/C) to the peer's **LAN IP**, restart the APIs |
| Push works one way only | Mismatched pair key | `PERSON_B_SYNC_API_KEY` (in A's `.env`) must equal `PERSON_A_SYNC_API_KEY` (in B's `.env`); same pattern for C |
| Firewall blocks the connection | OS firewall | Windows: `netsh advfirewall firewall add rule … localport=8001` (see windows_setup.md); macOS: allow Python in Firewall Options |
| `http://<MAC_B_IP>:8002` placeholder still in A's `.env` | Template never edited | Replace with the real LAN IP before relying on pulls |

Remember: `localhost`/`127.0.0.1` on one computer is **never** another
computer's address. `ping <peer-ip>` must succeed first.

## Database problems

| Symptom | Cause | Fix |
|---|---|---|
| Tables missing / `no such table` | API never started in that project folder (DB is created by the API, not the UI) | Start the project's API once; `init_db()` creates the schema |
| Demo data missing | `data/*.db` was deleted | Start API, then use the demo seed (e.g. `POST /demo/seed` on C) |
| Want a clean slate | — | Stop services, delete the project's `data/*.db`, restart the API — scripts never delete DBs silently |
| `database is locked` | Two API processes share one project folder | Stop duplicates; one API process per project |

## UI problems

| Symptom | Cause | Fix |
|---|---|---|
| Dashboard shows "API unavailable" banner | That project's API is down | Start its `uvicorn api:app …` process; the banner clears after the next refresh |
| Styles look default (no clay/glass/neu) | Dashboard started from the wrong folder, or `ui/theme.py` missing | Verify the working directory contains `ui/theme.py`; hard-refresh the browser (Ctrl/Cmd+Shift+R) |
| Charts render but table empty | No data yet for the filter range | Add records, or widen the date range; demo data is clearly labelled |

## Known limitations (honest list)

1. Streamlit multi-window sessions share one process per dashboard — fine for
   the academic demo, not a production web farm.
2. The gateway is an HTTP monitor/landing page; it does not proxy business
   requests (by design, to keep ownership boundaries clean).
3. The two `integration` launch paths (`run_all.py` without gateway and
   `start_all.py` with gateway) must not run simultaneously (same ports).
4. Dev keys (`dev-person-b-to-a-key`, `dev-person-c-to-a-key`) are
   placeholders for coursework use; change them in the `.env` files before
   any real deployment.
5. Only one physical copy of `Three_Person_Python_Projects.zip` existed among
   the uploads (two same-named uploads collided); see `input_inventory.md`.
