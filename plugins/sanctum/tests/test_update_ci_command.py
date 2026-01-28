# ruff: noqa: D101,D102,D103
"""BDD-style tests for update-ci command structure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


class TestUpdateCiCommand:
    """
    Feature: Update CI/CD configuration command

    As a plugin developer
    I want a slash command that reconciles CI configs with recent changes
    So that pre-commit hooks and workflows stay in sync with the codebase
    """

    @pytest.fixture()
    def command_path(self) -> Path:
        return PLUGIN_ROOT / "commands" / "update-ci.md"

    @pytest.fixture()
    def plugin_json_path(self) -> Path:
        return PLUGIN_ROOT / ".claude-plugin" / "plugin.json"

    def test_command_file_exists(self, command_path: Path) -> None:
        """Given the sanctum plugin, the update-ci command file should exist."""
        assert command_path.exists(), f"Missing {command_path}"

    def test_has_valid_frontmatter(self, command_path: Path) -> None:
        """Given the command file, it should have YAML frontmatter with description."""
        content = command_path.read_text()
        assert content.startswith("---"), "Must start with frontmatter delimiter"
        assert "description:" in content
        assert "usage:" in content

    def test_registered_in_plugin_json(self, plugin_json_path: Path) -> None:
        """Given plugin.json, update-ci should be registered in commands array."""
        plugin = json.loads(plugin_json_path.read_text())
        commands = plugin.get("commands", [])
        assert any("update-ci.md" in cmd for cmd in commands), (
            "update-ci.md not found in plugin.json commands"
        )

    def test_describes_change_window_detection(self, command_path: Path) -> None:
        """The command should explain how it determines what changed."""
        content = command_path.read_text()
        assert "git log" in content, "Should reference git log for change detection"

    def test_covers_both_hooks_and_workflows(self, command_path: Path) -> None:
        """The command should address both pre-commit hooks and GitHub workflows."""
        content = command_path.read_text()
        assert "pre-commit" in content.lower() or "hook" in content.lower()
        assert "workflow" in content.lower()

    def test_supports_dry_run(self, command_path: Path) -> None:
        """The command should support a --dry-run flag."""
        content = command_path.read_text()
        assert "--dry-run" in content

    def test_covers_makefile_ci_targets(self, command_path: Path) -> None:
        """The command should reconcile Makefile targets referenced by CI."""
        content = command_path.read_text()
        assert "makefile" in content.lower()
        assert "make" in content.lower()

    def test_scope_includes_makefiles_option(self, command_path: Path) -> None:
        """The --scope flag should include makefiles as a valid option."""
        content = command_path.read_text()
        assert "makefiles" in content.lower()
