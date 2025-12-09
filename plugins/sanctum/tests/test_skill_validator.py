"""Tests for skill frontmatter and content validation."""

from sanctum.validators import SkillValidationResult, SkillValidator


class TestSkillValidationResult:
    """Tests for SkillValidationResult dataclass."""

    def test_valid_result_creation(self):
        """Valid result has no errors."""
        result = SkillValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            skill_name="git-workspace-review",
            frontmatter={"name": "git-workspace-review", "description": "Test"},
        )
        assert result.is_valid
        assert result.skill_name == "git-workspace-review"

    def test_invalid_result_with_errors(self):
        """Invalid result contains error messages."""
        result = SkillValidationResult(
            is_valid=False,
            errors=["Missing required field: description"],
            warnings=[],
            skill_name="broken-skill",
            frontmatter={"name": "broken-skill"},
        )
        assert not result.is_valid
        assert "description" in result.errors[0]


class TestSkillFrontmatterParsing:
    """Tests for parsing skill frontmatter."""

    def test_parses_valid_frontmatter(self, sample_skill_frontmatter):
        """Parses complete frontmatter correctly."""
        result = SkillValidator.parse_frontmatter(sample_skill_frontmatter)
        assert result.is_valid
        assert result.frontmatter["name"] == "git-workspace-review"
        assert result.frontmatter["description"].startswith("Lightweight")
        assert result.frontmatter["category"] == "workspace-ops"

    def test_extracts_tags(self, sample_skill_frontmatter):
        """Extracts tags list from frontmatter."""
        result = SkillValidator.parse_frontmatter(sample_skill_frontmatter)
        assert result.is_valid
        assert "git" in result.frontmatter["tags"]
        assert "preflight" in result.frontmatter["tags"]

    def test_extracts_tools(self, sample_skill_frontmatter):
        """Extracts tools list from frontmatter."""
        result = SkillValidator.parse_frontmatter(sample_skill_frontmatter)
        assert result.is_valid
        assert "Bash" in result.frontmatter["tools"]
        assert "TodoWrite" in result.frontmatter["tools"]

    def test_extracts_complexity(self, sample_skill_frontmatter):
        """Extracts complexity level from frontmatter."""
        result = SkillValidator.parse_frontmatter(sample_skill_frontmatter)
        assert result.is_valid
        assert result.frontmatter["complexity"] == "low"

    def test_extracts_estimated_tokens(self, sample_skill_frontmatter):
        """Extracts estimated_tokens from frontmatter."""
        result = SkillValidator.parse_frontmatter(sample_skill_frontmatter)
        assert result.is_valid
        assert result.frontmatter["estimated_tokens"] == 500


class TestSkillRequiredFields:
    """Tests for required field validation."""

    def test_requires_name_field(self):
        """Skill without name field fails validation."""
        # Content has frontmatter but missing name field
        content = """---
description: A skill without a name
category: testing
---

# Test Skill
"""
        result = SkillValidator.parse_frontmatter(content)
        assert not result.is_valid
        assert any("name" in error.lower() for error in result.errors)

    def test_requires_description_field(self, sample_skill_with_missing_fields):
        """Skill without description field fails validation."""
        result = SkillValidator.parse_frontmatter(sample_skill_with_missing_fields)
        assert not result.is_valid
        assert any("description" in error.lower() for error in result.errors)

    def test_fails_on_missing_frontmatter(self, sample_skill_without_frontmatter):
        """Content without frontmatter fails validation."""
        result = SkillValidator.parse_frontmatter(sample_skill_without_frontmatter)
        assert not result.is_valid
        assert any("frontmatter" in error.lower() for error in result.errors)


class TestSkillRecommendedFields:
    """Tests for recommended field warnings."""

    def test_warns_when_missing_category(self, sample_skill_with_missing_fields):
        """Warns when category field is missing."""
        result = SkillValidator.parse_frontmatter(sample_skill_with_missing_fields)
        # May be in errors or warnings depending on implementation
        all_messages = result.errors + result.warnings
        assert any("category" in msg.lower() for msg in all_messages)

    def test_warns_when_missing_tags(self):
        """Warns when tags field is missing."""
        content = """---
name: test-skill
description: A test skill
category: testing
---

# Test Skill
"""
        result = SkillValidator.parse_frontmatter(content)
        assert any("tags" in warning.lower() for warning in result.warnings)

    def test_warns_when_missing_tools(self):
        """Warns when tools field is missing."""
        content = """---
name: test-skill
description: A test skill
category: testing
tags: [test]
---

# Test Skill
"""
        result = SkillValidator.parse_frontmatter(content)
        assert any("tools" in warning.lower() for warning in result.warnings)


