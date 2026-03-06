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

from hook_validator import (  # noqa: E402
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
# Tests: _validate_hook_action
# ---------------------------------------------------------------------------


class TestValidateHookAction:
    """Feature: _validate_hook_action validates a single hook action dict."""

    @pytest.mark.unit
    def test_non_dict_appends_error(self) -> None:
        """Scenario: Non-dict hook action adds error.
        Given a non-dict hook action
        When _validate_hook_action is called
        Then an error is appended and valid is False
        """
        result = _make_result()
        _validate_hook_action("PreToolUse", 0, 0, "not-a-dict", result)
        assert result["valid"] is False
        assert any("must be an object" in e for e in result["errors"])

    @pytest.mark.unit
    def test_missing_type_warns(self) -> None:
        """Scenario: Hook action without 'type' adds a warning."""
        result = _make_result()
        _validate_hook_action("PreToolUse", 0, 0, {"command": "echo hi"}, result)
        assert any("missing 'type' field" in w for w in result["warnings"])
        assert result["valid"] is True

    @pytest.mark.unit
    def test_command_type_missing_command_errors(self) -> None:
        """Scenario: type=command without 'command' field adds error."""
        result = _make_result()
        _validate_hook_action("PreToolUse", 0, 0, {"type": "command"}, result)
        assert result["valid"] is False
        assert any("missing 'command' field" in e for e in result["errors"])

    @pytest.mark.unit
    def test_valid_command_action(self) -> None:
        """Scenario: Valid command action with type and command passes."""
        result = _make_result()
        _validate_hook_action(
            "PreToolUse", 0, 0, {"type": "command", "command": "echo hi"}, result
        )
        assert result["valid"] is True
        assert result["errors"] == []


# ---------------------------------------------------------------------------
# Tests: _validate_hooks_array
# ---------------------------------------------------------------------------


class TestValidateHooksArray:
    """Feature: _validate_hooks_array validates the hooks list."""

    @pytest.mark.unit
    def test_non_list_errors(self) -> None:
        """Scenario: Non-list hooks adds error."""
        result = _make_result()
        _validate_hooks_array("PreToolUse", 0, "not-a-list", result)
        assert result["valid"] is False
        assert any("must be a list" in e for e in result["errors"])

    @pytest.mark.unit
    def test_empty_list_is_valid(self) -> None:
        """Scenario: Empty hooks list passes validation."""
        result = _make_result()
        _validate_hooks_array("PreToolUse", 0, [], result)
        assert result["valid"] is True

    @pytest.mark.unit
    def test_validates_each_action(self) -> None:
        """Scenario: Each item in hooks list is validated."""
        result = _make_result()
        hooks = [{"type": "command", "command": "echo hi"}, "bad"]
        _validate_hooks_array("PreToolUse", 0, hooks, result)
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Tests: _validate_matcher
# ---------------------------------------------------------------------------


class TestValidateMatcher:
    """Feature: _validate_matcher validates hook matcher."""

    @pytest.mark.unit
    def test_valid_string_matcher_adds_info(self) -> None:
        """Scenario: Valid regex string matcher adds info message."""
        result = _make_result()
        _validate_matcher("PreToolUse", 0, ".*", result)
        assert result["valid"] is True
        assert any("valid" in msg for msg in result["info"])

    @pytest.mark.unit
    def test_invalid_regex_errors(self) -> None:
        """Scenario: Invalid regex pattern adds error."""
        result = _make_result()
        _validate_matcher("PreToolUse", 0, "[invalid", result)
        assert result["valid"] is False
        assert any("invalid matcher regex" in e for e in result["errors"])

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

    @pytest.mark.unit
    def test_invalid_type_errors(self) -> None:
        """Scenario: Non-string, non-dict matcher type errors."""
        result = _make_result()
        _validate_matcher("PreToolUse", 0, 42, result)
        assert result["valid"] is False
        assert any("must be a string" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: _validate_hook_entry
# ---------------------------------------------------------------------------


class TestValidateHookEntry:
    """Feature: _validate_hook_entry validates a full hook entry."""

    @pytest.mark.unit
    def test_non_dict_entry_errors(self) -> None:
        """Scenario: Non-dict hook entry adds error."""
        result = _make_result()
        _validate_hook_entry("PreToolUse", 0, "not-dict", result)
        assert result["valid"] is False

    @pytest.mark.unit
    def test_missing_hooks_key_errors(self) -> None:
        """Scenario: Entry without 'hooks' key adds error."""
        result = _make_result()
        _validate_hook_entry("PreToolUse", 0, {"matcher": ".*"}, result)
        assert result["valid"] is False
        assert any("missing required 'hooks' field" in e for e in result["errors"])

    @pytest.mark.unit
    def test_valid_entry_with_matcher(self) -> None:
        """Scenario: Valid entry with hooks and matcher passes."""
        result = _make_result()
        entry = {
            "matcher": ".*",
            "hooks": [{"type": "command", "command": "echo hi"}],
        }
        _validate_hook_entry("PreToolUse", 0, entry, result)
        assert result["valid"] is True

    @pytest.mark.unit
    def test_entry_without_matcher_is_valid(self) -> None:
        """Scenario: Entry without matcher but with hooks passes."""
        result = _make_result()
        entry = {"hooks": [{"type": "command", "command": "echo hi"}]}
        _validate_hook_entry("PreToolUse", 0, entry, result)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Tests: _validate_event_hooks
# ---------------------------------------------------------------------------


class TestValidateEventHooks:
    """Feature: _validate_event_hooks validates a list of hook entries."""

    @pytest.mark.unit
    def test_non_list_errors(self) -> None:
        """Scenario: Non-list event hooks adds error."""
        result = _make_result()
        _validate_event_hooks("PreToolUse", "not-list", result)
        assert result["valid"] is False

    @pytest.mark.unit
    def test_empty_list_passes(self) -> None:
        """Scenario: Empty list of event hooks is valid."""
        result = _make_result()
        _validate_event_hooks("PreToolUse", [], result)
        assert result["valid"] is True

    @pytest.mark.unit
    def test_validates_each_entry(self) -> None:
        """Scenario: Each entry in the list is validated."""
        result = _make_result()
        entries = [
            {"hooks": [{"type": "command", "command": "echo"}]},
            "bad-entry",
        ]
        _validate_event_hooks("PreToolUse", entries, result)
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Tests: validate_json_hook
# ---------------------------------------------------------------------------


class TestValidateJsonHook:
    """Feature: validate_json_hook validates a hooks.json file."""

    @pytest.mark.unit
    def test_missing_file_errors(self, tmp_path: Path) -> None:
        """Scenario: Non-existent file returns error.
        Given a path that does not exist
        When validate_json_hook is called
        Then valid is False and error mentions file not found
        """
        missing = tmp_path / "hooks.json"
        result = validate_json_hook(missing)
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])

    @pytest.mark.unit
    def test_invalid_json_errors(self, tmp_path: Path) -> None:
        """Scenario: File with invalid JSON returns error."""
        hook_file = tmp_path / "hooks.json"
        hook_file.write_text("{bad json")
        result = validate_json_hook(hook_file)
        assert result["valid"] is False
        assert any("Invalid JSON" in e for e in result["errors"])

    @pytest.mark.unit
    def test_non_dict_root_errors(self, tmp_path: Path) -> None:
        """Scenario: Root element is not a dict returns error."""
        hook_file = tmp_path / "hooks.json"
        hook_file.write_text("[1, 2, 3]")
        result = validate_json_hook(hook_file)
        assert result["valid"] is False
        assert any("must be a JSON object" in e for e in result["errors"])

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
        """Scenario: Valid hooks.json with known events passes.
        Given a valid hooks.json with PreToolUse entries
        When validate_json_hook is called
        Then valid is True
        """
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

    @pytest.mark.unit
    def test_empty_dict_is_valid(self, tmp_path: Path) -> None:
        """Scenario: Empty hooks dict returns valid."""
        hook_file = tmp_path / "hooks.json"
        hook_file.write_text("{}")
        result = validate_json_hook(hook_file)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Tests: validate_python_hook
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
    def test_syntax_error_in_python_file(self, tmp_path: Path) -> None:
        """Scenario: Python file with syntax error returns error."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text("def bad syntax(:\n    pass")
        result = validate_python_hook(hook_file)
        assert result["valid"] is False
        assert any("syntax error" in e.lower() for e in result["errors"])

    @pytest.mark.unit
    def test_no_classes_warns(self, tmp_path: Path) -> None:
        """Scenario: Python file with no classes adds warning."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text("# Just a comment\ndef foo():\n    pass\n")
        result = validate_python_hook(hook_file)
        assert any("No classes" in w for w in result["warnings"])

    @pytest.mark.unit
    def test_class_without_agent_hooks_warns(self, tmp_path: Path) -> None:
        """Scenario: Python file with class not inheriting AgentHooks warns."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text("class MyHook(object):\n    pass\n")
        result = validate_python_hook(hook_file)
        assert any("AgentHooks" in w for w in result["warnings"])

    @pytest.mark.unit
    def test_valid_agent_hooks_subclass(self, tmp_path: Path) -> None:
        """Scenario: Python file with valid AgentHooks subclass passes.
        Given a Python file with valid AgentHooks subclass
        When validate_python_hook is called
        Then valid is True
        """
        hook_file = tmp_path / "hook.py"
        hook_file.write_text(
            "from sdk import AgentHooks\n\n"
            "class MyHooks(AgentHooks):\n"
            "    async def on_pre_tool_use(self, tool_name, tool_input):\n"
            "        pass\n"
        )
        result = validate_python_hook(hook_file)
        assert result["valid"] is True

    @pytest.mark.unit
    def test_non_async_callback_errors(self, tmp_path: Path) -> None:
        """Scenario: Synchronous callback method adds error."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text(
            "class MyHooks(AgentHooks):\n"
            "    def on_pre_tool_use(self, tool_name, tool_input):\n"
            "        pass\n"
        )
        result = validate_python_hook(hook_file)
        assert result["valid"] is False
        assert any("async" in e for e in result["errors"])

    @pytest.mark.unit
    def test_wrong_arguments_errors(self, tmp_path: Path) -> None:
        """Scenario: Callback with wrong argument list adds error."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text(
            "class MyHooks(AgentHooks):\n"
            "    async def on_pre_tool_use(self, wrong_arg):\n"
            "        pass\n"
        )
        result = validate_python_hook(hook_file)
        assert result["valid"] is False
        assert any("incorrect arguments" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: validate_hook_file (auto-detect type)
# ---------------------------------------------------------------------------


class TestValidateHookFile:
    """Feature: validate_hook_file auto-detects type."""

    @pytest.mark.unit
    def test_json_extension_routes_to_json_validator(self, tmp_path: Path) -> None:
        """Scenario: .json extension triggers JSON validation."""
        hook_file = tmp_path / "hooks.json"
        hook_file.write_text("{}")
        result = validate_hook_file(hook_file)
        assert result["valid"] is True

    @pytest.mark.unit
    def test_py_extension_routes_to_python_validator(self, tmp_path: Path) -> None:
        """Scenario: .py extension triggers Python validation."""
        hook_file = tmp_path / "hook.py"
        hook_file.write_text("# empty\n")
        result = validate_hook_file(hook_file)
        # Valid is True/False but no crash; warnings about no classes
        assert isinstance(result["valid"], bool)

    @pytest.mark.unit
    def test_unknown_extension_errors(self, tmp_path: Path) -> None:
        """Scenario: Unknown extension returns error."""
        hook_file = tmp_path / "hook.txt"
        result = validate_hook_file(hook_file)
        assert result["valid"] is False
        assert any("Cannot determine file type" in e for e in result["errors"])

    @pytest.mark.unit
    def test_explicit_type_json_overrides_extension(self, tmp_path: Path) -> None:
        """Scenario: Explicit file_type='json' overrides extension."""
        hook_file = tmp_path / "hooks.txt"
        hook_file.write_text("{}")
        result = validate_hook_file(hook_file, file_type="json")
        assert result["valid"] is True

    @pytest.mark.unit
    def test_explicit_type_python_overrides_extension(self, tmp_path: Path) -> None:
        """Scenario: Explicit file_type='python' overrides extension."""
        hook_file = tmp_path / "hooks.txt"
        hook_file.write_text("x = 1\n")
        result = validate_hook_file(hook_file, file_type="python")
        assert isinstance(result["valid"], bool)

    @pytest.mark.unit
    def test_unknown_file_type_errors(self, tmp_path: Path) -> None:
        """Scenario: Unknown explicit file_type returns error."""
        hook_file = tmp_path / "hooks.json"
        result = validate_hook_file(hook_file, file_type="yaml")
        assert result["valid"] is False
        assert any("Unknown file type" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: print_result
# ---------------------------------------------------------------------------


class TestPrintResult:
    """Feature: print_result does not crash."""

    @pytest.mark.unit
    def test_print_valid_result_no_crash(self) -> None:
        """Scenario: print_result with valid result does not crash."""
        result: ValidationResult = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": ["some info"],
        }
        print_result(result)  # Should not raise

    @pytest.mark.unit
    def test_print_valid_with_warnings(self) -> None:
        """Scenario: print_result with warnings does not crash."""
        result: ValidationResult = {
            "valid": True,
            "errors": [],
            "warnings": ["a warning"],
            "info": [],
        }
        print_result(result, verbose=True)  # Should not raise

    @pytest.mark.unit
    def test_print_invalid_result_no_crash(self) -> None:
        """Scenario: print_result with errors does not crash."""
        result: ValidationResult = {
            "valid": False,
            "errors": ["an error"],
            "warnings": [],
            "info": [],
        }
        print_result(result)  # Should not raise
