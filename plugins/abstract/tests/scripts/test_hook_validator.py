"""Tests for hook_validator script.

Feature: Hook validation
    As a developer
    I want hook files validated
    So that hook configurations are correct
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from hook_validator import (
    KNOWN_EVENTS,
    ValidationResult,
    _validate_event_hooks,
    _validate_hook_action,
    _validate_hook_entry,
    _validate_hooks_array,
    _validate_matcher,
    print_result,
    validate_hook_file,
    validate_json_hook,
    validate_python_hook,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result() -> ValidationResult:
    return {"valid": True, "errors": [], "warnings": [], "info": []}


# ---------------------------------------------------------------------------
# Tests: _validate_hook_action (parametrized)
# ---------------------------------------------------------------------------


class TestValidateHookAction:
    """Feature: _validate_hook_action validates a single hook action dict."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("action", "expect_valid", "error_fragment"),
        [
            ("not-a-dict", False, "must be an object"),
            ({"type": "command"}, False, "missing 'command' field"),
            (
                {"type": "command", "command": "echo hi"},
                True,
                "",
            ),
        ],
        ids=[
            "non-dict-errors",
            "command-type-missing-command",
            "valid-command-action",
        ],
    )
    def test_action_validation(self, action, expect_valid, error_fragment) -> None:
        """Scenario: Hook action validation produces correct outcome.
        Given a hook action of varying validity
        When _validate_hook_action is called
        Then valid and errors reflect the input correctness
        """
        result = _make_result()
        _validate_hook_action("PreToolUse", 0, 0, action, result)
        assert result["valid"] is expect_valid
        if error_fragment:
            assert any(error_fragment in e for e in result["errors"])

    @pytest.mark.unit
    def test_missing_type_warns(self) -> None:
        """Scenario: Hook action without 'type' adds a warning."""
        result = _make_result()
        _validate_hook_action("PreToolUse", 0, 0, {"command": "echo hi"}, result)
        assert any("missing 'type' field" in w for w in result["warnings"])
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Tests: _validate_hooks_array
# ---------------------------------------------------------------------------


class TestValidateHooksArray:
    """Feature: _validate_hooks_array validates the hooks list."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("hooks_value", "expect_valid"),
        [
            ("not-a-list", False),
            ([], True),
            ([{"type": "command", "command": "echo hi"}, "bad"], False),
        ],
        ids=["non-list-errors", "empty-list-valid", "mixed-items"],
    )
    def test_hooks_array_validation(self, hooks_value, expect_valid) -> None:
        """Scenario: Hooks array validation produces correct outcome."""
        result = _make_result()
        _validate_hooks_array("PreToolUse", 0, hooks_value, result)
        assert result["valid"] is expect_valid


# ---------------------------------------------------------------------------
# Tests: _validate_matcher (parametrized)
# ---------------------------------------------------------------------------


class TestValidateMatcher:
    """Feature: _validate_matcher validates hook matcher."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("matcher", "expect_valid", "msg_category", "msg_fragment"),
        [
            (".*", True, "info", "valid"),
            ("[invalid", False, "errors", "invalid matcher regex"),
            (42, False, "errors", "must be a string"),
        ],
        ids=[
            "valid-regex",
            "invalid-regex",
            "invalid-type",
        ],
    )
    def test_matcher_validation(
        self, matcher, expect_valid, msg_category, msg_fragment
    ) -> None:
        """Scenario: Matcher validation checks type and regex validity."""
        result = _make_result()
        _validate_matcher("PreToolUse", 0, matcher, result)
        assert result["valid"] is expect_valid
        assert any(msg_fragment in m for m in result[msg_category])

    @pytest.mark.unit
    def test_dict_matcher_warns_deprecated(self) -> None:
        """Scenario: Dict matcher format adds deprecation warning."""
        result = _make_result()
        _validate_matcher("PreToolUse", 0, {"toolName": "Skill"}, result)
        assert result["valid"] is True
        assert any("deprecated" in w for w in result["warnings"])

    @pytest.mark.unit
    def test_dict_matcher_unknown_field_warns(self) -> None:
        """Scenario: Dict matcher with unknown field adds extra warning."""
        result = _make_result()
        _validate_matcher(
            "PreToolUse", 0, {"toolName": "Skill", "unknownField": 1}, result
        )
        assert any("unknown matcher field" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Tests: _validate_hook_entry (parametrized)
# ---------------------------------------------------------------------------


class TestValidateHookEntry:
    """Feature: _validate_hook_entry validates a full hook entry."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("entry", "expect_valid", "error_fragment"),
        [
            ("not-dict", False, ""),
            ({"matcher": ".*"}, False, "missing required 'hooks' field"),
            (
                {
                    "matcher": ".*",
                    "hooks": [{"type": "command", "command": "echo hi"}],
                },
                True,
                "",
            ),
            (
                {"hooks": [{"type": "command", "command": "echo hi"}]},
                True,
                "",
            ),
        ],
        ids=[
            "non-dict-errors",
            "missing-hooks-key",
            "valid-with-matcher",
            "valid-without-matcher",
        ],
    )
    def test_hook_entry_validation(self, entry, expect_valid, error_fragment) -> None:
        """Scenario: Hook entry validation checks structure correctness."""
        result = _make_result()
        _validate_hook_entry("PreToolUse", 0, entry, result)
        assert result["valid"] is expect_valid
        if error_fragment:
            assert any(error_fragment in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: _validate_event_hooks
# ---------------------------------------------------------------------------


class TestValidateEventHooks:
    """Feature: _validate_event_hooks validates a list of hook entries."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("entries", "expect_valid"),
        [
            ("not-list", False),
            ([], True),
            (
                [
                    {"hooks": [{"type": "command", "command": "echo"}]},
                    "bad-entry",
                ],
                False,
            ),
        ],
        ids=["non-list", "empty-list", "mixed-entries"],
    )
    def test_event_hooks_validation(self, entries, expect_valid) -> None:
        """Scenario: Event hooks list validation produces correct outcome."""
        result = _make_result()
        _validate_event_hooks("PreToolUse", entries, result)
        assert result["valid"] is expect_valid


