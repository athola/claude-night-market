"""Tests for context warning hook output formatting and entry point.

Tests:
- format_hook_output() JSON structure
- get_context_usage_from_env() environment reading
- main() entry point behavior
"""

from __future__ import annotations

import json
from io import StringIO

import pytest

# Constants for PLR2004 magic values
TWENTY_PERCENT = 0.20
FORTY_FIVE_PERCENT = 0.45
FIFTY_PERCENT = 0.50
SIXTY_PERCENT = 0.60
EIGHTY_FIVE_PERCENT = 0.85
NINETY_PERCENT = 0.90


class TestFormatHookOutput:
    """Feature: Hook output formatting.

    As a hook
    I want correct JSON output format
    So that Claude Code can process warnings

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warning_output_has_additional_context(
        self, context_warning_full_module
    ) -> None:
        """Scenario: WARNING alert includes additionalContext."""
        alert = context_warning_full_module.assess_context_usage(0.45)
        output = context_warning_full_module.format_hook_output(alert)

        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
        assert "additionalContext" in output["hookSpecificOutput"]
        assert "WARNING" in output["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_output_has_additional_context(
        self, context_warning_full_module
    ) -> None:
        """Scenario: CRITICAL alert includes additionalContext."""
        alert = context_warning_full_module.assess_context_usage(0.60)
        output = context_warning_full_module.format_hook_output(alert)

        assert "additionalContext" in output["hookSpecificOutput"]
        assert "CRITICAL" in output["hookSpecificOutput"]["additionalContext"]
        assert "Recommendations:" in output["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ok_output_no_additional_context(self, context_warning_full_module) -> None:
        """Scenario: OK alert has no additionalContext."""
        alert = context_warning_full_module.assess_context_usage(0.20)
        output = context_warning_full_module.format_hook_output(alert)

        assert "additionalContext" not in output["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_output_is_json_serializable(self, context_warning_full_module) -> None:
        """Scenario: Hook output can be serialized to JSON."""
        alert = context_warning_full_module.assess_context_usage(0.55)
        output = context_warning_full_module.format_hook_output(alert)

        # Should not raise
        json_str = json.dumps(output)
        parsed = json.loads(json_str)

        assert "hookSpecificOutput" in parsed


class TestGetContextUsageFromEnv:
    """Feature: Environment variable reading.

    As a hook
    I want to read context usage from environment
    So that I can integrate with Claude Code

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reads_from_env_variable(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Read usage from CLAUDE_CONTEXT_USAGE."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.45")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage == 0.45

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_without_env(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Returns None without environment variable and estimation disabled."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_invalid_env_value(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Handle invalid environment value gracefully."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "not-a-number")
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_env_value(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Handle empty environment value."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "")
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage is None


class TestMainEntryPoint:
    """Feature: Hook main entry point.

    As a hook
    I want main() to handle various inputs correctly
    So that the hook is robust in production

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_no_context_usage(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() with no context usage outputs minimal JSON."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert data["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_warning_level(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() with 45% usage outputs WARNING."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.45")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" in data["hookSpecificOutput"]
        assert "WARNING" in data["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_ok_level(self, context_warning_full_module, monkeypatch) -> None:
        """Scenario: main() with 20% usage outputs minimal JSON."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.20")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" not in data["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_invalid_json_input(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() handles malformed JSON on stdin."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr("sys.stdin", StringIO("not valid json {"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "hookSpecificOutput" in data

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_hook_input_usage(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() reads usage from hook input JSON."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        hook_input = json.dumps({"context_usage": 0.55})
        monkeypatch.setattr("sys.stdin", StringIO(hook_input))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "CRITICAL" in data["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_env_takes_priority_over_input(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Environment variable takes priority over hook input."""
        hook_input = json.dumps({"context_usage": 0.55})  # Would be CRITICAL
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.20")  # OK
        monkeypatch.setattr("sys.stdin", StringIO(hook_input))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        # Should be OK (env) not CRITICAL (input)
        assert "additionalContext" not in data["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_critical_level(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() with 60% usage outputs CRITICAL."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.60")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" in data["hookSpecificOutput"]
        assert "CRITICAL" in data["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_invalid_usage_value(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() handles invalid usage value from hook input."""
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        hook_input = json.dumps({"context_usage": -0.5})
        monkeypatch.setattr("sys.stdin", StringIO(hook_input))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "hookSpecificOutput" in data

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_emergency_level(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() with 85% usage outputs EMERGENCY."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.85")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" in data["hookSpecificOutput"]
        ctx = data["hookSpecificOutput"]["additionalContext"]
        assert "Skill(conserve:clear-context)" in ctx
        assert "DELEGATE via continuation" in ctx

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_emergency_output_has_formatted_instructions(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() EMERGENCY output includes formatted workflow instructions."""
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.90")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        additional_context = data["hookSpecificOutput"]["additionalContext"]

        assert "Skill(conserve:clear-context)" in additional_context
        assert "continuation agent" in additional_context
        assert "DELEGATE via continuation" in additional_context
        # Should NOT contain manipulative/imperative language
        assert "MANDATORY" not in additional_context
        assert "YOU MUST" not in additional_context
        assert "BLOCKING" not in additional_context
