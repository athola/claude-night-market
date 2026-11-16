"""Plan artifacts record intent, not a preview of the diff.

"IDRs as records of intent" (Lachance, 2026): a record an agent fills in
drifts into narrating its planned implementation. Out of Scope keeps what
was chosen against on record, and task notes keep the decision, not the
steps.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BRIEFS = [
    ROOT / "skills" / "project-brainstorming" / "SKILL.md",
    ROOT / "commands" / "brainstorm.md",
]


def _brief_template(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("- Project Brief")
    return text[start : text.index("## Next Steps", start)]


@pytest.mark.unit
@pytest.mark.parametrize("path", BRIEFS, ids=["skill", "command"])
def test_brief_template_carries_problem_goals_and_out_of_scope(path: Path) -> None:
    """The orchestrator files issues from Out of Scope, so both briefs need it."""
    brief = _brief_template(path)
    for heading in ("## Problem Statement", "## Goals", "## Out of Scope"):
        assert heading in brief, heading
    # Google's design-doc sense: not negated goals
    assert "could reasonably be goals" in brief


@pytest.mark.unit
def test_blueprint_task_notes_record_the_decision_not_the_steps() -> None:
    """Steps are the diff's job; the plan keeps the choice and its reason."""
    text = (ROOT / "commands" / "blueprint.md").read_text(encoding="utf-8")
    assert "Implementation detail 1" not in text
    assert "**Decision Notes**" in text
