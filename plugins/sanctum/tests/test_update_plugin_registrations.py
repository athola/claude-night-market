#!/usr/bin/env python3
"""Tests for update_plugin_registrations.py script."""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update_plugin_registrations import PluginAuditor


class TestPluginAuditor:
    """Test the PluginAuditor class."""

    def test_scan_disk_files_finds_commands(self, tmp_path: Path) -> None:
        """Test scanning for command files."""
        # Create test structure
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "test-command.md").write_text("# Test")
        (commands_dir / "another-command.md").write_text("# Another")

        # Create module subdir (should be excluded)
        modules_dir = commands_dir / "test-modules"
        modules_dir.mkdir()
        (modules_dir / "module-file.md").write_text("# Module")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["commands"]) == 2
        assert "./commands/another-command.md" in result["commands"]
        assert "./commands/test-command.md" in result["commands"]
        assert "./commands/test-modules/module-file.md" not in result["commands"]

    def test_scan_disk_files_finds_skills(self, tmp_path: Path) -> None:
        """Test scanning for skill directories."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "test-skill").mkdir()
        (skills_dir / "another-skill").mkdir()
        (skills_dir / "__pycache__").mkdir()  # Should be excluded

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["skills"]) == 2
        assert "./skills/another-skill" in result["skills"]
        assert "./skills/test-skill" in result["skills"]
        assert "./skills/__pycache__" not in result["skills"]

    def test_scan_disk_files_finds_agents(self, tmp_path: Path) -> None:
        """Test scanning for agent files."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "test-agent.md").write_text("# Agent")
        (agents_dir / "another-agent.md").write_text("# Another")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["agents"]) == 2
        assert "./agents/another-agent.md" in result["agents"]
        assert "./agents/test-agent.md" in result["agents"]

    def test_scan_disk_files_finds_hooks(self, tmp_path: Path) -> None:
        """Test scanning for hook files."""
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "pre-commit.sh").write_text("#!/bin/bash")
        (hooks_dir / "post-commit.py").write_text("# Python hook")
        (hooks_dir / "guide.md").write_text("# Hook guide")
        (hooks_dir / "__init__.py").write_text("# Init")  # Should be excluded
        (hooks_dir / "test_hooks.py").write_text("# Test")  # Should be excluded

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["hooks"]) == 3
        assert "./hooks/guide.md" in result["hooks"]
        assert "./hooks/post-commit.py" in result["hooks"]
        assert "./hooks/pre-commit.sh" in result["hooks"]
        assert "./hooks/__init__.py" not in result["hooks"]
        assert "./hooks/test_hooks.py" not in result["hooks"]

    def test_scan_disk_files_excludes_cache_directories(self, tmp_path: Path) -> None:
        """Test that cache/temp directories are properly excluded."""
        # Create legitimate files
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "real-command.md").write_text("# Real")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "real-skill").mkdir()

        # Create cache directories that should be excluded
        # Python caches
        venv_cmd = commands_dir / ".venv"
        venv_cmd.mkdir()
        (venv_cmd / "fake-command.md").write_text("# Fake")

        pycache_skill = skills_dir / "__pycache__"
        pycache_skill.mkdir()

        # Node caches
        node_modules = skills_dir / "node_modules"
        node_modules.mkdir()

        # Rust caches
        target_skill = skills_dir / "target"
        target_skill.mkdir()

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        # Should only find legitimate files
        assert len(result["commands"]) == 1
        assert "./commands/real-command.md" in result["commands"]
        assert not any(".venv" in cmd for cmd in result["commands"])

        assert len(result["skills"]) == 1
        assert "./skills/real-skill" in result["skills"]
        assert not any("__pycache__" in skill for skill in result["skills"])
        assert not any("node_modules" in skill for skill in result["skills"])
        assert not any("target" in skill for skill in result["skills"])

    def test_compare_registrations_finds_missing(self, tmp_path: Path) -> None:
        """Test detecting missing registrations."""
        on_disk = {
            "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }
        in_json = {
            "commands": ["./commands/cmd1.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations("test", on_disk, in_json)

        assert "commands" in discrepancies["missing"]
        assert "./commands/cmd2.md" in discrepancies["missing"]["commands"]

    def test_compare_registrations_finds_stale(self, tmp_path: Path) -> None:
        """Test detecting stale registrations."""
        on_disk = {
            "commands": ["./commands/cmd1.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }
        in_json = {
            "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations("test", on_disk, in_json)

        assert "commands" in discrepancies["stale"]
        assert "./commands/cmd2.md" in discrepancies["stale"]["commands"]

    def test_fix_plugin_adds_missing(self, tmp_path: Path) -> None:
        """Test fixing adds missing registrations."""
        # Create plugin structure
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

        # Create auditor and simulate discrepancies
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        # Fix
        auditor.fix_plugin("test-plugin")

        # Verify
        with plugin_json.open() as f:
            data = json.load(f)

        assert len(data["commands"]) == 2
        assert "./commands/cmd1.md" in data["commands"]
        assert "./commands/cmd2.md" in data["commands"]

    def test_fix_plugin_removes_stale(self, tmp_path: Path) -> None:
        """Test fixing removes stale registrations."""
        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {
                    "name": "test-plugin",
                    "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
                },
                indent=2,
            )
        )

        # Create auditor and simulate discrepancies
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {},
            "stale": {"commands": ["./commands/cmd2.md"]},
        }

        # Fix
        auditor.fix_plugin("test-plugin")

        # Verify
        with plugin_json.open() as f:
            data = json.load(f)

        assert len(data["commands"]) == 1
        assert "./commands/cmd1.md" in data["commands"]
        assert "./commands/cmd2.md" not in data["commands"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
