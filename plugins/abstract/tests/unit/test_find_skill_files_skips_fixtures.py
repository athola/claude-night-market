"""Skill discovery does not treat test fixtures as shipped skills (ADR-0025)."""

from __future__ import annotations

from pathlib import Path

from abstract.utils import find_skill_files


def _skill(root: Path, *parts: str) -> Path:
    path = root.joinpath(*parts, "SKILL.md")
    path.parent.mkdir(parents=True)
    path.write_text("---\nname: x\n---\n# x\n", encoding="utf-8")
    return path


def test_fixture_skills_under_tests_are_not_discovered(tmp_path: Path) -> None:
    """A planted skill tree under tests/ is data for a test, not a skill to validate."""
    shipped = _skill(tmp_path, "skills", "real")
    _skill(tmp_path, "tests", "fixtures", "skill_graph", "p", "skills", "alpha")
    assert find_skill_files(tmp_path) == [shipped]


def test_a_skill_named_tests_is_still_found(tmp_path: Path) -> None:
    """Only a directory component named tests is skipped, not a skill mentioning it."""
    shipped = _skill(tmp_path, "skills", "testing-quality")
    assert find_skill_files(tmp_path) == [shipped]
