"""Pytest configuration and shared fixtures for abstract plugin testing.

This module provides reusable test fixtures following TDD/BDD principles:
- Focused fixtures that do one thing well
- Clear docstrings describing the "Given" state
- Type hints for better IDE support
- Edge case fixtures for boundary testing
"""

import pytest

# ============================================================================
# Original Fixtures (Backward Compatibility)
# ============================================================================


@pytest.fixture
def sample_skill_content() -> str:
    """Sample valid skill file content."""
    return """---
name: test-skill
description: A test skill for validation
category: testing
tags: [test, sample]
dependencies: []
---

## Overview

This is a test skill.

## Quick Start

1. Run the test
2. Check results

## Detailed Resources

- See documentation
- Check examples
"""


@pytest.fixture
def sample_skill_with_issues() -> str:
    """Sample skill content with validation issues."""
    return """---
name: test-skill
---

Some content without proper structure.
"""


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
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    return skill_dir


# ============================================================================
# Hook Testing Fixtures
# ============================================================================


@pytest.fixture
def skill_tool_env() -> dict[str, str]:
    """Given a complete Skill tool environment.

    Provides all environment variables that Claude Code sets
    when invoking a skill. Use this for testing hook execution.
    """
    return {
        "CLAUDE_TOOL_NAME": "Skill",
        "CLAUDE_TOOL_INPUT": '{"skill": "abstract:skill-auditor"}',
        "CLAUDE_SESSION_ID": "test-session-123",
    }


@pytest.fixture
def pre_skill_env(skill_tool_env: dict[str, str]) -> dict[str, str]:
    """Given environment for PreToolUse hook testing.

    Extends skill_tool_env with PreToolUse-specific variables.
    """
    return skill_tool_env


@pytest.fixture
def post_skill_env(skill_tool_env: dict[str, str]) -> dict[str, str]:
    """Given environment for PostToolUse hook testing.

    Extends skill_tool_env with PostToolUse-specific variables including
    tool output.
    """
    return {
        **skill_tool_env,
        "CLAUDE_TOOL_OUTPUT": "Skill validation completed successfully",
    }


@pytest.fixture
def skill_tool_env_failure(skill_tool_env: dict[str, str]) -> dict[str, str]:
    """Given a Skill tool environment indicating failure.

    Use this for testing failure detection and error handling.
    """
    return {
        **skill_tool_env,
        "CLAUDE_TOOL_OUTPUT": "Error: skill execution failed",
    }


@pytest.fixture
def skill_tool_env_partial(skill_tool_env: dict[str, str]) -> dict[str, str]:
    """Given a Skill tool environment indicating partial success.

    Use this for testing warning detection and partial outcomes.
    """
    return {
        **skill_tool_env,
        "CLAUDE_TOOL_OUTPUT": "Warning: some checks failed but execution continued",
    }


@pytest.fixture
def malformed_tool_env() -> dict[str, str]:
    """Given a malformed tool environment.

    Use this for testing error handling when input is invalid.
    """
    return {
        "CLAUDE_TOOL_NAME": "Skill",
        "CLAUDE_TOOL_INPUT": "invalid json{{{",
        "CLAUDE_SESSION_ID": "test-session-123",
    }


@pytest.fixture
def non_skill_env() -> dict[str, str]:
    """Given a non-Skill tool environment.

    Use this for testing that hooks only process Skill tool invocations.
    """
    return {
        "CLAUDE_TOOL_NAME": "Read",
        "CLAUDE_TOOL_INPUT": '{"file_path": "/tmp/test.txt"}',
        "CLAUDE_SESSION_ID": "test-session-123",
    }
