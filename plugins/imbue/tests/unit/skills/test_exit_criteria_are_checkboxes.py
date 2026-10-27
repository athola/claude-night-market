"""Every imbue skill states its exit criteria as `- [ ]` items.

.claude/rules/skill-exit-criteria.md requires the checkbox form, and the
repository-wide test checks only that the heading exists.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[3] / "skills"


def _exit_criteria(skill_md: Path) -> str:
    match = re.search(
        r"^## Exit Criteria\n(.*?)(?=^## |\Z)",
        skill_md.read_text(encoding="utf-8"),
        re.DOTALL | re.MULTILINE,
    )
    assert match, f"{skill_md} has no Exit Criteria section"
    return match.group(1)


@pytest.mark.unit
@pytest.mark.parametrize(
    "skill_md", sorted(SKILLS.glob("*/SKILL.md")), ids=lambda p: p.parent.name
)
def test_every_exit_criterion_is_a_checkbox(skill_md: Path) -> None:
    """Each item starts `- [ ] `; an item may wrap onto indented lines."""
    items = [
        line
        for line in _exit_criteria(skill_md).splitlines()
        if line.strip() and not line.startswith("  ")
    ]
    assert items
    assert all(line.startswith("- [ ] ") for line in items), items
