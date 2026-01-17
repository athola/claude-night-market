"""Tests for session-management skill.

This module tests the session-management skill content and structure:
- Frontmatter schema validation
- Workflow pattern documentation
- Best practices content
- Integration guidance

Issue #57: Document named session support in Sanctum workflows

Following TDD/BDD principles with Given/When/Then docstrings.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

# ============================================================================
# Skill Structure Tests
# ============================================================================


class TestSessionManagementSkillStructure:
    """Feature: Validate session-management skill structure.

    As a plugin developer
    I want the skill to follow standard structure
    So that it integrates correctly with the plugin system
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Return the skill SKILL.md path."""
        return (
            Path(__file__).parent.parent / "skills" / "session-management" / "SKILL.md"
        )

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Return the skill content."""
        return skill_path.read_text()

    def extract_frontmatter(self, content: str) -> dict[str, Any] | None:
        """Extract YAML frontmatter from content."""
        if not content.startswith("---"):
            return None

        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line == "---":
                end_idx = i
                break

        if end_idx is None:
            return None

        yaml_content = "\n".join(lines[1:end_idx])
        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Skill file exists.

        Given the session-management skill directory
        When checking for SKILL.md
        Then it should exist.
        """
        assert skill_path.exists(), "SKILL.md not found"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_content: str) -> None:
        """Scenario: Skill has YAML frontmatter.

        Given the skill content
        When checking for frontmatter
        Then it should start with ---.
        """
        assert skill_content.startswith("---"), "Missing frontmatter"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Frontmatter has required fields.

        Given skill frontmatter
        When checking required fields
        Then name and description should be present.
        """
        frontmatter = self.extract_frontmatter(skill_content)
        assert frontmatter is not None, "Invalid frontmatter"
        assert "name" in frontmatter, "Missing name field"
        assert "description" in frontmatter, "Missing description field"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_name_matches_directory(self, skill_content: str) -> None:
        """Scenario: Skill name matches directory.

        Given skill frontmatter
        When checking name field
        Then it should be 'session-management'.
        """
        frontmatter = self.extract_frontmatter(skill_content)
        assert frontmatter is not None
        assert frontmatter["name"] == "session-management"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_category(self, skill_content: str) -> None:
        """Scenario: Skill has category field.

        Given skill frontmatter
        When checking for category
        Then it should have a category defined.
        """
        frontmatter = self.extract_frontmatter(skill_content)
        assert frontmatter is not None
        assert "category" in frontmatter

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_tags(self, skill_content: str) -> None:
        """Scenario: Skill has tags field.

        Given skill frontmatter
        When checking for tags
        Then it should have tags defined.
        """
        frontmatter = self.extract_frontmatter(skill_content)
        assert frontmatter is not None
        assert "tags" in frontmatter
        assert isinstance(frontmatter["tags"], list)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_tools(self, skill_content: str) -> None:
        """Scenario: Skill has tools field.

        Given skill frontmatter
        When checking for tools
        Then it should have tools defined.
        """
        frontmatter = self.extract_frontmatter(skill_content)
        assert frontmatter is not None
        assert "tools" in frontmatter
        assert isinstance(frontmatter["tools"], list)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_complexity(self, skill_content: str) -> None:
        """Scenario: Skill has complexity field.

        Given skill frontmatter
        When checking for complexity
        Then it should have complexity defined.
        """
        frontmatter = self.extract_frontmatter(skill_content)
        assert frontmatter is not None
        assert "complexity" in frontmatter
        assert frontmatter["complexity"] in ["low", "medium", "high"]


# ============================================================================
# Content Validation Tests
# ============================================================================


class TestSessionManagementContent:
    """Feature: Validate session-management skill content.

    As a user
    I want comprehensive documentation
    So that I can use session management effectively
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill content."""
        skill_path = (
            Path(__file__).parent.parent / "skills" / "session-management" / "SKILL.md"
        )
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_overview_section(self, skill_content: str) -> None:
        """Scenario: Skill has overview section.

        Given the skill content
        When checking for Overview section
        Then it should be present.
        """
        assert "## Overview" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_available_commands_section(self, skill_content: str) -> None:
        """Scenario: Skill documents available commands.

        Given the skill content
        When checking for commands documentation
        Then Available Commands section should be present.
        """
        assert "## Available Commands" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_rename_command(self, skill_content: str) -> None:
        """Scenario: Skill documents /rename command.

        Given the skill content
        When checking for /rename documentation
        Then /rename should be mentioned.
        """
        assert "/rename" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_resume_command(self, skill_content: str) -> None:
        """Scenario: Skill documents /resume command.

        Given the skill content
        When checking for /resume documentation
        Then /resume should be mentioned.
        """
        assert "/resume" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_cli_resume_flag(self, skill_content: str) -> None:
        """Scenario: Skill documents --resume CLI flag.

        Given the skill content
        When checking for CLI resume documentation
        Then claude --resume should be mentioned.
        """
        assert "claude --resume" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_workflow_patterns_section(self, skill_content: str) -> None:
        """Scenario: Skill has workflow patterns.

        Given the skill content
        When checking for workflow documentation
        Then Workflow Patterns section should be present.
        """
        assert "## Workflow Patterns" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_best_practices_section(self, skill_content: str) -> None:
        """Scenario: Skill has best practices.

        Given the skill content
        When checking for best practices
        Then Best Practices section should be present.
        """
        assert "## Best Practices" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_troubleshooting_section(self, skill_content: str) -> None:
        """Scenario: Skill has troubleshooting guidance.

        Given the skill content
        When checking for troubleshooting
        Then Troubleshooting section should be present.
        """
        assert "## Troubleshooting" in skill_content


