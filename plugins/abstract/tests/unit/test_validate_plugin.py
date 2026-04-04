"""Tests for validate_plugin.py — plugin structure validator.

Covers duplicate hooks detection, hook script existence checks,
event type validation, and path reference validation.
"""

from __future__ import annotations

import json

# Import directly — the validator is a script, so add its parent to sys.path
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2] / "scripts"),
)
from validate_plugin import (
    PluginValidator,  # noqa: E402 - sys.path must be extended before import
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def plugin_dir(tmp_path: Path) -> Path:
    """Create a minimal valid plugin directory."""
    plugin_root = tmp_path / "test-plugin"
    plugin_root.mkdir()

    # .claude-plugin/plugin.json
    config_dir = plugin_root / ".claude-plugin"
    config_dir.mkdir()

    config = {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "hooks": [],
        "skills": [],
        "commands": [],
    }
    (config_dir / "plugin.json").write_text(json.dumps(config, indent=2))

    return plugin_root


@pytest.fixture()
def plugin_with_hooks(plugin_dir: Path) -> Path:
    """Create a plugin with a valid hooks/hooks.json."""
    hooks_dir = plugin_dir / "hooks"
    hooks_dir.mkdir()

    hooks_json = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": ("${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py"),
                            "timeout": 3,
                        }
                    ],
                }
            ]
        }
    }
    (hooks_dir / "hooks.json").write_text(json.dumps(hooks_json, indent=2))

    # Create the referenced hook script
    hook_script = hooks_dir / "my_hook.py"
    hook_script.write_text("#!/usr/bin/env python3\nprint('ok')\n")

    return plugin_dir


def _set_hooks(plugin_dir: Path, hooks_value: object) -> None:
    """Update the hooks field in plugin.json."""
    pj = plugin_dir / ".claude-plugin" / "plugin.json"
    data = json.loads(pj.read_text())
    data["hooks"] = hooks_value
    pj.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Tests: Duplicate hooks/hooks.json detection
# ---------------------------------------------------------------------------


class TestDuplicateHooksDetection:
    """The validator must flag explicit refs to hooks/hooks.json."""

    def test_empty_hooks_array_passes(self, plugin_with_hooks: Path) -> None:
        """Empty hooks array with auto-loaded hooks.json is fine."""
        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()
        assert exit_code == 0
        assert not v.issues["critical"]

    def test_explicit_hooks_json_ref_is_critical(self, plugin_with_hooks: Path) -> None:
        """Listing ./hooks/hooks.json in manifest triggers critical error."""
        _set_hooks(plugin_with_hooks, ["./hooks/hooks.json"])

        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()

        assert exit_code == 1
        assert any(
            "auto-loaded" in msg and "Duplicate" in msg for msg in v.issues["critical"]
        )

    def test_legacy_string_hooks_json_ref_is_valid(
        self, plugin_with_hooks: Path
    ) -> None:
        """Legacy string format is the old path ref, not a duplicate."""
        _set_hooks(plugin_with_hooks, "./hooks/hooks.json")

        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()

        assert exit_code == 0
        assert not any("auto-loaded" in msg for msg in v.issues["critical"])

    def test_additional_hooks_file_allowed(self, plugin_with_hooks: Path) -> None:
        """Extra hooks files beyond hooks.json are allowed."""
        extra = plugin_with_hooks / "hooks" / "extra-hooks.json"
        extra.write_text(json.dumps({"hooks": {}}, indent=2))
        _set_hooks(plugin_with_hooks, ["./hooks/extra-hooks.json"])

        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()

        assert exit_code == 0
        assert not v.issues["critical"]


# ---------------------------------------------------------------------------
# Tests: Hook script existence
# ---------------------------------------------------------------------------