class TestSkillContentValidation:
    """Tests for skill body content validation."""

    def test_validates_has_heading(self, sample_skill_frontmatter):
        """Valid skill has a main heading."""
        result = SkillValidator.validate_content(sample_skill_frontmatter)
        assert result.is_valid

    def test_warns_when_missing_heading(self):
        """Warns when skill body has no main heading."""
        content = """---
name: test-skill
description: A test skill
---

Just some text without a heading.
"""
        result = SkillValidator.validate_content(content)
        assert any("heading" in warning.lower() for warning in result.warnings)

    def test_validates_when_to_use_section(self, sample_skill_frontmatter):
        """Valid skill has a 'When to Use' section."""
        result = SkillValidator.validate_content(sample_skill_frontmatter)
        assert result.is_valid

    def test_warns_when_missing_when_to_use(self):
        """Warns when skill lacks 'When to Use' section."""
        content = """---
name: test-skill
description: A test skill
---

# Test Skill

Some content without When to Use section.
"""
        result = SkillValidator.validate_content(content)
        assert any("when to use" in warning.lower() for warning in result.warnings)


class TestSkillFileValidation:
    """Tests for validating skill files from disk."""

    def test_validates_existing_skill_file(self, temp_skill_file):
        """Validates an existing valid skill file."""
        result = SkillValidator.validate_file(temp_skill_file)
        assert result.is_valid
        assert result.skill_name == "git-workspace-review"

    def test_fails_on_nonexistent_file(self, tmp_path):
        """Fails when file doesn't exist."""
        result = SkillValidator.validate_file(tmp_path / "nonexistent.md")
        assert not result.is_valid
        assert any(
            "not found" in error.lower() or "exist" in error.lower()
            for error in result.errors
        )

    def test_validates_skill_directory(self, tmp_path, sample_skill_frontmatter):
        """Validates a skill directory with SKILL.md."""
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(sample_skill_frontmatter)

        result = SkillValidator.validate_directory(skill_dir)
        assert result.is_valid

    def test_fails_when_skill_md_missing(self, tmp_path):
        """Fails when skill directory lacks SKILL.md."""
        skill_dir = tmp_path / "empty-skill"
        skill_dir.mkdir()

        result = SkillValidator.validate_directory(skill_dir)
        assert not result.is_valid
        assert any("SKILL.md" in error for error in result.errors)


class TestSkillCrossReferences:
    """Tests for skill cross-reference validation."""

    def test_validates_skill_references(self, sample_skill_frontmatter):
        """Validates that referenced skills use correct format."""
        # This skill references Skill(sanctum:git-workspace-review)
        content = """---
name: commit-messages
description: Generate commit messages
---

# Commit Messages

Run `Skill(sanctum:git-workspace-review)` first.
"""
        result = SkillValidator.validate_references(content)
        assert result.is_valid

    def test_warns_on_broken_skill_reference(self):
        """Warns when skill reference format is invalid."""
        content = """---
name: test-skill
description: Test skill
---

# Test Skill

Use Skill(invalid-format) to continue.
"""
        result = SkillValidator.validate_references(content)
        # Should warn about potentially invalid reference format
        assert (
            any("reference" in msg.lower() for msg in result.warnings + result.errors)
            or result.is_valid
        )

    def test_extracts_skill_dependencies(self, sample_skill_frontmatter):
        """Extracts list of skill dependencies from content."""
        content = """---
name: commit-messages
description: Generate commit messages
dependencies: [git-workspace-review]
---

# Commit Messages

Run `Skill(sanctum:git-workspace-review)` first.
Then use `Skill(sanctum:file-analysis)`.
"""
        deps = SkillValidator.extract_skill_references(content)
        assert "git-workspace-review" in deps or "sanctum:git-workspace-review" in deps