# ============================================================================
# Workflow Pattern Tests
# ============================================================================


class TestWorkflowPatterns:
    """Feature: Validate workflow pattern documentation.

    As a user
    I want clear workflow patterns
    So that I can apply session management in my work
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill content."""
        skill_path = (
            Path(__file__).parent.parent / "skills" / "session-management" / "SKILL.md"
        )
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_debugging_pattern(self, skill_content: str) -> None:
        """Scenario: Skill documents debugging session pattern.

        Given the skill content
        When checking for debugging workflow
        Then debugging pattern should be documented.
        """
        content_lower = skill_content.lower()
        assert "debugging" in content_lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_feature_development_pattern(self, skill_content: str) -> None:
        """Scenario: Skill documents feature development pattern.

        Given the skill content
        When checking for feature development workflow
        Then feature pattern should be documented.
        """
        content_lower = skill_content.lower()
        assert "feature" in content_lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_pr_review_pattern(self, skill_content: str) -> None:
        """Scenario: Skill documents PR review pattern.

        Given the skill content
        When checking for PR review workflow
        Then PR review pattern should be documented.
        """
        content_lower = skill_content.lower()
        assert "pr review" in content_lower or "pr-review" in content_lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_investigation_pattern(self, skill_content: str) -> None:
        """Scenario: Skill documents investigation pattern.

        Given the skill content
        When checking for investigation workflow
        Then investigation pattern should be documented.
        """
        content_lower = skill_content.lower()
        assert "investigation" in content_lower or "investigate" in content_lower


# ============================================================================
# Naming Convention Tests
# ============================================================================


class TestNamingConventions:
    """Feature: Validate naming convention documentation.

    As a user
    I want clear naming conventions
    So that my sessions are consistently named
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill content."""
        skill_path = (
            Path(__file__).parent.parent / "skills" / "session-management" / "SKILL.md"
        )
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_naming_conventions_section(self, skill_content: str) -> None:
        """Scenario: Skill documents naming conventions.

        Given the skill content
        When checking for naming guidance
        Then Naming Conventions should be present.
        """
        assert (
            "Naming Conventions" in skill_content or "naming" in skill_content.lower()
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_example_names(self, skill_content: str) -> None:
        """Scenario: Skill provides example session names.

        Given the skill content
        When checking for examples
        Then example session names should be provided.
        """
        # Check for hyphenated example names
        hyphenated_pattern = r"debugging-\w+"
        assert re.search(hyphenated_pattern, skill_content) is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_when_to_name_guidance(self, skill_content: str) -> None:
        """Scenario: Skill explains when to name sessions.

        Given the skill content
        When checking for guidance
        Then 'when to name' guidance should be present.
        """
        content_lower = skill_content.lower()
        assert "when to" in content_lower or "should" in content_lower


# ============================================================================
# Integration Tests
# ============================================================================


class TestSanctumIntegration:
    """Feature: Validate sanctum integration documentation.

    As a user
    I want session management to integrate with sanctum
    So that I can use it with other skills
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Return the skill content."""
        skill_path = (
            Path(__file__).parent.parent / "skills" / "session-management" / "SKILL.md"
        )
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_git_workspace_review(self, skill_content: str) -> None:
        """Scenario: Skill references git-workspace-review.

        Given the skill content
        When checking for integration guidance
        Then git-workspace-review should be referenced.
        """
        assert "git-workspace-review" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_catchup(self, skill_content: str) -> None:
        """Scenario: Skill references /catchup command.

        Given the skill content
        When checking for recovery guidance
        Then /catchup should be referenced.
        """
        assert "/catchup" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_see_also_section(self, skill_content: str) -> None:
        """Scenario: Skill has See Also section.

        Given the skill content
        When checking for cross-references
        Then See Also section should be present.
        """
        assert "## See Also" in skill_content
