"""Tests for the consolidated frontmatter processing module."""

import pytest

from abstract.frontmatter import FrontmatterProcessor, FrontmatterResult


class TestFrontmatterResult:
    """Tests for FrontmatterResult dataclass."""

    def test_valid_result(self) -> None:
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

    def test_invalid_result_with_missing_fields(self) -> None:
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

    def test_valid_frontmatter(self) -> None:
        """Test detection of valid frontmatter."""
        content = "---\nname: test\n---\nBody content"
        assert FrontmatterProcessor.has_frontmatter(content)

    def test_missing_opening_delimiter(self) -> None:
        """Test detection of missing opening delimiter."""
        content = "name: test\n---\nBody content"
        assert not FrontmatterProcessor.has_frontmatter(content)

    def test_missing_closing_delimiter(self) -> None:
        """Test detection of missing closing delimiter."""
        content = "---\nname: test\nBody content"
        assert not FrontmatterProcessor.has_frontmatter(content)

    def test_empty_content(self) -> None:
        """Test empty content."""
        assert not FrontmatterProcessor.has_frontmatter("")

    def test_only_dashes(self) -> None:
        """Test content with only opening dashes."""
        assert not FrontmatterProcessor.has_frontmatter("---\n")


class TestParse:
    """Tests for FrontmatterProcessor.parse()."""

    def test_valid_frontmatter_parsing(self) -> None:
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

    def test_missing_frontmatter(self) -> None:
        """Test parsing content without frontmatter."""
        content = "Just some body content"
        result = FrontmatterProcessor.parse(content)

        assert not result.is_valid
        assert result.raw == ""
        assert result.parsed == {}
        assert result.body == content
        assert "Missing frontmatter" in result.parse_error

    def test_incomplete_frontmatter(self) -> None:
        """Test parsing incomplete frontmatter."""
        content = "---\nname: test\nBody content without closing"
        result = FrontmatterProcessor.parse(content)

        assert not result.is_valid
        assert "Incomplete frontmatter" in result.parse_error

    def test_custom_required_fields(self) -> None:
        """Test parsing with custom required fields."""
        content = "---\nname: test\n---\nBody"
        required = ["name", "category"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert not result.is_valid
        assert "category" in result.missing_fields
        assert "name" not in result.missing_fields

    def test_empty_required_fields(self) -> None:
        """Test parsing with no required fields."""
        content = "---\nname: test\n---\nBody"
        result = FrontmatterProcessor.parse(content, required_fields=[])

        assert result.is_valid
        assert result.missing_fields == []

    def test_yaml_parsing_error(self) -> None:
        """Test handling of YAML parsing errors."""
        content = "---\nname: test\ninvalid: [unclosed\n---\nBody"
        result = FrontmatterProcessor.parse(content)

        assert not result.is_valid
        assert "YAML parsing error" in result.parse_error

    def test_empty_frontmatter_value(self) -> None:
        """Test that empty values are treated as missing."""
        content = "---\nname: test\ndescription:\n---\nBody"
        required = ["name", "description"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert not result.is_valid
        assert "description" in result.missing_fields


class TestValidate:
    """Tests for FrontmatterProcessor.validate()."""

    def test_all_fields_present(self) -> None:
        """Test validation with all required fields present."""
        frontmatter = {"name": "test", "description": "A test"}
        missing = FrontmatterProcessor.validate(frontmatter, ["name", "description"])
        assert missing == []

    def test_missing_fields(self) -> None:
        """Test validation with missing fields."""
        frontmatter = {"name": "test"}
        required = ["name", "description", "category"]
        missing = FrontmatterProcessor.validate(frontmatter, required)
        assert "description" in missing
        assert "category" in missing
        assert "name" not in missing

    def test_empty_field_value(self) -> None:
        """Test that empty field values are treated as missing."""
        frontmatter = {"name": "test", "description": ""}
        missing = FrontmatterProcessor.validate(frontmatter, ["name", "description"])
        assert "description" in missing

    def test_none_field_value(self) -> None:
        """Test that None field values are treated as missing."""
        frontmatter = {"name": "test", "description": None}
        missing = FrontmatterProcessor.validate(frontmatter, ["name", "description"])
        assert "description" in missing


class TestExtractRaw:
    """Tests for FrontmatterProcessor.extract_raw()."""

    def test_extract_with_frontmatter(self) -> None:
        """Test extraction with valid frontmatter."""
        content = "---\nname: test\n---\n\nBody content"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert raw == "---\nname: test\n---"
        assert body == "Body content"

    def test_extract_without_frontmatter(self) -> None:
        """Test extraction without frontmatter."""
        content = "Just body content"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert raw == ""
        assert body == content

    def test_extract_preserves_body_formatting(self) -> None:
        """Test that body formatting is preserved."""
        content = "---\nname: test\n---\n\n## Heading\n\nParagraph"
        _raw, body = FrontmatterProcessor.extract_raw(content)

        assert "## Heading" in body
        assert "Paragraph" in body


class TestGetField:
    """Tests for FrontmatterProcessor.get_field()."""

    def test_get_existing_field(self) -> None:
        """Test getting an existing field."""
        content = "---\nname: test-skill\ndescription: A test\n---\nBody"
        value = FrontmatterProcessor.get_field(content, "name")
        assert value == "test-skill"

    def test_get_missing_field_with_default(self) -> None:
        """Test getting a missing field with default value."""
        content = "---\nname: test\n---\nBody"
        value = FrontmatterProcessor.get_field(
            content,
            "category",
            default="uncategorized",
        )
        assert value == "uncategorized"

    def test_get_missing_field_no_default(self) -> None:
        """Test getting a missing field without default."""
        content = "---\nname: test\n---\nBody"
        value = FrontmatterProcessor.get_field(content, "category")
        assert value is None


class TestParseFile:
    """Tests for FrontmatterProcessor.parse_file()."""

    def test_parse_existing_file(self, temp_skill_file) -> None:
        """Test parsing an existing file."""
        result = FrontmatterProcessor.parse_file(
            temp_skill_file,
            required_fields=["name"],
        )

        assert result.is_valid
        assert result.parsed["name"] == "test-skill"

    def test_parse_nonexistent_file(self, tmp_path) -> None:
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            FrontmatterProcessor.parse_file(tmp_path / "nonexistent.md")


class TestCheckMissingRecommended:
    """Tests for FrontmatterProcessor.check_missing_recommended()."""

    def test_all_recommended_present(self) -> None:
        """Test when all recommended fields are present."""
        frontmatter = {
            "category": "test",
            "tags": ["a", "b"],
            "dependencies": [],
            "tools": [],
        }
        missing = FrontmatterProcessor.check_missing_recommended(frontmatter)
        assert missing == []

    def test_some_recommended_missing(self) -> None:
        """Test when some recommended fields are missing."""
        frontmatter = {"category": "test"}
        missing = FrontmatterProcessor.check_missing_recommended(frontmatter)
        assert "tags" in missing
        assert "dependencies" in missing
        assert "tools" in missing
        assert "category" not in missing

    def test_custom_recommended_fields(self) -> None:
        """Test with custom recommended fields."""
        frontmatter = {"name": "test"}
        missing = FrontmatterProcessor.check_missing_recommended(
            frontmatter,
            recommended_fields=["author", "version"],
        )
        assert "author" in missing
        assert "version" in missing


class TestValidate210Fields:
    """Tests for Claude Code 2.1.0+ field validation."""

    def test_valid_context_fork(self) -> None:
        """Test valid context: fork field."""
        frontmatter = {"context": "fork"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []

    def test_invalid_context_value(self) -> None:
        """Test invalid context value."""
        frontmatter = {"context": "invalid"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "Invalid 'context' value" in errors[0]

    def test_valid_user_invocable_boolean(self) -> None:
        """Test valid user-invocable boolean field."""
        frontmatter = {"user-invocable": False}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []

    def test_invalid_user_invocable_string(self) -> None:
        """Test invalid user-invocable non-boolean."""
        frontmatter = {"user-invocable": "false"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "'user-invocable' must be boolean" in errors[0]

    def test_valid_hooks_structure(self) -> None:
        """Test valid hooks structure."""
        frontmatter = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "command": "echo test"},
                ],
                "Stop": [
                    {"command": "echo done"},
                ],
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []

    def test_hooks_with_once_true(self) -> None:
        """Test hooks with once: true option."""
        frontmatter = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "command": "echo test", "once": True},
                ],
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []

    def test_hooks_with_once_invalid_type(self) -> None:
        """Test hooks with invalid once value type."""
        frontmatter = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "command": "echo test", "once": "true"},
                ],
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "'once' must be boolean" in errors[0]

    def test_invalid_hook_event_type(self) -> None:
        """Test invalid hook event type."""
        frontmatter = {
            "hooks": {
                "InvalidEvent": [
                    {"command": "echo test"},
                ],
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "Invalid hook event type: InvalidEvent" in errors[0]

    def test_hooks_missing_command(self) -> None:
        """Test hook entry missing command."""
        frontmatter = {
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash"},  # Missing 'command'
                ],
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "missing 'command'" in errors[0]

    def test_hooks_not_a_dict(self) -> None:
        """Test hooks that isn't a dictionary."""
        frontmatter = {"hooks": "invalid"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "'hooks' must be a dictionary" in errors[0]

    def test_hook_entries_not_a_list(self) -> None:
        """Test hook entries that aren't a list."""
        frontmatter = {
            "hooks": {
                "PreToolUse": {"command": "echo test"},  # Should be a list
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "must be a list" in errors[0]

    def test_hook_entry_not_a_dict(self) -> None:
        """Test hook entry that isn't a dictionary."""
        frontmatter = {
            "hooks": {
                "PreToolUse": [
                    "echo test",  # Should be a dict with 'command' key
                ],
            }
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "must be a dict" in errors[0]

    def test_valid_permission_mode(self) -> None:
        """Test valid permissionMode values."""
        valid_modes = [
            "default",
            "acceptEdits",
            "dontAsk",
            "bypassPermissions",
            "plan",
            "ignore",
        ]
        for mode in valid_modes:
            frontmatter = {"permissionMode": mode}
            errors = FrontmatterProcessor.validate_210_fields(frontmatter)
            assert errors == [], f"Mode {mode} should be valid"

    def test_invalid_permission_mode(self) -> None:
        """Test invalid permissionMode value."""
        frontmatter = {"permissionMode": "invalid"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "Invalid 'permissionMode'" in errors[0]

    def test_valid_allowed_tools_list(self) -> None:
        """Test valid allowed-tools as YAML list."""
        frontmatter = {
            "allowed-tools": ["Read", "Grep", "Bash(npm *)"],
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []

    def test_valid_allowed_tools_string(self) -> None:
        """Test valid allowed-tools as comma-separated string."""
        frontmatter = {"allowed-tools": "Read, Grep, Bash(npm:*)"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []

    def test_invalid_allowed_tools_type(self) -> None:
        """Test invalid allowed-tools type."""
        frontmatter = {"allowed-tools": 123}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert "'allowed-tools' must be a list or string" in errors[0]

    def test_multiple_validation_errors(self) -> None:
        """Test frontmatter with multiple errors."""
        frontmatter = {
            "context": "invalid",
            "user-invocable": "yes",
            "permissionMode": "wrong",
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 3

    def test_no_210_fields(self) -> None:
        """Test frontmatter without any 2.1.0 fields."""
        frontmatter = {"name": "test", "description": "A test skill"}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert errors == []


class TestHas210Features:
    """Tests for detecting Claude Code 2.1.0+ features."""

    def test_has_context_fork(self) -> None:
        """Test detection of context: fork."""
        frontmatter = {"name": "test", "context": "fork"}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_has_user_invocable(self) -> None:
        """Test detection of user-invocable field."""
        frontmatter = {"name": "test", "user-invocable": False}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_has_hooks(self) -> None:
        """Test detection of hooks field."""
        frontmatter = {"name": "test", "hooks": {"Stop": []}}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_has_agent_field(self) -> None:
        """Test detection of agent field."""
        frontmatter = {"name": "test", "agent": "python-tester"}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_has_skills_field(self) -> None:
        """Test detection of skills field (agent feature)."""
        frontmatter = {"name": "test", "skills": ["skill1", "skill2"]}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_has_escalation_field(self) -> None:
        """Test detection of escalation field."""
        frontmatter = {"name": "test", "escalation": {"to": "opus"}}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_has_permission_mode(self) -> None:
        """Test detection of permissionMode field."""
        frontmatter = {"name": "test", "permissionMode": "acceptEdits"}
        assert FrontmatterProcessor.has_210_features(frontmatter)

    def test_no_210_features(self) -> None:
        """Test frontmatter without 2.1.0 features."""
        frontmatter = {
            "name": "test",
            "description": "A test",
            "category": "test",
            "tags": ["test"],
        }
        assert not FrontmatterProcessor.has_210_features(frontmatter)

    def test_empty_frontmatter(self) -> None:
        """Test empty frontmatter."""
        assert not FrontmatterProcessor.has_210_features({})


class TestAllHookEventTypes:
    """Tests to verify all hook event types are recognized."""

    def test_all_valid_hook_events(self) -> None:
        """Test all documented hook event types are valid."""
        expected_events = [
            "PreToolUse",
            "PostToolUse",
            "UserPromptSubmit",
            "PermissionRequest",
            "Notification",
            "Stop",
            "SubagentStop",
            "PreCompact",
            "SessionStart",
            "SessionEnd",
        ]
        assert FrontmatterProcessor.VALID_HOOK_EVENTS == expected_events

    def test_each_hook_event_type_validates(self) -> None:
        """Test each hook event type validates correctly."""
        for event_type in FrontmatterProcessor.VALID_HOOK_EVENTS:
            frontmatter = {
                "hooks": {
                    event_type: [{"command": "echo test"}],
                }
            }
            errors = FrontmatterProcessor.validate_210_fields(frontmatter)
            assert errors == [], f"Event type {event_type} should be valid"


class TestConstantDefinitions:
    """Tests to verify constant definitions are correct."""

    def test_skill_fields_defined(self) -> None:
        """Test 2.1.0 skill fields are defined."""
        expected_fields = [
            "context",
            "agent",
            "user-invocable",
            "hooks",
            "allowed-tools",
            "model",
        ]
        assert FrontmatterProcessor.CLAUDE_CODE_210_SKILL_FIELDS == expected_fields

    def test_agent_fields_defined(self) -> None:
        """Test 2.1.0 agent fields are defined."""
        expected_fields = [
            "hooks",
            "skills",
            "escalation",
            "permissionMode",
        ]
        assert FrontmatterProcessor.CLAUDE_CODE_210_AGENT_FIELDS == expected_fields

    def test_permission_modes_defined(self) -> None:
        """Test valid permission modes are defined."""
        expected_modes = [
            "default",
            "acceptEdits",
            "dontAsk",
            "bypassPermissions",
            "plan",
            "ignore",
        ]
        assert FrontmatterProcessor.VALID_PERMISSION_MODES == expected_modes
