"""
Feature: Voice Craft Plugin Registration

As a plugin system
I want all voice-craft components properly registered
So that skills, agents, and commands are discoverable
"""

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parents[3]


class TestPluginRegistration:
    """
    Feature: Voice craft components registered in plugin.json

    As a plugin developer
    I want all voice-craft components in plugin.json
    So that the plugin system can discover and load them
    """

    @pytest.fixture
    def plugin_json(self):
        path = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        return json.loads(path.read_text())

    @pytest.mark.unit
    def test_voice_skills_registered(self, plugin_json):
        """
        Scenario: All voice skills are listed in plugin.json
        Given the scribe plugin.json
        When I check the skills array
        Then all four voice skills are present
        """
        skills = plugin_json["skills"]
        expected = [
            "./skills/voice-extract",
            "./skills/voice-generate",
            "./skills/voice-review",
            "./skills/voice-learn",
        ]
        for skill in expected:
            assert skill in skills, f"{skill} not in plugin.json skills"

    @pytest.mark.unit
    def test_voice_agents_registered(self, plugin_json):
        """
        Scenario: Both review agents are listed in plugin.json
        Given the scribe plugin.json
        When I check the agents array
        Then prose-reviewer and craft-reviewer are present
        """
        agents = plugin_json["agents"]
        assert "./agents/prose-reviewer.md" in agents
        assert "./agents/craft-reviewer.md" in agents

    @pytest.mark.unit
    def test_voice_commands_registered(self, plugin_json):
        """
        Scenario: All voice commands are listed in plugin.json
        Given the scribe plugin.json
        When I check the commands array
        Then all four voice commands are present
        """
        commands = plugin_json["commands"]
        expected = [
            "./commands/voice-extract.md",
            "./commands/voice-generate.md",
            "./commands/voice-review.md",
            "./commands/voice-learn.md",
        ]
        for cmd in expected:
            assert cmd in commands, f"{cmd} not in plugin.json commands"

    @pytest.mark.unit
    def test_all_registered_files_exist(self, plugin_json):
        """
        Scenario: Every file referenced in plugin.json exists on disk
        Given plugin.json references skills, agents, and commands
        When I check each referenced path (relative to plugin root)
        Then every path resolves to an existing file or directory
        """
        for skill_path in plugin_json["skills"]:
            clean = skill_path.lstrip("./")
            full_path = PLUGIN_ROOT / clean
            assert full_path.exists(), f"Skill path missing: {skill_path}"

        for agent_path in plugin_json["agents"]:
            clean = agent_path.lstrip("./")
            full_path = PLUGIN_ROOT / clean
            assert full_path.exists(), f"Agent path missing: {agent_path}"

        for cmd_path in plugin_json["commands"]:
            clean = cmd_path.lstrip("./")
            full_path = PLUGIN_ROOT / clean
            assert full_path.exists(), f"Command path missing: {cmd_path}"

    @pytest.mark.unit
    def test_voice_keywords_present(self, plugin_json):
        """
        Scenario: Voice-related keywords are in plugin metadata
        Given the scribe plugin description includes voice features
        When I check the keywords array
        Then voice-related keywords are present for discovery
        """
        keywords = plugin_json["keywords"]
        assert "voice" in keywords
        assert "sico" in keywords


class TestOpenpackageAlignment:
    """
    Feature: openpackage.yml aligns with plugin.json

    As a plugin developer
    I want openpackage.yml and plugin.json in sync
    So that the marketplace and local installs agree
    """

    @pytest.mark.unit
    def test_openpackage_lists_voice_skills(self):
        """
        Scenario: openpackage.yml lists all voice skills
        Given the scribe openpackage.yml
        When I check its skills section
        Then all four voice skills are listed
        """
        content = (PLUGIN_ROOT / "openpackage.yml").read_text()
        assert "skills/voice-extract" in content
        assert "skills/voice-generate" in content
        assert "skills/voice-review" in content
        assert "skills/voice-learn" in content

    @pytest.mark.unit
    def test_openpackage_lists_voice_commands(self):
        """
        Scenario: openpackage.yml lists all voice commands
        Given the scribe openpackage.yml
        When I check its commands section
        Then all four voice commands are listed
        """
        content = (PLUGIN_ROOT / "openpackage.yml").read_text()
        assert "commands/voice-extract.md" in content
        assert "commands/voice-generate.md" in content
        assert "commands/voice-review.md" in content
        assert "commands/voice-learn.md" in content

    @pytest.mark.unit
    def test_openpackage_lists_voice_agents(self):
        """
        Scenario: openpackage.yml lists review agents
        Given the scribe openpackage.yml
        When I check its agents section
        Then prose-reviewer and craft-reviewer are listed
        """
        content = (PLUGIN_ROOT / "openpackage.yml").read_text()
        assert "agents/prose-reviewer.md" in content
        assert "agents/craft-reviewer.md" in content
