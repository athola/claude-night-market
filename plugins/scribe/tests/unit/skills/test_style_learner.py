"""BDD tests for scribe style-learner skill structure.

Feature: Style Learner States Its Combinational Thesis
  As a downstream skill that consumes style profiles
  I want style-learner to declare why it combines metrics
  with exemplars
  So that the dual approach is not perceived as redundant.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "style-learner"
    / "SKILL.md"
)


class TestStyleLearnerThesisFirst:
    """Feature: style-learner SKILL.md leads with a thesis."""

    @pytest.fixture
    def skill_text(self) -> str:
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        assert SKILL_FILE.exists()

    @pytest.mark.unit
    def test_skill_states_thesis_in_lead(self, skill_text: str) -> None:
        """Lead must contain a bolded thesis sentence."""
        h1_idx = skill_text.find("# Style Learning Skill")
        assert h1_idx >= 0
        lead = skill_text[h1_idx : h1_idx + 600]
        assert "**" in lead, "Lead must contain a bolded thesis sentence"

    @pytest.mark.unit
    def test_thesis_explains_dual_method_rationale(self, skill_text: str) -> None:
        """The dual-method approach must be justified, not just stated."""
        text_lower = skill_text.lower()
        assert "metrics" in text_lower and "exemplars" in text_lower
        assert (
            "alone" in text_lower or "fails" in text_lower or ("weak" in text_lower)
        ), (
            "Style-learner must explain WHY it combines metrics + "
            "exemplars (each fails alone), not just LIST that it does"
        )

    @pytest.mark.unit
    def test_no_tier_1_slop_in_prose_lead(self, skill_text: str) -> None:
        """Lead must not use tier-1 slop words ('comprehensive', etc.)."""
        h1_idx = skill_text.find("# Style Learning Skill")
        lead = skill_text[h1_idx : h1_idx + 800]
        forbidden = ["comprehensive", "actionable", "leverage", "delve"]
        for word in forbidden:
            assert word not in lead.lower(), (
                f"Tier-1 slop word '{word}' must not appear in the style-learner lead"
            )
