"""Tests for command file validation."""

from sanctum.validators import CommandValidationResult, CommandValidator


class TestCommandValidationResult:
    """Tests for CommandValidationResult dataclass."""

    def test_valid_result_creation(self) -> None:
        """Valid result has no errors."""
        result = CommandValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            command_name="commit-msg",
            description="Draft a commit message",
        )
        assert result.is_valid
        assert result.command_name == "commit-msg"

    def test_invalid_result_with_errors(self) -> None:
        """Invalid result contains error messages."""
        result = CommandValidationResult(
            is_valid=False,
            errors=["Missing required description"],
            warnings=[],
            command_name="broken-cmd",
            description=None,
        )
        assert not result.is_valid
        assert "description" in result.errors[0].lower()


class TestCommandFrontmatterParsing:
    """Tests for command frontmatter parsing."""

    def test_parses_valid_command(self, sample_command_content) -> None:
        """Parses valid command frontmatter correctly."""
        result = CommandValidator.parse_frontmatter(sample_command_content)
        assert result.is_valid
        assert "Conventional Commit" in result.description

    def test_extracts_description(self, sample_command_content) -> None:
        """Extracts description from frontmatter."""
        result = CommandValidator.parse_frontmatter(sample_command_content)
        assert result.is_valid
        assert result.description is not None
        assert len(result.description) > 0


class TestCommandRequiredFields:
    """Tests for required command fields."""

    def test_requires_description(self, sample_command_without_description) -> None:
        """Command without description fails validation."""
        result = CommandValidator.parse_frontmatter(sample_command_without_description)
        assert not result.is_valid
        assert any("description" in error.lower() for error in result.errors)

    def test_allows_minimal_frontmatter(self) -> None:
        """Command with only description passes."""
        content = """---
description: A minimal command
---

# Command

Do something.
"""
        result = CommandValidator.parse_frontmatter(content)
        assert result.is_valid

    def test_fails_on_missing_frontmatter(self) -> None:
        """Command without frontmatter fails."""
        content = """# Command Without Frontmatter

This has no YAML frontmatter.
"""
        result = CommandValidator.parse_frontmatter(content)
        assert not result.is_valid
        assert any("frontmatter" in error.lower() for error in result.errors)


class TestCommandContentValidation:
    """Tests for command body content validation."""

    def test_validates_has_heading(self, sample_command_content) -> None:
        """Valid command has a main heading."""
        result = CommandValidator.validate_content(sample_command_content)
        assert result.is_valid

    def test_warns_when_missing_heading(self) -> None:
        """Warns when command body has no main heading."""
        content = """---
description: A command
---

Just some text without a heading.
"""
        result = CommandValidator.validate_content(content)
        assert any("heading" in warning.lower() for warning in result.warnings)

    def test_validates_skill_references(self, sample_command_content) -> None:
        """Validates that skill references are properly formatted."""
        result = CommandValidator.validate_content(sample_command_content)
        assert result.is_valid


class TestCommandFileValidation:
    """Tests for validating command files from disk."""

    def test_validates_existing_command_file(self, temp_command_file) -> None:
        """Validates an existing valid command file."""
        result = CommandValidator.validate_file(temp_command_file)
        assert result.is_valid

    def test_fails_on_nonexistent_file(self, tmp_path) -> None:
        """Fails when file doesn't exist."""
        result = CommandValidator.validate_file(tmp_path / "nonexistent.md")
        assert not result.is_valid
        assert any(
            "not found" in error.lower() or "exist" in error.lower()
            for error in result.errors
        )

    def test_extracts_command_name_from_filename(self, tmp_path) -> None:
        """Extracts command name from filename when no heading present."""
        # Create command without main heading - name comes from filename
        content = """---
description: A command without heading
---

Just some content without a main heading.
"""
        cmd_file = tmp_path / "commands" / "my-command.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text(content)

        result = CommandValidator.validate_file(cmd_file)
        assert result.is_valid
        assert result.command_name == "my-command"


class TestCommandSkillReferences:
    """Tests for extracting and validating skill references in commands."""

    def test_extracts_skill_references(self, sample_command_content) -> None:
        """Extracts skill references from command content."""
        refs = CommandValidator.extract_skill_references(sample_command_content)
        assert "git-workspace-review" in refs or "sanctum:git-workspace-review" in refs
        assert "commit-messages" in refs or "sanctum:commit-messages" in refs

    def test_returns_empty_when_no_references(self) -> None:
        """Returns empty list when no skill references."""
        content = """---
description: A simple command
---

# Simple Command

Just run `git status`.
"""
        refs = CommandValidator.extract_skill_references(content)
        assert refs == []

    def test_validates_skill_references_exist(
        self,
        temp_full_plugin,
        sample_command_content,
    ) -> None:
        """Validates that referenced skills exist in the plugin."""
        result = CommandValidator.validate_skill_references(
            sample_command_content,
            temp_full_plugin,
        )
        assert result.is_valid
