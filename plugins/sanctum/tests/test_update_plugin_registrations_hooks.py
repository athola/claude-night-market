#!/usr/bin/env python3
"""Tests for PluginAuditor hooks.json resolution and parsing."""

import json
from pathlib import Path

from update_plugin_registrations import PluginAuditor


class TestHooksJsonResolution:
    """Test the hooks.json parsing and resolution functionality."""

    def test_extract_script_path_with_claude_plugin_root(self, tmp_path: Path) -> None:
        """Test extracting script path from CLAUDE_PLUGIN_ROOT variable."""
        auditor = PluginAuditor(tmp_path, dry_run=True)

        # Standard format
        result = auditor._extract_script_path("${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py")
        assert result == "./hooks/my_hook.py"

        # With python prefix
        result = auditor._extract_script_path(
            "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/pre_commit.py"
        )
        assert result == "./hooks/pre_commit.py"

    def test_extract_script_path_with_direct_path(self, tmp_path: Path) -> None:
        """Test extracting script path from direct ./hooks/ path."""
        auditor = PluginAuditor(tmp_path, dry_run=True)

        result = auditor._extract_script_path("./hooks/my_script.sh")
        assert result == "./hooks/my_script.sh"

    def test_extract_script_path_returns_none_for_invalid(self, tmp_path: Path) -> None:
        auditor = PluginAuditor(tmp_path, dry_run=True)

        result = auditor._extract_script_path("echo hello")
        assert result is None

        result = auditor._extract_script_path("")
        assert result is None

    def test_resolve_hooks_json_extracts_scripts(self, tmp_path: Path) -> None:
        """Test that resolve_hooks_json parses nested structure correctly."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()

        # Create hooks.json with typical nested structure
        hooks_json = hooks_dir / "hooks.json"
        hooks_data = {
            "hooks": {
                "UserPromptSubmit": [
                    {
                        "matcher": {},
                        "hooks": [
                            {"command": "${CLAUDE_PLUGIN_ROOT}/hooks/prompt_hook.py"},
                            {
                                "command": (
                                    "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/validate.py"
                                )
                            },
                        ],
                    }
                ],
                "SessionStart": [
                    {
                        "matcher": {},
                        "hooks": [{"command": "${CLAUDE_PLUGIN_ROOT}/hooks/init.sh"}],
                    }
                ],
            }
        }
        hooks_json.write_text(json.dumps(hooks_data, indent=2))

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.resolve_hooks_json(plugin_dir, "./hooks/hooks.json")

        assert isinstance(result, list), "resolve_hooks_json should return a list"
        assert len(result) == 3
        assert "./hooks/init.sh" in result
        assert "./hooks/prompt_hook.py" in result
        assert "./hooks/validate.py" in result

    def test_resolve_hooks_json_returns_none_for_missing_file(
        self, tmp_path: Path
    ) -> None:
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.resolve_hooks_json(plugin_dir, "./hooks/hooks.json")

        assert result is None

    def test_compare_registrations_with_hooks_json(self, tmp_path: Path) -> None:
        """Test that compare_registrations handles hooks.json references."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        hooks_dir = plugin_dir / "hooks"
        hooks_dir.mkdir()

        # Create actual hook files
        (hooks_dir / "hook_a.py").write_text("# Hook A")
        (hooks_dir / "hook_b.py").write_text("# Hook B")

        # Create hooks.json that only references hook_a
        hooks_json = hooks_dir / "hooks.json"
        hooks_data = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": {},
                        "hooks": [{"command": "${CLAUDE_PLUGIN_ROOT}/hooks/hook_a.py"}],
                    }
                ]
            }
        }
        hooks_json.write_text(json.dumps(hooks_data, indent=2))

        on_disk = {
            "commands": [],
            "skills": [],
            "agents": [],
            "hooks": ["./hooks/hook_a.py", "./hooks/hook_b.py"],  # Both on disk
        }
        # No explicit hooks in plugin.json - auto-loads from hooks.json
        in_json = {"commands": [], "skills": [], "agents": []}

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations(plugin_dir, on_disk, in_json)

        # hook_b.py is on disk but not in hooks.json - should be missing
        assert "hooks" in discrepancies["missing"]
        assert "./hooks/hook_b.py" in discrepancies["missing"]["hooks"]
