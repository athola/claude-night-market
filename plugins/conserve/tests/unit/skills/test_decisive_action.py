"""Tests for decisive-action skill.

This module validates the decisive action skill structure
and content following TDD/BDD patterns.

Issue #67: Question threshold for decisive action
"""

import re
from pathlib import Path

import pytest


class TestDecisiveActionStructure:
    """Feature: Decisive action skill structure.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "decisive-action"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the decisive-action skill directory
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


class TestDecisiveActionThresholds:
    """Feature: Decisive action question thresholds.

    As a developer
    I want clear guidance on when to ask vs proceed
    So that workflow is efficient without making wrong assumptions
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "decisive-action"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_ask_threshold(self, skill_content: str) -> None:
        """Scenario: Skill defines when to ask questions.

        Given the skill content
        When checking for ask threshold
        Then criteria for asking should be defined.
        """
        ask_indicators = ["when to ask", "ask if", "clarif", "ambigui"]
        has_ask_threshold = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in ask_indicators
        )
        assert has_ask_threshold, "Ask threshold not defined"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_proceed_threshold(self, skill_content: str) -> None:
        """Scenario: Skill defines when to proceed without asking.

        Given the skill content
        When checking for proceed threshold
        Then criteria for proceeding should be defined.
        """
        proceed_indicators = ["proceed", "without asking", "assume", "default"]
        has_proceed_threshold = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in proceed_indicators
        )
        assert has_proceed_threshold, "Proceed threshold not defined"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_destructive_operations(self, skill_content: str) -> None:
        """Scenario: Skill addresses destructive operations.

        Given the skill content
        When checking for destructive guidance
        Then destructive operations should always require confirmation.
        """
        destructive_indicators = ["destruct", "delete", "irreversible", "data loss"]
        has_destructive_guidance = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in destructive_indicators
        )
        assert has_destructive_guidance, "Destructive operation guidance not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_reversibility(self, skill_content: str) -> None:
        """Scenario: Skill considers reversibility.

        Given the skill content
        When checking for reversibility guidance
        Then reversible operations should be treated differently.
        """
        assert re.search(r"revers", skill_content, re.IGNORECASE), (
            "Reversibility not covered"
        )


class TestDecisiveActionSafetyMechanisms:
    """Feature: Safety mechanisms for decisive action.

    As a developer
    I want safety mechanisms
    So that decisive action doesn't cause harm
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "decisive-action"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_dry_run(self, skill_content: str) -> None:
        """Scenario: Skill mentions dry-run or preview.

        Given the skill content
        When checking for dry-run guidance
        Then preview mechanisms should be mentioned.
        """
        preview_indicators = ["dry.?run", "preview", "show.*before"]
        has_preview = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in preview_indicators
        )
        assert has_preview, "Dry-run/preview not covered"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_covers_undo_capability(self, skill_content: str) -> None:
        """Scenario: Skill mentions undo capability.

        Given the skill content
        When checking for undo guidance
        Then undo/rollback should be mentioned.
        """
        undo_indicators = ["undo", "rollback", "revert", "backup"]
        has_undo = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in undo_indicators
        )
        assert has_undo, "Undo capability not covered"


class TestDecisiveActionExamples:
    """Feature: Decisive action examples.

    As a developer
    I want clear examples
    So that I understand when to ask vs proceed
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill file content."""
        skill_dir = Path(__file__).parents[3] / "skills" / "decisive-action"
        skill_file = skill_dir / "SKILL.md"
        return skill_file.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_should_ask_examples(self, skill_content: str) -> None:
        """Scenario: Skill has 'should ask' examples.

        Given the skill content
        When checking for examples
        Then examples of when to ask should be present.
        """
        # Should have concrete examples
        assert re.search(
            r"(example|scenario).*ask", skill_content, re.IGNORECASE
        ) or re.search(r"ask.*(example|scenario)", skill_content, re.IGNORECASE), (
            "Should-ask examples not found"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_should_proceed_examples(self, skill_content: str) -> None:
        """Scenario: Skill has 'should proceed' examples.

        Given the skill content
        When checking for examples
        Then examples of when to proceed should be present.
        """
        proceed_example_indicators = [
            "standard approach",
            "easily reversible",
            "obvious",
            "clear",
        ]
        has_proceed_examples = any(
            re.search(indicator, skill_content, re.IGNORECASE)
            for indicator in proceed_example_indicators
        )
        assert has_proceed_examples, "Should-proceed examples not found"
