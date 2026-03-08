"""Tests for hookify helper utilities.

Covers all 6 functions in utils/helpers.py: format_rule_name,
get_project_root, validate_event_type, validate_action_type,
get_field_for_event, and truncate_text.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from hookify.utils.helpers import (
    format_rule_name,
    get_field_for_event,
    get_project_root,
    truncate_text,
    validate_action_type,
    validate_event_type,
)


class TestFormatRuleName:
    """Verify format_rule_name converts to kebab-case."""

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("Block Dangerous RM", "block-dangerous-rm"),
            ("Warn console.log", "warn-console-log"),
            ("UPPER CASE NAME", "upper-case-name"),
            ("already-kebab", "already-kebab"),
            ("CamelCaseName", "camelcasename"),
            ("has   multiple   spaces", "has-multiple-spaces"),
        ],
    )
    def test_converts_to_kebab_case(
        self, input_name: str, expected: str
    ) -> None:
        """Various name formats are normalized to kebab-case."""
        assert format_rule_name(input_name) == expected

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            ("  leading-trailing  ", "leading-trailing"),
            ("---hyphen-edges---", "hyphen-edges"),
            ("@special!chars#here", "special-chars-here"),
        ],
    )
    def test_strips_leading_trailing_hyphens(
        self, input_name: str, expected: str
    ) -> None:
        """Leading/trailing non-alphanumeric chars become stripped hyphens."""
        assert format_rule_name(input_name) == expected

    def test_collapses_multiple_hyphens(self) -> None:
        """Adjacent special characters collapse to a single hyphen."""
        assert format_rule_name("a---b") == "a-b"

    def test_empty_string(self) -> None:
        """Empty input returns empty output."""
        assert format_rule_name("") == ""

    def test_single_word(self) -> None:
        """Single lowercase word passes through unchanged."""
        assert format_rule_name("simple") == "simple"

    def test_numeric_content(self) -> None:
        """Numeric characters are preserved."""
        assert format_rule_name("Rule 42 Alpha") == "rule-42-alpha"


class TestGetProjectRoot:
    """Verify get_project_root finds the project root marker."""

    def test_returns_dir_with_git(self, tmp_path: Path) -> None:
        """Directory containing .git is identified as project root."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        with patch("hookify.utils.helpers.Path.cwd", return_value=tmp_path):
            result = get_project_root()
        assert result == tmp_path

    def test_returns_dir_with_claude(self, tmp_path: Path) -> None:
        """Directory containing .claude is identified as project root."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        with patch("hookify.utils.helpers.Path.cwd", return_value=tmp_path):
            result = get_project_root()
        assert result == tmp_path

    def test_walks_up_to_find_root(self, tmp_path: Path) -> None:
        """Finds .git in a parent directory when cwd is nested."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        with patch("hookify.utils.helpers.Path.cwd", return_value=nested):
            result = get_project_root()
        assert result == tmp_path

    def test_returns_cwd_when_no_markers(self, tmp_path: Path) -> None:
        """Falls back to cwd when no .git or .claude is found."""
        with patch("hookify.utils.helpers.Path.cwd", return_value=tmp_path):
            result = get_project_root()
        assert result == tmp_path


class TestValidateEventType:
    """Verify validate_event_type accepts only known events."""

    @pytest.mark.parametrize(
        "event",
        ["bash", "file", "stop", "prompt", "all"],
    )
    def test_valid_events(self, event: str) -> None:
        """Each known event type returns True."""
        assert validate_event_type(event) is True

    @pytest.mark.parametrize(
        "event",
        ["Bash", "STOP", "unknown", "", "pre_tool_use"],
    )
    def test_invalid_events(self, event: str) -> None:
        """Unknown or mis-cased event types return False."""
        assert validate_event_type(event) is False


class TestValidateActionType:
    """Verify validate_action_type accepts only known actions."""

    @pytest.mark.parametrize("action", ["warn", "block"])
    def test_valid_actions(self, action: str) -> None:
        """Each known action type returns True."""
        assert validate_action_type(action) is True

    @pytest.mark.parametrize(
        "action",
        ["Warn", "BLOCK", "allow", "deny", ""],
    )
    def test_invalid_actions(self, action: str) -> None:
        """Unknown or mis-cased action types return False."""
        assert validate_action_type(action) is False


class TestGetFieldForEvent:
    """Verify get_field_for_event returns correct field lists."""

    @pytest.mark.parametrize(
        ("event", "expected"),
        [
            ("bash", ["command"]),
            ("file", ["file_path", "new_text", "old_text", "content"]),
            ("stop", ["transcript"]),
            ("prompt", ["user_prompt"]),
            (
                "all",
                [
                    "command",
                    "file_path",
                    "new_text",
                    "user_prompt",
                    "transcript",
                ],
            ),
        ],
    )
    def test_known_events(
        self, event: str, expected: list[str]
    ) -> None:
        """Each event type returns its specific field list."""
        assert get_field_for_event(event) == expected

    def test_unknown_event_returns_empty(self) -> None:
        """Unknown event type returns an empty list."""
        assert get_field_for_event("nonexistent") == []

    def test_empty_string_returns_empty(self) -> None:
        """Empty string returns an empty list."""
        assert get_field_for_event("") == []


class TestTruncateText:
    """Verify truncate_text respects max_length and adds ellipsis."""

    def test_short_text_unchanged(self) -> None:
        """Text within limit is returned as-is."""
        assert truncate_text("hello", max_length=100) == "hello"

    def test_exact_length_unchanged(self) -> None:
        """Text at exactly max_length is returned as-is."""
        text = "a" * 100
        assert truncate_text(text, max_length=100) == text

    def test_long_text_truncated_with_ellipsis(self) -> None:
        """Text exceeding max_length is cut and gets '...' suffix."""
        text = "a" * 150
        result = truncate_text(text, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")
        assert result == "a" * 97 + "..."

    def test_default_max_length_is_100(self) -> None:
        """Default max_length is 100 characters."""
        text = "x" * 200
        result = truncate_text(text)
        assert len(result) == 100
        assert result.endswith("...")

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert truncate_text("", max_length=10) == ""

    def test_small_max_length(self) -> None:
        """Works correctly with very small max_length."""
        result = truncate_text("hello world", max_length=5)
        assert len(result) == 5
        assert result == "he..."
