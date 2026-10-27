"""A gating score is paired with a check outside the score.

A score used to gate a decision becomes the target, and agent work
measurably drifts from a visible proxy as it grows
(docs/knowledge-corpus/decoherence.md). These anchor on the added
clauses, so a revert fails them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL = Path(__file__).parents[3] / "skills" / "evaluation-framework" / "SKILL.md"


@pytest.fixture
def skill_text() -> str:
    """Return SKILL.md with whitespace collapsed."""
    return " ".join(SKILL.read_text().split())


def test_thresholds_section_names_the_proxy_risk(skill_text: str) -> None:
    """The thresholds step says a gating score becomes the target."""
    section = skill_text[
        skill_text.index("### 4. Apply Decision Thresholds") : skill_text.index(
            "## Quick Start"
        )
    ]
    assert "A score that gates a decision becomes the target" in section
    assert "docs/knowledge-corpus/decoherence.md" in section


def test_exit_criteria_require_an_outside_check(skill_text: str) -> None:
    """Exit criteria name the check that sits outside each gating score."""
    exit_section = skill_text[skill_text.index("## Exit Criteria") :]
    assert "check outside the score" in exit_section
