"""Launch all three FastAPI backends and all three Streamlit dashboards.

Usage (from Three_Person_Python_Projects/):
    python run_all.py

Each process runs with its own project directory as the working directory, so its
own .env configuration and SQLite database are used. Press Ctrl+C to stop all six
child processes.
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
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Service:
    key: str
    name: str
    project: str
    kind: str
    port: int
    health_url: str
    url: str


SERVICES = [
    Service(
        "a_api",
        "Person A API",
        "person_a_sachien_n_23MID0255",
        "api",
        8001,
        "http://127.0.0.1:8001/health",
        "http://127.0.0.1:8001",
    ),
    Service(
        "b_api",
        "Person B API",
        "person_b_shravan_n_a_23MID0445",
        "api",
        8002,
        "http://127.0.0.1:8002/health",
        "http://127.0.0.1:8002",
    ),
    Service(
        "c_api",
        "Person C API",
        "person_c_hariharan_s_23MID0182",
        "api",
        8003,
        "http://127.0.0.1:8003/health",
        "http://127.0.0.1:8003",
    ),
    Service(
        "a_ui",
        "Person A dashboard",
        "person_a_sachien_n_23MID0255",
        "ui",
        8501,
        "http://127.0.0.1:8501/_stcore/health",
        "http://127.0.0.1:8501",
    ),
    Service(
        "b_ui",
        "Person B dashboard",
        "person_b_shravan_n_a_23MID0445",
        "ui",
        8502,
        "http://127.0.0.1:8502/_stcore/health",
        "http://127.0.0.1:8502",
    ),
    Service(
        "c_ui",
        "Person C dashboard",
        "person_c_hariharan_s_23MID0182",
        "ui",
        8503,
        "http://127.0.0.1:8503/_stcore/health",
        "http://127.0.0.1:8503",
    ),
]


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_for(url: str, process: subprocess.Popen, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(0.4)
    return False


def _command(service: Service) -> list[str]:
    if service.kind == "api":
        return [
            sys.executable,
            "-m",
            "uvicorn",
            "api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(service.port),
            "--log-level",
            "info",
        ]
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(service.port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]


def _terminate(processes: dict[str, subprocess.Popen]) -> None:
    for key, process in processes.items():
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
            print(f"[run_all] Force-killing {key}")
            try:
                process.kill()
            except OSError:
                pass


def _manual_instructions() -> str:
    return (
        "\nManual startup alternative (run each command in a separate terminal):\n"
        "  cd person_a_sachien_n_23MID0255\n"
        "  python -m uvicorn api:app --host 127.0.0.1 --port 8001\n"
        "  python -m streamlit run app.py --server.port 8501\n\n"
        "  cd person_b_shravan_n_a_23MID0445\n"
        "  python -m uvicorn api:app --host 127.0.0.1 --port 8002\n"
        "  python -m streamlit run app.py --server.port 8502\n\n"
        "  cd person_c_hariharan_s_23MID0182\n"
        "  python -m uvicorn api:app --host 127.0.0.1 --port 8003\n"
        "  python -m streamlit run app.py --server.port 8503\n"
    )


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port-offset",
        type=int,
        default=0,
        help="Add this offset to all six suggested ports (e.g. 100 -> 8101/8601).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Accepted for compatibility; the launcher never opens a browser.",
    )
    args = parser.parse_args()
    if args.port_offset < 0 or args.port_offset > 50000:
        print("--port-offset must be between 0 and 50000.", file=sys.stderr)
        return 2
    services = [
        replace(
            service,
            port=service.port + args.port_offset,
            url=f"http://127.0.0.1:{service.port + args.port_offset}",
            health_url=(
                f"http://127.0.0.1:{service.port + args.port_offset}/health"
                if service.kind == "api"
                else f"http://127.0.0.1:{service.port + args.port_offset}/_stcore/health"
            ),
        )
        for service in SERVICES
    ]
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
        print("Install with: python -m pip install -r person_a_sachien_n_23MID0255/requirements.txt")
        return 2

    occupied = [service.port for service in services if _port_in_use(service.port)]
    if occupied:
        print(
            "These ports are already in use: "
            + ", ".join(str(port) for port in occupied)
            + ". Stop the existing services or retry with --port-offset 100.",
            file=sys.stderr,
        )
        return 2

    base_urls = {service.key: service.url for service in services}
    processes: dict[str, subprocess.Popen] = {}

    def service_env(service: Service) -> dict:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        if service.key == "a_api":
            env["API_BASE_URL"] = base_urls["a_api"]
            env["PERSON_B_API_URL"] = base_urls["b_api"]
            env["PERSON_C_API_URL"] = base_urls["c_api"]
        elif service.key == "b_api":
            env["API_BASE_URL"] = base_urls["b_api"]
            env["PERSON_A_API_URL"] = base_urls["a_api"]
        elif service.key == "c_api":
            env["API_BASE_URL"] = base_urls["c_api"]
            env["PERSON_A_API_URL"] = base_urls["a_api"]
        elif service.key == "a_ui":
            env["API_BASE_URL"] = base_urls["a_api"]
            env["PERSON_B_API_URL"] = base_urls["b_api"]
            env["PERSON_C_API_URL"] = base_urls["c_api"]
        elif service.key == "b_ui":
            env["API_BASE_URL"] = base_urls["b_api"]
            env["PERSON_A_API_URL"] = base_urls["a_api"]
        elif service.key == "c_ui":
            env["API_BASE_URL"] = base_urls["c_api"]
            env["PERSON_A_API_URL"] = base_urls["a_api"]
        return env
    print("=" * 72)
    print("Three independent Python projects — local development launcher")
    print("=" * 72)
    try:
        # APIs first, so the dashboards have something to talk to immediately.
        for service in services:
            if service.kind != "api":
                continue
            project_dir = ROOT / service.project
            if not project_dir.is_dir():
                print(f"Missing project directory: {project_dir}", file=sys.stderr)
                return 2
            print(f"[run_all] Starting {service.name} on port {service.port}")
            processes[service.key] = subprocess.Popen(
                _command(service),
                cwd=project_dir,
                env=service_env(service),
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        for service in services:
            if service.kind != "api":
                continue
            process = processes[service.key]
            if not _wait_for(service.health_url, process):
                if process.poll() is not None:
                    print(
                        f"[run_all] {service.name} exited with code {process.returncode}.",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"[run_all] {service.name} did not become healthy in time.",
                        file=sys.stderr,
                    )
                return 1

        for service in services:
            if service.kind != "ui":
                continue
            print(f"[run_all] Starting {service.name} on port {service.port}")
            processes[service.key] = subprocess.Popen(
                _command(service),
                cwd=ROOT / service.project,
                env=service_env(service),
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        for service in services:
            if service.kind != "ui":
                continue
            process = processes[service.key]
            if not _wait_for(service.health_url, process, timeout=90):
                if process.poll() is not None:
                    print(
                        f"[run_all] {service.name} exited with code {process.returncode}.",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"[run_all] {service.name} did not become healthy in time.",
                        file=sys.stderr,
                    )
                return 1

        print("\nAll six services are running:\n")
        for service in services:
            print(f"  {service.name:<24} {service.url}")
        print("\nAPI documentation:")
        print(f"  Person A  {base_urls['a_api']}/docs")
        print(f"  Person B  {base_urls['b_api']}/docs")
        print(f"  Person C  {base_urls['c_api']}/docs")
        print("\nPress Ctrl+C to stop all services.\n")
        while True:
            for service in services:
                process = processes[service.key]
                if process.poll() is not None:
                    print(
                        f"[run_all] {service.name} stopped unexpectedly with code "
                        f"{process.returncode}.",
                        file=sys.stderr,
                    )
                    return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[run_all] Interrupted; stopping child processes…")
        return 0
    finally:
        _terminate(processes)
        print(_manual_instructions())


if __name__ == "__main__":
    raise SystemExit(main())
