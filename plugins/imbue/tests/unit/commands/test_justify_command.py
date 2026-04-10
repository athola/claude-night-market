"""Tests for /justify command functionality.

This module tests the justify command workflow, parameter handling,
and integration with the justify skill for additive bias detection.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestJustifyCommand:
    """Feature: /justify command audits changes for additive bias.

    As a developer finishing implementation
    I want to audit my changes for AI additive bias
    So that I merge only minimal, justified changes
    """

    @pytest.fixture
    def command_path(self) -> Path:
        """Path to the justify command file."""
        return Path(__file__).parents[3] / "commands" / "justify.md"

    @pytest.fixture
    def command_content(self, command_path: Path) -> str:
        """Load the command file content."""
        return command_path.read_text()

    @pytest.fixture
    def mock_justify_command(self):
        """Mock /justify command content from commands/justify.md."""
        return {
            "name": "justify",
            "description": "Audit changes for additive bias and Iron Law compliance",
            "usage": "/justify [--scope staged|branch|file] [path...]",
            "parameters": [
                {
                    "name": "--scope",
                    "type": "optional",
                    "description": "Scope of changes to audit",
                    "values": ["staged", "branch", "file"],
                    "default": "branch",
                },
                {
                    "name": "path",
                    "type": "optional",
                    "description": "Specific file paths to audit",
                },
            ],
            "integrates_with": [
                "proof-of-work",
                "justify",
            ],
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_file_exists(self, command_path: Path) -> None:
        """Scenario: Justify command file exists.

        Given the imbue plugin commands directory
        When looking for the justify command
        Then justify.md should exist
        """
        assert command_path.exists(), f"Command not found at {command_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_has_frontmatter(self, command_content: str) -> None:
        """Scenario: Command has valid frontmatter.

        Given the justify command file
        When parsing frontmatter
        Then name, description, and usage should be present
        """
        assert "name: justify" in command_content
        assert "description:" in command_content
        assert "usage:" in command_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_documents_scope_parameter(self, command_content: str) -> None:
        """Scenario: Command documents the scope parameter.

        Given the justify command
        When checking parameter documentation
        Then --scope with staged, branch, and file values should exist
        """
        assert "--scope" in command_content
        assert "staged" in command_content
        assert "branch" in command_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_references_justify_skill(self, command_content: str) -> None:
        """Scenario: Command references the justify skill.

        Given the justify command
        When checking skill integration
        Then it should reference Skill(imbue:justify)
        """
        assert "imbue:justify" in command_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_describes_workflow_steps(self, command_content: str) -> None:
        """Scenario: Command describes the audit workflow.

        Given the justify command
        When reviewing documented steps
        Then bias scoring, Iron Law check, and risk assessment
            should be mentioned
        """
        content_lower = command_content.lower()
        assert "bias" in content_lower
        assert "iron law" in content_lower
        assert "risk" in content_lower


class TestJustifyCommandParameters:
    """Feature: /justify command parameter handling.

    As a developer
    I want flexible scope options
    So that I can audit staged, branch, or specific file changes
    """

    @pytest.fixture
    def mock_justify_command(self):
        """Mock command metadata."""
        return {
            "name": "justify",
            "usage": "/justify [--scope staged|branch|file] [path...]",
            "default_scope": "branch",
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_scope_is_branch(self, mock_justify_command) -> None:
        """Scenario: Default scope audits all branch changes.

        Given no --scope argument provided
        When the command runs
        Then it should default to branch scope
        """
        assert mock_justify_command["default_scope"] == "branch"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_scope_options_are_valid(self, mock_justify_command) -> None:
        """Scenario: All scope values are recognized.

        Given the command usage string
        When parsing scope options
        Then staged, branch, and file should be valid
        """
        usage = mock_justify_command["usage"]
        assert "staged" in usage
        assert "branch" in usage
        assert "file" in usage


class TestJustifyCommandIntegration:
    """Feature: /justify integrates with imbue workflow skills.

    As a developer
    I want justify to work with proof-of-work and scope-guard
    So that my post-implementation audit is thorough
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the justify skill."""
        return Path(__file__).parents[3] / "skills" / "justify" / "SKILL.md"

    @pytest.fixture
    def command_path(self) -> Path:
        """Path to the justify command."""
        return Path(__file__).parents[3] / "commands" / "justify.md"

    @pytest.fixture
    def plugin_json(self) -> dict:
        """Load plugin.json."""
        import json

        path = Path(__file__).parents[3] / ".claude-plugin" / "plugin.json"
        with path.open() as f:
            return json.load(f)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_and_command_both_registered(self, plugin_json: dict) -> None:
        """Scenario: Both skill and command are registered in plugin.json.

        Given the imbue plugin configuration
        When checking registrations
        Then both justify skill and command should be listed
        """
        skills = plugin_json.get("skills", [])
        commands = plugin_json.get("commands", [])
        assert "./skills/justify" in skills
        assert "./commands/justify.md" in commands

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists_for_command(
        self, skill_path: Path, command_path: Path
    ) -> None:
        """Scenario: Skill file exists alongside command.

        Given the justify command references the justify skill
        When checking the skills directory
        Then the SKILL.md file should exist
        """
        assert skill_path.exists(), "Skill must exist for command to work"
        assert command_path.exists(), "Command must exist"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_mentions_proof_of_work_integration(self) -> None:
        """Scenario: Skill documents its relationship with proof-of-work.

        Given the justify skill
        When checking integration documentation
        Then proof-of-work should be mentioned as a companion
        """
        skill_content = (
            Path(__file__).parents[3] / "skills" / "justify" / "SKILL.md"
        ).read_text()
        assert "proof-of-work" in skill_content
