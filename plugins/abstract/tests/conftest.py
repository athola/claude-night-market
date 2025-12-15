"""Pytest configuration and shared fixtures."""

import pytest


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
