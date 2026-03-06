"""Tests for war-room skill structure and Discussion publishing integration.

Validates that the war-room SKILL.md documents all 8 phases including
Phase 8 (Discussion Publishing) added in the discussions-fix branch.
"""

from pathlib import Path

import pytest


class TestWarRoomPhaseDocumentation:
    """Feature: War-room skill documents all execution phases.

    As a war-room user
    I want all phases documented in SKILL.md
    So that I can follow the complete deliberation workflow
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room skill."""
        return Path(__file__).parents[3] / "skills" / "war-room" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: War-room skill file exists.

        Given the attune plugin skills directory
        When looking for war-room
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_all_eight_phases(self, skill_content: str) -> None:
        """Scenario: Skill documents all 8 phases of deliberation.

        Given the war-room skill
        When reviewing the phase listing
        Then phases 1 through 8 should be present
        """
        expected_phases = [
            "Phase 1",
            "Phase 2",
            "Phase 3",
            "Phase 4",
            "Phase 5",
            "Phase 6",
            "Phase 7",
            "Phase 8",
        ]
        for phase in expected_phases:
            assert phase in skill_content, f"Missing {phase} in war-room SKILL.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_phase_8_is_discussion_publishing(self, skill_content: str) -> None:
        """Scenario: Phase 8 is Discussion Publishing.

        Given the war-room skill
        When checking Phase 8
        Then it should be labeled 'Discussion Publishing'
        """
        assert "Phase 8" in skill_content
        assert "Discussion Publishing" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_phase_8_is_optional(self, skill_content: str) -> None:
        """Scenario: Phase 8 is marked optional.

        Given the war-room skill
        When reviewing Phase 8 description
        Then it should indicate the step is optional
        """
        # Find Phase 8 context and verify optionality
        idx = skill_content.find("Phase 8")
        assert idx != -1
        surrounding = skill_content[idx : idx + 300]
        assert "optional" in surrounding.lower(), "Phase 8 should be marked as optional"


class TestWarRoomDiscussionPublishingSection:
    """Feature: War-room skill has a Discussion Publishing section.

    As a war-room facilitator
    I want clear documentation on Discussion publishing
    So that deliberation outcomes can be shared via GitHub Discussions
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "war-room" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_discussion_publishing_section_exists(self, skill_content: str) -> None:
        """Scenario: Discussion Publishing section exists.

        Given the war-room skill
        When looking for the Discussion Publishing heading
        Then it should be present
        """
        assert "### Discussion Publishing" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_discussion_publishing_requires_confirmation(
        self, skill_content: str
    ) -> None:
        """Scenario: Publishing requires user confirmation.

        Given the Discussion Publishing section
        When reviewing the workflow
        Then user confirmation should be required before publishing
        """
        section_start = skill_content.find("### Discussion Publishing")
        section = skill_content[section_start : section_start + 500]
        assert "confirmation" in section.lower(), (
            "Should require user confirmation before publishing"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_discussion_publishing_references_module(self, skill_content: str) -> None:
        """Scenario: Skill references the discussion-publishing module.

        Given the war-room skill
        When looking for module references
        Then discussion-publishing.md should be referenced
        """
        assert "discussion-publishing.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_discussion_publishing_handles_failures_gracefully(
        self, skill_content: str
    ) -> None:
        """Scenario: Publishing failures do not block the war room.

        Given the Discussion Publishing section
        When reviewing error handling
        Then failures should never block the workflow
        """
        section_start = skill_content.find("### Discussion Publishing")
        section = skill_content[section_start : section_start + 500]
        assert "never block" in section.lower() or "skip" in section.lower(), (
            "Publishing failures should never block war room workflow"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_discussion_publishing_creates_in_decisions_category(
        self, skill_content: str
    ) -> None:
        """Scenario: Discussions are created in the Decisions category.

        Given the Discussion Publishing section
        When reviewing the target category
        Then it should use the 'Decisions' category
        """
        section_start = skill_content.find("### Discussion Publishing")
        section = skill_content[section_start : section_start + 500]
        assert "Decisions" in section


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
