"""Tests for context warning threshold severity logic.

Tests the three-tier severity assessment:
- OK (under 40%)
- WARNING (40-50%)
- CRITICAL (50-80%)
- EMERGENCY (80%+)
"""

from __future__ import annotations

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
        Then it should return WARNING severity.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        test_cases = [FORTY_FIVE_PERCENT, FORTY_NINE_PERCENT]

        for usage in test_cases:
            alert = assess(usage)
            assert alert.severity == ContextSeverity.WARNING

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_status_at_fifty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage at 50% triggers CRITICAL.

        Given context usage is exactly 50%
        When assessing context usage
        Then it should return CRITICAL severity.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(FIFTY_PERCENT)

        assert alert.severity == ContextSeverity.CRITICAL
        assert alert.usage_percent == FIFTY_PERCENT
        assert "CRITICAL" in alert.message
        assert len(alert.recommendations) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_critical_status_between_fifty_and_eighty_percent(
        self, context_warning_module
    ) -> None:
        """Scenario: Context usage between 50-80% returns CRITICAL.

        Given context usage is between 50% and 80%
        When assessing context usage
        Then it should return CRITICAL severity.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(SIXTY_PERCENT)
        assert alert.severity == ContextSeverity.CRITICAL

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_status_at_eighty_percent(self, context_warning_module) -> None:
        """Scenario: Context usage at 80% triggers EMERGENCY.

        Given context usage is exactly 80%
        When assessing context usage
        Then it should return EMERGENCY severity.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(EIGHTY_PERCENT)

        assert alert.severity == ContextSeverity.EMERGENCY
        assert alert.usage_percent == EIGHTY_PERCENT
        assert "EMERGENCY" in alert.message
        assert len(alert.recommendations) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_status_above_eighty_percent(
        self, context_warning_module
    ) -> None:
        """Scenario: Context usage above 80% stays EMERGENCY.

        Given context usage is above 80%
        When assessing context usage
        Then it should return EMERGENCY severity.
        """
        assess = context_warning_module["assess_context_usage"]
        ContextSeverity = context_warning_module["ContextSeverity"]

        alert = assess(0.90)
        assert alert.severity == ContextSeverity.EMERGENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_alert_serialization_to_dict(self, context_warning_module) -> None:
        """Scenario: Alert can be serialized to a dictionary."""
        assess = context_warning_module["assess_context_usage"]

        alert = assess(FORTY_FIVE_PERCENT)
        alert_dict = alert.to_dict()

        assert "severity" in alert_dict
        assert "usage_percent" in alert_dict
        assert "message" in alert_dict
        assert "recommendations" in alert_dict
        assert alert_dict["usage_percent"] == pytest.approx(
            FORTY_FIVE_PERCENT_DISPLAY, abs=0.1
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_alert_serialization_to_json(self, context_warning_module) -> None:
        """Scenario: Alert can be serialized to JSON."""
        assess = context_warning_module["assess_context_usage"]

        alert = assess(FIFTY_PERCENT)
        alert_dict = alert.to_dict()

        # Should not raise
        json_str = json.dumps(alert_dict)
        parsed = json.loads(json_str)

        assert "severity" in parsed
        assert parsed["usage_percent"] == pytest.approx(FIFTY_PERCENT_DISPLAY, abs=0.1)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_threshold_constants_are_correct(self, context_warning_module) -> None:
        """Scenario: Threshold constants match expected values."""
        assert context_warning_module["WARNING_THRESHOLD"] == FORTY_PERCENT
        assert context_warning_module["CRITICAL_THRESHOLD"] == FIFTY_PERCENT
        assert context_warning_module["EMERGENCY_THRESHOLD"] == EIGHTY_PERCENT

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_usage_percent_rounded_correctly(self, context_warning_module) -> None:
        """Scenario: Usage percent is stored correctly in alert."""
        assess = context_warning_module["assess_context_usage"]

        test_cases = [
            (TWENTY_PERCENT, TWENTY_PERCENT_DISPLAY),
            (FORTY_PERCENT, FORTY_PERCENT_DISPLAY),
            (FIFTY_PERCENT, FIFTY_PERCENT_DISPLAY),
            (SIXTY_PERCENT, SIXTY_PERCENT_DISPLAY),
            (EIGHTY_PERCENT, EIGHTY_PERCENT_DISPLAY),
        ]

        for usage, expected_display in test_cases:
            alert = assess(usage)
            assert alert.usage_percent == pytest.approx(usage, abs=0.001)
            alert_dict = alert.to_dict()
            assert alert_dict["usage_percent"] == pytest.approx(
                expected_display, abs=0.1
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommendations_are_actionable(self, context_warning_module) -> None:
        """Scenario: Recommendations are non-empty for WARNING and above."""
        assess = context_warning_module["assess_context_usage"]

        for usage in [FORTY_PERCENT, FIFTY_PERCENT, EIGHTY_PERCENT]:
            alert = assess(usage)
            assert len(alert.recommendations) >= 1
            for rec in alert.recommendations:
                assert len(rec) > 10  # Each recommendation is meaningful

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_severity_enum_values(self, context_warning_module) -> None:
        """Scenario: ContextSeverity enum has all expected values."""
        ContextSeverity = context_warning_module["ContextSeverity"]

        assert hasattr(ContextSeverity, "OK")
        assert hasattr(ContextSeverity, "WARNING")
        assert hasattr(ContextSeverity, "CRITICAL")
        assert hasattr(ContextSeverity, "EMERGENCY")


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
        """Scenario: Context at exactly 0% is OK."""
        alert = context_warning_full_module.assess_context_usage(0.0)
        assert alert.severity == context_warning_full_module.ContextSeverity.OK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_at_exactly_100_percent(self, context_warning_full_module) -> None:
        """Scenario: Context at exactly 100% is EMERGENCY."""
        alert = context_warning_full_module.assess_context_usage(1.0)
        assert alert.severity == context_warning_full_module.ContextSeverity.EMERGENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_just_below_warning(self, context_warning_full_module) -> None:
        """Scenario: Context at 39.99% is OK."""
        alert = context_warning_full_module.assess_context_usage(0.3999)
        assert alert.severity == context_warning_full_module.ContextSeverity.OK

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_boundary_just_below_critical(self, context_warning_full_module) -> None:
        """Scenario: Context at 49.99% is WARNING."""
        alert = context_warning_full_module.assess_context_usage(0.4999)
        assert alert.severity == context_warning_full_module.ContextSeverity.WARNING


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
        """Scenario: Emergency threshold can be configured via env var."""
        monkeypatch.setenv("CONSERVE_EMERGENCY_THRESHOLD", "0.75")
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.76)
        assert alert.severity == context_warning.ContextSeverity.EMERGENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_default_emergency_threshold_when_not_set(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: Default emergency threshold is 80% when not configured."""
        monkeypatch.delenv("CONSERVE_EMERGENCY_THRESHOLD", raising=False)
        context_warning = context_warning_reloader()

        assert context_warning.EMERGENCY_THRESHOLD == EIGHTY_PERCENT

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_custom_threshold_below_critical(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: Custom threshold at 60% triggers EMERGENCY at 60%."""
        monkeypatch.setenv("CONSERVE_EMERGENCY_THRESHOLD", "0.60")
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(SIXTY_PERCENT)
        assert alert.severity == context_warning.ContextSeverity.EMERGENCY


class TestEmergencyRecommendations:
    """Feature: Emergency recommendations for graceful context wrap-up.

    Uses shared fixture: context_warning_reloader from conftest.py
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_recommendations_focus_on_graceful_completion(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: EMERGENCY recommendations focus on graceful completion."""
        monkeypatch.delenv("CONSERVE_SESSION_STATE_PATH", raising=False)
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.85)

        assert alert.severity == context_warning.ContextSeverity.EMERGENCY
        recs_text = " ".join(alert.recommendations).lower()
        assert "delegate" in recs_text or "continuation" in recs_text
        assert "session" in recs_text or "spawn" in recs_text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_recommendations_mention_auto_compact(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: EMERGENCY recommendations mention auto-compact."""
        monkeypatch.delenv("CONSERVE_SESSION_STATE_PATH", raising=False)
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.85)

        recs_text = " ".join(alert.recommendations).lower()
        assert "skill(conserve:clear-context)" in recs_text
        assert "continuation" in recs_text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_emergency_recommendations_include_summarize_step(
        self, context_warning_reloader, monkeypatch
    ) -> None:
        """Scenario: EMERGENCY recommendations include summarize step."""
        monkeypatch.delenv("CONSERVE_SESSION_STATE_PATH", raising=False)
        context_warning = context_warning_reloader()

        alert = context_warning.assess_context_usage(0.85)

        recs_text = " ".join(alert.recommendations).lower()
        assert "delegate" in recs_text or "remaining" in recs_text
        assert "continuation" in recs_text or "spawn" in recs_text
