# ruff: noqa: D101,D102,D103
"""BDD tests for smart-sourcing skill."""

from pathlib import Path

import pytest


class TestSmartSourcingSkillStructure:
    """Feature: Smart-sourcing skill provides intelligent citation guidelines.

    As a user making factual claims
    I want guidance on when to cite sources
    So that I balance accuracy with token efficiency
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        return Path(__file__).parents[3] / "skills" / "smart-sourcing" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        return skill_path.read_text()

    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Given the conserve plugin, smart-sourcing skill should exist."""
        assert skill_path.exists()

    @pytest.mark.unit
    def test_skill_defines_when_to_source(self, skill_content: str) -> None:
        """Given the skill, it should define when sources are required."""
        assert "REQUIRE" in skill_content or "When to Source" in skill_content
        # Should mention version numbers as requiring sources
        assert "version" in skill_content.lower()

    @pytest.mark.unit
    def test_skill_defines_when_not_to_source(self, skill_content: str) -> None:
        """Given the skill, it should define when sources are NOT required."""
        assert "DO NOT" in skill_content or "not require" in skill_content.lower()
        # Should mention general concepts don't need sources
        assert (
            "concept" in skill_content.lower() or "knowledge" in skill_content.lower()
        )

    @pytest.mark.unit
    def test_skill_addresses_token_cost(self, skill_content: str) -> None:
        """Given the skill, it should discuss token cost tradeoffs."""
        assert "token" in skill_content.lower()
        assert "cost" in skill_content.lower()

    @pytest.mark.unit
    def test_skill_provides_decision_framework(self, skill_content: str) -> None:
        """Given the skill, it should provide a decision framework."""
        assert (
            "framework" in skill_content.lower() or "decision" in skill_content.lower()
        )

    @pytest.mark.unit
    def test_skill_includes_examples(self, skill_content: str) -> None:
        """Given the skill, it should include practical examples."""
        assert "example" in skill_content.lower()
        assert "```" in skill_content  # Code blocks for examples
