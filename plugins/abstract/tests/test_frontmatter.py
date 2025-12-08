"""Tests for the consolidated frontmatter processing module."""

import pytest

from abstract.frontmatter import FrontmatterProcessor, FrontmatterResult


class TestFrontmatterResult:
    """Tests for FrontmatterResult dataclass."""

    def test_valid_result(self):
        """Test creation of valid FrontmatterResult."""
        result = FrontmatterResult(
            raw="---\nname: test\n---",
            parsed={"name": "test"},
            body="Content here",
            is_valid=True,
            missing_fields=[],
        )
        assert result.is_valid
        assert result.parsed == {"name": "test"}
        assert result.parse_error is None

    def test_invalid_result_with_missing_fields(self):
        """Test FrontmatterResult with missing required fields."""
        result = FrontmatterResult(
            raw="---\nname: test\n---",
            parsed={"name": "test"},
            body="Content",
            is_valid=False,
            missing_fields=["description"],
        )
        assert not result.is_valid
        assert "description" in result.missing_fields


class TestHasFrontmatter:
    """Tests for FrontmatterProcessor.has_frontmatter()."""

    def test_valid_frontmatter(self):
        """Test detection of valid frontmatter."""
        content = "---\nname: test\n---\nBody content"
        assert FrontmatterProcessor.has_frontmatter(content)

    def test_missing_opening_delimiter(self):
        """Test detection of missing opening delimiter."""
        content = "name: test\n---\nBody content"
        assert not FrontmatterProcessor.has_frontmatter(content)

    def test_missing_closing_delimiter(self):
        """Test detection of missing closing delimiter."""
        content = "---\nname: test\nBody content"
        assert not FrontmatterProcessor.has_frontmatter(content)

    def test_empty_content(self):
        """Test empty content."""
        assert not FrontmatterProcessor.has_frontmatter("")

    def test_only_dashes(self):
        """Test content with only opening dashes."""
        assert not FrontmatterProcessor.has_frontmatter("---\n")


