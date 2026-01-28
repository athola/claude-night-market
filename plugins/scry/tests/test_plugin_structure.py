"""Tests for scry plugin structure and validation."""

import json
from pathlib import Path

import pytest


class TestPluginJson:
    """Tests for plugin.json structure."""

    def test_plugin_json_exists(self, plugin_root: Path) -> None:
        """Plugin.json should exist."""
        plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
        assert plugin_json.exists(), "plugin.json not found"

    def test_plugin_json_valid(self, plugin_root: Path) -> None:
        """Plugin.json should be valid JSON."""
        plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
        with open(plugin_json) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_plugin_json_required_fields(self, plugin_root: Path) -> None:
        """Plugin.json should have required fields."""
        plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
        with open(plugin_json) as f:
            data = json.load(f)

        assert "name" in data, "Missing 'name' field"
        assert data["name"] == "scry"
        assert "version" in data, "Missing 'version' field"
        assert "description" in data, "Missing 'description' field"

    def test_plugin_json_metadata(self, plugin_root: Path) -> None:
        """Plugin.json should have recommended metadata."""
        plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
        with open(plugin_json) as f:
            data = json.load(f)

        assert "author" in data, "Missing 'author' field"
        assert "license" in data, "Missing 'license' field"
        assert "keywords" in data, "Missing 'keywords' field"


class TestSkillStructure:
    """Tests for skill directory structure."""

    EXPECTED_SKILLS = [
        "vhs-recording",
        "browser-recording",
        "gif-generation",
        "media-composition",
    ]

    def test_skills_directory_exists(self, skills_dir: Path) -> None:
        """Skills directory should exist."""
        assert skills_dir.exists(), "skills/ directory not found"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_directory_exists(self, skills_dir: Path, skill_name: str) -> None:
        """Each expected skill directory should exist."""
        skill_dir = skills_dir / skill_name
        assert skill_dir.exists(), f"Skill directory '{skill_name}' not found"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_has_skill_md(self, skills_dir: Path, skill_name: str) -> None:
        """Each skill should have a SKILL.md file."""
        skill_md = skills_dir / skill_name / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found for '{skill_name}'"

    @pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
    def test_skill_md_has_frontmatter(self, skills_dir: Path, skill_name: str) -> None:
        """Each SKILL.md should have YAML frontmatter."""
        skill_md = skills_dir / skill_name / "SKILL.md"
        content = skill_md.read_text()
        assert content.startswith("---"), (
            f"SKILL.md for '{skill_name}' missing frontmatter"
        )
        # Find closing frontmatter
        lines = content.split("\n")
        assert lines[0] == "---"
        closing_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line == "---":
                closing_idx = i
                break
        assert closing_idx is not None, f"Unclosed frontmatter in '{skill_name}'"


class TestCommandStructure:
    """Tests for command structure."""

    EXPECTED_COMMANDS = ["record-terminal.md", "record-browser.md"]

    def test_commands_directory_exists(self, commands_dir: Path) -> None:
        """Commands directory should exist."""
        assert commands_dir.exists(), "commands/ directory not found"

    @pytest.mark.parametrize("command_file", EXPECTED_COMMANDS)
    def test_command_exists(self, commands_dir: Path, command_file: str) -> None:
        """Each expected command file should exist."""
        cmd_path = commands_dir / command_file
        assert cmd_path.exists(), f"Command '{command_file}' not found"


class TestScriptsStructure:
    """Tests for scripts structure."""

    def test_scripts_directory_exists(self, scripts_dir: Path) -> None:
        """Scripts directory should exist."""
        assert scripts_dir.exists(), "scripts/ directory not found"

    def test_gif_demo_script_exists(self, scripts_dir: Path) -> None:
        """gif_demo.sh should exist."""
        gif_demo = scripts_dir / "gif_demo.sh"
        assert gif_demo.exists(), "gif_demo.sh not found"

    def test_gif_demo_script_executable(self, scripts_dir: Path) -> None:
        """gif_demo.sh should be executable."""
        import os

        gif_demo = scripts_dir / "gif_demo.sh"
        assert os.access(gif_demo, os.X_OK), "gif_demo.sh is not executable"

    def test_gif_demo_script_has_shebang(self, scripts_dir: Path) -> None:
        """gif_demo.sh should have proper shebang."""
        gif_demo = scripts_dir / "gif_demo.sh"
        content = gif_demo.read_text()
        assert content.startswith("#!/"), "gif_demo.sh missing shebang"