class TestHookScriptExistence:
    """The validator must flag missing hook scripts."""

    def test_script_with_arguments_resolves(self, plugin_with_hooks: Path) -> None:
        """Commands with arguments (script.py --flag) resolve correctly."""
        hooks_json = plugin_with_hooks / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        data["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
            "${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py --clear-state"
        )
        hooks_json.write_text(json.dumps(data))

        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()
        assert exit_code == 0

    def test_interpreter_prefix_resolves(self, plugin_with_hooks: Path) -> None:
        """Commands with interpreter prefix (python3 script.py) resolve."""
        hooks_json = plugin_with_hooks / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        data["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
            "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py"
        )
        hooks_json.write_text(json.dumps(data))

        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()
        assert exit_code == 0

    @pytest.mark.xfail(reason="Hook script existence check not yet implemented")
    def test_missing_hook_script_is_critical(self, plugin_with_hooks: Path) -> None:
        """A hooks.json referencing a nonexistent script is critical."""
        # Delete the hook script
        (plugin_with_hooks / "hooks" / "my_hook.py").unlink()

        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()

        assert exit_code == 1
        assert any("Hook script not found" in msg for msg in v.issues["critical"])

    @pytest.mark.xfail(reason="Hook script existence check not yet implemented")
    def test_existing_hook_script_passes(self, plugin_with_hooks: Path) -> None:
        """Valid hooks.json with existing scripts passes."""
        v = PluginValidator(plugin_with_hooks)
        exit_code = v.validate()

        assert exit_code == 0
        assert any("events and scripts checked" in msg for msg in v.issues["info"])


# ---------------------------------------------------------------------------
# Tests: Hook event type validation
# ---------------------------------------------------------------------------


class TestHookEventTypes:
    """The validator must flag unknown hook event types."""

    def test_valid_event_types_pass(self, plugin_with_hooks: Path) -> None:
        """Known event types produce no warnings."""
        v = PluginValidator(plugin_with_hooks)
        v.validate()
        assert not any("unknown event type" in msg for msg in v.issues["warnings"])

    @pytest.mark.xfail(reason="Event type validation not yet implemented")
    def test_unknown_event_type_warns(self, plugin_with_hooks: Path) -> None:
        """An unrecognized event type produces a warning."""
        hooks_json = plugin_with_hooks / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        data["hooks"]["FakeEvent"] = [
            {"hooks": [{"type": "command", "command": "echo hi"}]}
        ]
        hooks_json.write_text(json.dumps(data))

        v = PluginValidator(plugin_with_hooks)
        v.validate()

        assert any(
            "unknown event type" in msg and "FakeEvent" in msg
            for msg in v.issues["warnings"]
        )


# ---------------------------------------------------------------------------
# Tests: Referenced path validation
# ---------------------------------------------------------------------------


class TestPathValidation:
    """The validator must flag missing skills/commands/agents."""

    def test_missing_skill_path_is_critical(self, plugin_dir: Path) -> None:
        """A skill path pointing to nothing is a critical error."""
        pj = plugin_dir / ".claude-plugin" / "plugin.json"
        data = json.loads(pj.read_text())
        data["skills"] = ["./skills/nonexistent"]
        pj.write_text(json.dumps(data))

        v = PluginValidator(plugin_dir)
        exit_code = v.validate()

        assert exit_code == 1
        assert any(
            "not found" in msg and "nonexistent" in msg for msg in v.issues["critical"]
        )

    def test_missing_command_path_is_critical(self, plugin_dir: Path) -> None:
        """A command path pointing to nothing is a critical error."""
        pj = plugin_dir / ".claude-plugin" / "plugin.json"
        data = json.loads(pj.read_text())
        data["commands"] = ["./commands/missing.md"]
        pj.write_text(json.dumps(data))

        v = PluginValidator(plugin_dir)
        exit_code = v.validate()

        assert exit_code == 1
        assert any("not found" in msg for msg in v.issues["critical"])

    def test_valid_skill_directory_passes(self, plugin_dir: Path) -> None:
        """A skill directory with SKILL.md passes validation."""
        skill_dir = plugin_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: test\n---\nContent\n"
        )

        pj = plugin_dir / ".claude-plugin" / "plugin.json"
        data = json.loads(pj.read_text())
        data["skills"] = ["./skills/my-skill"]
        pj.write_text(json.dumps(data))

        v = PluginValidator(plugin_dir)
        exit_code = v.validate()

        assert exit_code == 0
