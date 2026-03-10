"""Tests for knowledge-intake skill structure and Discussion promotion.

Validates that the knowledge-intake SKILL.md documents all 9 steps
including Step 7 (PROMOTE to Discussions) added in the discussions-fix
branch.
"""

from pathlib import Path

import pytest


class TestKnowledgeIntakeWorkflowSteps:
    """Feature: Knowledge-intake skill documents all workflow steps.

    As a knowledge curator
    I want all intake steps documented in SKILL.md
    So that I can follow the complete intake pipeline
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the knowledge-intake skill."""
        return Path(__file__).parents[2] / "skills" / "knowledge-intake" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Knowledge-intake skill file exists.

        Given the memory-palace plugin skills directory
        When looking for knowledge-intake
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_nine_steps(self, skill_content: str) -> None:
        """Scenario: Skill documents all 9 intake steps.

        Given the knowledge-intake skill
        When reviewing the workflow steps
        Then steps 1 through 9 should be present in order
        """
        expected_steps = [
            "FETCH",
            "EVALUATE",
            "DECIDE",
            "STORE",
            "VALIDATE",
            "CONNECT",
            "PROMOTE",
            "APPLY",
            "PRUNE",
        ]
        for step in expected_steps:
            assert step in skill_content, (
                f"Missing step '{step}' in knowledge-intake SKILL.md"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_step_7_is_promote(self, skill_content: str) -> None:
        """Scenario: Step 7 is PROMOTE.

        Given the knowledge-intake skill
        When checking step ordering
        Then step 7 should be PROMOTE
        """
        assert "7. PROMOTE" in skill_content


class TestKnowledgeIntakeDiscussionPromotion:
    """Feature: Knowledge-intake promotes high-score entries to Discussions.

    As a knowledge curator
    I want evergreen entries promoted to GitHub Discussions
    So that high-value knowledge is discoverable by the team
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load the skill content."""
        path = Path(__file__).parents[2] / "skills" / "knowledge-intake" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_promotion_heading_exists(self, skill_content: str) -> None:
        """Scenario: Step 7 heading exists.

        Given the knowledge-intake skill
        When looking for the promotion section
        Then the Discussion Promotion heading should exist
        """
        assert "### Step 7: Discussion Promotion" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_promotion_requires_score_80_plus(self, skill_content: str) -> None:
        """Scenario: Promotion only triggers for score 80+.

        Given the Discussion Promotion section
        When reviewing the trigger condition
        Then it should require a score of 80 or above
        """
        section_start = skill_content.find("### Step 7: Discussion Promotion")
        section = skill_content[section_start : section_start + 600]
        assert "80" in section
        assert "evergreen" in section.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_promotion_targets_knowledge_category(self, skill_content: str) -> None:
        """Scenario: Promotion targets the Knowledge Discussion category.

        Given the Discussion Promotion section
        When reviewing the target category
        Then it should use the 'Knowledge' category
        """
        section_start = skill_content.find("### Step 7: Discussion Promotion")
        section = skill_content[section_start : section_start + 600]
        assert "Knowledge" in section

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_promotion_defaults_to_publish(self, skill_content: str) -> None:
        """Scenario: Promotion step defaults to publishing.

        Given the Discussion Promotion section
        When reviewing the step behavior
        Then publishing should be the default and never block intake
        """
        section_start = skill_content.find("### Step 7: Discussion Promotion")
        section = skill_content[section_start : section_start + 600]
        assert "default" in section.lower()
        assert "never block" in section.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_promotion_handles_existing_discussion(self, skill_content: str) -> None:
        """Scenario: Existing discussions get update offer instead.

        Given an entry with an existing discussion_url
        When the promotion step runs
        Then it should update the existing Discussion instead
        """
        section_start = skill_content.find("### Step 7: Discussion Promotion")
        section = skill_content[section_start : section_start + 600]
        assert "discussion_url" in section
        assert "update" in section.lower() and "discussion" in section

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_promotion_references_module(self, skill_content: str) -> None:
        """Scenario: Skill references the discussion-promotion module.

        Given the knowledge-intake skill
        When looking for module references
        Then discussion-promotion.md should be referenced
        """
        assert "discussion-promotion.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_below_80_skips_promotion(self, skill_content: str) -> None:
        """Scenario: Scores below 80 skip promotion entirely.

        Given the Discussion Promotion section
        When the score is below 80
        Then the step should be skipped
        """
        section_start = skill_content.find("### Step 7: Discussion Promotion")
        section = skill_content[section_start : section_start + 600]
        assert "below 80" in section.lower() or "skip" in section.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
