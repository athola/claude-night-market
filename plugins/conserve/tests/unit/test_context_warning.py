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
