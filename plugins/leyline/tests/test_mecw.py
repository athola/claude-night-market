"""Tests for MECW utilities."""

import pytest

from leyline import mecw


@pytest.mark.unit
class TestCalculateContextPressure:
    """Feature: Context pressure classification."""

    @pytest.mark.bdd
    def test_classifies_pressure_levels(self) -> None:
        """Scenario: Mapping usage ratios to pressure levels."""
        assert mecw.calculate_context_pressure(0, 100) == "LOW"
        assert mecw.calculate_context_pressure(40, 100) == "MODERATE"
        assert mecw.calculate_context_pressure(60, 100) == "HIGH"
        assert mecw.calculate_context_pressure(80, 100) == "CRITICAL"

    @pytest.mark.bdd
    def test_invalid_max_tokens_is_critical(self) -> None:
        """Scenario: Handling invalid max token values."""
        assert mecw.calculate_context_pressure(10, 0) == "CRITICAL"


@pytest.mark.unit
class TestMECWMonitor:
    """Feature: MECW monitoring warnings and recommendations."""

    @pytest.mark.bdd
    def test_emits_critical_warnings(self) -> None:
        """Scenario: CRITICAL pressure triggers warnings and actions."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(95)
        status = monitor.get_status()

        assert status.pressure_level == "CRITICAL"
        assert status.compliant is False
        assert any("CRITICAL" in warning for warning in status.warnings)
        assert "Execute context reset immediately" in status.recommendations

    @pytest.mark.bdd
    def test_detects_rapid_growth(self) -> None:
        """Scenario: Rapid growth in usage triggers warning."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(10)
        monitor.track_usage(15)
        monitor.track_usage(30)

        status = monitor.get_status()

        assert any(
            "Rapid context growth detected" in warning for warning in status.warnings
        )

    @pytest.mark.bdd
    def test_rejects_additional_tokens_when_over_limit(self) -> None:
        """Scenario: Additional tokens push usage over MECW threshold."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(60)

        can_proceed, issues = monitor.can_handle_additional(10)

        assert can_proceed is False
        assert any(
            "CRITICAL" in issue or "exceed MECW threshold" in issue for issue in issues
        )
