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

    def __init__(self, path: Path):
        self.path = path
        self.git_cmd = ["git", "-C", str(path)]

    def init(self, bare: bool = False) -> None:
        """Initialize a Git repository."""
        cmd = self.git_cmd + ["init", "--bare"] if bare else self.git_cmd + ["init"]
        subprocess.run(cmd, check=True, capture_output=True)

    def config(self, key: str, value: str) -> None:
        """Set Git configuration."""
        subprocess.run(
            self.git_cmd + ["config", key, value], check=True, capture_output=True
        )

    def add_file(self, file_path: str, content: str = "") -> Path:
        """Add a file to the repository."""
        full_path = self.path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path

    def stage_file(self, file_path: str) -> None:
        """Stage a file for commit."""
        subprocess.run(
            self.git_cmd + ["add", file_path], check=True, capture_output=True
        )

    def commit(self, message: str = "Test commit") -> str:
        """Create a commit."""
        subprocess.run(
            self.git_cmd + ["commit", "-m", message], check=True, capture_output=True
        )
        # Get commit hash
        result = subprocess.run(
            self.git_cmd + ["rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def create_branch(self, branch_name: str) -> None:
        """Create and checkout a new branch."""
        subprocess.run(
            self.git_cmd + ["checkout", "-b", branch_name],
            check=True,
            capture_output=True,
        )

    def get_status(self) -> dict[str, Any]:
        """Get repository status as a dictionary."""
        result = subprocess.run(
            self.git_cmd + ["status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )
        return {
            "porcelain": result.stdout.strip(),
            "has_changes": bool(result.stdout.strip()),
            "lines": result.stdout.strip().split("\n") if result.stdout.strip() else [],
        }

    def get_diff(self, cached: bool = False) -> str:
        """Get diff output."""
        cmd = self.git_cmd + ["diff", "--cached"] if cached else self.git_cmd + ["diff"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout

    def add_remote(self, name: str, url: str) -> None:
        """Add a remote repository."""
        subprocess.run(
            self.git_cmd + ["remote", "add", name, url], check=True, capture_output=True
        )


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> GitRepository:
    """Create a temporary Git repository for testing."""
    repo = GitRepository(tmp_path)
    repo.init()
    repo.config("user.name", "Test User")
    repo.config("user.email", "test@example.com")
    repo.config("init.defaultBranch", "main")
    return repo


@pytest.fixture
def mock_bash_tool():
    """Mock Bash tool for testing Git operations."""
    mock = Mock()

    def mock_execute(command: str, **kwargs):
        """Mock bash execution with common Git commands."""
        if "git status" in command:
            return "## main...origin/main\nM file1.txt\nA file2.txt\n"
        elif "git diff" in command:
            return "diff --git a/file1.txt b/file1.txt\nindex 123..456 789\n"
        elif "git log" in command:
            return "abc1234 Test commit\n"
        else:
            return ""

    mock.side_effect = mock_execute
    return mock


@pytest.fixture
def mock_todo_tool():
    """Mock TodoWrite tool for testing task management."""
    mock = Mock()

    def mock_create(todos: list[dict[str, Any]]):
        """Mock todo creation."""
        return {"status": "success", "todos": todos}

    mock.side_effect = mock_create
    return mock


@pytest.fixture
def staged_changes_context():
    """Context with staged changes for testing commit skills."""
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
    """Context for PR preparation testing."""
    return {
        "base_branch": "main",
        "feature_branch": "feature/new-functionality",
        "changed_files": [
            {"path": "src/feature.py", "changes": 150, "type": "feature"},
            {"path": "tests/test_feature.py", "changes": 75, "type": "test"},
            {"path": "docs/feature.md", "changes": 50, "type": "docs"},
        ],
        "commits": [
            {"hash": "abc123", "message": "feat: Add initial feature implementation"},
            {"hash": "def456", "message": "test: Add comprehensive test suite"},
            {"hash": "ghi789", "message": "docs: Update documentation for new feature"},
        ],
    }


class GitCommandMatcher:
    """Helper for matching Git commands in mock assertions."""

    def __init__(self, command_pattern: str):
        self.pattern = command_pattern

    def __eq__(self, other: str) -> bool:
        return self.pattern in other

    def __repr__(self) -> str:
        return f"GitCommandMatcher({self.pattern!r})"


def git_cmd(pattern: str) -> GitCommandMatcher:
    """Create a Git command matcher for testing."""
    return GitCommandMatcher(pattern)


@pytest.fixture
def sample_repository_state():
    """Sample repository state for testing workspace operations."""
    return {
        "is_git_repo": True,
        "current_branch": "main",
        "has_staged_changes": True,
        "has_unstaged_changes": False,
        "has_untracked_files": True,
        "is_clean": False,
        "ahead_count": 2,
        "behind_count": 0,
        "staged_files": ["file1.txt", "file2.py"],
        "unstaged_files": [],
        "untracked_files": ["temp.tmp"],
        "remotes": {"origin": "https://github.com/user/repo.git"},
    }


@pytest.fixture(autouse=True)
def isolate_tests(tmp_path: Path, monkeypatch):
    """Isolate tests by changing to temporary directory."""
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def sanctum_plugin_root() -> Path:
    """Return the path to the sanctum plugin root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_skill_frontmatter() -> str:
    """Sample valid skill frontmatter content."""
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
    """Sample skill content with missing required fields."""
    return """---
name: incomplete-skill
---

Some content without description or category.
"""


@pytest.fixture
def sample_skill_without_frontmatter() -> str:
    """Sample skill content without frontmatter."""
    return """# Missing Frontmatter

This skill has no YAML frontmatter at all.
"""


@pytest.fixture
def sample_command_content() -> str:
    """Sample valid command content."""
    return """---
description: Draft a Conventional Commit message for staged changes.
---

# Draft a Conventional Commit Message

To draft a commit message, load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture repository status.
2. Run `Skill(sanctum:commit-messages)` and create its TodoWrite items.
"""


@pytest.fixture
def sample_command_without_description() -> str:
    """Sample command content missing required description."""
    return """---
tags: [git, commit]
---

# Some Command

This command has tags but no description.
"""


@pytest.fixture
def sample_agent_content() -> str:
    """Sample valid agent markdown content."""
    return """# Git Workspace Agent

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
    """Sample valid plugin.json structure."""
    return {
        "name": "sanctum",
        "version": "2.0.0",
        "description": "Git and workspace operations for active development workflows",
        "commands": [
            "./commands/commit-msg.md",
            "./commands/pr.md",
        ],
        "skills": [
            "./skills/git-workspace-review",
            "./skills/commit-messages",
        ],
        "agents": [
            "./agents/git-workspace-agent.md",
        ],
        "keywords": ["git", "workspace", "commit", "pr"],
        "author": {
            "name": "Claude Skills",
            "url": "https://github.com/superpowers-marketplace",
        },
        "license": "MIT",
    }


@pytest.fixture
def sample_plugin_json_minimal() -> dict:
    """Sample minimal valid plugin.json with only required fields."""
    return {
        "name": "minimal-plugin",
        "version": "1.0.0",
        "description": "A minimal plugin",
    }


@pytest.fixture
def sample_plugin_json_invalid() -> dict:
    """Sample invalid plugin.json missing required fields."""
    return {
        "name": "broken-plugin",
        # Missing version and description
        "commands": [],
    }


@pytest.fixture
def temp_skill_file(tmp_path, sample_skill_frontmatter):
    """Create a temporary skill file."""
    skill_dir = tmp_path / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(sample_skill_frontmatter)
    return skill_file


@pytest.fixture
def temp_command_file(tmp_path, sample_command_content):
    """Create a temporary command file."""
    cmd_dir = tmp_path / "commands"
    cmd_dir.mkdir(parents=True)
    cmd_file = cmd_dir / "test-command.md"
    cmd_file.write_text(sample_command_content)
    return cmd_file


@pytest.fixture
def temp_agent_file(tmp_path, sample_agent_content):
    """Create a temporary agent file."""
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir(parents=True)
    agent_file = agent_dir / "test-agent.md"
    agent_file.write_text(sample_agent_content)
    return agent_file


@pytest.fixture
def temp_plugin_dir(tmp_path, sample_plugin_json):
    """Create a temporary plugin directory with plugin.json."""
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    plugin_json = plugin_dir / "plugin.json"
    plugin_json.write_text(json.dumps(sample_plugin_json, indent=2))
    return tmp_path


@pytest.fixture
def temp_full_plugin(
    tmp_path, sample_plugin_json, sample_skill_frontmatter, sample_command_content
):
    """Create a complete temporary plugin structure."""
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