class TestParse:
    """Tests for FrontmatterProcessor.parse()."""

    def test_valid_frontmatter_parsing(self):
        """Test parsing valid frontmatter."""
        content = (
            "---\nname: test-skill\ndescription: A test skill\n---\n\nBody content"
        )
        result = FrontmatterProcessor.parse(content)

        assert result.is_valid
        assert result.parsed["name"] == "test-skill"
        assert result.parsed["description"] == "A test skill"
        assert result.body == "Body content"
        assert result.missing_fields == []
        assert result.parse_error is None

    def test_missing_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "Just some body content"
        result = FrontmatterProcessor.parse(content)

        assert not result.is_valid
        assert result.raw == ""
        assert result.parsed == {}
        assert result.body == content
        assert "Missing frontmatter" in result.parse_error

    def test_incomplete_frontmatter(self):
        """Test parsing incomplete frontmatter."""
        content = "---\nname: test\nBody content without closing"
        result = FrontmatterProcessor.parse(content)

        assert not result.is_valid
        assert "Incomplete frontmatter" in result.parse_error

    def test_custom_required_fields(self):
        """Test parsing with custom required fields."""
        content = "---\nname: test\n---\nBody"
        required = ["name", "category"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert not result.is_valid
        assert "category" in result.missing_fields
        assert "name" not in result.missing_fields

    def test_empty_required_fields(self):
        """Test parsing with no required fields."""
        content = "---\nname: test\n---\nBody"
        result = FrontmatterProcessor.parse(content, required_fields=[])

        assert result.is_valid
        assert result.missing_fields == []

    def test_yaml_parsing_error(self):
        """Test handling of YAML parsing errors."""
        content = "---\nname: test\ninvalid: [unclosed\n---\nBody"
        result = FrontmatterProcessor.parse(content)

        assert not result.is_valid
        assert "YAML parsing error" in result.parse_error

    def test_empty_frontmatter_value(self):
        """Test that empty values are treated as missing."""
        content = "---\nname: test\ndescription:\n---\nBody"
        required = ["name", "description"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert not result.is_valid
        assert "description" in result.missing_fields


class TestValidate:
    """Tests for FrontmatterProcessor.validate()."""

    def test_all_fields_present(self):
        """Test validation with all required fields present."""
        frontmatter = {"name": "test", "description": "A test"}
        missing = FrontmatterProcessor.validate(frontmatter, ["name", "description"])
        assert missing == []

    def test_missing_fields(self):
        """Test validation with missing fields."""
        frontmatter = {"name": "test"}
        required = ["name", "description", "category"]
        missing = FrontmatterProcessor.validate(frontmatter, required)
        assert "description" in missing
        assert "category" in missing
        assert "name" not in missing

    def test_empty_field_value(self):
        """Test that empty field values are treated as missing."""
        frontmatter = {"name": "test", "description": ""}
        missing = FrontmatterProcessor.validate(frontmatter, ["name", "description"])
        assert "description" in missing

    def test_none_field_value(self):
        """Test that None field values are treated as missing."""
        frontmatter = {"name": "test", "description": None}
        missing = FrontmatterProcessor.validate(frontmatter, ["name", "description"])
        assert "description" in missing


class TestExtractRaw:
    """Tests for FrontmatterProcessor.extract_raw()."""

    def test_extract_with_frontmatter(self):
        """Test extraction with valid frontmatter."""
        content = "---\nname: test\n---\n\nBody content"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert raw == "---\nname: test\n---"
        assert body == "Body content"

    def test_extract_without_frontmatter(self):
        """Test extraction without frontmatter."""
        content = "Just body content"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert raw == ""
        assert body == content

    def test_extract_preserves_body_formatting(self):
        """Test that body formatting is preserved."""
        content = "---\nname: test\n---\n\n## Heading\n\nParagraph"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert "## Heading" in body
        assert "Paragraph" in body


class TestGetField:
    """Tests for FrontmatterProcessor.get_field()."""

    def test_get_existing_field(self):
        """Test getting an existing field."""
        content = "---\nname: test-skill\ndescription: A test\n---\nBody"
        value = FrontmatterProcessor.get_field(content, "name")
        assert value == "test-skill"

    def test_get_missing_field_with_default(self):
        """Test getting a missing field with default value."""
        content = "---\nname: test\n---\nBody"
        value = FrontmatterProcessor.get_field(
            content, "category", default="uncategorized"
        )
        assert value == "uncategorized"

    def test_get_missing_field_no_default(self):
        """Test getting a missing field without default."""
        content = "---\nname: test\n---\nBody"
        value = FrontmatterProcessor.get_field(content, "category")
        assert value is None


class TestParseFile:
    """Tests for FrontmatterProcessor.parse_file()."""

    def test_parse_existing_file(self, temp_skill_file):
        """Test parsing an existing file."""
        result = FrontmatterProcessor.parse_file(
            temp_skill_file, required_fields=["name"]
        )

        assert result.is_valid
        assert result.parsed["name"] == "test-skill"

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            FrontmatterProcessor.parse_file(tmp_path / "nonexistent.md")


class TestCheckMissingRecommended:
    """Tests for FrontmatterProcessor.check_missing_recommended()."""

    def test_all_recommended_present(self):
        """Test when all recommended fields are present."""
        frontmatter = {
            "category": "test",
            "tags": ["a", "b"],
            "dependencies": [],
            "tools": [],
        }
        missing = FrontmatterProcessor.check_missing_recommended(frontmatter)
        assert missing == []

    def test_some_recommended_missing(self):
        """Test when some recommended fields are missing."""
        frontmatter = {"category": "test"}
        missing = FrontmatterProcessor.check_missing_recommended(frontmatter)
        assert "tags" in missing
        assert "dependencies" in missing
        assert "tools" in missing
        assert "category" not in missing

    def test_custom_recommended_fields(self):
        """Test with custom recommended fields."""
        frontmatter = {"name": "test"}
        missing = FrontmatterProcessor.check_missing_recommended(
            frontmatter, recommended_fields=["author", "version"]
        )
        assert "author" in missing
        assert "version" in missing
