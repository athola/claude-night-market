"""Tests for session-replay skill structure and content.

Validates that the skill file, command file, and plugin registration
all exist and contain the required fields. Follows the BDD-style
pattern used across skill tests in this project.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parents[3] / "skills" / "session-replay"
COMMANDS_ROOT = Path(__file__).parents[3] / "commands"
PLUGIN_JSON = Path(__file__).parents[3] / ".claude-plugin" / "plugin.json"


class TestSessionReplaySkillExists:
    """Feature: session-replay skill files are present on disk.

    As a developer using the scribe plugin
    I want the session-replay skill to be installed
    So that I can convert sessions into animated GIF replays
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        return SKILL_ROOT / "SKILL.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_exists(self, skill_path: Path) -> None:
        """Scenario: SKILL.md exists at the expected path.

        Given the scribe plugin
        When checking for the session-replay skill
        Then SKILL.md should exist under skills/session-replay/
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"


class TestSessionReplayFrontmatter:
    """Feature: SKILL.md has valid YAML frontmatter.

    As a plugin loader
    I want the skill to declare its metadata
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_frontmatter_delimiters(self, skill_content: str) -> None:
        """Scenario: File begins with YAML frontmatter.

        Given the session-replay SKILL.md
        When reading the file
        Then it should begin with '---' frontmatter delimiters
        """
        assert skill_content.startswith("---")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_name_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares the skill name.

        Given the session-replay SKILL.md
        When reading the frontmatter
        Then it should contain 'name: session-replay'
        """
        assert "name: session-replay" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_category_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares a category."""
        assert "category:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_tags_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares relevant tags."""
        assert "tags:" in skill_content
        assert "recording" in skill_content
        assert "demo" in skill_content
        assert "session-capture" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_complexity_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares complexity."""
        assert "complexity:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_estimated_tokens(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares token budget."""
        assert "estimated_tokens:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_dependencies(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares scry dependency."""
        assert "dependencies:" in skill_content
        assert "scry:vhs-recording" in skill_content


class TestSessionReplayIntegrationPoints:
    """Feature: Skill documents integration with scry.

    As a replay user
    I want session-replay to integrate with scry
    So that tapes are rendered into GIFs automatically
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_scry_vhs(self, skill_content: str) -> None:
        """Scenario: Skill references VHS recording.

        Given the session-replay skill
        When reading integration points
        Then it should reference scry:vhs-recording
        """
        assert "scry:vhs-recording" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_tech_tutorial(self, skill_content: str) -> None:
        """Scenario: Skill references tutorial integration.

        Given the session-replay skill
        When reading integration points
        Then it should reference scribe:tech-tutorial
        """
        assert "scribe:tech-tutorial" in skill_content


class TestSessionReplayContent:
    """Feature: Skill body covers the full workflow.

    As a user following the skill
    I want clear steps from parsing to rendering
    So that I produce a GIF every time
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_parse_step(self, skill_content: str) -> None:
        """Scenario: Workflow includes session parsing."""
        assert "Parse the Session" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_generate_step(self, skill_content: str) -> None:
        """Scenario: Workflow includes tape generation."""
        assert "Generate VHS Tape" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_render_step(self, skill_content: str) -> None:
        """Scenario: Workflow includes GIF rendering."""
        assert "Render GIF" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_error_handling(self, skill_content: str) -> None:
        """Scenario: Skill documents error handling."""
        assert "Error Handling" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_example(self, skill_content: str) -> None:
        """Scenario: Skill includes a usage example."""
        assert "## Example" in skill_content


class TestSessionReplayCommand:
    """Feature: A command file exists to invoke the skill.

    As a user
    I want a /session-replay slash command
    So that I can invoke the skill quickly
    """

    @pytest.fixture
    def command_path(self) -> Path:
        return COMMANDS_ROOT / "session-replay.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_file_exists(self, command_path: Path) -> None:
        """Scenario: Command file exists.

        Given the scribe plugin
        When checking for the session-replay command
        Then session-replay.md should exist under commands/
        """
        assert command_path.exists(), f"Command not found at {command_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_references_skill(self, command_path: Path) -> None:
        """Scenario: Command invokes the skill.

        Given the session-replay command
        When reading its content
        Then it should reference Skill(scribe:session-replay)
        """
        content = command_path.read_text()
        assert "scribe:session-replay" in content


class TestSessionReplayRegistration:
    """Feature: Skill and command registered in plugin.json.

    As a plugin loader
    I want session-replay in the plugin manifest
    So that the system discovers and loads it
    """

    @pytest.fixture
    def plugin_json_content(self) -> str:
        return PLUGIN_JSON.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_registered(self, plugin_json_content: str) -> None:
        """Scenario: Skill listed in plugin.json skills."""
        assert "skills/session-replay" in plugin_json_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_registered(self, plugin_json_content: str) -> None:
        """Scenario: Command listed in plugin.json commands."""
        assert "commands/session-replay.md" in plugin_json_content
