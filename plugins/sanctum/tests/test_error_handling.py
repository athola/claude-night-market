#!/usr/bin/env python3
"""Tests for error handling scenarios in plugin management."""

import json
import os
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update_plugin_registrations import PluginAuditor


class TestErrorHandling:
    """Test error handling scenarios for PluginAuditor."""

    def test_malformed_plugin_json_handling(self, tmp_path: Path) -> None:
        """Verify read_plugin_json returns None for malformed JSON."""
        config_dir = tmp_path / ".claude-plugin"
        config_dir.mkdir()
        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text("{not valid json, missing quotes: true")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.read_plugin_json(tmp_path)

        assert result is None

    def test_missing_directory_handling(self, tmp_path: Path) -> None:
        """Verify scan_disk_files handles missing commands/skills/agents dirs."""
        # Plugin dir exists but has no subdirectories
        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert result["commands"] == []
        assert result["skills"] == []
        assert result["agents"] == []
        assert result["hooks"] == []

    def test_write_permission_failures(self, tmp_path: Path) -> None:
        """Verify fix_plugin handles read-only plugin.json gracefully."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {"name": "test-plugin", "commands": ["./commands/cmd1.md"]}, indent=2
            )
        )

        # Make plugin.json read-only
        os.chmod(plugin_json, 0o444)

        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        try:
            # Should raise PermissionError when trying to write
            with pytest.raises(PermissionError):
                auditor.fix_plugin("test-plugin")
        finally:
            # Restore permissions for cleanup
            os.chmod(plugin_json, 0o644)

    def test_missing_git_history(self, tmp_path: Path) -> None:
        """Verify PluginAuditor works without a .git directory."""
        # Create a minimal plugin structure with no .git
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps({"name": "test-plugin", "commands": []}, indent=2)
        )

        # Should not raise even without .git
        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.read_plugin_json(plugin_dir)

        assert result is not None
        assert result["name"] == "test-plugin"

    def test_fix_plugin_handles_missing_plugin_json(self, tmp_path: Path) -> None:
        """Verify fix_plugin raises when plugin.json doesn't exist."""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()
        # No plugin.json created

        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd1.md"]},
            "stale": {},
        }

        # fix_plugin tries to open plugin.json directly - should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            auditor.fix_plugin("test-plugin")

    def test_scan_disk_files_empty_plugin(self, tmp_path: Path) -> None:
        """Verify scanning a completely empty plugin directory."""
        # Create only the plugin dir, nothing inside
        plugin_dir = tmp_path / "empty-plugin"
        plugin_dir.mkdir()

        auditor = PluginAuditor(tmp_path, dry_run=True)
        result = auditor.scan_disk_files(plugin_dir)

        assert result["commands"] == []
        assert result["skills"] == []
        assert result["agents"] == []
        assert result["hooks"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
