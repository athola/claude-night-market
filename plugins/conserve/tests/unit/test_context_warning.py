"""Tests for context warning hook with two-tier MECW alerts.

This module tests the context warning hook that implements 40% warning
and 50% critical thresholds for context usage monitoring.
"""

import json

import pytest

# Constants for PLR2004 magic values
ZERO = 0.0
TWENTY_PERCENT = 0.20
THIRTY_NINE_PERCENT = 0.39
FORTY_PERCENT = 0.40
FORTY_FIVE_PERCENT = 0.45
FORTY_NINE_PERCENT = 0.49
FIFTY_PERCENT = 0.50
SIXTY_PERCENT = 0.60
EIGHTY_PERCENT = 0.80
HUNDRED = 100

# Expected percentage values for assertions
TWENTY_PERCENT_DISPLAY = 20.0
THIRTY_NINE_PERCENT_DISPLAY = 39.0
FORTY_PERCENT_DISPLAY = 40.0
FORTY_FIVE_PERCENT_DISPLAY = 45.0
FORTY_NINE_PERCENT_DISPLAY = 49.0
FIFTY_PERCENT_DISPLAY = 50.0
SIXTY_PERCENT_DISPLAY = 60.0
EIGHTY_PERCENT_DISPLAY = 80.0


class TestContextWarningHook:
    """Feature: Two-tier context warnings for MECW compliance.

    As a context optimization workflow
    I want to receive warnings at 40% and critical alerts at 50%
    So that I can proactively optimize context usage
    """

    @pytest.fixture
    def context_warning_module(self):
        """Import the context_warning module."""
        import importlib.util
        import sys
        from pathlib import Path

        # Get absolute path to context_warning.py
        hooks_path = Path(__file__).resolve().parent.parent.parent / "hooks"
        module_path = hooks_path / "context_warning.py"

        # Load module using importlib
        spec = importlib.util.spec_from_file_location("context_warning", module_path)
        context_warning = importlib.util.module_from_spec(spec)
        sys.modules["context_warning"] = context_warning
        spec.loader.exec_module(context_warning)

        return {
            "WARNING_THRESHOLD": context_warning.WARNING_THRESHOLD,
            "CRITICAL_THRESHOLD": context_warning.CRITICAL_THRESHOLD,
            "ContextSeverity": context_warning.ContextSeverity,
            "ContextAlert": context_warning.ContextAlert,
            "assess_context_usage": context_warning.assess_context_usage,
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ok_status_under_forty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage under 40% returns OK status.

        Given context usage is below 40%
        When assessing context usage
        Then it should return OK severity
        And no recommendations should be provided.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        # Test various values under 40%
        test_cases = [ZERO, TWENTY_PERCENT, THIRTY_NINE_PERCENT]

        for usage in test_cases:
            alert = assess(usage)

            assert alert.severity == ContextSeverity.OK
            assert alert.usage_percent == usage
            assert "OK" in alert.message
            assert len(alert.recommendations) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warning_status_at_forty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage at 40% triggers WARNING.

        Given context usage is exactly 40%
        When assessing context usage
        Then it should return WARNING severity
        And provide optimization recommendations.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(FORTY_PERCENT)

        assert alert.severity == ContextSeverity.WARNING
        assert alert.usage_percent == FORTY_PERCENT
        assert "WARNING" in alert.message
        assert len(alert.recommendations) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warning_status_between_forty_and_fifty_percent(
        self, context_warning_module
    ) -> None:
        """Scenario: Context usage between 40-50% returns WARNING.

        Given context usage is between 40% and 50%
        When assessing context usage
        Then it should return WARNING severity
        And recommend preparing optimization strategy.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        test_cases = [FORTY_FIVE_PERCENT, FORTY_NINE_PERCENT]

        for usage in test_cases:
            alert = assess(usage)

            assert alert.severity == ContextSeverity.WARNING
            assert alert.usage_percent == usage
            assert "WARNING" in alert.message
            assert any(
                "optimization" in rec.lower() or "monitor" in rec.lower()
                for rec in alert.recommendations
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_status_at_fifty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage at 50% triggers CRITICAL.

        Given context usage is exactly 50%
        When assessing context usage
        Then it should return CRITICAL severity
        And recommend immediate optimization.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(FIFTY_PERCENT)

        assert alert.severity == ContextSeverity.CRITICAL
        assert alert.usage_percent == FIFTY_PERCENT
        assert "CRITICAL" in alert.message
        assert len(alert.recommendations) > 0
        assert any("immediate" in rec.lower() for rec in alert.recommendations)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_status_above_fifty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage above 50% returns CRITICAL.

        Given context usage is above 50%
        When assessing context usage
        Then it should return CRITICAL severity
        And recommend immediate actions.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        test_cases = [SIXTY_PERCENT, EIGHTY_PERCENT]

        for usage in test_cases:
            alert = assess(usage)

            assert alert.severity == ContextSeverity.CRITICAL
            assert alert.usage_percent == usage
            assert "CRITICAL" in alert.message

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_alert_serialization_to_dict(self, context_warning_module) -> None:
        """Scenario: ContextAlert serializes correctly to dictionary.

        Given a ContextAlert with all fields populated
        When converting to dictionary
        Then it should contain all required fields with correct types.
        """
        ContextSeverity = context_warning_module["ContextSeverity"]
        ContextAlert = context_warning_module["ContextAlert"]

        alert = ContextAlert(
            severity=ContextSeverity.WARNING,
            usage_percent=FORTY_FIVE_PERCENT,
            message="Test message",
            recommendations=["Rec 1", "Rec 2"],
        )

        result = alert.to_dict()

        assert isinstance(result, dict)
        assert result["severity"] == "warning"
        assert result["usage_percent"] == FORTY_FIVE_PERCENT_DISPLAY
        assert result["message"] == "Test message"
        assert result["recommendations"] == ["Rec 1", "Rec 2"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_alert_serialization_to_json(self, context_warning_module) -> None:
        """Scenario: ContextAlert can be serialized to JSON.

        Given a ContextAlert
        When serializing to JSON
        Then it should produce valid JSON string.
        """
        ContextSeverity = context_warning_module["ContextSeverity"]
        ContextAlert = context_warning_module["ContextAlert"]

        alert = ContextAlert(
            severity=ContextSeverity.CRITICAL,
            usage_percent=FIFTY_PERCENT,
            message="Critical warning",
            recommendations=["Summarize immediately"],
        )

        # Should not raise
        json_str = json.dumps(alert.to_dict())
        parsed = json.loads(json_str)

        assert parsed["severity"] == "critical"
        assert parsed["usage_percent"] == FIFTY_PERCENT_DISPLAY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_threshold_constants_are_correct(self, context_warning_module) -> None:
        """Scenario: Threshold constants have correct values.

        Given the context warning module
        When checking threshold constants
        Then WARNING_THRESHOLD should be 0.40
        And CRITICAL_THRESHOLD should be 0.50.
        """
        assert context_warning_module["WARNING_THRESHOLD"] == FORTY_PERCENT
        assert context_warning_module["CRITICAL_THRESHOLD"] == FIFTY_PERCENT

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_usage_percent_rounded_correctly(self, context_warning_module) -> None:
        """Scenario: Usage percentage is rounded to one decimal place.

        Given a ContextAlert with precise usage value
        When converting to dictionary
        Then usage_percent should be rounded to one decimal.
        """
        ContextSeverity = context_warning_module["ContextSeverity"]
        ContextAlert = context_warning_module["ContextAlert"]

        # Test value with many decimal places
        usage = 0.456789
        alert = ContextAlert(
            severity=ContextSeverity.WARNING,
            usage_percent=usage,
            message="Test",
            recommendations=[],
        )

        result = alert.to_dict()

        # Should be rounded to 45.7
        expected_rounded = 45.7
        assert result["usage_percent"] == expected_rounded

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommendations_are_actionable(self, context_warning_module) -> None:
        """Scenario: Recommendations provide actionable guidance.

        Given context usage at WARNING or CRITICAL levels
        When assessing context usage
        Then recommendations should include specific actions.
        """
        assess = context_warning_module["assess_context_usage"]

        # Warning level should recommend monitoring and preparation
        warning_alert = assess(FORTY_FIVE_PERCENT)
        assert any(
            any(word in rec.lower() for word in ["monitor", "prepare", "invoke"])
            for rec in warning_alert.recommendations
        )

        # Critical level should recommend immediate action
        critical_alert = assess(SIXTY_PERCENT)
        assert any(
            any(
                word in rec.lower()
                for word in ["summarize", "delegate", "clear", "immediate"]
            )
            for rec in critical_alert.recommendations
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_severity_enum_values(self, context_warning_module) -> None:
        """Scenario: ContextSeverity enum has correct values.

        Given the ContextSeverity enum
        When checking its values
        Then it should have ok, warning, and critical levels.
        """
        ContextSeverity = context_warning_module["ContextSeverity"]

        assert ContextSeverity.OK.value == "ok"
        assert ContextSeverity.WARNING.value == "warning"
        assert ContextSeverity.CRITICAL.value == "critical"


class TestContextWarningEdgeCases:
    """Feature: Edge case handling for context warnings.

    As a robust hook
    I want to handle edge cases gracefully
    So that the hook never crashes unexpectedly
    """

    @pytest.fixture
    def context_warning_module(self):
        """Import the context_warning module."""
        import importlib.util
        import sys
        from pathlib import Path

        hooks_path = Path(__file__).resolve().parent.parent.parent / "hooks"
        module_path = hooks_path / "context_warning.py"

        spec = importlib.util.spec_from_file_location("context_warning", module_path)
        context_warning = importlib.util.module_from_spec(spec)
        sys.modules["context_warning"] = context_warning
        spec.loader.exec_module(context_warning)

        return context_warning

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_negative_usage_raises(self, context_warning_module) -> None:
        """Scenario: Negative usage value raises ValueError.

        Given a negative context usage value
        When assessing context usage
        Then it should raise ValueError.
        """
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            context_warning_module.assess_context_usage(-0.1)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_over_100_percent_raises(self, context_warning_module) -> None:
        """Scenario: Usage over 100% raises ValueError.

        Given context usage over 1.0 (100%)
        When assessing context usage
        Then it should raise ValueError.
        """
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            context_warning_module.assess_context_usage(1.1)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_at_exactly_zero(self, context_warning_module) -> None:
        """Scenario: Context at exactly 0% is OK.

        Given context usage at exactly 0%
        When assessing context usage
        Then severity should be OK.
        """
        alert = context_warning_module.assess_context_usage(0.0)
        assert alert.severity == context_warning_module.ContextSeverity.OK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_at_exactly_100_percent(self, context_warning_module) -> None:
        """Scenario: Context at exactly 100% is CRITICAL.

        Given context usage at exactly 100%
        When assessing context usage
        Then severity should be CRITICAL.
        """
        alert = context_warning_module.assess_context_usage(1.0)
        assert alert.severity == context_warning_module.ContextSeverity.CRITICAL

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_just_below_warning(self, context_warning_module) -> None:
        """Scenario: Context at 39.99% is OK.

        Given context usage just below 40%
        When assessing context usage
        Then severity should be OK.
        """
        alert = context_warning_module.assess_context_usage(0.3999)
        assert alert.severity == context_warning_module.ContextSeverity.OK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_just_below_critical(self, context_warning_module) -> None:
        """Scenario: Context at 49.99% is WARNING.

        Given context usage just below 50%
        When assessing context usage
        Then severity should be WARNING.
        """
        alert = context_warning_module.assess_context_usage(0.4999)
        assert alert.severity == context_warning_module.ContextSeverity.WARNING


class TestFormatHookOutput:
    """Feature: Hook output formatting.

    As a hook
    I want correct JSON output format
    So that Claude Code can process warnings
    """

    @pytest.fixture
    def context_warning_module(self):
        """Import the context_warning module."""
        import importlib.util
        import sys
        from pathlib import Path

        hooks_path = Path(__file__).resolve().parent.parent.parent / "hooks"
        module_path = hooks_path / "context_warning.py"

        spec = importlib.util.spec_from_file_location("context_warning", module_path)
        context_warning = importlib.util.module_from_spec(spec)
        sys.modules["context_warning"] = context_warning
        spec.loader.exec_module(context_warning)

        return context_warning

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warning_output_has_additional_context(
        self, context_warning_module
    ) -> None:
        """Scenario: WARNING alert includes additionalContext.

        Given a WARNING severity alert
        When formatting hook output
        Then additionalContext should be present.
        """
        alert = context_warning_module.assess_context_usage(0.45)
        output = context_warning_module.format_hook_output(alert)

        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
        assert "additionalContext" in output["hookSpecificOutput"]
        assert "WARNING" in output["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_output_has_additional_context(
        self, context_warning_module
    ) -> None:
        """Scenario: CRITICAL alert includes additionalContext.

        Given a CRITICAL severity alert
        When formatting hook output
        Then additionalContext should be present with recommendations.
        """
        alert = context_warning_module.assess_context_usage(0.60)
        output = context_warning_module.format_hook_output(alert)

        assert "additionalContext" in output["hookSpecificOutput"]
        assert "CRITICAL" in output["hookSpecificOutput"]["additionalContext"]
        assert "Recommendations:" in output["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ok_output_no_additional_context(self, context_warning_module) -> None:
        """Scenario: OK alert has no additionalContext.

        Given an OK severity alert
        When formatting hook output
        Then additionalContext should NOT be present.
        """
        alert = context_warning_module.assess_context_usage(0.20)
        output = context_warning_module.format_hook_output(alert)

        assert "additionalContext" not in output["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_output_is_json_serializable(self, context_warning_module) -> None:
        """Scenario: Hook output can be serialized to JSON.

        Given any alert
        When formatting and serializing to JSON
        Then it should produce valid JSON.
        """
        alert = context_warning_module.assess_context_usage(0.55)
        output = context_warning_module.format_hook_output(alert)

        # Should not raise
        json_str = json.dumps(output)
        parsed = json.loads(json_str)

        assert "hookSpecificOutput" in parsed


class TestGetContextUsageFromEnv:
    """Feature: Environment variable reading.

    As a hook
    I want to read context usage from environment
    So that I can integrate with Claude Code
    """

    @pytest.fixture
    def context_warning_module(self):
        """Import the context_warning module."""
        import importlib.util
        import sys
        from pathlib import Path

        hooks_path = Path(__file__).resolve().parent.parent.parent / "hooks"
        module_path = hooks_path / "context_warning.py"

        spec = importlib.util.spec_from_file_location("context_warning", module_path)
        context_warning = importlib.util.module_from_spec(spec)
        sys.modules["context_warning"] = context_warning
        spec.loader.exec_module(context_warning)

        return context_warning

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reads_from_env_variable(self, context_warning_module, monkeypatch) -> None:
        """Scenario: Read usage from CLAUDE_CONTEXT_USAGE.

        Given CLAUDE_CONTEXT_USAGE environment variable is set
        When getting context usage
        Then it should return the float value.
        """
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.45")
        usage = context_warning_module.get_context_usage_from_env()
        assert usage == 0.45

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_without_env(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: Returns None without environment variable.

        Given CLAUDE_CONTEXT_USAGE is not set
        When getting context usage
        Then it should return None.
        """
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        usage = context_warning_module.get_context_usage_from_env()
        assert usage is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_invalid_env_value(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: Handle invalid environment value gracefully.

        Given invalid CLAUDE_CONTEXT_USAGE value
        When getting context usage
        Then it should return None (not crash).
        """
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "not-a-number")
        usage = context_warning_module.get_context_usage_from_env()
        assert usage is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_env_value(self, context_warning_module, monkeypatch) -> None:
        """Scenario: Handle empty environment value.

        Given empty CLAUDE_CONTEXT_USAGE value
        When getting context usage
        Then it should return None.
        """
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "")
        usage = context_warning_module.get_context_usage_from_env()
        assert usage is None


class TestMainEntryPoint:
    """Feature: Hook main entry point.

    As a hook
    I want main() to handle various inputs correctly
    So that the hook is robust in production
    """

    @pytest.fixture
    def context_warning_module(self):
        """Import the context_warning module."""
        import importlib.util
        import sys
        from pathlib import Path

        hooks_path = Path(__file__).resolve().parent.parent.parent / "hooks"
        module_path = hooks_path / "context_warning.py"

        spec = importlib.util.spec_from_file_location("context_warning", module_path)
        context_warning = importlib.util.module_from_spec(spec)
        sys.modules["context_warning"] = context_warning
        spec.loader.exec_module(context_warning)

        return context_warning

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_no_context_usage(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: main() with no context usage outputs minimal JSON.

        Given no context usage available from env or stdin
        When running main
        Then it should output minimal valid JSON.
        """
        from io import StringIO

        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert data["hookSpecificOutput"]["hookEventName"] == "PreToolUse"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_warning_level(self, context_warning_module, monkeypatch) -> None:
        """Scenario: main() with 45% usage outputs WARNING.

        Given 45% context usage in environment
        When running main
        Then it should output WARNING alert with additionalContext.
        """
        from io import StringIO

        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.45")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" in data["hookSpecificOutput"]
        assert "WARNING" in data["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_ok_level(self, context_warning_module, monkeypatch) -> None:
        """Scenario: main() with 20% usage outputs minimal JSON.

        Given 20% context usage in environment
        When running main
        Then it should output JSON without additionalContext.
        """
        from io import StringIO

        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.20")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" not in data["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_invalid_json_input(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: main() handles malformed JSON on stdin.

        Given malformed JSON on stdin
        When running main
        Then it should handle gracefully and return 0.
        """
        from io import StringIO

        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr("sys.stdin", StringIO("not valid json {"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        # Should still output valid JSON
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "hookSpecificOutput" in data

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_hook_input_usage(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: main() reads usage from hook input JSON.

        Given context_usage in hook input JSON
        When running main with no env var
        Then it should use the hook input value.
        """
        from io import StringIO

        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        hook_input = json.dumps({"context_usage": 0.55})
        monkeypatch.setattr("sys.stdin", StringIO(hook_input))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "CRITICAL" in data["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_env_takes_priority_over_input(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: Environment variable takes priority over hook input.

        Given both env var (20%) and hook input (55%) have usage
        When running main
        Then env var should be used (OK, not CRITICAL).
        """
        from io import StringIO

        hook_input = json.dumps({"context_usage": 0.55})  # Would be CRITICAL
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.20")  # OK
        monkeypatch.setattr("sys.stdin", StringIO(hook_input))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        # Should be OK (env) not CRITICAL (input)
        assert "additionalContext" not in data["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_critical_level(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: main() with 60% usage outputs CRITICAL.

        Given 60% context usage in environment
        When running main
        Then it should output CRITICAL alert.
        """
        from io import StringIO

        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.60")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "additionalContext" in data["hookSpecificOutput"]
        assert "CRITICAL" in data["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_invalid_usage_value(
        self, context_warning_module, monkeypatch
    ) -> None:
        """Scenario: main() handles invalid usage value from hook input.

        Given invalid context_usage value (negative) in hook input
        When running main
        Then it should handle gracefully and return minimal output.
        """
        from io import StringIO

        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        hook_input = json.dumps({"context_usage": -0.5})
        monkeypatch.setattr("sys.stdin", StringIO(hook_input))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "hookSpecificOutput" in data
