"""Service registry for the CSI3007 integrated project.

Single source of truth describing the three independently owned applications
and the integration gateway. Used by ``start_all.py``, the gateway and the
health checks. Importing this module requires only the standard library plus
``shared.config``.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from shared.config import REPO_ROOT, SERVICES, SERVICES_BY_KEY, ServiceEndpoint
from shared.exceptions import ServiceRegistryError

__all__ = [
    "list_services",
    "get_service",
    "project_dir",
    "person_projects",
    "service_summary",
    "PROJECT_SUMMARY",
]


def list_services() -> list[dict]:
    """Return every registered service as a plain dict."""
    return [asdict(service) for service in SERVICES]


def get_service(key: str) -> ServiceEndpoint:
    try:
        return SERVICES_BY_KEY[key]
    except KeyError as exc:
        raise ServiceRegistryError(f"Unknown service key: {key!r}") from exc


def project_dir(service: ServiceEndpoint | str) -> Path:
    """Absolute path of a service's project directory."""
    endpoint = get_service(service) if isinstance(service, str) else service
    return REPO_ROOT / endpoint.project_dir


def person_projects() -> list[ServiceEndpoint]:
    """The three person-owned API services (one per student)."""
    return [SERVICES_BY_KEY[key] for key in ("a_api", "b_api", "c_api")]


PROJECT_SUMMARY = [
    {
        "person": "Person A",
        "owner": "Sachien N",
        "registration": "23MID0255",
        "title": "Smart Expense Categorization and Budget Manager",
        "design_system": "Claymorphism",
        "api_port": 8001,
        "ui_port": 8501,
        "database": "person_a_sachien_n_23MID0255/data/person_a.db",
    },
    {
        "person": "Person B",
        "owner": "Shravan N A",
        "registration": "23MID0445",
        "title": "Smart Subscription Manager",
        "design_system": "Glassmorphism",
        "api_port": 8002,
        "ui_port": 8502,
        "database": "person_b_shravan_n_a_23MID0445/data/person_b.db",
    },
    {
        "person": "Person C",
        "owner": "Hariharan S",
        "registration": "23MID0182",
        "title": "Smart Home Electricity Monitoring and TNEB Bill Verification System",
        "design_system": "Neumorphism",
        "api_port": 8003,
        "ui_port": 8503,
        "database": "person_c_hariharan_s_23MID0182/data/person_c.db",
    },
]


def service_summary() -> list[dict]:
    """Compact per-service info for the landing page and health endpoint."""
    return [
        {
            "key": s.key,
            "label": s.label,
            "kind": s.kind,
            "url": s.base_url,
            "health_url": s.health_url,
            "owner": s.owner,
            "registration": s.registration,
            "design_system": s.design_system,
        }
        for s in SERVICES
    ]
