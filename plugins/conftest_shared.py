"""Shared test fixtures for claude-night-market plugins.

This module consolidates commonly duplicated fixtures:
- temp_skill_file / temp_skill_dir: temporary SKILL.md creation
- mock_claude_tools: mock Claude Code tool calls
- mock_todo_write: mock TodoWrite tool
- pytest marker registration: standard markers
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_skill_file(tmp_path: Path, sample_skill_content: str) -> Path:
    """Create a temporary SKILL.md in a uniquely-named directory."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(sample_skill_content)
    return skill_file


@pytest.fixture
def temp_skill_dir(tmp_path: Path) -> Path:
    """Create a temporary skills/ directory."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir


@pytest.fixture
def mock_claude_tools() -> dict[str, Mock]:
    """Mock Claude Code tool calls with spec constraints."""
    tools = {
        "Read": Mock(spec=callable),
        "Glob": Mock(spec=callable),
        "Grep": Mock(spec=callable),
        "Bash": Mock(spec=callable),
        "Write": Mock(spec=callable),
        "Edit": Mock(spec=callable),
        "TodoWrite": Mock(spec=callable),
        "AskUserQuestion": Mock(spec=callable),
    }
    tools["Read"].return_value = "Mock file content"
    tools["Glob"].return_value = []
    tools["Grep"].return_value = []
    tools["Bash"].return_value = "Mock bash output"
    return tools


class MockTodoWrite:
    """Richer mock for TodoWrite that tracks calls."""

    def __init__(self) -> None:
        self.items: list[dict] = []

    def __call__(self, **kwargs) -> None:
        self.items.append(kwargs)

    def add(self, **kwargs) -> None:
        self.items.append(kwargs)

    def update_status(self, item_id: str, status: str) -> None:
        for item in self.items:
            if item.get("id") == item_id:
                item["status"] = status

    def get_by_status(self, status: str) -> list[dict]:
        return [i for i in self.items if i.get("status") == status]


@pytest.fixture
def mock_todo_write() -> MockTodoWrite:
    """Mock TodoWrite tool with call tracking."""
    return MockTodoWrite()


# Standard marker registration
_STANDARD_MARKERS = [
    "unit: Unit tests for individual components",
    "integration: Integration tests for workflow orchestration",
    "performance: Performance and scalability tests",
    "slow: Tests that take longer to execute",
    "bdd: Behavior-driven development style tests",
]
_PERFORMANCE_KEYWORDS = ["performance", "scalability", "benchmark"]
_BDD_KEYWORDS = ["bdd", "behavior", "feature", "scenario"]


def register_standard_markers(config) -> None:
    """Register standard test markers used across plugins."""
    for marker in _STANDARD_MARKERS:
        config.addinivalue_line("markers", marker)


def tag_items_by_keywords(items) -> None:
    """Auto-tag test items based on keywords in their node IDs."""
    for item in items:
        if any(kw in item.nodeid for kw in _PERFORMANCE_KEYWORDS):
            item.add_marker(pytest.mark.performance)
        if any(kw in item.nodeid for kw in _BDD_KEYWORDS):
            item.add_marker(pytest.mark.bdd)
