"""Tests for response-compression skill.

This module validates the response compression skill structure
and content following TDD/BDD patterns.

Covers:
- Issue #63: response-compression skill
- Issue #65: termination and directness guidelines
"""

import re
from pathlib import Path

import pytest


class TestResponseCompressionStructure:
    """Feature: Response compression skill structure.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "response-compression"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the response-compression skill directory
        When checking for SKILL.md
        Then the file should exist.
        """
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md has valid frontmatter.

        Given the SKILL.md file
        When parsing the file
        Then it should have YAML frontmatter.
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        assert content.startswith("---"), "SKILL.md should start with frontmatter"
        assert content.count("---") >= 2, "SKILL.md should have closing frontmatter"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_frontmatter_has_required_fields(self, skill_dir: Path) -> None:
        """Scenario: Frontmatter has required fields.

        Given the SKILL.md frontmatter
        When checking required fields
        Then name, description, and category should be present.
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        parts = content.split("---", 2)
        assert len(parts) >= 3, "Could not extract frontmatter"
        frontmatter = parts[1]

        assert "name:" in frontmatter, "Frontmatter missing 'name' field"
        assert "description:" in frontmatter, "Frontmatter missing 'description' field"
        assert "category:" in frontmatter, "Frontmatter missing 'category' field"


class TestResponseCompressionBloatElimination:
    """Feature: Response bloat elimination patterns.

    As a developer
    I want guidance on eliminating response bloat
    So that responses are concise and efficient
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "response-compression"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_emoji_elimination(self, skill_content: str) -> None:
        """Scenario: Skill covers emoji elimination.

        Given the skill content
        When checking for emoji guidance
        Then emoji elimination should be documented.
        """
        assert re.search(r"emoji", skill_content, re.IGNORECASE), (
            "Emoji elimination not covered"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_filler_word_elimination(self, skill_content: str) -> None:
        """Scenario: Skill covers filler word elimination.

        Given the skill content
        When checking for filler guidance
        Then filler words like 'just', 'simply' should be mentioned.
        """
        filler_words = ["just", "simply", "basically", "essentially"]
        has_filler_guidance = any(
            re.search(rf"\b{word}\b", skill_content, re.IGNORECASE)
            for word in filler_words
        )
        assert has_filler_guidance, "Filler word elimination not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_hedging_elimination(self, skill_content: str) -> None:
        """Scenario: Skill covers hedging language elimination.

        Given the skill content
        When checking for hedging guidance
        Then hedging words should be documented.
        """
        assert re.search(r"hedg", skill_content, re.IGNORECASE), (
            "Hedging language elimination not covered"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_hype_elimination(self, skill_content: str) -> None:
        """Scenario: Skill covers hype word elimination.

        Given the skill content
        When checking for hype guidance
        Then hype words should be mentioned.
        """
        hype_indicators = ["powerful", "amazing", "robust", "hype"]
        has_hype_guidance = any(
            re.search(rf"\b{word}\b", skill_content, re.IGNORECASE)
            for word in hype_indicators
        )
        assert has_hype_guidance, "Hype word elimination not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_before_after_examples(self, skill_content: str) -> None:
        """Scenario: Skill has before/after transformation examples.

        Given the skill content
        When checking for examples
        Then before and after examples should exist.
        """
        assert re.search(r"before", skill_content, re.IGNORECASE), (
            "Before examples not found"
        )
        assert re.search(r"after", skill_content, re.IGNORECASE), (
            "After examples not found"
        )


class TestResponseTermination:
    """Feature: Response termination guidelines (Issue #65).

    As a developer
    I want guidance on immediate response termination
    So that responses don't include unnecessary summaries
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "response-compression"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_termination_rules(self, skill_content: str) -> None:
        """Scenario: Skill covers termination rules.

        Given the skill content
        When checking for termination guidance
        Then termination rules should be documented.
        """
        termination_indicators = ["terminat", "end response", "stop", "conclud"]
        has_termination = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in termination_indicators
        )
        assert has_termination, "Response termination rules not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_summary_avoidance(self, skill_content: str) -> None:
        """Scenario: Skill covers summary avoidance.

        Given the skill content
        When checking for summary guidance
        Then unnecessary summary avoidance should be mentioned.
        """
        assert re.search(r"summar", skill_content, re.IGNORECASE), (
            "Summary avoidance not covered"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_next_steps_avoidance(self, skill_content: str) -> None:
        """Scenario: Skill covers 'next steps' avoidance.

        Given the skill content
        When checking for next steps guidance
        Then 'next steps' pattern should be addressed.
        """
        assert re.search(r"next step", skill_content, re.IGNORECASE), (
            "'Next steps' avoidance not covered"
        )


class TestDirectnessGuidelines:
    """Feature: Direct language guidelines (Issue #65).

    As a developer
    I want guidance on direct language
    So that responses are information-dense without being rude
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "response-compression"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_encouragement_bloat(self, skill_content: str) -> None:
        """Scenario: Skill covers encouragement bloat.

        Given the skill content
        When checking for encouragement guidance
        Then phrases like 'Great question!' should be addressed.
        """
        encouragement_patterns = [
            "great question",
            "excellent",
            "good point",
            "encouragement",
        ]
        has_encouragement_guidance = any(
            re.search(pattern, skill_content, re.IGNORECASE)
            for pattern in encouragement_patterns
        )
        assert has_encouragement_guidance, "Encouragement bloat not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_rapport_building_avoidance(self, skill_content: str) -> None:
        """Scenario: Skill covers rapport-building avoidance.

        Given the skill content
        When checking for rapport guidance
        Then phrases like "I'd be happy to" should be addressed.
        """
        rapport_indicators = ["happy to", "feel free", "rapport", "let me know"]
        has_rapport_guidance = any(
            re.search(pattern, skill_content, re.IGNORECASE)
            for pattern in rapport_indicators
        )
        assert has_rapport_guidance, "Rapport-building avoidance not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_preserves_not_rude_balance(self, skill_content: str) -> None:
        """Scenario: Skill maintains direct != rude balance.

        Given the skill content
        When checking for balance guidance
        Then the skill should clarify directness is not rudeness.
        """
        balance_indicators = ["not rude", "direct", "helpful", "balance", "preserve"]
        has_balance = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in balance_indicators
        )
        assert has_balance, "Direct != rude balance not covered"


class TestPreservationGuidelines:
    """Feature: Content preservation guidelines.

    As a developer
    I want to know what content to preserve
    So that important information is not eliminated
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "response-compression"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_technical_emoji_preservation(self, skill_content: str) -> None:
        """Scenario: Skill covers technical emoji preservation.

        Given the skill content
        When checking for preservation guidance
        Then status indicators should be mentioned as exceptions.
        """
        # Should mention that status indicators like checkmarks are OK
        status_indicators = ["status", "indicator", "check", "warning"]
        has_preservation = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in status_indicators
        )
        assert has_preservation, "Technical emoji preservation not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_safety_info_preservation(self, skill_content: str) -> None:
        """Scenario: Skill covers safety info preservation.

        Given the skill content
        When checking for safety guidance
        Then safety warnings should be preserved.
        """
        assert re.search(r"safety|warning|critical", skill_content, re.IGNORECASE), (
            "Safety info preservation not covered"
        )
