"""Tests for scope-guard skill structure and Discussion deferral integration.

Validates that the scope-guard SKILL.md documents the deferral workflow
including Step 4 (Discussion creation) added in the discussions-fix branch.
"""

from pathlib import Path

import pytest


class TestScopeGuardSkillStructure:
    """Feature: Scope-guard skill has valid structure.

    As a developer using scope-guard
    I want a well-structured skill file
    So that I can reliably evaluate feature worthiness
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the scope-guard skill."""
        return Path(__file__).parents[3] / "skills" / "scope-guard" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Scope-guard skill file exists.

        Given the imbue plugin skills directory
        When looking for scope-guard
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_worthiness_scoring(self, skill_content: str) -> None:
        """Scenario: Skill defines worthiness scoring.

        Given the scope-guard skill
        When reviewing the evaluation framework
        Then worthiness scoring should be present
        """
        assert "Worthiness" in skill_content
        assert "scope-guard:worthiness-scored" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_github_integration_module(
        self, skill_content: str
    ) -> None:
        """Scenario: Skill references the github-integration module.

        Given the scope-guard skill
        When looking for module references
        Then github-integration.md should be referenced
        """
        assert "github-integration.md" in skill_content


class TestScopeGuardDeferralWorkflow:
    """Feature: Scope-guard deferral creates GitHub issues and Discussions.

    As a developer deferring a feature
    I want the deferral workflow to capture full context
    So that deferred work is not lost when branches merge
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[3] / "skills" / "scope-guard" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deferral_step_1_creates_github_issue(self, skill_content: str) -> None:
        """Scenario: Deferral Step 1 creates a GitHub issue.

        Given the scope-guard deferral workflow
        When reviewing mandatory steps
        Then Step 1 should create a GitHub issue
        """
        assert "Create GitHub issue immediately" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deferral_step_2_marks_progress(self, skill_content: str) -> None:
        """Scenario: Deferral Step 2 marks progress tracking.

        Given the scope-guard deferral workflow
        When reviewing mandatory steps
        Then step 2 should mark scope-guard:github-issue-created
        """
        assert "scope-guard:github-issue-created" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deferral_step_3_offers_discussion_creation(
        self, skill_content: str
    ) -> None:
        """Scenario: Deferral Step 3 offers Discussion creation.

        Given the scope-guard deferral workflow
        When reviewing the discussion integration
        Then Step 3 should offer to create a Discussion
        """
        assert "Offer Discussion creation" in skill_content
        assert "Deliberations" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deferral_discussion_is_optional(self, skill_content: str) -> None:
        """Scenario: Discussion creation is optional.

        Given the scope-guard deferral workflow
        When reviewing Step 3
        Then it should prompt with Y/n (default yes)
        And declining should continue the workflow
        """
        assert "Y/n" in skill_content
        assert (
            "declined" in skill_content.lower() or "continue" in skill_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_deferral_step_4_is_backlog(self, skill_content: str) -> None:
        """Scenario: Step 4 is optional backlog queue addition.

        Given the scope-guard deferral workflow
        When reviewing step numbering
        Then step 4 should reference backlog/queue.md
        """
        # After the Discussion step was inserted, backlog moved to step 4
        assert "backlog/queue.md" in skill_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
