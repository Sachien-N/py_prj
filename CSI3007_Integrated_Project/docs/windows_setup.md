# Windows Setup — Detailed (Windows 10 / 11)

## 1. Install Python

1. Download Python 3.12 from <https://www.python.org/downloads/windows/>.
2. Run the installer. **Tick "Add python.exe to PATH"** before clicking
   Install Now.
3. Verify in PowerShell:

```powershell
python --version    # expected: Python 3.11+ 
```

## 2. Unzip the project

Right-click `CSI3007_Integrated_Projects_A_B_C.zip` → *Extract All…* to a
path **without** spaces if possible, e.g. `C:\dev\CSI3007_Integrated_Project`.

## 3. One-time setup

```powershell
cd C:\dev\CSI3007_Integrated_Project
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

What it does: creates `.venv`, installs the pinned dependencies, copies each
`.env.example` to `.env` (idempotent — never overwrites), compiles all
modules as a syntax check.

If PowerShell blocks scripts, use the manual path:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item person_a_sachien_n_23MID0255\.env.example person_a_sachien_n_23MID0255\.env
Copy-Item person_b_shravan_n_a_23MID0445\.env.example person_b_shravan_n_a_23MID0445\.env
Copy-Item person_c_hariharan_s_23MID0182\.env.example person_c_hariharan_s_23MID0182\.env
```

## 4. Start (integrated mode)

```powershell
.\.venv\Scripts\python.exe start_all.py
```

Expected console output: seven `[start_all] Starting …` lines, then the URL
table. Open <http://127.0.0.1:8000> for the landing page.

Start scripts alternative: `scripts\start_windows.ps1` (uses `.venv` when
present, falls back to system Python).

## 5. Start (independent mode — one project only)

```powershell
cd person_a_sachien_n_23MID0255
..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8001
# second terminal:
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
```

## 6. Windows Firewall (cross-computer demo)

When another laptop must reach this machine's APIs, allow inbound ports on
**private networks**:

```powershell
# Administrator PowerShell — repeat per port or per machine demo
netsh advfirewall firewall add rule name="CSI3007 A API" dir=in action=allow protocol=TCP localport=8001
netsh advfirewall firewall add rule name="CSI3007 B API" dir=in action=allow protocol=TCP localport=8002
netsh advfirewall firewall add rule name="CSI3007 C API" dir=in action=allow protocol=TCP localport=8003
```

Then set the *client* machine's `.env` URLs to the server's LAN IP, e.g.
`PERSON_A_API_URL=http://192.168.1.20:8001`. `localhost` on machine 1 is
**not** reachable from machine 2.

## 7. Stopping and cleaning

- `Ctrl+C` in the launcher window stops all children (the launcher also
  force-kills stragglers after 10 s).
- Suspect a zombie process? `netstat -ano | findstr :8001` then
  `taskkill /PID <pid> /F`.
- Full reset: delete `.venv`, `__pycache__`, `.pytest_cache`, and (optionally)
  `data/*.db` — then re-run §3.

## 8. Known Windows quirks

- **Port already in use** → run `python start_all.py --port-offset 100`.
- **`python` opens the Microsoft Store** → disable *App execution aliases*
  for python in Settings, or use `py -3.12`.
- **Long path errors during extraction** → extract to `C:\dev\...` (short
  path) rather than a deep Desktop folder.
- Antivirus slow-scanning the first Streamlit start can add ~10 s; the
  launcher waits up to 90 s for UI health.
