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


class TestValidateReferences:
    """Tests for SkillValidator.validate_references()."""

    def test_returns_valid_for_well_formed_refs(self) -> None:
        content = """---
name: test-skill
---

Use Skill(other-plugin:my-skill) for that.
Also see Skill(simple-skill).
"""
        result = SkillValidator.validate_references(content)
        assert result.is_valid
        assert len(result.warnings) == 0

    def test_warns_on_malformed_skill_ref(self) -> None:
        content = """---
name: test-skill
---

Skill(bad ref with spaces)
"""
        result = SkillValidator.validate_references(content)
        assert any("bad ref with spaces" in w for w in result.warnings)

    def test_extracts_skill_name_from_frontmatter(self) -> None:
        content = """---
name: my-cool-skill
---

# Body
"""
        result = SkillValidator.validate_references(content)
        assert result.skill_name == "my-cool-skill"

    def test_no_frontmatter_returns_none_skill_name(self) -> None:
        content = "No frontmatter here."
        result = SkillValidator.validate_references(content)
        assert result.skill_name is None
        assert result.has_frontmatter is False


class TestExtractSkillReferences:
    """Tests for SkillValidator.extract_skill_references()."""

    def test_extracts_skill_refs_from_content(self) -> None:
        content = "Use Skill(foo:bar) and Skill(baz-qux)."
        refs = SkillValidator.extract_skill_references(content)
        assert "bar" in refs
        assert "baz-qux" in refs

    def test_includes_frontmatter_dependencies(self) -> None:
        content = """---
name: test-skill
dependencies:
  - plugin-a:skill-x
  - plugin-b:skill-y
---

Body text.
"""
        refs = SkillValidator.extract_skill_references(content)
        assert "plugin-a:skill-x" in refs
        assert "plugin-b:skill-y" in refs


class TestExtractDependencies:
    """Tests for SkillValidator.extract_dependencies()."""

    def test_extracts_deps_from_section(self) -> None:
        content = """---
name: test-skill
---

# Skill

## Dependencies
- plugin-a
- plugin-b
"""
        deps = SkillValidator.extract_dependencies(content)
        assert "plugin-a" in deps
        assert "plugin-b" in deps

    def test_returns_empty_when_no_deps_section(self) -> None:
        content = "---\nname: test\n---\n# No deps"
        deps = SkillValidator.extract_dependencies(content)
        assert deps == []
