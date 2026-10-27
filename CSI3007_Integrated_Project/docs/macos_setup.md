# macOS Setup — Detailed (macOS 13+)

## 1. Install Python

Check what you already have:

```bash
python3 --version
```

If it is older than 3.11, install via Homebrew (`brew install python`) or the
installer from <https://www.python.org/downloads/macos/>. Verify with
`python3 --version`.

## 2. Unzip the project

```bash
unzip ~/Downloads/CSI3007_Integrated_Projects_A_B_C.zip -d ~/dev/
cd ~/dev/CSI3007_Integrated_Project
```

## 3. One-time setup

```bash
bash scripts/setup_macos.sh
```

What it does: creates `.venv`, installs the pinned dependencies, copies each
`.env.example` to `.env` (idempotent — never overwrites), compiles all
modules as a syntax check.

Manual alternative:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp person_a_sachien_n_23MID0255/.env.example person_a_sachien_n_23MID0255/.env
cp person_b_shravan_n_a_23MID0445/.env.example person_b_shravan_n_a_23MID0445/.env
cp person_c_hariharan_s_23MID0182/.env.example person_c_hariharan_s_23MID0182/.env
```

## 4. Start (integrated mode)

```bash
.venv/bin/python start_all.py
# or
bash scripts/start_macos.sh
```

Open <http://127.0.0.1:8000> for the landing page; dashboards on 8501/8502/8503.

## 5. Start (independent mode — one project only)

```bash
cd person_c_hariharan_s_23MID0182
../.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8003
# second terminal:
../.venv/bin/python -m streamlit run app.py --server.port 8503
```

## 6. macOS firewall (cross-computer demo)

System Settings → Network → Firewall → Options: allow Python, or add inbound
rules for ports 8001–8003 when prompted the first time a LAN peer connects.
On the *client* machine, point the relevant `.env` URL at the server's LAN IP
(Find your IP: `ipconfig getifaddr en0`), e.g.
`PERSON_A_API_URL=http://192.168.1.20:8001`. `localhost` on machine 1 is
**not** reachable from machine 2.

## 7. Stopping and cleaning

- `Ctrl+C` stops all child processes (SIGTERM, then SIGKILL after 10 s).
- Stray listener? `lsof -iTCP:8001 -sTCP:LISTEN` then `kill -9 <pid>`.
- Full reset: delete `.venv`, `__pycache__`, `.pytest_cache`, optionally
  `data/*.db`; re-run §3.

## 8. Known macOS quirks

- **Command Line Tools prompt** appears on first `venv` creation on a fresh
  macOS — let it install, then rerun the script.
- **python3: command not found** → install via Homebrew or python.org.
- Gatekeeper is not involved (no unsigned binaries — everything is source +
  wheels).
- If Streamlit's first start is slow while macOS verifies certificates, the
  launcher's 90-second UI health window absorbs it.
