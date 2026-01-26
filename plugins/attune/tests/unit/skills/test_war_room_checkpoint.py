"""Tests for war-room-checkpoint skill structure and content.

This module validates that the war-room-checkpoint skill properly defines
the inline reversibility assessment framework for embedded War Room escalation.

Following TDD/BDD principles to ensure skill quality standards are met.
"""

from pathlib import Path

import pytest
import yaml


class TestWarRoomCheckpointSkillStructure:
    """Feature: War-room-checkpoint skill has valid structure.

    As a command integrator
    I want a well-structured checkpoint skill
    So that commands can reliably invoke War Room assessment
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room-checkpoint skill."""
        return Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.fixture
    def skill_frontmatter(self, skill_content: str) -> dict:
        """Parse the YAML frontmatter from the skill."""
        # Extract frontmatter between --- markers
        parts = skill_content.split("---", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1])
        return {}

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: War-room-checkpoint skill file exists.

        Given the attune plugin skills directory
        When looking for war-room-checkpoint
        Then SKILL.md should exist
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_valid_frontmatter(self, skill_frontmatter: dict) -> None:
        """Scenario: Skill has valid YAML frontmatter.

        Given the war-room-checkpoint skill
        When parsing frontmatter
        Then required fields should be present
        """
        required_fields = ["name", "description", "triggers", "use_when"]
        for field in required_fields:
            assert field in skill_frontmatter, f"Missing frontmatter field: {field}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_name_matches(self, skill_frontmatter: dict) -> None:
        """Scenario: Skill name is correct.

        Given the war-room-checkpoint skill
        When checking the name field
        Then it should be 'war-room-checkpoint'
        """
        assert skill_frontmatter["name"] == "war-room-checkpoint"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_is_lightweight(self, skill_frontmatter: dict) -> None:
        """Scenario: Skill is marked as lightweight complexity.

        Given the war-room-checkpoint skill
        When checking complexity
        Then it should be 'lightweight' (not advanced like full war-room)
        """
        assert skill_frontmatter.get("complexity") == "lightweight"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_depends_on_war_room(self, skill_frontmatter: dict) -> None:
        """Scenario: Skill declares dependency on war-room skill.

        Given the war-room-checkpoint skill
        When checking dependencies
        Then it should depend on attune:war-room
        """
        deps = skill_frontmatter.get("dependencies", [])
        assert "attune:war-room" in deps, "Should depend on attune:war-room"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_low_token_estimate(self, skill_frontmatter: dict) -> None:
        """Scenario: Skill has low token estimate for inline use.

        Given the war-room-checkpoint skill (designed for inline invocation)
        When checking estimated tokens
        Then it should be <= 500 (lightweight)
        """
        tokens = skill_frontmatter.get("estimated_tokens", 0)
        assert tokens <= 500, f"Token estimate {tokens} too high for inline use"


class TestWarRoomCheckpointReversibilityAssessment:
    """Feature: Skill defines reversibility assessment for checkpoints.

    As a command developer
    I want clear RS calculation guidance
    So that checkpoints correctly assess decision complexity
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room-checkpoint skill."""
        return Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_five_dimensions(self, skill_content: str) -> None:
        """Scenario: Skill defines the 5 RS dimensions.

        Given the war-room-checkpoint skill
        When reviewing RS calculation
        Then all 5 dimensions should be documented
        """
        dimensions = [
            "Reversal Cost",
            "Time Lock-In",
            "Blast Radius",
            "Information Loss",
            "Reputation Impact",
        ]
        for dim in dimensions:
            assert dim in skill_content, f"Missing RS dimension: {dim}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_mode_selection(self, skill_content: str) -> None:
        """Scenario: Skill defines mode selection logic.

        Given the war-room-checkpoint skill
        When reviewing escalation logic
        Then it should define express, lightweight, and full_council modes
        """
        modes = ["express", "lightweight", "full_council"]
        for mode in modes:
            assert mode in skill_content.lower(), f"Missing mode: {mode}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_profile_thresholds(self, skill_content: str) -> None:
        """Scenario: Skill references threshold profiles.

        Given the war-room-checkpoint skill
        When reviewing configuration options
        Then it should reference profile names (default, startup, regulated)
        """
        profiles = ["default", "startup", "regulated"]
        for profile in profiles:
            assert profile in skill_content.lower(), f"Missing profile: {profile}"


