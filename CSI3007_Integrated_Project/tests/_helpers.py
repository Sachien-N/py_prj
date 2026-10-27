"""Repository-level tests for the CSI3007 integrated project.

Run from the repository root with any of:
    python -m pytest tests/ -q
    python -m pytest tests/test_individual_projects.py -q

These tests validate the integrated repository as a whole (structure,
per-project health, API contracts, data exchange configuration and a live
end-to-end exchange). The three applications keep their own test suites
under ``person_*/tests``; ``test_individual_projects.py`` runs those too.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PROJECT_DIRS = {
    "person_a": "person_a_sachien_n_23MID0255",
    "person_b": "person_b_shravan_n_a_23MID0445",
    "person_c": "person_c_hariharan_s_23MID0182",
}

PROJECT_META = {
    "person_a_sachien_n_23MID0255": ("Sachien N", "23MID0255", "Claymorphism"),
    "person_b_shravan_n_a_23MID0445": ("Shravan N A", "23MID0445", "Glassmorphism"),
    "person_c_hariharan_s_23MID0182": ("Hariharan S", "23MID0182", "Neumorphism"),
}


def _project_file(project: str, *parts: str) -> Path:
    return REPO_ROOT / PROJECT_DIRS[project] / Path(*parts)
