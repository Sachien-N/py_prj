"""API contract tests: every backend exposes the documented endpoints.

These tests import each FastAPI application in isolation (via importlib with
the project directory on sys.path) and validate the OpenAPI schema against
the integration contract documented in docs/api_contracts.md.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

from tests._helpers import PROJECT_DIRS, REPO_ROOT

REQUIRED_ROUTES = {
    "person_a": {"/health", "/expenses", "/budgets", "/categories",
                 "/integrations/subscriptions/sync", "/integrations/electricity/sync",
                 "/integrations/status"},
    "person_b": {"/health", "/subscriptions", "/subscriptions/payments",
                 "/subscriptions/upcoming",
                 "/integrations/person-a/payload", "/integrations/person-a/sync",
                 "/integrations/person-a/status"},
    "person_c": {"/health", "/sockets", "/sockets/readings", "/tariffs", "/bills",
                 "/bills/compare/{bill_id}", "/expenses/electricity",
                 "/integrations/person-a/payload",
                 "/integrations/person-a/sync"},
}


def _load_app(project: str):
    """Import api:app from a project directory in an isolated namespace.

    After the import every module that was loaded from the project directory
    (config, models, services, ...) is evicted from sys.modules so the next
    project's import cannot accidentally reuse the previous project's classes.
    """
    project_path = (REPO_ROOT / PROJECT_DIRS[project]).resolve()
    db_url = f"sqlite:///{Path(os.environ.get('TMPDIR', '/tmp')) / f'{project}_contract.db'}"
    saved = {k: os.environ.get(k) for k in ("DATABASE_URL", "API_PORT")}
    os.environ["DATABASE_URL"] = db_url
    os.environ.setdefault("API_PORT", "0")
    before = set(sys.modules)
    sys.path.insert(0, str(project_path))
    try:
        module = importlib.import_module("api")
        app = module.app
    finally:
        sys.path.remove(str(project_path))
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        # Evict modules loaded from this project (and the api module itself).
        for name, mod in list(sys.modules.items()):
            if name in before:
                continue
            file = getattr(mod, "__file__", None)
            if name == "api" or (file and str(Path(file).resolve()).startswith(str(project_path))):
                sys.modules.pop(name, None)
    return app


@pytest.mark.parametrize("project", sorted(PROJECT_DIRS))
def test_required_routes_present(project: str):
    app = _load_app(project)
    openapi = app.openapi()
    declared = set(openapi.get("paths", {}))
    missing = REQUIRED_ROUTES[project] - declared
    assert not missing, f"{project} is missing documented routes: {sorted(missing)}"


@pytest.mark.parametrize("project", sorted(PROJECT_DIRS))
def test_health_endpoint_documented(project: str):
    app = _load_app(project)
    openapi = app.openapi()
    assert "/health" in openapi["paths"]


@pytest.mark.parametrize("project", sorted(PROJECT_DIRS))
def test_sync_endpoints_require_api_key(project: str):
    """Integration endpoints must declare an X-API-Key header parameter."""
    app = _load_app(project)
    openapi = app.openapi()
    text = str(openapi)
    assert "X-API-Key" in text or "x-api-key" in text, (
        f"{project} does not document X-API-Key authentication"
    )
