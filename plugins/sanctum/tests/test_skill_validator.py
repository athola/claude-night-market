# ruff: noqa: D101,D102,D103,PLR2004,E501
"""Tests for skill validator helpers."""

from pathlib import Path

import pytest

from sanctum.validators import SkillValidationResult, SkillValidator


def test_valid_result_creation() -> None:
    result = SkillValidationResult(
        is_valid=True, errors=[], warnings=[], frontmatter={}
    )
    assert result.is_valid is True


def test_parses_valid_frontmatter() -> None:
    frontmatter = """---
name: test-skill
description: A test skill
complexity: low
---
"""
    result = SkillValidator.parse_frontmatter(frontmatter)
    assert result.is_valid
    assert result.frontmatter["complexity"] == "low"


def test_fails_on_missing_frontmatter() -> None:
    content = "# Skill without frontmatter"
    result = SkillValidator.validate_content(content)
    assert result.is_valid is False


def test_warns_when_missing_category() -> None:
    content = """---
name: test-skill
description: A test skill
---

# Test Skill
"""
    result = SkillValidator.parse_frontmatter(content)
    assert any("category" in warning.lower() for warning in result.warnings)


@pytest.mark.bdd
def test_validates_has_heading() -> None:
    content = """---
name: test-skill
description: A test skill
category: testing
---

# Test Skill
## When to Use
Use when testing validators.
"""
    result = SkillValidator.validate_content(content)
    assert result.is_valid
    assert result.has_workflow is True


@pytest.mark.bdd
def test_validate_directory_missing_skill_file(tmp_path: Path) -> None:
    skill_dir = tmp_path / "missing-skill"
    skill_dir.mkdir()

    result = SkillValidator.validate_directory(skill_dir)

    assert result.is_valid is False
    assert any("SKILL.md" in err for err in result.errors)


@pytest.mark.bdd
def test_validate_directory_success(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        """---
name: demo-skill
description: Demo skill
category: testing
tags: [demo]
tools: [Bash]
---

# Demo Skill
## When to Use
Always demo.
"""
    )

    result = SkillValidator.validate_directory(skill_dir)

    assert result.is_valid is True
    assert result.skill_name == "demo-skill"
