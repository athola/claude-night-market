"""Tests for skill frontmatter and content validation."""

from sanctum.validators import SkillValidationResult, SkillValidator


class TestSkillValidationResult:
    """Tests for SkillValidationResult dataclass."""

    def test_valid_result_creation(self) -> None:

    def test_parses_valid_frontmatter(self, sample_skill_frontmatter) -> None:
        result = SkillValidator.parse_frontmatter(sample_skill_frontmatter)
        assert result.is_valid
        assert result.frontmatter["complexity"] == "low"

    def test_extracts_estimated_tokens(self, sample_skill_frontmatter) -> None:
description: A skill without a name
category: testing
---

# Test Skill
"""Test test requires name field."""
        result = SkillValidator.parse_frontmatter(sample_skill_with_missing_fields)
        assert not result.is_valid
        assert any("description" in error.lower() for error in result.errors)

    def test_fails_on_missing_frontmatter(
        self, sample_skill_without_frontmatter
    ) -> None:
        """Test test fails on missing frontmatter."""

    def test_warns_when_missing_category(
        self, sample_skill_with_missing_fields
    ) -> None:
        """Test test warns when missing category."""
        content = """---
name: test-skill
description: A test skill
category: testing
---

# Test Skill
"""Test test warns when missing category."""
        content = """---
name: test-skill
description: A test skill
category: testing
tags: [test]
---

# Test Skill
"""Test test warns when missing category."""

    def test_validates_has_heading(self, sample_skill_frontmatter) -> None:
name: test-skill
description: A test skill
---

Just some text without a heading.
"""Test test validates has heading."""
        result = SkillValidator.validate_content(sample_skill_frontmatter)
        assert result.is_valid

    def test_warns_when_missing_when_to_use(self) -> None:

    def test_validates_existing_skill_file(self, temp_skill_file) -> None:
        skill_dir = tmp_path / "empty-skill"
        skill_dir.mkdir()

        result = SkillValidator.validate_directory(skill_dir)
        assert not result.is_valid
        assert any("SKILL.md" in error for error in result.errors)


class TestSkillCrossReferences:
    """Tests for skill cross-reference validation."""

    def test_validates_skill_references(self, sample_skill_frontmatter) -> None:
        content = """---
name: test-skill
description: Test skill
---

# Test Skill

Use Skill(invalid-format) to continue.
"""Test test validates skill references."""
        content = """---
name: commit-messages
description: Generate commit messages
dependencies: [git-workspace-review]
---

# Commit Messages

Run `Skill(sanctum:git-workspace-review)` first.
Then use `Skill(sanctum:file-analysis)`.
"""Test test validates skill references."""
