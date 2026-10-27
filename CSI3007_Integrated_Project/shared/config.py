"""Central configuration for the integration layer and launcher.

Every value can be overridden with environment variables (optionally loaded
from the repository root ``.env`` file). The person applications keep their
own per-project configuration; this module only coordinates the shared
services (gateway, launcher, health checks).

Secrets are never hardcoded: sync keys between projects stay in each
project's ``.env`` (copied from its ``.env.example`` during setup).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # Optional: python-dotenv ships with the projects' requirements.
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is in requirements anyway
    def load_dotenv(*_args, **_kwargs) -> bool:  # type: ignore[misc]
        return False

REPO_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(REPO_ROOT / ".env", override=False)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class ServiceEndpoint:
    """One runnable piece of the integrated system."""

    key: str
    label: str
    project_dir: str
    kind: str  # "api" | "ui" | "gateway"
    port: int
    owner: str
    registration: str
    design_system: str
    health_path: str = "/health"

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def health_url(self) -> str:
        if self.kind == "ui":
            return f"{self.base_url}/_stcore/health"
        return f"{self.base_url}{self.health_path}"


GATEWAY_PORT = _env_int("GATEWAY_PORT", 8000)

SERVICES: list[ServiceEndpoint] = [
    ServiceEndpoint(
        "gateway", "Integration Gateway", ".", "gateway", GATEWAY_PORT,
        "Course CSI3007", "—", "Landing page",
    ),
    ServiceEndpoint(
        "a_api", "Person A API", "person_a_sachien_n_23MID0255", "api", 8001,
        "Sachien N", "23MID0255", "Claymorphism",
    ),
    ServiceEndpoint(
        "a_ui", "Person A Dashboard", "person_a_sachien_n_23MID0255", "ui", 8501,
        "Sachien N", "23MID0255", "Claymorphism",
    ),
    ServiceEndpoint(
        "b_api", "Person B API", "person_b_shravan_n_a_23MID0445", "api", 8002,
        "Shravan N A", "23MID0445", "Glassmorphism",
    ),
    ServiceEndpoint(
        "b_ui", "Person B Dashboard", "person_b_shravan_n_a_23MID0445", "ui", 8502,
        "Shravan N A", "23MID0445", "Glassmorphism",
    ),
    ServiceEndpoint(
        "c_api", "Person C API", "person_c_hariharan_s_23MID0182", "api", 8003,
        "Hariharan S", "23MID0182", "Neumorphism",
    ),
    ServiceEndpoint(
        "c_ui", "Person C Dashboard", "person_c_hariharan_s_23MID0182", "ui", 8503,
        "Hariharan S", "23MID0182", "Neumorphism",
    ),
]

SERVICES_BY_KEY: dict[str, ServiceEndpoint] = {s.key: s for s in SERVICES}

HEALTH_TIMEOUT_SECONDS = _env_float("HEALTH_TIMEOUT_SECONDS", 2.0)
STARTUP_TIMEOUT_SECONDS = _env_float("STARTUP_TIMEOUT_SECONDS", 60.0)


def apply_port_offset(offset: int) -> list[ServiceEndpoint]:
    """Return a copy of SERVICES with every port shifted by ``offset``."""
    if offset == 0:
        return list(SERVICES)
    shifted: list[ServiceEndpoint] = []
    for service in SERVICES:
        if service.kind == "gateway":
            shifted.append(service)
            continue
        shifted.append(
            ServiceEndpoint(
                key=service.key,
                label=service.label,
                project_dir=service.project_dir,
                kind=service.kind,
                port=service.port + offset,
                owner=service.owner,
                registration=service.registration,
                design_system=service.design_system,
                health_path=service.health_path,
            )
        )
    return shifted
