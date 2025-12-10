"""Test configuration and fixtures for sanctum plugin tests.

This module provides common fixtures and utilities for testing sanctum plugin
components including skills, commands, agents, and Git operations.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# Plugin root for test data
PLUGIN_ROOT = Path(__file__).parent.parent


class GitRepository:
    """Helper class to create and manage test Git repositories."""

    def __init__(self, path: Path) -> None:
        cmd = [*self.git_cmd, "init", "--bare"] if bare else [*self.git_cmd, "init"]
        subprocess.run(cmd, check=True, capture_output=True, shell=False)  # noqa: S603

    def config(self, key: str, value: str) -> None:
        full_path = self.path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path

    def stage_file(self, file_path: str) -> None:
        subprocess.run(
            [*self.git_cmd, "commit", "-m", message],
            check=True,
            capture_output=True,
            shell=False,
        )  # noqa: S603
        # Get commit hash
        result = subprocess.run(
            [*self.git_cmd, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )  # noqa: S603
        return result.stdout.strip()

    def create_branch(self, branch_name: str) -> None:
        result = subprocess.run(
            [*self.git_cmd, "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )  # noqa: S603
        return {
            "porcelain": result.stdout.strip(),
            "has_changes": bool(result.stdout.strip()),
            "lines": result.stdout.strip().split("\n") if result.stdout.strip() else [],
        }

    def get_diff(self, cached: bool = False) -> str:
        subprocess.run(
            [*self.git_cmd, "remote", "add", name, url],
            check=True,
            capture_output=True,
            shell=False,
        )  # noqa: S603


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> GitRepository:
    mock = Mock()

    def mock_execute(command: str, **kwargs) -> str:
    mock = Mock()

    def mock_create(todos: list[dict[str, Any]]):
    return {
        "repository_path": "/test/repo",
        "staged_files": [
            {"path": "src/main.py", "status": "M", "additions": 10, "deletions": 5},
            {"path": "README.md", "status": "A", "additions": 25, "deletions": 0},
            {
                "path": "tests/test_main.py",
                "status": "M",
                "additions": 15,
                "deletions": 3,
            },
        ],
        "git_status": {
            "branch": "main",
            "ahead": 0,
            "behind": 0,
            "has_untracked": True,
        },
    }


@pytest.fixture
def pull_request_context():

    def __init__(self, command_pattern: str) -> None:
        return self.pattern in other

    def __repr__(self) -> str:
    return GitCommandMatcher(pattern)


@pytest.fixture
def sample_repository_state():
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def sanctum_plugin_root() -> Path:
    return """---
name: git-workspace-review
description: Lightweight preflight checklist for verifying repo path, staged changes, and diffs.
category: workspace-ops
tags: [git, preflight, status, diff, staged]
tools: [Bash, TodoWrite]
complexity: low
estimated_tokens: 500
---

# Git Workspace Review

## When to Use
Use this skill before any workflow that depends on understanding current changes.

## Required TodoWrite Items
1. `git-review:repo-confirmed`
2. `git-review:status-overview`
"""


@pytest.fixture
def sample_skill_with_missing_fields() -> str:
name: incomplete-skill
---

Some content without description or category.
"""


@pytest.fixture
def sample_skill_without_frontmatter() -> str:

This skill has no YAML frontmatter at all.
"""


@pytest.fixture
def sample_command_content() -> str:
description: Draft a Conventional Commit message for staged changes.
---

# Draft a Conventional Commit Message

To draft a commit message, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture repository status.
2. Run `Skill(sanctum:commit-messages)` and create its TodoWrite items.
"""


@pytest.fixture
def sample_command_without_description() -> str:
tags: [git, commit]
---

# Some Command

This command has tags but no description.
"""


@pytest.fixture
def sample_agent_content() -> str:

An agent specialized in git workspace operations.

## Capabilities
- Review repository status
- Analyze staged changes
- Prepare commit messages

## Tools
- Bash
- TodoWrite
"""


@pytest.fixture
def sample_plugin_json() -> dict:
    return {
        "name": "minimal-plugin",
        "version": "1.0.0",
        "description": "A minimal plugin",
    }


@pytest.fixture
def sample_plugin_json_invalid() -> dict:
    skill_dir = tmp_path / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(sample_skill_frontmatter)
    return skill_file


@pytest.fixture
def temp_command_file(tmp_path, sample_command_content):
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir(parents=True)
    agent_file = agent_dir / "test-agent.md"
    agent_file.write_text(sample_agent_content)
    return agent_file


@pytest.fixture
def temp_plugin_dir(tmp_path, sample_plugin_json):
    # Create plugin.json
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(json.dumps(sample_plugin_json, indent=2))

    # Create skills
    for skill_path in sample_plugin_json.get("skills", []):
        skill_dir = tmp_path / Path(skill_path)
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(sample_skill_frontmatter)

    # Create commands
    cmd_dir = tmp_path / "commands"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    for cmd_path in sample_plugin_json.get("commands", []):
        cmd_file = tmp_path / Path(cmd_path)
        cmd_file.write_text(sample_command_content)

    # Create agents
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    for agent_path in sample_plugin_json.get("agents", []):
        agent_file = tmp_path / Path(agent_path)
        agent_file.write_text("# Agent\n\nAgent content.")

    return tmp_path