# ---------------------------------------------------------------------------
# Tests: validate_json_hook (parametrized)
# ---------------------------------------------------------------------------


class TestValidateJsonHook:
    """Feature: validate_json_hook validates a hooks.json file."""

    @pytest.mark.unit
    def test_missing_file_errors(self, tmp_path: Path) -> None:
        """Scenario: Non-existent file returns error."""
        missing = tmp_path / "hooks.json"
        result = validate_json_hook(missing)
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("content", "expect_valid", "error_fragment"),
        [
            ("{bad json", False, "Invalid JSON"),
            ("[1, 2, 3]", False, "must be a JSON object"),
            ("{}", True, ""),
        ],
        ids=[
            "invalid-json",
            "non-dict-root",
            "empty-dict-valid",
        ],
    )
    def test_json_content_validation(
        self, tmp_path: Path, content, expect_valid, error_fragment
    ) -> None:
        """Scenario: JSON content is validated for structure."""
        hook_file = tmp_path / "hooks.json"
        hook_file.write_text(content)
        result = validate_json_hook(hook_file)
        assert result["valid"] is expect_valid
        if error_fragment:
            assert any(error_fragment in e for e in result["errors"])

    @pytest.mark.unit
    def test_unknown_event_type_warns(self, tmp_path: Path) -> None:
        """Scenario: Unknown event type adds warning."""
        hook_file = tmp_path / "hooks.json"
        data = {"UnknownEvent": []}
        hook_file.write_text(json.dumps(data))
        result = validate_json_hook(hook_file)
        assert any("Unknown event type" in w for w in result["warnings"])

    @pytest.mark.unit
    def test_valid_hooks_json(self, tmp_path: Path) -> None:
        """Scenario: Valid hooks.json with known events passes."""
        hook_file = tmp_path / "hooks.json"
        data = {
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [{"type": "command", "command": "echo hi"}],
                }
            ]
        }
        hook_file.write_text(json.dumps(data))
        result = validate_json_hook(hook_file)
        assert result["valid"] is True
        assert result["errors"] == []


# ---------------------------------------------------------------------------
# Tests: validate_python_hook (parametrized)
# ---------------------------------------------------------------------------


