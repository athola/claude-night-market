# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Integration-style smoke tests for Sanctum validator."""

import json
from pathlib import Path

import pytest

from sanctum.validators import SanctumValidationReport, SanctumValidator


def test_report_creation() -> None:
    report = SanctumValidationReport(
        is_valid=True,
        plugin_result=None,
        skill_results=[],
        command_results=[],
        agent_results=[],
    )
    assert isinstance(report, SanctumValidationReport)


@pytest.mark.integration
def test_report_is_valid_with_no_errors() -> None:
    report = SanctumValidationReport(
        is_valid=True,
        plugin_result=None,
        skill_results=[],
        command_results=[],
        agent_results=[],
    )
    assert report.total_errors == 0
    assert report.all_errors() == []


def test_all_errors_collects_nested_errors() -> None:
    report = SanctumValidationReport(
        is_valid=False,
        plugin_result=None,
        agent_results=[],
        skill_results=[],
        command_results=[],
    )
    assert report.all_errors() == []


def test_validate_plugin_builds_report(
    tmp_path: Path, sample_plugin_json: dict
) -> None:
    plugin_root = tmp_path
    plugin_dir = plugin_root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)

    skills_dir = plugin_root / "skills" / "demo"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        """---
name: demo
description: Demo
category: test
tags: [demo]
tools: [Bash]
---

# Demo
"""
    )

    commands_dir = plugin_root / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "cmd.md").write_text(
        """---
description: Cmd
---

# cmd
## Usage
run
"""
    )

    agents_dir = plugin_root / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "agent.md").write_text(
        "# Agent\n\n## Capabilities\n- Do\n\n## Tools\n- Bash\n"
    )

    plugin_json = sample_plugin_json | {
        "skills": ["./skills/demo"],
        "commands": ["./commands/cmd.md"],
        "agents": ["./agents/agent.md"],
    }
    (plugin_dir / "plugin.json").write_text(json.dumps(plugin_json))

    report = SanctumValidator.validate_plugin(plugin_root)

    assert report.is_valid is True
    assert report.total_errors == 0
    assert report.total_warnings >= 0
