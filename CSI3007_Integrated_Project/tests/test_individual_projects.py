"""Runs each project's own test suite and checks repository structure."""

from __future__ import annotations

import subprocess
import sys

import pytest

from tests._helpers import PROJECT_DIRS, PROJECT_META, REPO_ROOT


@pytest.mark.parametrize("project", sorted(PROJECT_DIRS))
def test_project_suite_passes(project: str):
    """Run the per-project pytest suite in a subprocess (isolated config)."""
    project_dir = REPO_ROOT / PROJECT_DIRS[project]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"{project} test suite failed:\n{result.stdout[-3000:]}\n{result.stderr[-1000:]}"
    )
    assert "passed" in result.stdout


@pytest.mark.parametrize(
    "project_dir_name",
    sorted(PROJECT_META),
)
def test_ownership_files_present(project_dir_name: str):
    """Each project folder exists with entry points, README and .env template."""
    owner, registration, design_system = PROJECT_META[project_dir_name]
    root = REPO_ROOT / project_dir_name
    for required in (
        "app.py",
        "api.py",
        "config.py",
        "models.py",
        "schemas.py",
        "database.py",
        "ui/dashboard.py",
        "ui/theme.py",
        ".streamlit/config.toml",
        "README.md",
        ".env.example",
        "requirements.txt",
    ):
        assert (root / required).is_file(), f"missing {project_dir_name}/{required}"
    readme = (root / "README.md").read_text(encoding="utf-8", errors="replace").lower()
    assert owner.lower() in readme, f"{project_dir_name} README does not name {owner}"
    assert registration.lower() in readme, f"{project_dir_name} README lacks registration number"


@pytest.mark.parametrize(
    "project_dir_name,design_system",
    [(k, v[2]) for k, v in sorted(PROJECT_META.items())],
)
def test_design_system_theme_modules(project_dir_name: str, design_system: str):
    """Every project declares its own design system in ui/theme.py."""
    theme = (REPO_ROOT / project_dir_name / "ui" / "theme.py").read_text(encoding="utf-8")
    assert f'DESIGN_SYSTEM = "{design_system}"' in theme
    assert "def apply_theme" in theme


def test_integrated_repository_layout():
    """Required top-level files and folders exist."""
    for required in (
        "README.md",
        "requirements.txt",
        "pytest.ini",
        "start_all.py",
        "run_all.py",
        ".gitignore",
        ".env.example",
        "integration/api_gateway.py",
        "integration/service_registry.py",
        "integration/health_checks.py",
        "shared/config.py",
        "shared/logging_config.py",
        "shared/exceptions.py",
        "scripts/setup_windows.ps1",
        "scripts/setup_macos.sh",
        "scripts/start_windows.ps1",
        "scripts/start_macos.sh",
        "docs/input_inventory.md",
    ):
        assert (REPO_ROOT / required).is_file(), f"missing {required}"
    for folder in ("docs", "integration", "shared", "scripts", "tests", "integration_tests"):
        assert (REPO_ROOT / folder).is_dir(), f"missing folder {folder}"


def test_registry_ownership_matches_structure():
    """The service registry names the correct owners and folders."""
    sys.path.insert(0, str(REPO_ROOT))
    from integration.service_registry import PROJECT_SUMMARY  # noqa: E402

    for entry in PROJECT_SUMMARY:
        folder = REPO_ROOT / {
            "Person A": "person_a_sachien_n_23MID0255",
            "Person B": "person_b_shravan_n_a_23MID0445",
            "Person C": "person_c_hariharan_s_23MID0182",
        }[entry["person"]]
        assert folder.is_dir()
        config_text = (folder / "config.py").read_text(encoding="utf-8").lower()
        assert entry["owner"].lower() in config_text
        assert entry["registration"].lower() in config_text