class TestWarRoomCheckpointTriggerConditions:
    """Feature: Skill documents trigger conditions for target commands.

    As a command developer
    I want clear trigger conditions
    So that I know when to invoke the checkpoint
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room-checkpoint skill."""
        return Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_do_issue_triggers(self, skill_content: str) -> None:
        """Scenario: Skill documents /do-issue trigger conditions.

        Given the war-room-checkpoint skill
        When reviewing command triggers
        Then /do-issue conditions should be documented
        """
        assert "do-issue" in skill_content.lower()
        # Should mention multiple issues or conflicts
        assert "3+" in skill_content or "3 issues" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_pr_review_triggers(self, skill_content: str) -> None:
        """Scenario: Skill documents /pr-review trigger conditions.

        Given the war-room-checkpoint skill
        When reviewing command triggers
        Then /pr-review conditions should be documented
        """
        assert "pr-review" in skill_content.lower()
        # Should mention blocking issues or architecture
        assert "blocking" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_architecture_review_triggers(
        self, skill_content: str
    ) -> None:
        """Scenario: Skill documents /architecture-review trigger conditions.

        Given the war-room-checkpoint skill
        When reviewing command triggers
        Then /architecture-review conditions should be documented
        """
        assert "architecture-review" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_fix_pr_triggers(self, skill_content: str) -> None:
        """Scenario: Skill documents /fix-pr trigger conditions.

        Given the war-room-checkpoint skill
        When reviewing command triggers
        Then /fix-pr conditions should be documented
        """
        assert "fix-pr" in skill_content.lower()


class TestWarRoomCheckpointConfidenceCalculation:
    """Feature: Skill defines confidence calculation for auto-continue.

    As a workflow designer
    I want clear confidence scoring rules
    So that auto-continue decisions are predictable
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room-checkpoint skill."""
        return Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_confidence_threshold(self, skill_content: str) -> None:
        """Scenario: Skill defines confidence threshold for auto-continue.

        Given the war-room-checkpoint skill
        When reviewing auto-continue logic
        Then a confidence threshold should be specified (0.8)
        """
        assert "0.8" in skill_content or "80%" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_confidence_factors(self, skill_content: str) -> None:
        """Scenario: Skill defines factors that affect confidence.

        Given the war-room-checkpoint skill
        When reviewing confidence calculation
        Then factors like dissent and voting margin should be documented
        """
        # Should mention factors that reduce confidence
        assert "dissent" in skill_content.lower()
        assert "voting" in skill_content.lower() or "margin" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_user_confirmation_logic(self, skill_content: str) -> None:
        """Scenario: Skill defines when user confirmation is required.

        Given the war-room-checkpoint skill
        When reviewing control flow
        Then user confirmation conditions should be specified
        """
        assert "requires_user_confirmation" in skill_content


class TestWarRoomCheckpointResponseFormat:
    """Feature: Skill defines checkpoint response format.

    As a command integrator
    I want a clear response format
    So that commands can process War Room results consistently
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room-checkpoint skill."""
        return Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_response_fields(self, skill_content: str) -> None:
        """Scenario: Skill defines expected response fields.

        Given the war-room-checkpoint skill
        When reviewing response format
        Then key fields should be documented
        """
        expected_fields = [
            "should_escalate",
            "selected_mode",
            "reversibility_score",
            "confidence",
        ]
        for field in expected_fields:
            assert field in skill_content, f"Missing response field: {field}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_includes_examples(self, skill_content: str) -> None:
        """Scenario: Skill includes worked examples.

        Given the war-room-checkpoint skill
        When reviewing documentation quality
        Then concrete examples should be provided
        """
        # Should have at least one yaml/code block example
        assert "```yaml" in skill_content or "```python" in skill_content
        # Should have example section
        assert "example" in skill_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_express_vs_escalate_paths(
        self, skill_content: str
    ) -> None:
        """Scenario: Skill documents both express and escalate response paths.

        Given the war-room-checkpoint skill
        When reviewing response generation
        Then both paths should be documented
        """
        # Express mode path
        assert "express mode" in skill_content.lower()
        # Escalate mode path
        assert "escalate" in skill_content.lower()


class TestWarRoomCheckpointIntegration:
    """Feature: Skill documents integration with related skills and commands.

    As a plugin developer
    I want clear integration guidance
    So that the checkpoint works seamlessly with the ecosystem
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the war-room-checkpoint skill."""
        return Path(__file__).parents[3] / "skills" / "war-room-checkpoint" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_references_parent_war_room(self, skill_content: str) -> None:
        """Scenario: Skill references parent war-room skill.

        Given the war-room-checkpoint skill
        When reviewing related skills
        Then it should reference attune:war-room
        """
        assert "attune:war-room" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_lists_target_commands(self, skill_content: str) -> None:
        """Scenario: Skill lists all target commands.

        Given the war-room-checkpoint skill
        When reviewing integration points
        Then all target commands should be listed
        """
        target_commands = ["/do-issue", "/pr-review", "/architecture-review", "/fix-pr"]
        for cmd in target_commands:
            assert cmd in skill_content, f"Missing target command: {cmd}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_invocation_pattern(self, skill_content: str) -> None:
        """Scenario: Skill documents how commands should invoke it.

        Given the war-room-checkpoint skill
        When reviewing invocation guidance
        Then a clear invocation pattern should be provided
        """
        # Should show Skill() invocation pattern
        assert "Skill(" in skill_content
        assert "source_command" in skill_content
        assert "decision_needed" in skill_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
