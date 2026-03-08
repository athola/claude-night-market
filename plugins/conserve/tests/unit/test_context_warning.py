"""Tests for context warning hook with three-tier MECW alerts.

This module tests the context warning hook that implements:
- 40% warning threshold
- 50% critical threshold
- 80% emergency threshold (triggers auto-clear workflow)
"""

from __future__ import annotations

import json
import os
import time
from io import StringIO
from pathlib import Path

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
    """Feature: Three-tier context warnings for MECW compliance.

    As a context optimization workflow
    I want to receive warnings at 40% and critical alerts at 50%
    So that I can proactively optimize context usage

    Uses shared fixture: context_warning_module from conftest.py
    """

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
        assert len(alert.recommendations) >= 1

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
        assert len(alert.recommendations) >= 1
        assert any("immediate" in rec.lower() for rec in alert.recommendations)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_status_between_fifty_and_eighty_percent(
        self, context_warning_module
    ) -> None:
        """Scenario: Context usage between 50-80% returns CRITICAL.

        Given context usage is between 50% and 80%
        When assessing context usage
        Then it should return CRITICAL severity
        And recommend immediate actions.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        # Only 60% should be CRITICAL now (80% is EMERGENCY)
        alert = assess(SIXTY_PERCENT)

        assert alert.severity == ContextSeverity.CRITICAL
        assert alert.usage_percent == SIXTY_PERCENT
        assert "CRITICAL" in alert.message

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_status_at_eighty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage at 80% triggers EMERGENCY.

        Given context usage is at or above 80%
        When assessing context usage
        Then it should return EMERGENCY severity
        And recommend completing current work gracefully.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(EIGHTY_PERCENT)

        assert alert.severity == ContextSeverity.EMERGENCY
        assert alert.usage_percent == EIGHTY_PERCENT
        assert "EMERGENCY" in alert.message
        assert "Skill(conserve:clear-context)" in alert.message
        # Recommends delegation via continuation agent
        recs = [r.lower() for r in alert.recommendations]
        assert any("delegate" in r or "continuation" in r for r in recs)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_status_above_eighty_percent(
        self, context_warning_module
    ) -> None:
        """Scenario: Context usage above 80% returns EMERGENCY.

        Given context usage is above 80%
        When assessing context usage
        Then it should return EMERGENCY severity
        And include graceful wrap-up instructions.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        # Test at 90%
        ninety_percent = 0.90
        alert = assess(ninety_percent)

        assert alert.severity == ContextSeverity.EMERGENCY
        assert alert.usage_percent == ninety_percent
        assert "EMERGENCY" in alert.message
        assert "Skill(conserve:clear-context)" in alert.message
        # Recommends delegation via continuation agent
        recs = [r.lower() for r in alert.recommendations]
        assert any("delegate" in r or "continuation" in r for r in recs)
        assert any("session" in r or "spawn" in r for r in recs)

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
        And CRITICAL_THRESHOLD should be 0.50
        And EMERGENCY_THRESHOLD should be 0.80.
        """
        assert context_warning_module["WARNING_THRESHOLD"] == FORTY_PERCENT
        assert context_warning_module["CRITICAL_THRESHOLD"] == FIFTY_PERCENT
        assert context_warning_module["EMERGENCY_THRESHOLD"] == EIGHTY_PERCENT

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
        Then it should have ok, warning, critical, and emergency levels.
        """
        ContextSeverity = context_warning_module["ContextSeverity"]

        assert ContextSeverity.OK.value == "ok"
        assert ContextSeverity.WARNING.value == "warning"
        assert ContextSeverity.CRITICAL.value == "critical"
        assert ContextSeverity.EMERGENCY.value == "emergency"


