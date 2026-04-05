"""Tests for cartograph plugin structure and registration.

Feature: Cartograph plugin integrity

As an ecosystem maintainer
I want to verify the cartograph plugin is correctly structured
So that it integrates with Claude Code and night-market tooling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_PLUGIN_ROOT = Path(__file__).parents[2]
_PLUGIN_JSON = _PLUGIN_ROOT / ".claude-plugin" / "plugin.json"


@pytest.fixture
def plugin_manifest() -> dict:
    """Load and return the plugin.json manifest."""
    return json.loads(_PLUGIN_JSON.read_text())


class TestPluginManifest:
    """Feature: Plugin manifest validity

    As a plugin consumer
    I want a valid plugin.json
    So that Claude Code can load the plugin correctly.
    """

    @pytest.mark.unit
    def test_plugin_json_exists(self) -> None:
        """Scenario: Plugin manifest file exists
        Given the cartograph plugin directory
        When checking for plugin.json
        Then it exists at .claude-plugin/plugin.json.
        """
        assert _PLUGIN_JSON.exists()

    @pytest.mark.unit
    def test_plugin_json_is_valid_json(self) -> None:
        """Scenario: Plugin manifest is parseable
        Given the plugin.json file
        When parsing as JSON
        Then it succeeds without errors.
        """
        data = json.loads(_PLUGIN_JSON.read_text())
        assert isinstance(data, dict)

    @pytest.mark.unit
    def test_required_fields_present(self, plugin_manifest: dict) -> None:
        """Scenario: Manifest has required fields
        Given the plugin manifest
        When checking for required fields
        Then name, version, and description are present.
        """
        assert plugin_manifest["name"] == "cartograph"
        assert "version" in plugin_manifest
        assert "description" in plugin_manifest

    @pytest.mark.unit
    def test_has_commands(self, plugin_manifest: dict) -> None:
        """Scenario: Plugin registers commands
        Given the plugin manifest
        When checking commands
        Then at least one command is registered.
        """
        commands = plugin_manifest.get("commands", [])
        assert len(commands) >= 1

    @pytest.mark.unit
    def test_has_skills(self, plugin_manifest: dict) -> None:
        """Scenario: Plugin registers skills
        Given the plugin manifest
        When checking skills
        Then at least 3 skills are registered (architecture,
        data-flow, dependency-graph).
        """
        skills = plugin_manifest.get("skills", [])
        assert len(skills) >= 5

    @pytest.mark.unit
    def test_has_agents(self, plugin_manifest: dict) -> None:
        """Scenario: Plugin registers agents
        Given the plugin manifest
        When checking agents
        Then at least one agent is registered.
        """
        agents = plugin_manifest.get("agents", [])
        assert len(agents) >= 1


class TestRegisteredFilesExist:
    """Feature: All registered paths resolve to real files

    As a plugin loader
    I want all registered commands, skills, and agents to exist
    So that invocations don't fail with missing file errors.
    """

    @pytest.mark.unit
    def test_command_files_exist(self, plugin_manifest: dict) -> None:
        """Scenario: Registered commands exist on disk
        Given the commands listed in plugin.json
        When checking each path
        Then every command file exists.
        """
        for cmd_path in plugin_manifest.get("commands", []):
            # Paths in plugin.json are relative to plugin root
            resolved = _PLUGIN_ROOT / cmd_path.lstrip("./")
            assert resolved.exists(), f"Missing command: {cmd_path}"

    @pytest.mark.unit
    def test_skill_directories_exist(self, plugin_manifest: dict) -> None:
        """Scenario: Registered skills exist on disk
        Given the skills listed in plugin.json
        When checking each path
        Then every skill directory contains a SKILL.md.
        """
        for skill_path in plugin_manifest.get("skills", []):
            resolved = _PLUGIN_ROOT / skill_path.lstrip("./")
            skill_file = resolved / "SKILL.md"
            assert skill_file.exists(), f"Missing skill: {skill_path}/SKILL.md"

    @pytest.mark.unit
    def test_agent_files_exist(self, plugin_manifest: dict) -> None:
        """Scenario: Registered agents exist on disk
        Given the agents listed in plugin.json
        When checking each path
        Then every agent file exists.
        """
        for agent_path in plugin_manifest.get("agents", []):
            resolved = _PLUGIN_ROOT / agent_path.lstrip("./")
            assert resolved.exists(), f"Missing agent: {agent_path}"


class TestSkillFrontmatter:
    """Feature: Skill files have valid frontmatter

    As a skill loader
    I want valid YAML frontmatter in each SKILL.md
    So that skills are discoverable and described.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "skill_name",
        [
            "architecture-diagram",
            "data-flow",
            "dependency-graph",
            "workflow-diagram",
            "class-diagram",
        ],
    )
    def test_skill_has_description_frontmatter(self, skill_name: str) -> None:
        """Scenario: Skill has description in frontmatter
        Given a skill SKILL.md file
        When reading its frontmatter
        Then a description field is present.
        """
        skill_file = _PLUGIN_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_file.read_text()
        assert content.startswith("---"), f"{skill_name}/SKILL.md missing frontmatter"
        assert "description:" in content.split("---")[1]
