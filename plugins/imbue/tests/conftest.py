"""Shared fixtures and configuration for imbue plugin testing.

This module provides common test fixtures, mocks, and utilities for testing
the imbue plugin's skills, commands, and agents following TDD/BDD principles.
"""

import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# Add the scripts directory to Python path for importing imbue_validator
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    from scripts.imbue_validator import ImbueValidator
except ImportError:
    ImbueValidator = None


@pytest.fixture
def imbue_plugin_root():
    """Return the imbue plugin root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_skill_content() -> str:
    """Sample valid skill file content with frontmatter."""
    return """---
name: test-review-skill
description: Test skill for review workflow methodology
category: review-patterns
usage_patterns:
  - review-preflight
  - evidence-capture
dependencies:
  - imbue:evidence-logging
tools:
  - Read
  - Glob
  - Grep
tags:
  - workflow
  - evidence
  - review
---

# Test Review Skill

This is a test skill for validating review workflow patterns.

## TodoWrite Items

- `test-skill:context-established`
- `test-skill:evidence-captured`
- `test-skill:findings-generated`

## Usage

Use this skill to test review workflow patterns.
"""


@pytest.fixture
def sample_plugin_json():
    """Sample valid plugin.json configuration."""
    return {
        "name": "imbue",
        "version": "2.0.0",
        "description": (
            "Intelligent workflow methodologies for analysis, evidence gathering, "
            "and structured output patterns"
        ),
        "author": "Claude Skills (superpowers-marketplace)",
        "license": "MIT",
        "skills": [
            {
                "name": "review-core",
                "description": (
                    "Foundational workflow scaffolding for any detailed review"
                ),
                "file": "skills/review-core/SKILL.md",
            },
            {
                "name": "evidence-logging",
                "description": (
                    "Workflow for capturing reproducible evidence and audit trails"
                ),
                "file": "skills/evidence-logging/SKILL.md",
            },
            {
                "name": "diff-analysis",
                "description": (
                    "Methodology for categorizing changes and assessing risks"
                ),
                "file": "skills/diff-analysis/SKILL.md",
            },
            {
                "name": "catchup",
                "description": (
                    "Methodology for summarizing changes and extracting insights"
                ),
                "file": "skills/catchup/SKILL.md",
            },
            {
                "name": "structured-output",
                "description": "Guide for formatting review deliverables consistently",
                "file": "skills/structured-output/SKILL.md",
                "dependencies": ["imbue:evidence-logging"],
            },
        ],
        "commands": [
            {
                "name": "review",
                "description": "Start structured review workflow with evidence logging",
                "usage": "/review [target]",
                "file": "commands/review.md",
            },
            {
                "name": "catchup",
                "description": "Quickly understand recent changes and extract insights",
                "usage": "/catchup [baseline]",
                "file": "commands/catchup.md",
            },
        ],
        "agents": [
            {
                "name": "review-analyst",
                "description": "Autonomous agent for conducting structured reviews",
                "file": "agents/review-analyst.md",
                "tools": ["Read", "Glob", "Grep", "Bash"],
            },
        ],
    }


@pytest.fixture
def mock_git_repository(tmp_path):
    """Create a mock git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    git_executable = shutil.which("git") or "git"
    subprocess.run(  # noqa: S603
        [git_executable, "init"], cwd=repo_path, capture_output=True, check=True
    )
    subprocess.run(  # noqa: S603
        [git_executable, "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(  # noqa: S603
        [git_executable, "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
    )

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Project\n\nInitial setup.")
    (repo_path / "src").mkdir()
    (repo_path / "src" / "main.py").write_text('print("Hello, World!")')

    subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use
        [git_executable, "add", "."], cwd=repo_path, capture_output=True, check=True
    )
    subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use
        [git_executable, "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Create a second commit with changes
    (repo_path / "src" / "utils.py").write_text('def helper():\n    return "helper"')
    (repo_path / "src" / "main.py").write_text(
        "from utils import helper\nprint(helper())",
    )

    subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use
        [git_executable, "add", "."], cwd=repo_path, capture_output=True, check=True
    )
    subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use
        [git_executable, "commit", "-m", "Add helper function"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    return repo_path


@pytest.fixture
def sample_evidence_log():
    """Sample evidence log structure."""
    return {
        "session_id": "test-session-123",
        "timestamp": datetime.now(UTC).isoformat(),
        "context": {"repository": "/test/repo", "branch": "main", "baseline": "HEAD~1"},
        "evidence": [
            {
                "id": "E1",
                "command": "git status",
                "output": "On branch main\nnothing to commit, working tree clean",
                "timestamp": datetime.now(UTC).isoformat(),
                "working_directory": "/test/repo",
            },
            {
                "id": "E2",
                "command": "git diff --stat",
                "output": (
                    " src/main.py | 2 +-\n"
                    " 1 file changed, 2 insertions(+), 1 deletion(-)"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
                "working_directory": "/test/repo",
            },
        ],
        "citations": [
            {
                "id": "C1",
                "url": "https://example.com/docs",
                "title": "Example Documentation",
                "accessed": datetime.now(UTC).isoformat(),
                "relevant_snippet": "This is relevant information",
            },
        ],
    }


@pytest.fixture
def temp_skill_file(tmp_path, sample_skill_content):
    """Create a temporary skill file."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(sample_skill_content)
    return skill_file


@pytest.fixture
def temp_skill_dir(tmp_path):
    """Create a temporary skill directory structure."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create multiple skill directories
    for skill_name in [
        "review-core",
        "evidence-logging",
        "diff-analysis",
        "catchup",
        "structured-output",
    ]:
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(f"""---
name: {skill_name}
description: Test skill for {skill_name}
category: review-patterns
---""")

    return skills_dir


@pytest.fixture
def mock_todo_write():
    """Mock TodoWrite tool for testing."""
    mock = Mock()
    mock.return_value = None
    # Configure mock to track calls
    return mock


@pytest.fixture
def mock_claude_tools():
    """Mock Claude Code tools."""
    tools = {
        "Read": Mock(),
        "Glob": Mock(),
        "Grep": Mock(),
        "Bash": Mock(),
        "Write": Mock(),
        "Edit": Mock(),
        "TodoWrite": Mock(),
        "AskUserQuestion": Mock(),
    }

    # Configure default return values
    tools["Read"].return_value = "Mock file content"
    tools["Glob"].return_value = []
    tools["Grep"].return_value = []
    tools["Bash"].return_value = "Mock bash output"

    return tools


@pytest.fixture
def mock_git_operations():
    """Mock git operations for testing."""

    class MockGit:
        def __init__(self) -> None:
            self.status_output = "On branch main\nnothing to commit, working tree clean"
            self.diff_output = "diff --git a/file.py b/file.py"
            self.log_output = "commit abc123\nAuthor: Test User\n\nInitial commit"

        def status(self):
            return self.status_output

        def diff(self, args=None):
            return self.diff_output

        def log(self, args=None):
            return self.log_output

    return MockGit()


@pytest.fixture
def sample_diff_analysis():
    """Sample diff analysis results."""
    return {
        "baseline": "HEAD~1",
        "changes": [
            {
                "file": "src/main.py",
                "type": "modified",
                "lines_added": 5,
                "lines_removed": 2,
                "semantic_category": "feature",
                "risk_level": "Low",
            },
            {
                "file": "tests/test_main.py",
                "type": "added",
                "lines_added": 15,
                "lines_removed": 0,
                "semantic_category": "tests",
                "risk_level": "Low",
            },
        ],
        "summary": {
            "total_files": 2,
            "total_lines_added": 20,
            "total_lines_removed": 2,
            "categories": {"feature": 1, "tests": 1},
            "risk_levels": {"Low": 2},
        },
    }


@pytest.fixture
def sample_review_findings():
    """Sample review findings with evidence references."""
    return [
        {
            "id": "F1",
            "title": "Missing error handling",
            "description": "The new function lacks proper error handling",
            "severity": "Medium",
            "category": "Correctness",
            "file": "src/utils.py",
            "line": 15,
            "evidence_refs": ["E1", "E2"],
            "recommendation": "Add try-catch block for potential exceptions",
        },
        {
            "id": "F2",
            "title": "Inconsistent naming",
            "description": "Variable naming doesn't follow project conventions",
            "severity": "Low",
            "category": "Style",
            "file": "src/main.py",
            "line": 8,
            "evidence_refs": ["E3"],
            "recommendation": "Rename variable to follow snake_case convention",
        },
    ]


@pytest.fixture
def mock_imbue_validator(imbue_plugin_root):
    """Create ImbueValidator instance with mocked dependencies."""
    if ImbueValidator is not None:
        # Initialize with real plugin root but mock file operations
        return ImbueValidator(str(imbue_plugin_root))
    else:
        # If the module doesn't exist yet, create a mock
        mock_validator = Mock()
        mock_validator.plugin_root = str(imbue_plugin_root)
        mock_validator.scan_review_workflows = Mock(return_value=[])
        mock_validator.validate_review_workflows = Mock(return_value=[])
        mock_validator.generate_report = Mock(return_value="Mock report")
        return mock_validator


@pytest.fixture
def sample_review_report():
    """Sample structured review report."""
    return {
        "metadata": {
            "review_id": "review-123",
            "timestamp": datetime.now(UTC).isoformat(),
            "reviewer": "Test Reviewer",
            "target": "/test/repo",
            "baseline": "HEAD~1",
        },
        "summary": {
            "total_findings": 2,
            "severity_distribution": {"High": 0, "Medium": 1, "Low": 1},
            "category_distribution": {"Correctness": 1, "Style": 1},
        },
        "findings": [
            {
                "id": "F1",
                "title": "Test Finding",
                "description": "This is a test finding",
                "severity": "Medium",
                "category": "Correctness",
                "file": "src/test.py",
                "line": 10,
                "evidence_refs": ["E1"],
                "recommendation": "Fix the issue",
            },
        ],
        "evidence_log": {
            "session_id": "session-123",
            "total_evidence": 1,
            "evidence_items": [
                {
                    "id": "E1",
                    "command": "grep -r 'test' src/",
                    "output": "src/test.py:10: test function",
                },
            ],
        },
        "actions": [
            {
                "id": "A1",
                "description": "Implement error handling",
                "priority": "High",
                "assignee": "Developer",
                "due_date": "2024-12-11",
            },
        ],
        "appendix": {
            "commands_used": ["git status", "git diff", "grep -r 'test' src/"],
            "external_references": ["https://example.com/guidelines"],
        },
    }


# Test markers for pytest configuration
def pytest_configure(config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers",
        "integration: Integration tests for workflow orchestration",
    )
    config.addinivalue_line("markers", "performance: Performance and scalability tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to execute")
    config.addinivalue_line("markers", "bdd: Behavior-driven development style tests")


def pytest_collection_modifyitems(config, items) -> None:
    """Add custom markers to items based on their content."""
    for item in items:
        # Add performance marker to performance tests
        if "performance" in item.nodeid or any(
            keyword in item.nodeid for keyword in ["performance", "scalability"]
        ):
            item.add_marker(pytest.mark.performance)

        # Add bdd marker to BDD-style tests
        if "bdd" in item.nodeid or any(
            keyword in item.nodeid
            for keyword in ["bdd", "behavior", "feature", "scenario"]
        ):
            item.add_marker(pytest.mark.bdd)


# Helper functions for test data generation
def create_mock_skill(name: str, has_evidence_patterns: bool = True) -> dict[str, Any]:
    """Create a mock skill configuration."""
    skill = {
        "name": name,
        "description": f"Test skill for {name}",
        "file": f"skills/{name}/SKILL.md",
        "category": "review-patterns",
    }

    if has_evidence_patterns:
        skill["usage_patterns"] = ["evidence-capture", "review-workflow"]

    return skill


def create_mock_evidence_item(e_id: str, command: str, output: str) -> dict[str, Any]:
    """Create a mock evidence item."""
    return {
        "id": e_id,
        "command": command,
        "output": output,
        "timestamp": datetime.now(UTC).isoformat(),
        "working_directory": "/test/repo",
    }


def create_mock_finding(
    f_id: str,
    severity: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    """Create a mock review finding."""
    return {
        "id": f_id,
        "title": f"Finding {f_id}",
        "description": f"This is finding {f_id}",
        "severity": severity,
        "category": "Correctness",
        "file": "src/test.py",
        "line": 10,
        "evidence_refs": evidence_refs,
        "recommendation": f"Fix finding {f_id}",
    }
