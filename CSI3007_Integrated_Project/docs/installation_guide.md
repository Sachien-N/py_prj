# Installation Guide (Windows + macOS)

## Requirements

- **Python 3.11 or newer** (tested with 3.12 and 3.13). One interpreter is
  enough for all seven services.
- No compilers, no external database server, no admin rights required.
- First install downloads the pinned wheels (~150 MB); everything else is local.

## One-time setup

### Windows 10/11 (PowerShell)

```powershell
cd path\to\CSI3007_Integrated_Project
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

or manually:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item person_a_sachien_n_23MID0255\.env.example person_a_sachien_n_23MID0255\.env
Copy-Item person_b_shravan_n_a_23MID0445\.env.example person_b_shravan_n_a_23MID0445\.env
Copy-Item person_c_hariharan_s_23MID0182\.env.example person_c_hariharan_s_23MID0182\.env
```

### macOS (Terminal)

```bash
cd /path/to/CSI3007_Integrated_Project
bash scripts/setup_macos.sh
```

or manually:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp person_a_sachien_n_23MID0255/.env.example person_a_sachien_n_23MID0255/.env
cp person_b_shravan_n_a_23MID0445/.env.example person_b_shravan_n_a_23MID0445/.env
cp person_c_hariharan_s_23MID0182/.env.example person_c_hariharan_s_23MID0182/.env
```

The `.env` files contain local development defaults (ports, URLs, dev sync
keys). They are pre-wired so the integrated demo works immediately on one
machine; edit them only when running across computers (see
`troubleshooting.md`).

## Starting

| Mode | Command |
|---|---|
| **Integrated** (gateway + 3 APIs + 3 dashboards) | `python start_all.py` (or `scripts/start_windows.ps1` / `bash scripts/start_macos.sh`) |
| Integrated, ports busy | `python start_all.py --port-offset 100` |
| Integrated without landing page | `python start_all.py --no-gateway` |
| **Independent** — Person A | `cd person_a_sachien_n_23MID0255` then `python -m uvicorn api:app --port 8001` **and** `python -m streamlit run app.py --server.port 8501` |
| Independent — Person B | same in `person_b_shravan_n_a_23MID0445` with ports 8002 / 8502 |
| Independent — Person C | same in `person_c_hariharan_s_23MID0182` with ports 8003 / 8503 |
| Original launcher (no gateway) | `python run_all.py` |

Then open:

| Page | URL |
|---|---|
| Landing page (gateway) | <http://127.0.0.1:8000> |
| A dashboard · Claymorphism | <http://127.0.0.1:8501> |
| B dashboard · Glassmorphism | <http://127.0.0.1:8502> |
| C dashboard · Neumorphism | <http://127.0.0.1:8503> |
| OpenAPI docs | 8001/8002/8003 `/docs` |

Stop everything with `Ctrl+C` in the launcher terminal.

## Running the tests

```bash
# repository-level tests (includes running each project's own suite)
python -m pytest tests/ -q

# live cross-project integration tests (spawns real servers on 8011-8013)
python -m pytest integration_tests/ -q

# one project's suite alone
cd person_a_sachien_n_23MID0255 && python -m pytest tests/ -q
```

## Demo data

The shipped `data/person_*.db` files already contain clearly-labelled
demonstration data. For a clean start, stop the services and delete the
`data/*.db` file of the project(s) you want reset — schemas are re-created
on API start-up (see `database_design.md` for the seeding endpoints).