class TestValidatePythonHook:
    """Feature: validate_python_hook validates Python SDK hook files."""

    @pytest.mark.unit
    def test_missing_file_errors(self, tmp_path: Path) -> None:
        """Scenario: Non-existent Python file returns error."""
        missing = tmp_path / "hook.py"
        result = validate_python_hook(missing)
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("code", "expect_valid", "msg_category", "msg_fragment"),
        [
            (
                "def bad syntax(:\n    pass",
                False,
                "errors",
                "syntax error",
            ),
            (
                "# Just a comment\ndef foo():\n    pass\n",
                True,
                "warnings",
                "No classes",
            ),
            (
                "class MyHook(object):\n    pass\n",
                True,
                "warnings",
                "AgentHooks",
            ),
            (
                (
                    "from sdk import AgentHooks\n\n"
                    "class MyHooks(AgentHooks):\n"
                    "    async def on_pre_tool_use(self, tool_name, tool_input):\n"
                    "        pass\n"
                ),
                True,
                "info",
                "",
            ),
            (
                (
                    "class MyHooks(AgentHooks):\n"
                    "    def on_pre_tool_use(self, tool_name, tool_input):\n"
                    "        pass\n"
                ),
                False,
                "errors",
                "async",
            ),
            (
                (
                    "class MyHooks(AgentHooks):\n"
                    "    async def on_pre_tool_use(self, wrong_arg):\n"
                    "        pass\n"
                ),
                False,
                "errors",
                "incorrect arguments",
            ),
        ],
        ids=[
            "syntax-error",
            "no-classes",
            "class-not-agent-hooks",
            "valid-agent-hooks",
            "non-async-callback",
            "wrong-arguments",
        ],
    )
    def test_python_hook_validation(
        self, tmp_path: Path, code, expect_valid, msg_category, msg_fragment
    ) -> None:
        """Scenario: Python hook files are validated for correctness."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text(code)
        result = validate_python_hook(hook_file)
        assert result["valid"] is expect_valid
        if msg_fragment:
            assert any(msg_fragment.lower() in m.lower() for m in result[msg_category])


# ---------------------------------------------------------------------------
# Tests: validate_hook_file (parametrized)
# ---------------------------------------------------------------------------


class TestValidateHookFile:
    """Feature: validate_hook_file auto-detects type."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("filename", "content", "file_type", "expect_valid_type"),
        [
            ("hooks.json", "{}", None, True),
            ("hook.py", "# empty\n", None, None),
            ("hook.txt", "", None, False),
            ("hooks.txt", "{}", "json", True),
            ("hooks.txt", "x = 1\n", "python", None),
        ],
        ids=[
            "json-extension",
            "py-extension",
            "unknown-extension",
            "explicit-json-type",
            "explicit-python-type",
        ],
    )
    def test_file_type_routing(
        self, tmp_path: Path, filename, content, file_type, expect_valid_type
    ) -> None:
        """Scenario: File type routing works by extension and explicit type."""
        hook_file = tmp_path / filename
        if content or filename != "hook.txt":
            hook_file.write_text(content)
        kwargs = {"file_type": file_type} if file_type else {}
        result = validate_hook_file(hook_file, **kwargs)
        if expect_valid_type is not None:
            assert result["valid"] is expect_valid_type
        else:
            assert isinstance(result["valid"], bool)

    @pytest.mark.unit
    def test_unknown_file_type_errors(self, tmp_path: Path) -> None:
        """Scenario: Unknown explicit file_type returns error."""
        hook_file = tmp_path / "hooks.json"
        result = validate_hook_file(hook_file, file_type="yaml")
        assert result["valid"] is False
        assert any("Unknown file type" in e for e in result["errors"])

    @pytest.mark.unit
    def test_unknown_extension_errors(self, tmp_path: Path) -> None:
        """Scenario: Unknown extension returns error with message."""
        hook_file = tmp_path / "hook.txt"
        result = validate_hook_file(hook_file)
        assert result["valid"] is False
        assert any("Cannot determine file type" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: print_result
# ---------------------------------------------------------------------------


class TestPrintResult:
    """Feature: print_result does not crash."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("result_data", "verbose"),
        [
            (
                {"valid": True, "errors": [], "warnings": [], "info": ["some info"]},
                False,
            ),
            (
                {"valid": True, "errors": [], "warnings": ["a warning"], "info": []},
                True,
            ),
            (
                {"valid": False, "errors": ["an error"], "warnings": [], "info": []},
                False,
            ),
        ],
        ids=["valid-with-info", "valid-with-warnings", "invalid-with-errors"],
    )
    def test_print_result_no_crash(self, result_data, verbose) -> None:
        """Scenario: print_result handles various result shapes."""
        result: ValidationResult = result_data
        print_result(result, verbose=verbose)  # Should not raise


# ---------------------------------------------------------------------------
# Tests: KNOWN_EVENTS completeness (Claude Code 2.1.50)
# ---------------------------------------------------------------------------


class TestKnownEvents:
    """Feature: KNOWN_EVENTS contains all valid Claude Code hook events."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "event",
        [
            "SessionStart",
            "ConfigChange",
            "Setup",
            "PermissionRequest",
        ],
    )
    def test_individual_known_events(self, event: str) -> None:
        """Scenario: Previously rejected events are now accepted."""
        assert event in KNOWN_EVENTS

    @pytest.mark.unit
    def test_all_known_events_accepted(self) -> None:
        """Scenario: All 19 official events are present in KNOWN_EVENTS."""
        expected = {
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
        }
        assert KNOWN_EVENTS == expected

    @pytest.mark.unit
    def test_previously_rejected_events_no_warning(self, tmp_path: Path) -> None:
        """Scenario: Events that previously triggered warnings now pass."""
        hook_file = tmp_path / "hooks.json"
        data = {
            "SessionStart": [{"hooks": [{"type": "command", "command": "echo init"}]}],
            "PermissionRequest": [
                {"hooks": [{"type": "command", "command": "echo permit"}]}
            ],
            "Setup": [{"hooks": [{"type": "command", "command": "echo setup"}]}],
            "ConfigChange": [{"hooks": [{"type": "command", "command": "echo cfg"}]}],
        }
        hook_file.write_text(json.dumps(data))
        result = validate_json_hook(hook_file)
        assert result["valid"] is True
        assert not any("Unknown event type" in w for w in result["warnings"])
