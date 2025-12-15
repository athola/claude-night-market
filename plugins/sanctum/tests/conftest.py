# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Common fixtures for sanctum tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest


@dataclass
class GitRepository:
    """Lightweight in-memory git-like repository for tests."""

    path: Path
    staged: set[str] = field(default_factory=set)
    commits: list[dict[str, Any]] = field(default_factory=list)
    current_branch: str = "main"

    def add_file(self, file_path: str, content: str) -> Path:
        full = self.path / file_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        return full

    def stage_file(self, file_path: str) -> None:
        self.staged.add(file_path)

    def commit(self, message: str) -> str:
        self.commits.append({"message": message, "files": sorted(self.staged)})
        self.staged.clear()
        return message

    def create_branch(self, branch_name: str) -> None:
        self.current_branch = branch_name


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> GitRepository:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    return GitRepository(repo_path)


@pytest.fixture
def staged_changes_context() -> dict[str, Any]:
    return {
        "modified": ["src/main.py"],
        "added": ["README.md"],
        "deleted": ["old_file.py"],
        "untracked": ["temp.tmp"],
        "stats": {"total_additions": 150, "total_deletions": 75},
    }


@pytest.fixture
def mock_todo_tool() -> Mock:
    return Mock()


@pytest.fixture
def pull_request_context() -> dict[str, Any]:
    return {
        "title": "feat: Add feature",
        "description": "Implements new functionality with tests",
        "changes": ["src/feature.py", "tests/test_feature.py"],
    }


@pytest.fixture
def sample_agent_content() -> str:
    return """# Agent\n\n## Capabilities\n- Do things\n\n## Tools\n- Bash\n"""


@pytest.fixture
def sample_agent_with_capabilities() -> str:
    return """# Agent\n\n## Capabilities\n- Analyze\n- Plan\n\n## Tools\n- Bash\n"""


@pytest.fixture
def sample_agent_without_tools() -> str:
    return """# Agent\n\n## Capabilities\n- Analyze\n"""


@pytest.fixture
def sample_agent_without_capabilities() -> str:
    return """# Agent\n\n## Tools\n- Bash\n"""


@pytest.fixture
def sample_agent_file(tmp_path: Path, sample_agent_content: str) -> Path:
    file = tmp_path / "agent.md"
    file.write_text(sample_agent_content)
    return file


@pytest.fixture
def sample_command_content() -> str:
    return """# Command\n\n## Description\nDo the thing.\n"""


@pytest.fixture
def sample_command_with_tags() -> str:
    return """# Command\n\n## Tags\n- git\n- commit\n"""


@pytest.fixture
def sample_plugin_json() -> dict[str, Any]:
    return {
        "name": "sanctum",
        "version": "0.1.0",
        "skills": ["git-workspace-review"],
    }


@pytest.fixture
def mock_bash_tool() -> Mock:
    return Mock()
