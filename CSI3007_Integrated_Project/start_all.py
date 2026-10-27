"""Integrated launcher for the CSI3007 three-project repository.

Starts, in order:
  1. The three FastAPI backends        (ports 8001, 8002, 8003)
  2. The integration gateway           (port 8000 — central landing page)
  3. The three Streamlit dashboards    (ports 8501, 8502, 8503)

then waits until every service is healthy and prints all URLs. Press Ctrl+C
to stop everything.

Usage (from the repository root):
    python start_all.py                 # start all seven services
    python start_all.py --no-gateway    # skip the landing-page gateway
    python start_all.py --port-offset 100   # 8101/8102/8103 + 8100, 8601..8603

Each child process runs with its own project directory as the working
directory, so it uses its own .env and its own SQLite database. The
applications stay independent: any of them can also be started alone
(see README.md).
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from shared.config import (  # noqa: E402
    STARTUP_TIMEOUT_SECONDS,
    apply_port_offset,
)
from shared.logging_config import setup_logging  # noqa: E402

log = setup_logging()


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_for(url: str, process: subprocess.Popen, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            pass
        time.sleep(0.4)
    return False


def _command(service) -> list[str]:
    if service.kind == "api":
        return [
            sys.executable, "-m", "uvicorn", "api:app",
            "--host", "127.0.0.1", "--port", str(service.port),
            "--log-level", "info",
        ]
    if service.kind == "gateway":
        return [
            sys.executable, "-m", "uvicorn", "integration.api_gateway:app",
            "--host", "127.0.0.1", "--port", str(service.port),
            "--log-level", "info",
        ]
    return [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.address", "127.0.0.1", "--server.port", str(service.port),
        "--server.headless", "true", "--browser.gatherUsageStats", "false",
    ]


def _service_env(service, urls: dict[str, str]) -> dict:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Pin each service to its OWN database so a stray global DATABASE_URL on
    # the machine can never redirect a project to somebody else's storage.
    if service.kind in ("api", "ui"):
        db_name = {"a": "person_a.db", "b": "person_b.db", "c": "person_c.db"}[
            service.key[0]
        ]
        db_path = REPO_ROOT / service.project_dir / "data" / db_name
        env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    if service.key in ("a_api", "a_ui"):
        env["API_BASE_URL"] = urls["a_api"]
        env["PERSON_B_API_URL"] = urls["b_api"]
        env["PERSON_C_API_URL"] = urls["c_api"]
    elif service.key in ("b_api", "b_ui"):
        env["API_BASE_URL"] = urls["b_api"]
        env["PERSON_A_API_URL"] = urls["a_api"]
    elif service.key in ("c_api", "c_ui"):
        env["API_BASE_URL"] = urls["c_api"]
        env["PERSON_A_API_URL"] = urls["a_api"]
    return env


def _terminate(processes: dict[str, subprocess.Popen]) -> None:
    for process in processes.values():
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
    deadline = time.time() + 10
    for process in processes.values():
        while process.poll() is None and time.time() < deadline:
            time.sleep(0.1)
    for key, process in processes.items():
        if process.poll() is None:
            log.warning("Force-killing %s", key)
            try:
                process.kill()
            except OSError:
                pass


def _manual_instructions() -> str:
    return (
        "\nManual startup alternative (one terminal per service):\n"
        "  cd person_a_sachien_n_23MID0255 && python -m uvicorn api:app --port 8001\n"
        "  cd person_a_sachien_n_23MID0255 && python -m streamlit run app.py --server.port 8501\n"
        "  cd person_b_shravan_n_a_23MID0445 && python -m uvicorn api:app --port 8002\n"
        "  cd person_b_shravan_n_a_23MID0445 && python -m streamlit run app.py --server.port 8502\n"
        "  cd person_c_hariharan_s_23MID0182 && python -m uvicorn api:app --port 8003\n"
        "  cd person_c_hariharan_s_23MID0182 && python -m streamlit run app.py --server.port 8503\n"
        "  python -m uvicorn integration.api_gateway:app --port 8000\n"
    )


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port-offset", type=int, default=0,
                        help="Shift all application ports by this amount.")
    parser.add_argument("--no-gateway", action="store_true",
                        help="Do not start the integration gateway on port 8000.")
    parser.add_argument("--timeout", type=float, default=STARTUP_TIMEOUT_SECONDS,
                        help="Seconds to wait for each service to become healthy.")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        print("Python 3.11 or newer is required.", file=sys.stderr)
        return 2
    try:
        import fastapi  # noqa: F401
        import streamlit  # noqa: F401
        import sqlalchemy  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        print("Install with: python -m pip install -r requirements.txt", file=sys.stderr)
        return 2

    services = apply_port_offset(args.port_offset)
    if args.no_gateway:
        services = [s for s in services if s.kind != "gateway"]

    occupied = [s.port for s in services if _port_in_use(s.port)]
    if occupied:
        print(
            "These ports are already in use: " + ", ".join(map(str, occupied))
            + ".\nStop the existing services or retry with --port-offset 100.",
            file=sys.stderr,
        )
        return 2

    urls = {s.key: s.base_url for s in services}
    processes: dict[str, subprocess.Popen] = {}
    print("=" * 72)
    print("CSI3007 Integrated Project — starting services")
    print("=" * 72)
    try:
        for group in ("api", "gateway", "ui"):
            for service in services:
                if service.kind != group:
                    continue
                project_dir = REPO_ROOT / service.project_dir
                if not project_dir.is_dir():
                    print(f"Missing project directory: {project_dir}", file=sys.stderr)
                    return 2
                print(f"[start_all] Starting {service.label} on port {service.port}")
                processes[service.key] = subprocess.Popen(
                    _command(service),
                    cwd=project_dir if service.kind != "gateway" else REPO_ROOT,
                    env=_service_env(service, urls),
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                )
                if group == "api":
                    if not _wait_for(service.health_url, processes[service.key], args.timeout):
                        print(f"[start_all] {service.label} failed its health check.",
                              file=sys.stderr)
                        return 1
            if group == "gateway":
                for service in services:
                    if service.kind == "gateway" and not _wait_for(
                        service.health_url, processes[service.key], args.timeout
                    ):
                        print("[start_all] Gateway failed its health check.",
                              file=sys.stderr)
                        return 1
            if group == "ui":
                for service in services:
                    if service.kind == "ui" and not _wait_for(
                        service.health_url, processes[service.key], args.timeout + 30
                    ):
                        print(f"[start_all] {service.label} failed its health check.",
                              file=sys.stderr)
                        return 1

        print("\nAll services are running:\n")
        for service in services:
            print(f"  {service.label:<26} {service.base_url}"
                  f"   ({service.owner} — {service.design_system})")
        landing = urls.get("gateway")
        if landing:
            print(f"\nCentral landing page: {landing}")
        print("\nAPI documentation:")
        print(f"  Person A  {urls['a_api']}/docs")
        print(f"  Person B  {urls['b_api']}/docs")
        print(f"  Person C  {urls['c_api']}/docs")
        print("\nPress Ctrl+C to stop all services.\n")
        while True:
            for key, process in processes.items():
                if process.poll() is not None:
                    print(f"[start_all] {key} stopped unexpectedly "
                          f"with code {process.returncode}.", file=sys.stderr)
                    return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[start_all] Interrupted; stopping child processes…")
        return 0
    finally:
        _terminate(processes)
        print(_manual_instructions())


if __name__ == "__main__":
    raise SystemExit(main())
