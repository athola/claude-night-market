"""Folded leyline skills survive as modules of the skill that absorbed them.

Issue #781: every skill's name and description is resident in every
session, so contracts that no user invokes directly were folded into the
skill that routes their intent. The guidance must stay reachable: each
folded skill's directory is gone, its content is a module of the target,
and the target's SKILL.md names that module so a reader can find it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SKILLS = Path(__file__).resolve().parents[3] / "skills"

FOLDS = [
    ("pytest-config", "testing-quality-standards"),
    ("utility", "evaluation-framework"),
    ("quota-management", "service-registry"),
    ("usage-logging", "service-registry"),
    ("deferred-capture", "decision-journal"),
    ("storage-templates", "decision-journal"),
]


def _frontmatter(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---")[1])


@pytest.mark.unit
@pytest.mark.parametrize(("source", "target"), FOLDS)
def test_folded_skill_directory_is_gone(source: str, target: str) -> None:
    assert not (SKILLS / source).exists(), f"{source} should be folded into {target}"


@pytest.mark.unit
@pytest.mark.parametrize(("source", "target"), FOLDS)
def test_folded_skill_is_a_module_of_its_target(source: str, target: str) -> None:
    module = SKILLS / target / "modules" / f"{source}.md"

    assert module.is_file()
    assert _frontmatter(module)["name"] == source


@pytest.mark.unit
@pytest.mark.parametrize(("source", "target"), FOLDS)
def test_target_skill_lists_and_points_at_the_module(source: str, target: str) -> None:
    skill = SKILLS / target / "SKILL.md"
    entry = f"modules/{source}.md"

    assert entry in _frontmatter(skill)["modules"]
    body = skill.read_text(encoding="utf-8").split("---", 2)[2]
    assert entry in body, f"{target} SKILL.md body never says when to load {entry}"


@pytest.mark.unit
@pytest.mark.parametrize(("source", "target"), FOLDS)
def test_no_skill_still_depends_on_a_folded_skill(source: str, target: str) -> None:
    """A dependency on a folded name points at a node the skill graph lost."""
    stale = [
        str(skill.relative_to(SKILLS.parents[1]))
        for skill in SKILLS.parents[1].glob("*/skills/*/SKILL.md")
        if source in (_frontmatter(skill).get("dependencies") or [])
    ]

    assert not stale, f"{stale} depend on {source}; depend on {target} instead"
