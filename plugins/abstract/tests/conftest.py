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


# ============================================================================
# Budget Validation Testing Fixtures
# ============================================================================


@pytest.fixture
def temp_plugin_structure(tmp_path):
    """Create a temporary plugin structure for testing validate_budget.py.

    Given a temporary directory with:
    - test-plugin-a with 2 skills and 1 command
    - test-plugin-b with 1 skill (verbose description > 150 chars)
    """
    plugins_dir = tmp_path / "plugins"

    # Create test-plugin-a with skills
    plugin_a = plugins_dir / "test-plugin-a"
    skill_a1 = plugin_a / "skills" / "skill-one"
    skill_a1.mkdir(parents=True)
    (skill_a1 / "SKILL.md").write_text("""---
name: skill-one
description: A short description for skill one
category: testing
---

# Skill One

Content here.
""")

    skill_a2 = plugin_a / "skills" / "skill-two"
    skill_a2.mkdir(parents=True)
    (skill_a2 / "SKILL.md").write_text("""---
name: skill-two
description: |
  A multi-line description
  that spans multiple lines
  for testing purposes
category: testing
---

# Skill Two

Content here.
""")

    # Create test-plugin-a with commands
    commands_a = plugin_a / "commands"
    commands_a.mkdir(parents=True)
    (commands_a / "test-command.md").write_text("""---
name: test-command
description: A command description
---

# Test Command

Usage info.
""")

    # Create test-plugin-b with verbose description
    plugin_b = plugins_dir / "test-plugin-b"
    skill_b1 = plugin_b / "skills" / "verbose-skill"
    skill_b1.mkdir(parents=True)
    # Create a description that exceeds 150 chars
    long_desc = "A" * 200
    (skill_b1 / "SKILL.md").write_text(f"""---
name: verbose-skill
description: {long_desc}
category: testing
---

# Verbose Skill

Content here.
""")

    return tmp_path


@pytest.fixture
def empty_plugin_structure(tmp_path):
    """Create an empty plugin structure (no skills/commands).

    Given a temporary directory with a plugins/ folder but no content.
    """
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def skill_content_single_line():
    """Sample skill with single-line description."""
    return """---
name: test-skill
description: A simple single-line description
category: testing
tags:
  - unit-test
---

# Test Skill

Content here.
"""


@pytest.fixture
def skill_content_multi_line():
    """Sample skill with multi-line description."""
    return """---
name: test-skill
description: |
  A multi-line description
  that spans several lines
  for comprehensive testing
category: testing
---

# Test Skill

Content here.
"""


@pytest.fixture
def skill_content_no_description():
    """Sample skill without description field."""
    return """---
name: test-skill
category: testing
---

# Test Skill

Content here.
"""


@pytest.fixture
def skill_content_no_name():
    """Sample skill without name field."""
    return """---
description: A description without name
category: testing
---

# Test Skill

Content here.
"""