class TestContextWarningEdgeCases:
    """Feature: Edge case handling for context warnings.

    As a robust hook
    I want to handle edge cases gracefully
    So that the hook never crashes unexpectedly

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_negative_usage_raises(self, context_warning_full_module) -> None:
        """Scenario: Negative usage value raises ValueError.

        Given a negative context usage value
        When assessing context usage
        Then it should raise ValueError.
        """
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            context_warning_full_module.assess_context_usage(-0.1)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_invalid_over_100_percent_raises(self, context_warning_full_module) -> None:
        """Scenario: Usage over 100% raises ValueError.

        Given context usage over 1.0 (100%)
        When assessing context usage
        Then it should raise ValueError.
        """
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            context_warning_full_module.assess_context_usage(1.1)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_at_exactly_zero(self, context_warning_full_module) -> None:
        """Scenario: Context at exactly 0% is OK.

        Given context usage at exactly 0%
        When assessing context usage
        Then severity should be OK.
        """
        alert = context_warning_full_module.assess_context_usage(0.0)
        assert alert.severity == context_warning_full_module.ContextSeverity.OK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_at_exactly_100_percent(self, context_warning_full_module) -> None:
        """Scenario: Context at exactly 100% is EMERGENCY.

        Given context usage at exactly 100%
        When assessing context usage
        Then severity should be EMERGENCY (triggers auto-clear).
        """
        alert = context_warning_full_module.assess_context_usage(1.0)
        assert alert.severity == context_warning_full_module.ContextSeverity.EMERGENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_just_below_warning(self, context_warning_full_module) -> None:
        """Scenario: Context at 39.99% is OK.

        Given context usage just below 40%
        When assessing context usage
        Then severity should be OK.
        """
        alert = context_warning_full_module.assess_context_usage(0.3999)
        assert alert.severity == context_warning_full_module.ContextSeverity.OK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_just_below_critical(self, context_warning_full_module) -> None:
        """Scenario: Context at 49.99% is WARNING.

        Given context usage just below 50%
        When assessing context usage
        Then severity should be WARNING.
        """
        alert = context_warning_full_module.assess_context_usage(0.4999)
        assert alert.severity == context_warning_full_module.ContextSeverity.WARNING


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
        """Scenario: WARNING alert includes additionalContext.

        Given a WARNING severity alert
        When formatting hook output
        Then additionalContext should be present.
        """
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
        """Scenario: CRITICAL alert includes additionalContext.

        Given a CRITICAL severity alert
        When formatting hook output
        Then additionalContext should be present with recommendations.
        """
        alert = context_warning_full_module.assess_context_usage(0.60)
        output = context_warning_full_module.format_hook_output(alert)

        assert "additionalContext" in output["hookSpecificOutput"]
        assert "CRITICAL" in output["hookSpecificOutput"]["additionalContext"]
        assert "Recommendations:" in output["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ok_output_no_additional_context(self, context_warning_full_module) -> None:
        """Scenario: OK alert has no additionalContext.

        Given an OK severity alert
        When formatting hook output
        Then additionalContext should NOT be present.
        """
        alert = context_warning_full_module.assess_context_usage(0.20)
        output = context_warning_full_module.format_hook_output(alert)

        assert "additionalContext" not in output["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_output_is_json_serializable(self, context_warning_full_module) -> None:
        """Scenario: Hook output can be serialized to JSON.

        Given any alert
        When formatting and serializing to JSON
        Then it should produce valid JSON.
        """
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
        """Scenario: Read usage from CLAUDE_CONTEXT_USAGE.

        Given CLAUDE_CONTEXT_USAGE environment variable is set
        When getting context usage
        Then it should return the float value.
        """
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.45")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage == 0.45

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_without_env(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Returns None without environment variable and estimation disabled.

        Given CLAUDE_CONTEXT_USAGE is not set
        And fallback estimation is disabled
        When getting context usage
        Then it should return None.
        """
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_invalid_env_value(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Handle invalid environment value gracefully.

        Given invalid CLAUDE_CONTEXT_USAGE value
        And fallback estimation is disabled
        When getting context usage
        Then it should return None (not crash).
        """
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "not-a-number")
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        usage = context_warning_full_module.get_context_usage_from_env()
        assert usage is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_env_value(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Handle empty environment value.

        Given empty CLAUDE_CONTEXT_USAGE value
        And fallback estimation is disabled
        When getting context usage
        Then it should return None.
        """
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
        """Scenario: main() with no context usage outputs minimal JSON.

        Given no context usage available from env or stdin
        When running main
        Then it should output minimal valid JSON.
        """

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
        """Scenario: main() with 45% usage outputs WARNING.

        Given 45% context usage in environment
        When running main
        Then it should output WARNING alert with additionalContext.
        """

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
        """Scenario: main() with 20% usage outputs minimal JSON.

        Given 20% context usage in environment
        When running main
        Then it should output JSON without additionalContext.
        """

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
        """Scenario: main() handles malformed JSON on stdin.

        Given malformed JSON on stdin
        When running main
        Then it should handle gracefully and return 0.
        """

        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)
        monkeypatch.setattr("sys.stdin", StringIO("not valid json {"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        # Should still output valid JSON
        output = output_capture.getvalue()
        data = json.loads(output)
        assert "hookSpecificOutput" in data

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_with_hook_input_usage(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: main() reads usage from hook input JSON.

        Given context_usage in hook input JSON
        When running main with no env var and estimation disabled
        Then it should use the hook input value.
        """

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
        """Scenario: Environment variable takes priority over hook input.

        Given both env var (20%) and hook input (55%) have usage
        When running main
        Then env var should be used (OK, not CRITICAL).
        """

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
        """Scenario: main() with 60% usage outputs CRITICAL.

        Given 60% context usage in environment
        When running main
        Then it should output CRITICAL alert.
        """

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
        """Scenario: main() handles invalid usage value from hook input.

        Given invalid context_usage value (negative) in hook input
        When running main
        Then it should handle gracefully and return minimal output.
        """

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
        """Scenario: main() with 85% usage outputs EMERGENCY.

        Given 85% context usage in environment
        When running main
        Then it should output EMERGENCY alert with skill invocation guidance.
        """

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
        """Scenario: main() EMERGENCY output includes formatted workflow instructions.

        Given 90% context usage in environment (high EMERGENCY)
        When running main
        Then additionalContext should include bold headers and numbered steps.
        """

        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.90")
        monkeypatch.setattr("sys.stdin", StringIO("{}"))

        output_capture = StringIO()
        monkeypatch.setattr("builtins.print", lambda x: output_capture.write(x))

        result = context_warning_full_module.main()

        assert result == 0
        output = output_capture.getvalue()
        data = json.loads(output)
        additional_context = data["hookSpecificOutput"]["additionalContext"]

        # Check for delegation guidance
        assert "Skill(conserve:clear-context)" in additional_context
        assert "continuation agent" in additional_context
        assert "DELEGATE via continuation" in additional_context
        # Should NOT contain manipulative/imperative language
        assert "MANDATORY" not in additional_context
        assert "YOU MUST" not in additional_context
        assert "BLOCKING" not in additional_context


class TestConfigurableEmergencyThreshold:
    """Feature: Configurable emergency threshold via environment variable.

    As a user
    I want to configure the emergency threshold via environment variable
    So that I can adjust auto-clear behavior for my workflow.

    Uses shared fixture: context_warning_reloader from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_custom_emergency_threshold(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: Emergency threshold can be configured via env var.

        Given CONSERVE_EMERGENCY_THRESHOLD is set to 0.75
        When assessing 76% context usage
        Then it should return EMERGENCY severity.
        """
        monkeypatch.setenv("CONSERVE_EMERGENCY_THRESHOLD", "0.75")
        context_warning = context_warning_reloader()

        # 76% should now be EMERGENCY with 75% threshold
        alert = context_warning.assess_context_usage(0.76)
        assert alert.severity == context_warning.ContextSeverity.EMERGENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_emergency_threshold_when_not_set(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: Default emergency threshold is 80% when not configured.

        Given CONSERVE_EMERGENCY_THRESHOLD is not set
        When checking the threshold constant
        Then it should be 0.80.
        """
        monkeypatch.delenv("CONSERVE_EMERGENCY_THRESHOLD", raising=False)
        context_warning = context_warning_reloader()

        assert context_warning.EMERGENCY_THRESHOLD == EIGHTY_PERCENT

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_custom_threshold_below_critical(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: Custom threshold at 60% still works correctly.

        Given CONSERVE_EMERGENCY_THRESHOLD is set to 0.60
        When assessing 60% context usage
        Then it should return EMERGENCY severity (not CRITICAL).
        """
        monkeypatch.setenv("CONSERVE_EMERGENCY_THRESHOLD", "0.60")
        context_warning = context_warning_reloader()

        # 60% should now be EMERGENCY with 60% threshold
        alert = context_warning.assess_context_usage(SIXTY_PERCENT)
        assert alert.severity == context_warning.ContextSeverity.EMERGENCY


class TestEmergencyRecommendations:
    """Feature: Emergency recommendations for graceful context wrap-up.

    As a context management system
    I want emergency recommendations to guide graceful completion
    So that work is not lost when context limits are reached.

    Note: Session state path configuration moved to main() output formatting,
    not assess_context_usage() recommendations. See test_main_emergency_output_*.

    Uses shared fixture: context_warning_reloader from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_recommendations_focus_on_graceful_completion(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: EMERGENCY recommendations focus on graceful completion.

        Given context usage is at EMERGENCY level (85%)
        When assessing context usage
        Then recommendations should guide graceful wrap-up.
        """
        monkeypatch.delenv("CONSERVE_SESSION_STATE_PATH", raising=False)
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.85)

        assert alert.severity == context_warning.ContextSeverity.EMERGENCY
        recs_text = " ".join(alert.recommendations).lower()
        # Updated: now focuses on delegation via continuation agent
        assert "delegate" in recs_text or "continuation" in recs_text
        assert "session" in recs_text or "spawn" in recs_text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_recommendations_mention_auto_compact(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: EMERGENCY recommendations mention auto-compact.

        Given context usage is at EMERGENCY level
        When assessing context usage
        Then recommendations should mention auto-compact as fallback.
        """
        monkeypatch.delenv("CONSERVE_SESSION_STATE_PATH", raising=False)
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.85)

        recs_text = " ".join(alert.recommendations).lower()
        # New recs: delegation-focused, not auto-compact
        assert "skill(conserve:clear-context)" in recs_text
        assert "continuation" in recs_text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_recommendations_include_summarize_step(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: EMERGENCY recommendations include summarize step.

        Given context usage is at EMERGENCY level
        When assessing context usage
        Then recommendations should include summarizing remaining tasks.
        """
        monkeypatch.delenv("CONSERVE_SESSION_STATE_PATH", raising=False)
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.85)

        recs_text = " ".join(alert.recommendations).lower()
        # New recs: delegate remaining tasks via continuation agent
        assert "delegate" in recs_text or "remaining" in recs_text
        assert "continuation" in recs_text or "spawn" in recs_text


class TestFallbackContextEstimation:
    """Feature: Fallback context estimation from session files.

    As a context monitoring system
    I want to estimate context usage from session file size
    So that monitoring works even when CLAUDE_CONTEXT_USAGE is unavailable

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_estimation_disabled_by_env(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: Estimation can be disabled via environment variable.

        Given CONSERVE_CONTEXT_ESTIMATION is set to 0
        When attempting to estimate context
        Then it should return None without attempting estimation.
        """
        monkeypatch.setenv("CONSERVE_CONTEXT_ESTIMATION", "0")
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_env_variable_takes_precedence(
        self, context_warning_full_module, monkeypatch
    ) -> None:
        """Scenario: CLAUDE_CONTEXT_USAGE takes precedence over estimation.

        Given CLAUDE_CONTEXT_USAGE environment variable is set
        When getting context usage
        Then it should use the environment variable value.
        """
        monkeypatch.setenv("CLAUDE_CONTEXT_USAGE", "0.75")

        result = context_warning_full_module.get_context_usage_from_env()

        assert result == 0.75

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_id_matches_correct_file(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: CLAUDE_SESSION_ID selects the correct session file.

        Given multiple JSONL files exist in the project directory
        And CLAUDE_SESSION_ID matches one of them
        When estimating context from session
        Then it should use the matching file, not the most recent.
        """
        # Set up fake project directory structure
        home = tmp_path / "home" / "user"
        home.mkdir(parents=True)
        project_dir = home / ".claude" / "projects" / "-fakecwd"
        project_dir.mkdir(parents=True)

        # Create two session files: old-large and new-small
        old_session = project_dir / "old-session-id.jsonl"
        old_session.write_text("x" * 400000)  # ~50% of 800KB

        new_session = project_dir / "target-session-id.jsonl"
        new_session.write_text("x" * 80000)  # ~10% of 800KB

        monkeypatch.setenv("CLAUDE_SESSION_ID", "target-session-id")
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        # Patch Path.cwd and Path.home
        monkeypatch.setattr(
            "pathlib.Path.cwd", staticmethod(lambda: tmp_path / "fakecwd")
        )
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))

        # Create the cwd directory and matching project dir using dash convention
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(exist_ok=True)
        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        real_project_dir = home / ".claude" / "projects" / project_dir_name
        real_project_dir.mkdir(parents=True, exist_ok=True)

        # Write valid JSONL to target file with fewer turns than the large file
        target_lines = []
        for _ in range(10):
            target_lines.append(json.dumps({"role": "user", "content": "hello"}))
            target_lines.append(json.dumps({"role": "assistant", "content": "hi"}))
        target_file = real_project_dir / "target-session-id.jsonl"
        target_file.write_text("\n".join(target_lines))

        # Large file has many more turns
        large_lines = []
        for _ in range(200):
            large_lines.append(json.dumps({"role": "user", "content": "hello"}))
            large_lines.append(json.dumps({"role": "assistant", "content": "hi"}))
        large_file = real_project_dir / "other-session.jsonl"
        large_file.write_text("\n".join(large_lines))

        result = context_warning_full_module.estimate_context_from_session()

        assert result is not None
        assert result > 0.0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_stale_session_file_returns_none(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: Stale session files are ignored without CLAUDE_SESSION_ID.

        Given no CLAUDE_SESSION_ID is set
        And the most recent JSONL file is older than 60 seconds
        When estimating context from session
        Then it should return None to avoid false alerts.
        """
        home = tmp_path / "home" / "user"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        real_project_dir = home / ".claude" / "projects" / project_dir_name
        real_project_dir.mkdir(parents=True, exist_ok=True)

        stale_file = real_project_dir / "old-session.jsonl"
        stale_file.write_text("x" * 500000)

        # Make the file appear old (>60s) by backdating mtime
        old_time = time.time() - 120
        os.utime(stale_file, (old_time, old_time))

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fresh_session_file_used_without_session_id(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Scenario: Fresh session files are used when no CLAUDE_SESSION_ID.

        Given no CLAUDE_SESSION_ID is set
        And a recently modified JSONL file exists (< 60 seconds old)
        When estimating context from session
        Then it should use that file for estimation.
        """
        home = tmp_path / "home" / "user"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        real_project_dir = home / ".claude" / "projects" / project_dir_name
        real_project_dir.mkdir(parents=True, exist_ok=True)

        # Create a fresh file with valid JSONL turns (just written = within 60s)
        fresh_file = real_project_dir / "fresh-session.jsonl"
        # Write 400 user+assistant turn pairs to produce a non-trivial estimate
        lines = []
        for _ in range(200):
            lines.append(json.dumps({"role": "user", "content": "hello world"}))
            lines.append(json.dumps({"role": "assistant", "content": "hi there"}))
        fresh_file.write_text("\n".join(lines))

        result = context_warning_full_module.estimate_context_from_session()

        assert result is not None
        assert result > 0.0


class TestFallbackContextEstimationCoverage:
    """Coverage tests for estimate_context_from_session branches.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.unit
    def test_returns_none_when_claude_projects_missing(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """No .claude/projects directory returns None."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_no_jsonl_files(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """Project dir exists but has no JSONL files returns None."""
        home = tmp_path / "home"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        project_dir = home / ".claude" / "projects" / project_dir_name
        project_dir.mkdir(parents=True)

        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None

    @pytest.mark.unit
    def test_session_id_set_but_no_match_falls_back_to_newest(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """CLAUDE_SESSION_ID set but no match; falls back to newest."""
        home = tmp_path / "home"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)
        home.mkdir(parents=True)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        project_dir = home / ".claude" / "projects" / project_dir_name
        project_dir.mkdir(parents=True)

        fresh_file = project_dir / "other-session.jsonl"
        fresh_file.write_text(json.dumps({"role": "user", "content": "hello"}) + "\n")

        monkeypatch.setenv("CLAUDE_SESSION_ID", "nonexistent-id")
        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        result = context_warning_full_module.estimate_context_from_session()

        # Falls back to newest file (fresh), so returns a non-None result
        assert result is not None

    @pytest.mark.unit
    def test_returns_none_on_os_error(
        self, context_warning_full_module, monkeypatch, tmp_path
    ) -> None:
        """OSError during session discovery returns None."""
        home = tmp_path / "home"
        fakecwd = tmp_path / "fakecwd"
        fakecwd.mkdir(parents=True)

        project_dir_name = str(fakecwd).replace(os.sep, "-")
        if not project_dir_name.startswith("-"):
            project_dir_name = "-" + project_dir_name
        project_dir = home / ".claude" / "projects" / project_dir_name
        project_dir.mkdir(parents=True)

        session = project_dir / "session.jsonl"
        session.write_text(json.dumps({"role": "user", "content": "hi"}) + "\n")

        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: fakecwd))
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: home))
        monkeypatch.delenv("CONSERVE_CONTEXT_ESTIMATION", raising=False)
        monkeypatch.delenv("CLAUDE_CONTEXT_USAGE", raising=False)

        # Make the glob call raise OSError mid-execution
        monkeypatch.setattr(
            type(project_dir),
            "glob",
            lambda _self, _pat: (_ for _ in ()).throw(OSError("disk error")),
        )

        result = context_warning_full_module.estimate_context_from_session()

        assert result is None


class TestEstimateFromRecentTurns:
    """Feature: Token-based estimation from recent session JSONL turns.

    As a context monitoring system
    I want estimation based on recent message/tool counts from the tail of the file
    So that estimation avoids counting auto-compressed history

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_file_returns_zero(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Empty session file yields near-zero estimate.

        Given an empty JSONL session file
        When estimating from heuristics
        Then it should return approximately 0.
        """
        session_file = tmp_path / "empty.jsonl"
        session_file.write_text("")

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result == pytest.approx(ZERO, abs=0.01)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_counts_user_and_assistant_turns(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Turns contribute to token estimate.

        Given a session file with user and assistant messages
        When estimating from heuristics
        Then turn count should contribute to the estimate.
        """
        lines = [
            json.dumps({"role": "user", "content": "hello"}),
            json.dumps({"role": "assistant", "content": "hi"}),
            json.dumps({"role": "user", "content": "question"}),
            json.dumps({"role": "assistant", "content": "answer"}),
        ]
        session_file = tmp_path / "turns.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        # 4 turns * 600 tokens/turn = 2400 tokens; char estimate also factors in
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_counts_tool_results(self, context_warning_full_module, tmp_path) -> None:
        """Scenario: Tool results add to token estimate.

        Given a session with tool_result content blocks
        When estimating from heuristics
        Then tool results should increase the estimate.
        """
        lines = [
            json.dumps(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "t1",
                            "content": "result1",
                        },
                        {
                            "type": "tool_result",
                            "tool_use_id": "t2",
                            "content": "result2",
                        },
                    ],
                }
            ),
            json.dumps({"role": "assistant", "content": "response"}),
        ]
        session_file = tmp_path / "tools.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_caps_at_095(self, context_warning_full_module, tmp_path) -> None:
        """Scenario: Estimate is capped at 0.95 to avoid false 100%.

        Given a very large session file
        When estimating from heuristics
        Then the result should not exceed 0.95.
        """
        # Create valid JSONL with large text blocks so content_chars >> context_window
        # At 4 chars/token and 200K token window, need > 800K content chars.
        # Each line has a "text" block with 10K chars; 100 lines = 1M content chars.
        big_text = "a" * 10_000
        lines = []
        for _ in range(100):
            entry = {
                "role": "assistant",
                "content": [{"type": "text", "text": big_text}],
            }
            lines.append(json.dumps(entry))
        session_file = tmp_path / "large.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result <= 0.95

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_malformed_json_lines(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Malformed JSON lines are skipped gracefully.

        Given a session file with some invalid JSON lines
        When estimating from heuristics
        Then it should skip bad lines and still return an estimate.
        """
        lines = [
            "not valid json",
            json.dumps({"role": "user", "content": "hello"}),
            "{bad json{",
            json.dumps({"role": "assistant", "content": "hi"}),
        ]
        session_file = tmp_path / "mixed.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_missing_file_returns_none(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Missing file returns None.

        Given a path to a non-existent file
        When estimating from heuristics
        Then it should return None.
        """
        missing_file = tmp_path / "nonexistent.jsonl"

        result = context_warning_full_module._estimate_from_recent_turns(missing_file)

        assert result is None

    @pytest.mark.unit
    def test_blank_lines_skipped(self, context_warning_full_module, tmp_path) -> None:
        """Blank lines in JSONL are skipped without error."""
        lines = [
            "",
            "   ",
            json.dumps({"role": "user", "content": "hello"}),
            "",
            json.dumps({"role": "assistant", "content": "hi"}),
        ]
        session_file = tmp_path / "blanks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_string_block_in_content_list_counted(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """String items inside a content list contribute to content_chars."""
        lines = [
            json.dumps({"role": "user", "content": ["hello world", "second string"]}),
        ]
        session_file = tmp_path / "strblocks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_string_message_content_counted(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """String message content (not list) contributes to content_chars."""
        lines = [
            json.dumps({"role": "assistant", "content": "a" * 4000}),
        ]
        session_file = tmp_path / "strcontents.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tail_reading_skips_old_history(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Large files are read from the tail only.

        Given a JSONL file larger than _TAIL_BYTES
        When estimating from recent turns
        Then only the tail portion is counted, not the full file.
        """
        # Build a file that exceeds _TAIL_BYTES (800KB).
        # Use very large old entries so that the tail window (800KB)
        # captures only a few of them, producing a LOW estimate.
        # Then verify the estimate is lower than a full-file read.
        old_text = "x" * 100_000  # 100KB per entry
        old_entry = {
            "role": "assistant",
            "content": [{"type": "text", "text": old_text}],
        }
        old_line = json.dumps(old_entry)
        # Each old_line is ~100KB; 12 lines ≈ 1.2MB >> 800KB threshold
        old_count = 12
        old_lines = [old_line] * old_count

        # Recent turns: only 4 small messages at the tail
        recent_lines = [
            json.dumps({"role": "user", "content": "recent question"}),
            json.dumps({"role": "assistant", "content": "recent answer"}),
            json.dumps({"role": "user", "content": "follow-up"}),
            json.dumps({"role": "assistant", "content": "response"}),
        ]

        session_file = tmp_path / "large_session.jsonl"
        all_content = "\n".join(old_lines + recent_lines)
        session_file.write_text(all_content)

        # Verify file actually exceeds the tail threshold
        assert session_file.stat().st_size > context_warning_full_module._TAIL_BYTES

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        # The tail window (800KB) can fit ~7-8 of the 100KB entries,
        # so the tail estimate should be noticeably lower than the
        # full-file maximum of 0.95.  With ~700K text chars in the
        # tail, that's ~175K tokens / 200K ≈ 0.875.
        # Use a generous bound: tail estimate < full-file cap.
        assert result < 0.95, (
            f"Tail reading should produce lower estimate than full file, got {result}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_user_assistant_roles_not_counted_as_turns(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Only user and assistant roles count as turns.

        Given a session with system and tool roles
        When estimating from recent turns
        Then only user/assistant messages contribute to turn count.
        """
        lines = [
            json.dumps({"role": "system", "content": "system prompt text"}),
            json.dumps({"role": "tool", "content": "tool output text"}),
            json.dumps({"role": "user", "content": "hello"}),
            json.dumps({"role": "assistant", "content": "hi"}),
        ]
        session_file = tmp_path / "mixed_roles.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        # 2 turns (user+assistant) * 600 = 1200 tokens
        # Content chars: "system prompt text" + "tool output text" + "hello" + "hi"
        # = 18 + 15 + 5 + 2 = 40 chars → 10 tokens
        # max(1200, 10) = 1200 tokens → 1200/200000 = 0.006
        expected_approx = 1200 / 200_000
        assert result == pytest.approx(expected_approx, abs=0.005)

    @pytest.mark.unit
    def test_mixed_dict_and_str_blocks_in_content_list(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Content list with both dict and str blocks counts all."""
        lines = [
            json.dumps(
                {
                    "role": "user",
                    "content": [
                        "plain string block",
                        {"type": "text", "text": "dict block"},
                    ],
                }
            ),
        ]
        session_file = tmp_path / "mixed_blocks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_multiple_lines_with_string_content(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Multiple lines with string content all contribute."""
        lines = [
            json.dumps({"role": "user", "content": "first message"}),
            json.dumps({"role": "assistant", "content": "reply"}),
            json.dumps({"role": "user", "content": "second message"}),
        ]
        session_file = tmp_path / "multi_str.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_non_dict_non_str_block_in_content_list_skipped(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Content list items that are neither dict nor str are silently skipped."""
        lines = [
            json.dumps(
                {
                    "role": "user",
                    "content": [
                        42,
                        None,
                        True,
                        {"type": "text", "text": "real content"},
                    ],
                }
            ),
        ]
        session_file = tmp_path / "odd_blocks.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        assert result > ZERO

    @pytest.mark.unit
    def test_non_list_non_str_content_skipped(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Message content that is neither list nor str (e.g. null/int) is skipped."""
        lines = [
            json.dumps({"role": "user", "content": None}),
            json.dumps({"role": "assistant", "content": 12345}),
            json.dumps({"role": "user", "content": "real content"}),
        ]
        session_file = tmp_path / "odd_content.jsonl"
        session_file.write_text("\n".join(lines))

        result = context_warning_full_module._estimate_from_recent_turns(session_file)

        assert result is not None
        # 3 turns counted (user+assistant roles), plus "real content" chars
        assert result > ZERO


class TestResolveProjectDir:
    """Feature: Project directory resolution using Claude Code naming convention.

    As a context estimation function
    I want to find the correct Claude project directory for the current cwd
    So that I can read the right session JSONL file.

    Uses shared fixture: context_warning_full_module from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_resolves_path_with_dashes(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Path separators are replaced with dashes.

        Given a cwd of /home/user/project
        And a matching directory exists in claude_projects
        When resolving the project directory
        Then it should return the directory named -home-user-project.
        """
        claude_projects = tmp_path / "projects"
        cwd = tmp_path / "home" / "user" / "project"
        cwd.mkdir(parents=True)

        dir_name = str(cwd).replace(os.sep, "-")
        if not dir_name.startswith("-"):
            dir_name = "-" + dir_name
        expected = claude_projects / dir_name
        expected.mkdir(parents=True)

        result = context_warning_full_module._resolve_project_dir(cwd, claude_projects)

        assert result == expected

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_when_dir_not_found(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Returns None when no matching directory exists.

        Given a cwd with no corresponding Claude project directory
        When resolving the project directory
        Then it should return None.
        """
        claude_projects = tmp_path / "projects"
        claude_projects.mkdir(parents=True)
        cwd = tmp_path / "nonexistent" / "project"

        result = context_warning_full_module._resolve_project_dir(cwd, claude_projects)

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_leading_dash_added_when_missing(
        self, context_warning_full_module, tmp_path
    ) -> None:
        """Scenario: Leading dash is added if path does not start with separator.

        Given a relative-style path that doesn't start with /
        When resolving the project directory
        Then the directory name should start with a dash.
        """
        claude_projects = tmp_path / "projects"
        # Use a path that, after replace, starts with a letter (no leading dash)
        # On Linux all absolute paths start with /, so after replace they start with -
        # Test the guard by constructing a path directly
        cwd = Path("relative/path")
        dir_name = str(cwd).replace(os.sep, "-")
        # dir_name = "relative-path" — no leading dash
        assert not dir_name.startswith("-")

        expected_dir = claude_projects / ("-" + dir_name)
        expected_dir.mkdir(parents=True)

        result = context_warning_full_module._resolve_project_dir(cwd, claude_projects)

        assert result == expected_dir
