"""Tests for war-room skill structure and Discussion publishing integration.

Validates that the war-room SKILL.md documents all 8 phases including
Phase 8 (Discussion Publishing) added in the discussions-fix branch.
"""

from __future__ import annotations

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
    @pytest.mark.parametrize(
        "phase",
        [
            "Phase 1",
            "Phase 2",
            "Phase 3",
            "Phase 4",
            "Phase 5",
            "Phase 6",
            "Phase 7",
            "Phase 8",
        ],
        ids=[f"phase-{i}" for i in range(1, 9)],
    )
    def test_skill_documents_phase(self, skill_content: str, phase: str) -> None:
        """Scenario: Skill documents each phase of deliberation.

        Given the war-room skill
        When reviewing the phase listing
        Then the specified phase should be present
        """
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
    def test_phase_8_defaults_to_publish(self, skill_content: str) -> None:
        """Scenario: Phase 8 defaults to publishing.

        Given the war-room skill
        When reviewing Phase 8 references
        Then it should indicate publishing is the default
        """
        # "default" appears in the Discussion Publishing section
        # which documents Phase 8 behavior
        assert "publishing is the default" in skill_content.lower(), (
            "Phase 8 should default to publishing"
        )


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
    def test_discussion_publishing_allows_opt_out(self, skill_content: str) -> None:
        """Scenario: Publishing allows user opt-out.

        Given the Discussion Publishing section
        When reviewing the workflow
        Then the user should be able to opt out
        """
        section_start = skill_content.find("### Discussion Publishing")
        section = skill_content[section_start : section_start + 600]
        assert "opt out" in section.lower() or "decline" in section.lower(), (
            "Should allow user to opt out of publishing"
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
        section = skill_content[section_start : section_start + 700]
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
        section = skill_content[section_start : section_start + 700]
        assert "Decisions" in section


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
