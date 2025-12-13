# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Tests for plugin validator helpers."""

import json
from pathlib import Path

from sanctum.validators import PluginValidationResult, PluginValidator


def test_valid_result_creation() -> None:
    result = PluginValidationResult(
        is_valid=False, errors=["missing version"], warnings=[]
    )
    assert not result.is_valid


def test_validates_complete_plugin_json(sample_plugin_json) -> None:
    result = PluginValidator.validate_structure(sample_plugin_json)
    assert result.is_valid is True


def test_fails_when_missing_description() -> None:
    plugin_json = {"name": "test", "version": "1.0.0"}
    result = PluginValidator.validate_structure(plugin_json)
    assert result.is_valid is False


def test_warns_on_empty_arrays() -> None:
    plugin_json = {
        "name": "test",
        "version": "1.0.0",
        "description": "t",
        "commands": [],
        "skills": [],
    }
    result = PluginValidator.validate_structure(plugin_json)

    assert any("commands" in warn for warn in result.warnings)
    assert any("skills" in warn for warn in result.warnings)


def test_valid_semver_version() -> None:
    plugin_json = {"name": "test", "version": "1.2.3", "description": "t"}
    result = PluginValidator.validate_structure(plugin_json)
    assert result.is_valid is True


def test_warns_on_empty_commands_array() -> None:
    plugin_json = {
        "name": "test",
        "version": "1.0.0",
        "description": "t",
        "commands": [],
    }
    result = PluginValidator.validate_structure(plugin_json)
    assert any("commands" in warn for warn in result.warnings)


def test_validate_directory_success(tmp_path: Path, sample_plugin_json: dict) -> None:
    plugin_root = tmp_path
    plugin_dir = plugin_root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)

    skills_dir = plugin_root / "skills" / "git-workspace-review"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        """---
name: git-workspace-review
description: Check repo state
category: git
tags: [git]
tools: [Bash]
---

# Git Workspace Review
"""
    )

    commands_dir = plugin_root / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "catchup.md").write_text(
        """---
description: Catch up branch
---

# /catchup
## Usage
Use it.
"""
    )

    agents_dir = plugin_root / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "agent.md").write_text(
        "# Agent\n\n## Capabilities\n- Do\n\n## Tools\n- Bash\n"
    )

    plugin_json = sample_plugin_json | {
        "skills": ["./skills/git-workspace-review"],
        "commands": ["./commands/catchup.md"],
        "agents": ["./agents/agent.md"],
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(plugin_json))

    result = PluginValidator.validate_directory(plugin_root)

    assert result.is_valid is True
    assert result.has_skills is True
    assert result.has_commands is True
    assert result.has_agents is True


def test_validate_directory_reports_missing_references(
    tmp_path: Path, sample_plugin_json: dict
) -> None:
    plugin_root = tmp_path
    plugin_dir = plugin_root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)

    plugin_json = sample_plugin_json | {
        "skills": ["./skills/missing"],
        "commands": ["./commands/missing.md"],
        "agents": ["./agents/missing.md"],
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(plugin_json))

    result = PluginValidator.validate_directory(plugin_root)

    assert result.is_valid is False
    assert any("Referenced command file not found" in err for err in result.errors)
    assert any("skill directory not found" in err for err in result.errors)
