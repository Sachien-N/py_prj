"""Data-exchange configuration tests.

Validates that the cross-application exchange is configured coherently:
matching API keys per pair, correct URL wiring, idempotency fields in
payload schemas, and environment templates that agree with the code.
"""

from __future__ import annotations

import pytest

from tests._helpers import PROJECT_DIRS, REPO_ROOT


def _env_template(project: str) -> dict[str, str]:
    text = (REPO_ROOT / PROJECT_DIRS[project] / ".env.example").read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def test_person_a_pull_urls_and_keys_match_producers():
    """A's template must point at B and C with the keys B and C expect."""
    a = _env_template("person_a")
    b = _env_template("person_b")
    c = _env_template("person_c")
    assert a["PERSON_B_SYNC_API_KEY"] == b["PERSON_A_SYNC_API_KEY"]
    assert a["PERSON_C_SYNC_API_KEY"] == c["PERSON_A_SYNC_API_KEY"]
    assert a["PERSON_B_API_URL"].endswith(":8002")
    assert a["PERSON_C_API_URL"].endswith(":8003")


def test_ports_are_unique_and_documented():
    """Every project uses its own API/UI port pair (8001-8003 / 8501-8503)."""
    ports = {}
    for project, folder in PROJECT_DIRS.items():
        env = _env_template(project)
        ports[project] = int(env["API_PORT"])
    assert ports["person_a"] == 8001
    assert ports["person_b"] == 8002
    assert ports["person_c"] == 8003
    assert len(set(ports.values())) == 3


@pytest.mark.parametrize(
    "project,source_file,marker",
    [
        # A's schemas define the incoming payload contracts (A receives).
        ("person_a", "schemas.py", "source_app"),
        ("person_a", "schemas.py", "external_id"),
        # B and C build outgoing payloads in their integration services.
        ("person_b", "services/integration_service.py", "source_app"),
        ("person_b", "services/integration_service.py", "external_id"),
        ("person_c", "services/expense_service.py", "source_app"),
        ("person_c", "services/expense_service.py", "external_id"),
    ],
)
def test_payload_schemas_carry_idempotency_fields(project, source_file, marker):
    """Exchange payloads must carry idempotency + producer identity fields."""
    text = (REPO_ROOT / PROJECT_DIRS[project] / source_file).read_text(encoding="utf-8")
    assert marker in text, f"{project}/{source_file} lacks '{marker}'"


def test_each_project_owns_its_database():
    """DATABASE_URL templates point into the project's own data/ folder."""
    for project, folder in PROJECT_DIRS.items():
        env = _env_template(project)
        assert env["DATABASE_URL"].startswith("sqlite:///")
        assert "data/" in env["DATABASE_URL"], f"{project} must keep its DB in data/"
        assert folder.split("_")[0] + "_" in env["DATABASE_URL"] or "person_" in env["DATABASE_URL"]


def test_no_real_secrets_in_templates():
    """Templates use dev placeholder keys, never real credentials."""
    for project in PROJECT_DIRS:
        env = _env_template(project)
        for key, value in env.items():
            if "KEY" in key:
                assert "dev-" in value or "<" in value, (
                    f"{project} {key} looks like a real secret"
                )
