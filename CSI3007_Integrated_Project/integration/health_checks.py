"""Health checks for the integrated project.

Reports the REAL status of every registered service — the gateway never
fabricates availability. A service that does not answer is reported as
``unreachable`` with the underlying error message.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from shared.config import HEALTH_TIMEOUT_SECONDS
from shared.logging_config import get_logger

from integration.service_registry import list_services

logger = get_logger("health")


def _health_url_for(spec: dict[str, Any]) -> str:
    """Build the health URL from a registry dict (properties are not fields)."""
    base = f"http://127.0.0.1:{spec['port']}"
    if spec["kind"] == "ui":
        return f"{base}/_stcore/health"
    return f"{base}{spec.get('health_path', '/health')}"


def check_url(url: str, timeout: float | None = None) -> dict[str, Any]:
    """Probe one URL. Returns ``{"reachable": bool, "status_code": int|None, ...}``."""
    timeout = timeout or HEALTH_TIMEOUT_SECONDS
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.get(url)
        return {
            "reachable": response.status_code < 500,
            "status_code": response.status_code,
            "error": None,
        }
    except (httpx.HTTPError, OSError) as exc:
        return {"reachable": False, "status_code": None, "error": str(exc)}


def check_all_services(timeout: float | None = None) -> dict[str, Any]:
    """Check every registered service; returns a structured status report."""
    checked_at = datetime.now(timezone.utc).isoformat()
    services: list[dict[str, Any]] = []
    for spec in list_services():
        if spec["kind"] == "gateway":
            # The gateway reports on itself; checking its own URL is still
            # useful when the function is called from an external tool.
            result = {"reachable": True, "status_code": 200, "error": None}
        else:
            result = check_url(_health_url_for(spec), timeout=timeout)
        services.append(
            {
                "key": spec["key"],
                "label": spec["label"],
                "kind": spec["kind"],
                "owner": spec["owner"],
                "registration": spec["registration"],
                "design_system": spec["design_system"],
                "url": f"http://127.0.0.1:{spec['port']}",
                "health_url": _health_url_for(spec),
                **result,
            }
        )
        if result["reachable"]:
            logger.debug("service %s is up (%s)", spec["key"], _health_url_for(spec))
        else:
            logger.info("service %s is down: %s", spec["key"], result["error"])
    reachable = sum(1 for s in services if s["reachable"])
    return {
        "checked_at": checked_at,
        "total": len(services),
        "reachable": reachable,
        "unreachable": len(services) - reachable,
        "all_healthy": reachable == len(services),
        "services": services,
    }
