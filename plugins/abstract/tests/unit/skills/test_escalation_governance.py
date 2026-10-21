"""Escalation governance counts a concern's models before escalating.

A task that crosses two coexisting models of one concern looks harder
than it is. That is a knowledge gap, which the Iron Law answers with
investigation (docs/knowledge-corpus/decoherence.md). These anchor on
the added clause, so a revert fails them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL = Path(__file__).parents[3] / "skills" / "escalation-governance" / "SKILL.md"


@pytest.fixture
def skill_text() -> str:
    """Return SKILL.md with whitespace collapsed."""
    return " ".join(SKILL.read_text().split())


def test_investigation_step_counts_models_of_the_concern(skill_text: str) -> None:
    """Step 2 asks how many ways the codebase already models the concern."""
    step_two = skill_text[
        skill_text.index("### 2. Have I investigated") : skill_text.index(
            "### 3. Is escalation"
        )
    ]
    assert "How many ways does this codebase already model the concern" in step_two


def test_coexisting_models_are_a_knowledge_gap(skill_text: str) -> None:
    """Coexisting models are read, and do not justify escalation."""
    assert "read both before escalating" in skill_text
