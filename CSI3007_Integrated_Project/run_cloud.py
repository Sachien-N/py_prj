"""Cloud Entrypoint Runner for CSI3007 Integrated Applications.

Supports running a single service or launching all services on cloud platforms like Render or Railway.

Usage:
    python run_cloud.py --service a_api      # Run Person A FastAPI backend on $PORT
    python run_cloud.py --service a_ui       # Run Person A Streamlit UI on $PORT
    python run_cloud.py --service b_api      # Run Person B FastAPI backend on $PORT
    python run_cloud.py --service b_ui       # Run Person B Streamlit UI on $PORT
    python run_cloud.py --service c_api      # Run Person C FastAPI backend on $PORT
    python run_cloud.py --service c_ui       # Run Person C Streamlit UI on $PORT
    python run_cloud.py --service gateway    # Run Integration Gateway on $PORT
    python run_cloud.py --service all        # Launch all services together (Single Container Mode)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from shared.logging_config import setup_logging

log = setup_logging()


def run_service(service_name: str) -> None:
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    if service_name == "gateway":
        log.info(f"Starting Gateway on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "integration.api_gateway:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=REPO_ROOT,
            check=True,
        )

    elif service_name == "a_api":
        log.info(f"Starting Person A API on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=REPO_ROOT / "person_a_sachien_n_23MID0255",
            check=True,
        )

    elif service_name == "a_ui":
        log.info(f"Starting Person A Streamlit UI on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                str(port),
                "--server.address",
                host,
                "--server.headless",
                "true",
            ],
            cwd=REPO_ROOT / "person_a_sachien_n_23MID0255",
            check=True,
        )

    elif service_name == "b_api":
        log.info(f"Starting Person B API on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=REPO_ROOT / "person_b_shravan_n_a_23MID0445",
            check=True,
        )

    elif service_name == "b_ui":
        log.info(f"Starting Person B Streamlit UI on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                str(port),
                "--server.address",
                host,
                "--server.headless",
                "true",
            ],
            cwd=REPO_ROOT / "person_b_shravan_n_a_23MID0445",
            check=True,
        )

    elif service_name == "c_api":
        log.info(f"Starting Person C API on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=REPO_ROOT / "person_c_hariharan_s_23MID0182",
            check=True,
        )

    elif service_name == "c_ui":
        log.info(f"Starting Person C Streamlit UI on {host}:{port}")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                str(port),
                "--server.address",
                host,
                "--server.headless",
                "true",
            ],
            cwd=REPO_ROOT / "person_c_hariharan_s_23MID0182",
            check=True,
        )

    elif service_name == "all":
        log.info("Launching all services in single container mode...")
        # Start start_all.py which manages all 7 subservices locally
        subprocess.run([sys.executable, "start_all.py"], cwd=REPO_ROOT, check=True)

    else:
        log.error(f"Unknown service: {service_name}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cloud service launcher")
    parser.add_argument(
        "--service",
        type=str,
        default=os.getenv("SERVICE_NAME", "gateway"),
        help="Service to start (a_api, a_ui, b_api, b_ui, c_api, c_ui, gateway, all)",
    )
    args = parser.parse_args()
    run_service(args.service)


if __name__ == "__main__":
    main()
