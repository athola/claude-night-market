"""Tests for the DORA metrics module.

DORA's State of DevOps research defines four delivery-performance metrics:
deployment frequency, lead time for changes, change failure rate, and time
to restore service. The thresholds for Elite/High/Medium/Low tiers come
directly from that research and are exercised here as boundary cases.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from minister.dora_metrics import (
    DEFAULT_FAILURE_LABEL,
    DeploymentEvent,
    DORAMetrics,
    FailureEvent,
    classify_change_failure_rate,
    classify_deployment_frequency,
    classify_lead_time,
    classify_time_to_restore,
    compute_metrics,
    format_report,
)


class TestClassifyDeploymentFrequency:
    def test_elite_threshold(self) -> None:
        assert classify_deployment_frequency(per_day=1.5) == "Elite"

    def test_elite_boundary(self) -> None:
        # >=1/day is Elite per DORA research
        assert classify_deployment_frequency(per_day=1.0) == "Elite"

    def test_high_boundary(self) -> None:
        # 1/week boundary: per_day == 1/7 must classify as High,
        # not Medium. Pins the `>=` in the High branch and would
        # fail if the inequality flipped to `>`.
        assert classify_deployment_frequency(per_day=1 / 7) == "High"

    def test_high_tier(self) -> None:
        # 1/week to 1/day is High
        assert classify_deployment_frequency(per_day=0.3) == "High"

    def test_medium_boundary(self) -> None:
        # 1/month boundary: per_day == 1/30 must classify as
        # Medium, not Low. Pins the `>=` in the Medium branch.
        assert classify_deployment_frequency(per_day=1 / 30) == "Medium"

    def test_medium_tier(self) -> None:
        # 1/month to 1/week
        assert classify_deployment_frequency(per_day=0.05) == "Medium"

    def test_low_tier(self) -> None:
        # < 1/month
        assert classify_deployment_frequency(per_day=0.01) == "Low"

    def test_zero(self) -> None:
        assert classify_deployment_frequency(per_day=0.0) == "Low"


class TestClassifyLeadTime:
    def test_elite_under_one_day(self) -> None:
        assert classify_lead_time(hours=12.0) == "Elite"

    def test_elite_boundary(self) -> None:
        assert classify_lead_time(hours=24.0) == "Elite"

    def test_high_one_day_to_one_week(self) -> None:
        assert classify_lead_time(hours=72.0) == "High"

    def test_high_boundary(self) -> None:
        # 1 week boundary: 24*7 hours must classify as High,
        # not Medium. Pins the `<=` in the High branch.
        assert classify_lead_time(hours=24 * 7) == "High"

    def test_medium_one_week_to_one_month(self) -> None:
        assert classify_lead_time(hours=24 * 14) == "Medium"

    def test_medium_boundary(self) -> None:
        # 1 month boundary: 24*30 hours must classify as Medium,
        # not Low. Pins the `<=` in the Medium branch.
        assert classify_lead_time(hours=24 * 30) == "Medium"

    def test_low_over_one_month(self) -> None:
        assert classify_lead_time(hours=24 * 60) == "Low"


class TestClassifyChangeFailureRate:
    def test_elite_low_failure(self) -> None:
        assert classify_change_failure_rate(rate=0.05) == "Elite"

    def test_elite_boundary(self) -> None:
        # 0-15% is Elite
        assert classify_change_failure_rate(rate=0.15) == "Elite"

    def test_high_tier(self) -> None:
        assert classify_change_failure_rate(rate=0.25) == "High"

    def test_high_boundary(self) -> None:
        # 30% boundary must classify as High, not Medium.
        # Pins the `<=` in the High branch.
        assert classify_change_failure_rate(rate=0.30) == "High"

    def test_medium_tier(self) -> None:
        assert classify_change_failure_rate(rate=0.40) == "Medium"

    def test_medium_boundary(self) -> None:
        # 45% boundary must classify as Medium, not Low.
        # Pins the `<=` in the Medium branch.
        assert classify_change_failure_rate(rate=0.45) == "Medium"

    def test_low_tier(self) -> None:
        assert classify_change_failure_rate(rate=0.60) == "Low"


class TestClassifyTimeToRestore:
    """TRS is the only DORA classifier that uses strict `<` rather
    than `<=`, so its tier boundaries fall into the *next* tier,
    not the better one. These boundary tests pin that asymmetry so
    a future contributor who flips `<` to `<=` (perhaps to match
    the other three classifiers) breaks tests rather than silently
    regresses production behavior.
    """

    def test_elite_under_one_hour(self) -> None:
        assert classify_time_to_restore(hours=0.5) == "Elite"

    def test_elite_just_under_one_hour(self) -> None:
        # 0.999h is still under the strict `< 1.0` threshold.
        assert classify_time_to_restore(hours=0.999) == "Elite"

    def test_one_hour_is_high_not_elite(self) -> None:
        # Strict `<`: exactly 1.0h is High, not Elite.
        assert classify_time_to_restore(hours=1.0) == "High"

    def test_high_under_one_day(self) -> None:
        assert classify_time_to_restore(hours=12.0) == "High"

    def test_one_day_is_medium_not_high(self) -> None:
        # Strict `<`: exactly 24h is Medium, not High.
        assert classify_time_to_restore(hours=24.0) == "Medium"

    def test_medium_under_one_week(self) -> None:
        assert classify_time_to_restore(hours=24 * 3) == "Medium"

    def test_one_week_is_low_not_medium(self) -> None:
        # Strict `<`: exactly 24*7=168h is Low, not Medium.
        assert classify_time_to_restore(hours=24 * 7) == "Low"

    def test_low_over_one_week(self) -> None:
        assert classify_time_to_restore(hours=24 * 14) == "Low"


class TestComputeMetrics:
    """End-to-end metric computation from event lists."""

    def test_empty_events(self) -> None:
        metrics = compute_metrics(deployments=[], failures=[], window_days=30)
        # No deploys: DF=0, but other metrics should still produce something defensible
        assert metrics.deployment_frequency == 0.0
        assert metrics.change_failure_rate == 0.0

    def test_basic_window(self) -> None:
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        deployments = [
            DeploymentEvent(
                sha="a" * 40,
                deployed_at=now - timedelta(days=i),
                commit_at=now - timedelta(days=i, hours=2),
            )
            for i in range(10)
        ]
        metrics = compute_metrics(
            deployments=deployments,
            failures=[],
            window_days=30,
            window_end=now,
        )
        # 10 deploys / 30 days = 0.333/day -> High tier
        assert metrics.deployment_frequency == pytest.approx(10 / 30, rel=1e-3)
        # All deploys had 2h lead time
        assert metrics.lead_time_hours == pytest.approx(2.0, rel=1e-3)

    def test_change_failure_rate_calculation(self) -> None:
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        deployments = [
            DeploymentEvent(
                sha=f"{i:040d}",
                deployed_at=now - timedelta(hours=i),
                commit_at=now - timedelta(hours=i),
            )
            for i in range(10)
        ]
        # Two deployments triggered failures
        failures = [
            FailureEvent(
                opened_at=now - timedelta(hours=1, minutes=30),
                resolved_at=now - timedelta(hours=1),
            ),
            FailureEvent(
                opened_at=now - timedelta(hours=3, minutes=30),
                resolved_at=now - timedelta(hours=3),
            ),
        ]
        metrics = compute_metrics(
            deployments=deployments,
            failures=failures,
            window_days=30,
            window_end=now,
        )
        assert metrics.change_failure_rate == pytest.approx(0.2, rel=1e-3)

    def test_time_to_restore_median(self) -> None:
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        failures = [
            FailureEvent(
                opened_at=now - timedelta(hours=10),
                resolved_at=now - timedelta(hours=9),
            ),
            FailureEvent(
                opened_at=now - timedelta(hours=8),
                resolved_at=now - timedelta(hours=4),
            ),
            FailureEvent(
                opened_at=now - timedelta(hours=6),
                resolved_at=now - timedelta(hours=4),
            ),
        ]
        metrics = compute_metrics(
            deployments=[],
            failures=failures,
            window_days=30,
            window_end=now,
        )
        # restore times: [1h, 4h, 2h]; median is 2h
        assert metrics.time_to_restore_hours == pytest.approx(2.0, rel=1e-3)

    def test_unresolved_failures_excluded_from_trs(self) -> None:
        """Unresolved failures should not contribute to median TRS."""
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        failures = [
            FailureEvent(
                opened_at=now - timedelta(hours=10),
                resolved_at=now - timedelta(hours=9),
            ),
            FailureEvent(opened_at=now - timedelta(hours=5), resolved_at=None),
        ]
        metrics = compute_metrics(
            deployments=[], failures=failures, window_days=30, window_end=now
        )
        # Only one resolved failure, restore time 1h
        assert metrics.time_to_restore_hours == pytest.approx(1.0, rel=1e-3)


class TestDORAMetricsTier:
    def test_tier_returns_per_metric_classification(self) -> None:
        m = DORAMetrics(
            deployment_frequency=2.0,
            lead_time_hours=12.0,
            change_failure_rate=0.05,
            time_to_restore_hours=0.5,
        )
        tiers = m.tier()
        assert tiers["deployment_frequency"] == "Elite"
        assert tiers["lead_time"] == "Elite"
        assert tiers["change_failure_rate"] == "Elite"
        assert tiers["time_to_restore"] == "Elite"

    def test_bottleneck_identifies_weakest(self) -> None:
        m = DORAMetrics(
            deployment_frequency=2.0,  # Elite
            lead_time_hours=12.0,  # Elite
            change_failure_rate=0.50,  # Low
            time_to_restore_hours=0.5,  # Elite
        )
        assert m.bottleneck() == "change_failure_rate"

    def test_bottleneck_ties_break_deterministically(self) -> None:
        # Two Low metrics; first declared wins for stability
        m = DORAMetrics(
            deployment_frequency=0.01,  # Low
            lead_time_hours=24.0,  # Elite
            change_failure_rate=0.60,  # Low
            time_to_restore_hours=1.0,  # High
        )
        # deployment_frequency declared first in dataclass order
        assert m.bottleneck() == "deployment_frequency"

    def test_overall_tier_is_weakest(self) -> None:
        m = DORAMetrics(
            deployment_frequency=2.0,  # Elite
            lead_time_hours=72.0,  # High
            change_failure_rate=0.05,  # Elite
            time_to_restore_hours=0.5,  # Elite
        )
        assert m.overall_tier() == "High"


class TestFormatReport:
    def test_includes_all_four_metrics(self) -> None:
        m = DORAMetrics(
            deployment_frequency=4.2,
            lead_time_hours=2.1,
            change_failure_rate=0.08,
            time_to_restore_hours=0.75,
        )
        report = format_report(m, window_days=30)
        assert "Deployment Frequency" in report
        assert "Lead Time for Changes" in report
        assert "Change Failure Rate" in report
        assert "Time to Restore Service" in report

    def test_marks_bottleneck(self) -> None:
        m = DORAMetrics(
            deployment_frequency=4.2,
            lead_time_hours=2.1,
            change_failure_rate=0.40,  # Medium - bottleneck
            time_to_restore_hours=0.75,
        )
        report = format_report(m, window_days=30)
        # The bottleneck row should be visually distinguishable
        assert "bottleneck" in report.lower() or "<-" in report or "←" in report

    def test_window_days_in_header(self) -> None:
        m = DORAMetrics(
            deployment_frequency=1.0,
            lead_time_hours=10.0,
            change_failure_rate=0.10,
            time_to_restore_hours=1.0,
        )
        report = format_report(m, window_days=14)
        assert "14" in report


class TestDefaults:
    def test_default_failure_label_is_bug(self) -> None:
        assert DEFAULT_FAILURE_LABEL == "bug"


# =============================================================================
# Collector and CLI tests (subprocess-mocked)
# =============================================================================


class TestCollectDeploymentsFromGit:
    """End-to-end via mocked subprocess output."""

    def test_parses_git_log_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from minister import dora_metrics

        sample = (
            "abc1234567890123456789012345678901234567|"
            "2026-04-15T10:00:00+00:00|2026-04-15T10:30:00+00:00\n"
            "def1234567890123456789012345678901234567|"
            "2026-04-16T11:00:00+00:00|2026-04-16T11:30:00+00:00\n"
        )

        def fake_run_git(args: list[str], cwd: object = None) -> str:
            return sample

        monkeypatch.setattr(dora_metrics, "_run_git", fake_run_git)
        events = dora_metrics.collect_deployments_from_git(
            branch="main",
            window_days=30,
            window_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert len(events) == 2
        assert events[0].sha == "abc1234567890123456789012345678901234567"

    def test_skips_malformed_lines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from minister import dora_metrics

        def fake_run_git(args: list[str], cwd: object = None) -> str:
            return "abc|2026-04-15T10:00:00+00:00\nshorty\n\n"

        monkeypatch.setattr(dora_metrics, "_run_git", fake_run_git)
        events = dora_metrics.collect_deployments_from_git(
            branch="main",
            window_days=30,
            window_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert events == []


class TestCollectFailuresFromGh:
    """gh CLI absence and JSON parsing edge cases."""

    def test_gh_missing_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess as _sub

        from minister import dora_metrics

        def raise_missing(*args: object, **kwargs: object) -> object:
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(_sub, "run", raise_missing)
        events = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert events == []

    def test_parses_gh_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess as _sub

        from minister import dora_metrics

        class FakeRun:
            stdout = (
                '[{"createdAt": "2026-04-20T10:00:00Z", '
                '"closedAt": "2026-04-20T11:30:00Z", "state": "CLOSED"}, '
                '{"createdAt": "2026-04-22T10:00:00Z", '
                '"closedAt": null, "state": "OPEN"}]'
            )

        def fake_run(*args: object, **kwargs: object) -> FakeRun:
            return FakeRun()

        monkeypatch.setattr(_sub, "run", fake_run)
        events = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert len(events) == 2
        assert events[0].resolved_at is not None
        assert events[1].resolved_at is None

    def test_invalid_json_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess as _sub

        from minister import dora_metrics

        class FakeRun:
            stdout = "not json {{{"

        def fake_run(*args: object, **kwargs: object) -> FakeRun:
            return FakeRun()

        monkeypatch.setattr(_sub, "run", fake_run)
        events = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert events == []


class TestRunCli:
    """End-to-end CLI smoke test with mocked collectors."""

    def test_human_report(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from minister import dora_metrics

        monkeypatch.setattr(
            dora_metrics, "collect_deployments_from_git", lambda **kw: []
        )
        monkeypatch.setattr(dora_metrics, "collect_failures_from_gh", lambda **kw: [])
        rc = dora_metrics.run_cli(["--window", "30"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "DORA Metrics" in out

    def test_json_output(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import json as _json

        from minister import dora_metrics

        monkeypatch.setattr(
            dora_metrics, "collect_deployments_from_git", lambda **kw: []
        )
        monkeypatch.setattr(dora_metrics, "collect_failures_from_gh", lambda **kw: [])
        rc = dora_metrics.run_cli(["--window", "30", "--json"])
        assert rc == 0
        payload = _json.loads(capsys.readouterr().out)
        assert payload["success"] is True
        assert payload["data"]["window_days"] == 30
        assert "tiers" in payload["data"]


class TestBuildParser:
    def test_parser_has_window_default(self) -> None:
        from minister.dora_metrics import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.window == 30
        assert args.failure_label == "bug"
