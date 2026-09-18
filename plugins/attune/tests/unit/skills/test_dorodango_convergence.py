"""Dorodango converges on records and can un-converge (ADR-0025)."""

from __future__ import annotations

from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "dorodango"


@pytest.fixture(scope="module")
def skill_text() -> str:
    """The dorodango SKILL.md text."""
    return (_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def test_clarity_and_consistency_are_bound_to_exit_codes(skill_text: str) -> None:
    """A reviewer's '0 issues' alone no longer converges a dimension."""
    assert "linter and formatter exit codes" in skill_text
    assert "irreversible" not in skill_text


def test_a_regression_un_converges_its_dimension(skill_text: str) -> None:
    """A later regression reopens a converged dimension in both files."""
    assert "un-converges" in skill_text
    passes = (_SKILL_DIR / "modules" / "pass-definitions.md").read_text(
        encoding="utf-8"
    )
    assert "un-converge correctness" in passes
