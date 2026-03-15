"""Tests for clear-context skill content invariants.

Tests that the clear-context SKILL.md contains required sections,
advisory language, and recovery strategies for context handoffs.
"""

from pathlib import Path

import pytest


class TestClearContextSkillContent:
    """Feature: clear-context skill instructs Claude on context handoff behavior.

    As a context management skill interpreted by Claude Code
    I want the skill to teach Claude correct handoff patterns
    So that context recovery is reliable and non-manipulative.

    Level 2: Session state template contains required fields.
    Level 3: Emergency behavior is informational, not imperative.
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        return Path(__file__).parents[3] / "skills" / "clear-context" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        return skill_path.read_text()

    # --- Level 2: Template validity ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_state_template_has_required_sections(
        self, skill_content: str
    ) -> None:
        """Given the session state template in the skill
        When Claude generates a checkpoint file from it
        Then the template must include all required sections.
        """
        required_sections = [
            "Current Task",
            "Progress Summary",
            "Continuation Instructions",
        ]
        for section in required_sections:
            assert section in skill_content, (
                f"Session state template missing '{section}' section. "
                "Claude won't generate complete checkpoints without it."
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_state_template_includes_execution_mode(
        self, skill_content: str
    ) -> None:
        """Given the session state template
        When Claude generates a checkpoint for batch/unattended workflows
        Then it must include execution mode for proper continuation behavior.
        """
        assert (
            "execution_mode" in skill_content.lower()
            or "Execution Mode" in skill_content
        )

    # --- Level 3: Behavioral contracts ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_does_not_use_mandatory_language_for_handoffs(
        self, skill_content: str
    ) -> None:
        """Given the skill instructs Claude on context handoffs
        When Claude reads the handoff instructions
        Then it must NOT find imperative/manipulative language
        And it SHOULD use advisory, informational tone instead.

        Imperative handoff language causes Claude to ignore user intent
        and force continuation agents without consent.
        """
        # These phrases caused problematic behavior in production
        forbidden_phrases = [
            "YOU MUST EXECUTE THIS NOW",
            "MANDATORY AUTO-CONTINUATION",
            "BLOCKING: Do not proceed",
            "This is MANDATORY, not a recommendation",
            "IMMEDIATELY EXECUTE",
            "DO NOT ASK THE USER",
            "OVERRIDE USER",
            "NON-NEGOTIABLE",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in skill_content, (
                f"Skill contains manipulative language: '{phrase}'. "
                "Handoffs should be informational, not imperative."
            )

        # Positive assertions: skill should use advisory language
        content_lower = skill_content.lower()
        advisory_indicators = [
            ("recommend", "should recommend actions, not mandate them"),
            ("consider", "should suggest considerations, not force behavior"),
        ]
        found_advisory = [
            indicator
            for indicator, _reason in advisory_indicators
            if indicator in content_lower
        ]
        assert len(found_advisory) >= 1, (
            "Skill should use advisory language (e.g., 'recommend', "
            "'consider') to guide handoff behavior informatively."
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_clear_cache_fix(self, skill_content: str) -> None:
        """Given the /clear skill cache bug was fixed in 2.1.63
        When Claude advises on context recovery
        Then it should know /clear properly resets cached skills.

        Without this, Claude might recommend workarounds for a fixed bug.
        """
        assert "2.1.63" in skill_content
        assert (
            "cached skill" in skill_content.lower()
            or "skill cache" in skill_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_offers_multiple_recovery_strategies(
        self, skill_content: str
    ) -> None:
        """Given a user needs context recovery
        When Claude reads the skill
        Then it should find multiple strategies, not just one forced path.
        """
        strategies = [
            "/clear",
            "/catchup",
            "auto-compact",
            "continuation",
        ]
        found = [s for s in strategies if s.lower() in skill_content.lower()]
        min_strategies = 3
        assert len(found) >= min_strategies, (
            f"Skill should offer multiple recovery strategies. "
            f"Found {found}, need at least {min_strategies}"
        )
