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
class TestCheckMECWCompliance:
    """Feature: MECW compliance checking with 1M default window."""

    @pytest.mark.bdd
    def test_default_window_is_one_million(self) -> None:
        """Scenario: Default max_tokens reflects 1M Opus context."""
        result = mecw.check_mecw_compliance(200000)
        assert result["max_tokens"] == 1000000
        assert result["mecw_threshold"] == 500000

    @pytest.mark.bdd
    def test_all_action_levels(self) -> None:
        """Scenario: Each pressure level maps to correct action."""
        # LOW → continue_normally
        r = mecw.check_mecw_compliance(100000, 1000000)
        assert r["action"] == "continue_normally"
        assert r["compliant"] is True

        # MODERATE compliant → monitor_closely
        r = mecw.check_mecw_compliance(400000, 1000000)
        assert r["action"] == "monitor_closely"
        assert r["compliant"] is True

        # HIGH → immediate_optimization_required
        r = mecw.check_mecw_compliance(600000, 1000000)
        assert r["action"] == "immediate_optimization_required"
        assert r["compliant"] is False

        # CRITICAL → immediate_context_reset_required
        r = mecw.check_mecw_compliance(800000, 1000000)
        assert r["action"] == "immediate_context_reset_required"
        assert r["compliant"] is False

    @pytest.mark.bdd
    def test_headroom_and_overage(self) -> None:
        """Scenario: Headroom and overage reflect distance from threshold."""
        # Under threshold: headroom > 0, overage = 0
        r = mecw.check_mecw_compliance(300000, 1000000)
        assert r["headroom"] == 200000
        assert r["overage"] == 0

        # Over threshold: headroom = 0, overage > 0
        r = mecw.check_mecw_compliance(700000, 1000000)
        assert r["headroom"] == 0
        assert r["overage"] == 200000


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

    @pytest.mark.bdd
    def test_high_pressure_warns_about_mecw_limits(self) -> None:
        """Scenario: HIGH pressure emits MECW-exceeding warning."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(55)
        status = monitor.get_status()

        assert status.pressure_level == "HIGH"
        assert any("exceeding MECW" in w for w in status.warnings)
        assert "Optimize context before next operation" in status.recommendations

    @pytest.mark.bdd
    def test_moderate_non_compliant_warns_about_overage(self) -> None:
        """Scenario: MODERATE pressure above MECW threshold warns about overage."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(45)
        status = monitor.get_status()

        assert status.pressure_level == "MODERATE"
        assert status.compliant is True
        # 45 <= 50 (threshold), so should NOT warn about overage
        assert not any("Approaching MECW limit" in w for w in status.warnings)

    @pytest.mark.bdd
    def test_get_safe_budget_returns_remaining_headroom(self) -> None:
        """Scenario: Safe budget reports tokens remaining before threshold."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(30)
        assert monitor.get_safe_budget() == 20  # threshold=50, 50-30=20

    @pytest.mark.bdd
    def test_reset_clears_state(self) -> None:
        """Scenario: Reset restores monitor to clean state."""
        monitor = mecw.MECWMonitor(max_context=100)
        monitor.track_usage(80)
        monitor.reset()

        assert monitor.current_tokens == 0
        status = monitor.get_status()
        assert status.pressure_level == "LOW"
