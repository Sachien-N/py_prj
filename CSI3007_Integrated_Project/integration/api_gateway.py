"""Integration gateway for the CSI3007 integrated project.

A small FastAPI application that provides:

* ``GET /``          — the central landing page (links to all three dashboards
  and API docs, with each owner and design system clearly labelled).
* ``GET /health``    — gateway liveness.
* ``GET /services``  — live status of every registered service (real checks,
  never fabricated).
* ``GET /projects``  — the ownership/design-system summary.

Run with:
    python -m uvicorn integration.api_gateway:app --host 127.0.0.1 --port 8000

The gateway does NOT merge databases or business logic: each application
remains authoritative for its own data and exposes its documented REST API.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from integration.health_checks import check_all_services
from integration.service_registry import PROJECT_SUMMARY, service_summary
from shared.config import GATEWAY_PORT
from shared.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("gateway")

app = FastAPI(
    title="CSI3007 Integration Gateway",
    description=(
        "Central landing page and health dashboard for three independently "
        "owned Python projects (Advanced Python Programming, CSI3007)."
    ),
    version="1.0.0",
)

_LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CSI3007 — Three Independent Python Projects</title>
<style>
  :root {
    --bg: #f1f5f9; --card: #ffffff; --text: #0f172a; --muted: #64748b;
    --a: #0f766e; --b: #4f46e5; --c: #d97706; --border: #e2e8f0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh;
    display: flex; flex-direction: column; align-items: center;
    padding: 48px 20px;
  }
  header { text-align: center; margin-bottom: 36px; max-width: 860px; }
  header h1 { font-size: 1.9rem; margin-bottom: 10px; }
  header p { color: var(--muted); line-height: 1.6; }
  .grid {
    display: grid; gap: 24px; width: 100%; max-width: 1080px;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 20px; padding: 28px; display: flex; flex-direction: column;
    gap: 12px; box-shadow: 0 8px 24px rgba(15, 23, 42, .06);
  }
  .badge {
    align-self: flex-start; font-size: .78rem; font-weight: 700;
    letter-spacing: .04em; text-transform: uppercase; color: #fff;
    padding: 4px 12px; border-radius: 999px;
  }
  .badge.a { background: var(--a); } .badge.b { background: var(--b); }
  .badge.c { background: var(--c); }
  .card h2 { font-size: 1.15rem; line-height: 1.35; }
  .owner { color: var(--muted); font-size: .95rem; }
  .links { margin-top: auto; display: flex; flex-wrap: wrap; gap: 10px; }
  .links a {
    text-decoration: none; font-weight: 600; font-size: .92rem;
    padding: 9px 16px; border-radius: 12px; border: 1px solid var(--border);
    color: var(--text); background: var(--bg); transition: transform .15s ease;
  }
  .links a:hover { transform: translateY(-2px); }
  footer {
    margin-top: 40px; color: var(--muted); font-size: .85rem;
    text-align: center; line-height: 1.6; max-width: 860px;
  }
  .status { margin-top: 8px; font-size: .85rem; }
</style>
</head>
<body>
  <header>
    <h1>CSI3007 · Advanced Python Programming</h1>
    <p>Three independently owned Python applications. Each project keeps its
    own database, business logic, tests and design system; the applications
    exchange only permitted data through authenticated REST APIs.</p>
    <p class="status" id="status">Loading live service status…</p>
  </header>
  <div class="grid">
    <div class="card">
      <span class="badge a">Person A · Claymorphism</span>
      <h2>Smart Expense Categorization and Budget Manager</h2>
      <p class="owner">Sachien N · Registration No. 23MID0255</p>
      <p class="owner">FastAPI (8001) · Streamlit (8501) · SQLite (person_a.db)</p>
      <div class="links">
        <a href="http://127.0.0.1:8501" target="_blank" rel="noopener">Open Dashboard</a>
        <a href="http://127.0.0.1:8001/docs" target="_blank" rel="noopener">API Docs</a>
      </div>
    </div>
    <div class="card">
      <span class="badge b">Person B · Glassmorphism</span>
      <h2>Smart Subscription Manager</h2>
      <p class="owner">Shravan N A · Registration No. 23MID0445</p>
      <p class="owner">FastAPI (8002) · Streamlit (8502) · SQLite (person_b.db)</p>
      <div class="links">
        <a href="http://127.0.0.1:8502" target="_blank" rel="noopener">Open Dashboard</a>
        <a href="http://127.0.0.1:8002/docs" target="_blank" rel="noopener">API Docs</a>
      </div>
    </div>
    <div class="card">
      <span class="badge c">Person C · Neumorphism</span>
      <h2>Smart Home Electricity Monitoring and TNEB Bill Verification System</h2>
      <p class="owner">Hariharan S · Registration No. 23MID0182</p>
      <p class="owner">FastAPI (8003) · Streamlit (8503) · SQLite (person_c.db)</p>
      <div class="links">
        <a href="http://127.0.0.1:8503" target="_blank" rel="noopener">Open Dashboard</a>
        <a href="http://127.0.0.1:8003/docs" target="_blank" rel="noopener">API Docs</a>
      </div>
    </div>
  </div>
  <footer>
    Independent execution: every dashboard and API also runs on its own without
    the others (except where a documented integration feature needs a peer).
    Integration data flows: B → A (subscription expenses), C → A (electricity
    expenses), all authenticated with per-pair X-API-Key headers.
  </footer>
  <script>
    fetch("/services").then(r => r.json()).then(data => {
      const el = document.getElementById("status");
      el.textContent = "Live status: " + data.reachable + "/" + data.total +
        " services reachable · checked at " + data.checked_at;
    }).catch(() => {
      document.getElementById("status").textContent =
        "Live status: unavailable (gateway started without service access)";
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing() -> HTMLResponse:
    """Central landing page with clearly labelled access to each project."""
    return HTMLResponse(content=_LANDING_PAGE)


@app.get("/health")
def health() -> dict:
    """Gateway liveness probe."""
    return {
        "status": "healthy",
        "service": "integration-gateway",
        "port": GATEWAY_PORT,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/services")
def services() -> JSONResponse:
    """Live status of every registered service (real checks, real errors)."""
    report = check_all_services()
    return JSONResponse(status_code=200, content=report)


@app.get("/projects")
def projects() -> list[dict]:
    """Ownership, titles and design systems of the three projects."""
    return PROJECT_SUMMARY


@app.get("/registry")
def registry() -> list[dict]:
    """Full service registry (used by the launcher and tests)."""
    return service_summary()


if __name__ == "__main__":  # pragma: no cover - manual convenience
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=GATEWAY_PORT, log_level="info")
