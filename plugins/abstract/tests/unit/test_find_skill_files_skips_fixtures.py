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


def test_a_skill_whose_name_contains_test_is_still_found(tmp_path: Path) -> None:
    """A path component only has to contain `test` for the guard to skip it.

    The guard matches a whole path component, so `testing-quality` is
    found. The old name for this test promised a skill directory named
    `tests`, which the body never planted and which the implementation
    skips; that case is covered below.
    """
    shipped = _skill(tmp_path, "skills", "testing-quality")
    assert find_skill_files(tmp_path) == [shipped]


def test_a_skill_directory_named_tests_is_skipped(tmp_path: Path) -> None:
    """The guard is on the component, so a skill called `tests` is collateral.

    Discovery cannot tell a skill directory named `tests` from a fixture
    tree, and the fixture case is the one that matters. This pins the
    trade-off so a future rename of the guard has to face it.
    """
    shipped = _skill(tmp_path, "skills", "real")
    _skill(tmp_path, "skills", "tests")

    assert find_skill_files(tmp_path) == [shipped]


def test_a_checkout_under_a_tests_directory_still_finds_skills(
    tmp_path: Path,
) -> None:
    """Only components below the search root mark a fixture.

    A repository cloned into ~/tests/ must not lose every skill because
    an ancestor of the root happens to be named `tests`.
    """
    root = tmp_path / "tests" / "plugin"
    shipped = _skill(root, "skills", "real")
    assert find_skill_files(root) == [shipped]
