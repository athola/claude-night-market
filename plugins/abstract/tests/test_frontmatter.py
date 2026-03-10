"""Tests for the consolidated frontmatter processing module."""

from __future__ import annotations

import pytest

from abstract.frontmatter import FrontmatterProcessor, FrontmatterResult


class TestFrontmatterResult:
    """Tests for FrontmatterResult dataclass."""

    def test_valid_result(self) -> None:
        """Given valid metadata, FrontmatterResult marks is_valid True."""
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
        """Given missing required fields, FrontmatterResult marks is_valid False."""
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

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            ("---\nname: test\n---\nBody content", True),
            ("name: test\n---\nBody content", False),
            ("---\nname: test\nBody content", False),
            ("", False),
            ("---\n", False),
        ],
        ids=[
            "valid-frontmatter",
            "missing-opening",
            "missing-closing",
            "empty-content",
            "only-dashes",
        ],
    )
    def test_frontmatter_detection(self, content: str, expected: bool) -> None:
        """Given content, has_frontmatter returns correct boolean."""
        assert FrontmatterProcessor.has_frontmatter(content) is expected


class TestParse:
    """Tests for FrontmatterProcessor.parse()."""

    def test_valid_frontmatter_parsing(self) -> None:
        """Given valid frontmatter, parse returns correct fields and body."""
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

    @pytest.mark.parametrize(
        ("content", "error_fragment"),
        [
            ("Just some body content", "Missing frontmatter"),
            ("---\nname: test\nBody content without closing", "Incomplete frontmatter"),
            ("---\nname: test\ninvalid: [unclosed\n---\nBody", "YAML parsing error"),
        ],
        ids=[
            "missing-frontmatter",
            "incomplete-frontmatter",
            "yaml-parsing-error",
        ],
    )
    def test_invalid_content_sets_parse_error(
        self, content: str, error_fragment: str
    ) -> None:
        """Given invalid content, parse sets appropriate parse_error."""
        result = FrontmatterProcessor.parse(content)
        assert not result.is_valid
        assert error_fragment in result.parse_error

    def test_custom_required_fields(self) -> None:
        """Given custom required fields, missing ones are reported."""
        content = "---\nname: test\n---\nBody"
        required = ["name", "category"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert not result.is_valid
        assert "category" in result.missing_fields
        assert "name" not in result.missing_fields

    def test_empty_required_fields(self) -> None:
        """Given no required fields, any frontmatter is valid."""
        content = "---\nname: test\n---\nBody"
        result = FrontmatterProcessor.parse(content, required_fields=[])

        assert result.is_valid
        assert result.missing_fields == []

    def test_empty_frontmatter_value(self) -> None:
        """Given empty values, they are treated as missing."""
        content = "---\nname: test\ndescription:\n---\nBody"
        required = ["name", "description"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert not result.is_valid
        assert "description" in result.missing_fields


class TestValidate:
    """Tests for FrontmatterProcessor.validate()."""

    @pytest.mark.parametrize(
        ("frontmatter", "required", "expected_missing"),
        [
            (
                {"name": "test", "description": "A test"},
                ["name", "description"],
                [],
            ),
            (
                {"name": "test"},
                ["name", "description", "category"],
                ["description", "category"],
            ),
            (
                {"name": "test", "description": ""},
                ["name", "description"],
                ["description"],
            ),
            (
                {"name": "test", "description": None},
                ["name", "description"],
                ["description"],
            ),
        ],
        ids=[
            "all-present",
            "multiple-missing",
            "empty-value-treated-missing",
            "none-value-treated-missing",
        ],
    )
    def test_validate_missing_fields(
        self,
        frontmatter: dict,
        required: list,
        expected_missing: list,
    ) -> None:
        """Given frontmatter and required fields, correct missing list returned."""
        missing = FrontmatterProcessor.validate(frontmatter, required)
        assert sorted(missing) == sorted(expected_missing)


class TestExtractRaw:
    """Tests for FrontmatterProcessor.extract_raw()."""

    def test_extract_with_frontmatter(self) -> None:
        """Given content with frontmatter, raw and body are split correctly."""
        content = "---\nname: test\n---\n\nBody content"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert raw == "---\nname: test\n---"
        assert body == "Body content"

    def test_extract_without_frontmatter(self) -> None:
        """Given content without frontmatter, raw is empty and body is full content."""
        content = "Just body content"
        raw, body = FrontmatterProcessor.extract_raw(content)

        assert raw == ""
        assert body == content

    def test_extract_preserves_body_formatting(self) -> None:
        """Given content with headings, body formatting is preserved."""
        content = "---\nname: test\n---\n\n## Heading\n\nParagraph"
        _raw, body = FrontmatterProcessor.extract_raw(content)

        assert "## Heading" in body
        assert "Paragraph" in body


class TestGetField:
    """Tests for FrontmatterProcessor.get_field()."""

    @pytest.mark.parametrize(
        ("content", "field", "default", "expected"),
        [
            (
                "---\nname: test-skill\ndescription: A test\n---\nBody",
                "name",
                None,
                "test-skill",
            ),
            (
                "---\nname: test\n---\nBody",
                "category",
                "uncategorized",
                "uncategorized",
            ),
            (
                "---\nname: test\n---\nBody",
                "category",
                None,
                None,
            ),
        ],
        ids=[
            "existing-field",
            "missing-with-default",
            "missing-no-default",
        ],
    )
    def test_get_field_values(
        self, content: str, field: str, default, expected
    ) -> None:
        """Given content and field name, correct value is returned."""
        value = FrontmatterProcessor.get_field(content, field, default=default)
        assert value == expected


class TestParseFile:
    """Tests for FrontmatterProcessor.parse_file()."""

    def test_parse_existing_file(self, temp_skill_file) -> None:
        """Given an existing skill file, parsing succeeds."""
        result = FrontmatterProcessor.parse_file(
            temp_skill_file,
            required_fields=["name"],
        )

        assert result.is_valid
        assert result.parsed["name"] == "test-skill"

    def test_parse_nonexistent_file(self, tmp_path) -> None:
        """Given a nonexistent path, FileNotFoundError is raised."""
        with pytest.raises(FileNotFoundError):
            FrontmatterProcessor.parse_file(tmp_path / "nonexistent.md")


class TestCheckMissingRecommended:
    """Tests for FrontmatterProcessor.check_missing_recommended()."""

    @pytest.mark.parametrize(
        ("frontmatter", "custom_fields", "expected_missing"),
        [
            (
                {"category": "test", "tags": ["a"], "dependencies": [], "tools": []},
                None,
                [],
            ),
            (
                {"category": "test"},
                None,
                ["tags", "dependencies", "tools"],
            ),
            (
                {"name": "test"},
                ["author", "version"],
                ["author", "version"],
            ),
        ],
        ids=[
            "all-present",
            "some-missing",
            "custom-recommended-fields",
        ],
    )
    def test_check_missing_recommended(
        self, frontmatter, custom_fields, expected_missing
    ) -> None:
        """Given frontmatter, missing recommended fields are reported."""
        kwargs = {}
        if custom_fields is not None:
            kwargs["recommended_fields"] = custom_fields
        missing = FrontmatterProcessor.check_missing_recommended(frontmatter, **kwargs)
        assert sorted(missing) == sorted(expected_missing)


class TestValidate210Fields:
    """Tests for Claude Code 2.1.0+ field validation."""

    @pytest.mark.parametrize(
        ("frontmatter", "expected_error_count", "error_fragment"),
        [
            ({"context": "fork"}, 0, ""),
            ({"context": "invalid"}, 1, "Invalid 'context' value"),
            ({"user-invocable": False}, 0, ""),
            ({"user-invocable": "false"}, 1, "'user-invocable' must be boolean"),
            ({"permissionMode": "default"}, 0, ""),
            ({"permissionMode": "acceptEdits"}, 0, ""),
            ({"permissionMode": "dontAsk"}, 0, ""),
            ({"permissionMode": "bypassPermissions"}, 0, ""),
            ({"permissionMode": "plan"}, 0, ""),
            ({"permissionMode": "ignore"}, 0, ""),
            ({"permissionMode": "invalid"}, 1, "Invalid 'permissionMode'"),
            ({"allowed-tools": ["Read", "Grep"]}, 0, ""),
            ({"allowed-tools": "Read, Grep"}, 0, ""),
            ({"allowed-tools": 123}, 1, "'allowed-tools' must be a list or string"),
            ({"name": "test", "description": "A test skill"}, 0, ""),
        ],
        ids=[
            "valid-context-fork",
            "invalid-context",
            "valid-user-invocable",
            "invalid-user-invocable-string",
            "permission-default",
            "permission-acceptEdits",
            "permission-dontAsk",
            "permission-bypassPermissions",
            "permission-plan",
            "permission-ignore",
            "invalid-permission-mode",
            "valid-allowed-tools-list",
            "valid-allowed-tools-string",
            "invalid-allowed-tools-type",
            "no-210-fields",
        ],
    )
    def test_field_validation(
        self, frontmatter, expected_error_count, error_fragment
    ) -> None:
        """Given frontmatter with 2.1.0 fields, correct errors are reported."""
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == expected_error_count
        if error_fragment:
            assert any(error_fragment in e for e in errors)

    def test_valid_hooks_structure(self) -> None:
        """Given valid hooks dict with entries, no errors are returned."""
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

    @pytest.mark.parametrize(
        ("hooks_value", "error_fragment"),
        [
            ("invalid", "'hooks' must be a dictionary"),
            (
                {"PreToolUse": {"command": "echo test"}},
                "must be a list",
            ),
            (
                {"PreToolUse": ["echo test"]},
                "must be a dict",
            ),
            (
                {"PreToolUse": [{"matcher": "Bash"}]},
                "missing 'command'",
            ),
            (
                {"InvalidEvent": [{"command": "echo test"}]},
                "Invalid hook event type: InvalidEvent",
            ),
        ],
        ids=[
            "hooks-not-dict",
            "entries-not-list",
            "entry-not-dict",
            "missing-command",
            "invalid-event-type",
        ],
    )
    def test_invalid_hooks_structures(self, hooks_value, error_fragment) -> None:
        """Given invalid hooks structure, correct error is returned."""
        frontmatter = {"hooks": hooks_value}
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 1
        assert error_fragment in errors[0]

    def test_hooks_with_once_true(self) -> None:
        """Given hooks with once: true, no errors are returned."""
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
        """Given hooks with once as a string, an error is returned."""
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

    def test_multiple_validation_errors(self) -> None:
        """Given frontmatter with multiple errors, all are reported."""
        frontmatter = {
            "context": "invalid",
            "user-invocable": "yes",
            "permissionMode": "wrong",
        }
        errors = FrontmatterProcessor.validate_210_fields(frontmatter)
        assert len(errors) == 3


class TestHas210Features:
    """Tests for detecting Claude Code 2.1.0+ features."""

    @pytest.mark.parametrize(
        ("frontmatter", "expected"),
        [
            ({"name": "test", "context": "fork"}, True),
            ({"name": "test", "user-invocable": False}, True),
            ({"name": "test", "hooks": {"Stop": []}}, True),
            ({"name": "test", "agent": "python-tester"}, True),
            ({"name": "test", "skills": ["skill1", "skill2"]}, True),
            ({"name": "test", "escalation": {"to": "opus"}}, True),
            ({"name": "test", "permissionMode": "acceptEdits"}, True),
            (
                {
                    "name": "test",
                    "description": "A test",
                    "category": "test",
                    "tags": ["test"],
                },
                False,
            ),
            ({}, False),
        ],
        ids=[
            "context-fork",
            "user-invocable",
            "hooks",
            "agent",
            "skills",
            "escalation",
            "permission-mode",
            "no-210-features",
            "empty-frontmatter",
        ],
    )
    def test_210_feature_detection(self, frontmatter: dict, expected: bool) -> None:
        """Given frontmatter, has_210_features returns correct boolean."""
        assert FrontmatterProcessor.has_210_features(frontmatter) is expected


class TestAllHookEventTypes:
    """Tests to verify all hook event types are recognized."""

    def test_all_valid_hook_events(self) -> None:
        """Given the expected event list, VALID_HOOK_EVENTS matches."""
        expected_events = (
            "Setup",
            "SessionStart",
            "SessionEnd",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "PostToolUseFailure",
            "PermissionRequest",
            "Notification",
            "SubagentStart",
            "SubagentStop",
            "Stop",
            "TeammateIdle",
            "TaskCompleted",
            "ConfigChange",
            "InstructionsLoaded",
            "PreCompact",
            "WorktreeCreate",
            "WorktreeRemove",
        )
        assert FrontmatterProcessor.VALID_HOOK_EVENTS == expected_events

    @pytest.mark.parametrize(
        "event_type",
        [
            "Setup",
            "SessionStart",
            "SessionEnd",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "PostToolUseFailure",
            "PermissionRequest",
            "Notification",
            "SubagentStart",
            "SubagentStop",
            "Stop",
            "TeammateIdle",
            "TaskCompleted",
            "ConfigChange",
            "InstructionsLoaded",
            "PreCompact",
            "WorktreeCreate",
            "WorktreeRemove",
        ],
    )
    def test_each_hook_event_type_validates(self, event_type: str) -> None:
        """Given a valid event type, no validation errors are returned."""
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
        """Given 2.1.0 skill fields constant, expected values are present."""
        expected_fields = (
            "context",
            "agent",
            "user-invocable",
            "hooks",
            "allowed-tools",
            "model",
        )
        assert FrontmatterProcessor.CLAUDE_CODE_210_SKILL_FIELDS == expected_fields

    def test_agent_fields_defined(self) -> None:
        """Given 2.1.0+ agent fields constant, expected values are present."""
        expected_fields = (
            "hooks",
            "skills",
            "escalation",
            "permissionMode",
            "background",
            "isolation",
        )
        assert FrontmatterProcessor.CLAUDE_CODE_210_AGENT_FIELDS == expected_fields

    def test_permission_modes_defined(self) -> None:
        """Given valid permission modes constant, expected values are present."""
        expected_modes = (
            "default",
            "acceptEdits",
            "dontAsk",
            "bypassPermissions",
            "plan",
            "ignore",
        )
        assert FrontmatterProcessor.VALID_PERMISSION_MODES == expected_modes
