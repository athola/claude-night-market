"""Tests for the DORA metrics module.

DORA's State of DevOps research defines four delivery-performance metrics:
deployment frequency, lead time for changes, change failure rate, and time
to restore service. The thresholds for Elite/High/Medium/Low tiers come
directly from that research and are exercised here as boundary cases.
"""

from __future__ import annotations

import json as _json
import subprocess as _sub
import typing
from datetime import datetime, timedelta, timezone

import pytest

from minister import dora_metrics
from minister.dora_metrics import (
    DEFAULT_FAILURE_LABEL,
    CollectionResult,
    DeploymentEvent,
    DORAMetrics,
    FailureEvent,
    build_parser,
    classify_change_failure_rate,
    classify_deployment_frequency,
    classify_lead_time,
    classify_time_to_restore,
    compute_metrics,
    format_report,
)


class TestClassifyDeploymentFrequency:
    """Pins the DF tier boundaries: Elite/High/Medium/Low per DORA research."""

    def test_elite_threshold(self) -> None:
        """A rate comfortably above 1/day classifies as Elite."""
        assert classify_deployment_frequency(per_day=1.5) == "Elite"

    def test_elite_boundary(self) -> None:
        """Exactly 1/day is Elite (the `>=` boundary, per DORA research)."""
        assert classify_deployment_frequency(per_day=1.0) == "Elite"

    def test_high_boundary(self) -> None:
        """Exactly 1/week (per_day == 1/7) is High, not Medium.

        Pins the `>=` in the High branch and would fail if the
        inequality flipped to `>`.
        """
        assert classify_deployment_frequency(per_day=1 / 7) == "High"

    def test_high_tier(self) -> None:
        """A rate strictly between 1/week and 1/day classifies as High."""
        assert classify_deployment_frequency(per_day=0.3) == "High"

    def test_medium_boundary(self) -> None:
        """Exactly 1/month (per_day == 1/30) is Medium, not Low.

        Pins the `>=` in the Medium branch.
        """
        assert classify_deployment_frequency(per_day=1 / 30) == "Medium"

    def test_medium_tier(self) -> None:
        """A rate strictly between 1/month and 1/week classifies as Medium."""
        assert classify_deployment_frequency(per_day=0.05) == "Medium"

    def test_low_tier(self) -> None:
        """A rate below 1/month classifies as Low."""
        assert classify_deployment_frequency(per_day=0.01) == "Low"

    def test_zero(self) -> None:
        """Zero deploys per day is a well-defined Low, not an error case."""
        assert classify_deployment_frequency(per_day=0.0) == "Low"


class TestClassifyLeadTime:
    """Pins the lead-time tier boundaries: Elite/High/Medium/Low per DORA research."""

    def test_elite_under_one_day(self) -> None:
        """A lead time well under one day classifies as Elite."""
        assert classify_lead_time(hours=12.0) == "Elite"

    def test_elite_boundary(self) -> None:
        """Exactly 24 hours is Elite (the `<=` boundary)."""
        assert classify_lead_time(hours=24.0) == "Elite"

    def test_high_one_day_to_one_week(self) -> None:
        """A lead time strictly between one day and one week classifies as High."""
        assert classify_lead_time(hours=72.0) == "High"

    def test_high_boundary(self) -> None:
        """Exactly one week (24*7 hours) is High, not Medium.

        Pins the `<=` in the High branch.
        """
        assert classify_lead_time(hours=24 * 7) == "High"

    def test_medium_one_week_to_one_month(self) -> None:
        """A lead time strictly between one week and one month classifies as Medium."""
        assert classify_lead_time(hours=24 * 14) == "Medium"

    def test_medium_boundary(self) -> None:
        """Exactly one month (24*30 hours) is Medium, not Low.

        Pins the `<=` in the Medium branch.
        """
        assert classify_lead_time(hours=24 * 30) == "Medium"

    def test_low_over_one_month(self) -> None:
        """A lead time over one month classifies as Low."""
        assert classify_lead_time(hours=24 * 60) == "Low"


class TestClassifyChangeFailureRate:
    """Pins the CFR tier boundaries: Elite/High/Medium/Low per DORA research."""

    def test_elite_low_failure(self) -> None:
        """A failure rate well inside the 0-15% band classifies as Elite."""
        assert classify_change_failure_rate(rate=0.05) == "Elite"

    def test_elite_boundary(self) -> None:
        """Exactly 15% is still Elite, the top of the 0-15% band."""
        assert classify_change_failure_rate(rate=0.15) == "Elite"

    def test_high_tier(self) -> None:
        """A failure rate strictly between 15% and 30% classifies as High."""
        assert classify_change_failure_rate(rate=0.25) == "High"

    def test_high_boundary(self) -> None:
        """Exactly 30% is High, not Medium.

        Pins the `<=` in the High branch.
        """
        assert classify_change_failure_rate(rate=0.30) == "High"

    def test_medium_tier(self) -> None:
        """A failure rate strictly between 30% and 45% classifies as Medium."""
        assert classify_change_failure_rate(rate=0.40) == "Medium"

    def test_medium_boundary(self) -> None:
        """Exactly 45% is Medium, not Low.

        Pins the `<=` in the Medium branch.
        """
        assert classify_change_failure_rate(rate=0.45) == "Medium"

    def test_low_tier(self) -> None:
        """A failure rate above 45% classifies as Low."""
        assert classify_change_failure_rate(rate=0.60) == "Low"


class TestClassifyTimeToRestore:
    """Pins the TRS boundary asymmetry: this classifier uses strict `<`.

    TRS is the only DORA classifier that uses strict `<` rather than
    `<=`, so its tier boundaries fall into the *next* tier, not the
    better one. These boundary tests pin that asymmetry so a future
    contributor who flips `<` to `<=` (perhaps to match the other
    three classifiers) breaks tests rather than silently regressing
    production behavior.
    """

    def test_elite_under_one_hour(self) -> None:
        """A restore time well under one hour classifies as Elite."""
        assert classify_time_to_restore(hours=0.5) == "Elite"

    def test_elite_just_under_one_hour(self) -> None:
        """0.999h is still under the strict `< 1.0` threshold, so it stays Elite."""
        assert classify_time_to_restore(hours=0.999) == "Elite"

    def test_one_hour_is_high_not_elite(self) -> None:
        """Strict `<`: exactly 1.0h is High, not Elite."""
        assert classify_time_to_restore(hours=1.0) == "High"

    def test_high_under_one_day(self) -> None:
        """A restore time strictly between one hour and one day classifies as High."""
        assert classify_time_to_restore(hours=12.0) == "High"

    def test_one_day_is_medium_not_high(self) -> None:
        """Strict `<`: exactly 24h is Medium, not High."""
        assert classify_time_to_restore(hours=24.0) == "Medium"

    def test_medium_under_one_week(self) -> None:
        """A restore time strictly between one day and one week classifies as Medium."""
        assert classify_time_to_restore(hours=24 * 3) == "Medium"

    def test_one_week_is_low_not_medium(self) -> None:
        """Strict `<`: exactly 24*7=168h is Low, not Medium."""
        assert classify_time_to_restore(hours=24 * 7) == "Low"

    def test_low_over_one_week(self) -> None:
        """A restore time over one week classifies as Low."""
        assert classify_time_to_restore(hours=24 * 14) == "Low"


class TestComputeMetrics:
    """End-to-end metric computation from event lists."""

    def test_empty_events(self) -> None:
        """Empty input distinguishes "no signal" from "perfect" (issue #527).

        DF stays float (0 deploys/day is well-defined Low); CFR/LT/TRS
        become None (will classify as N/A, not Elite).
        """
        metrics = compute_metrics(deployments=[], failures=[], window_days=30)
        assert metrics.deployment_frequency == 0.0
        assert metrics.change_failure_rate is None
        assert metrics.lead_time_hours is None
        assert metrics.time_to_restore_hours is None

    def test_basic_window(self) -> None:
        """Deployment frequency and lead time are computed from a run of deploys."""
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
        """CFR is the ratio of failure-triggering deploys to total deploys."""
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
        """TRS is the median restore duration across resolved failures, not the mean."""
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
    """Tests for DORAMetrics.tier(), .bottleneck(), and .overall_tier()."""

    def test_tier_returns_per_metric_classification(self) -> None:
        """tier() maps each of the four metric values to its own DORA tier."""
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
        """bottleneck() names the single metric with the lowest tier."""
        m = DORAMetrics(
            deployment_frequency=2.0,  # Elite
            lead_time_hours=12.0,  # Elite
            change_failure_rate=0.50,  # Low
            time_to_restore_hours=0.5,  # Elite
        )
        assert m.bottleneck() == "change_failure_rate"

    def test_bottleneck_ties_break_deterministically(self) -> None:
        """When two metrics tie for weakest, the first declared field wins."""
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
        """overall_tier() reports the weakest tier across all four metrics."""
        m = DORAMetrics(
            deployment_frequency=2.0,  # Elite
            lead_time_hours=72.0,  # High
            change_failure_rate=0.05,  # Elite
            time_to_restore_hours=0.5,  # Elite
        )
        assert m.overall_tier() == "High"


class TestFormatReport:
    """Tests for the human-readable report renderer."""

    def test_includes_all_four_metrics(self) -> None:
        """The rendered report names all four DORA metrics by their full labels."""
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
        """The bottleneck row is visually distinguishable from the other three."""
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
        """The report header states the measurement window width in days."""
        m = DORAMetrics(
            deployment_frequency=1.0,
            lead_time_hours=10.0,
            change_failure_rate=0.10,
            time_to_restore_hours=1.0,
        )
        report = format_report(m, window_days=14)
        assert "14" in report


class TestDefaults:
    """Tests for module-level default constants."""

    def test_default_failure_label_is_bug(self) -> None:
        """The default GitHub label used to identify prod failures is "bug"."""
        assert DEFAULT_FAILURE_LABEL == "bug"


# =============================================================================
# Collector and CLI tests (subprocess-mocked)
# =============================================================================


class TestCollectDeploymentsFromGit:
    """End-to-end via mocked subprocess output."""

    def test_parses_git_log_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Well-formed `sha|author-date|commit-date` lines become DeploymentEvents."""
        sample = (
            "abc1234567890123456789012345678901234567|"
            "2026-04-15T10:00:00+00:00|2026-04-15T10:30:00+00:00\n"
            "def1234567890123456789012345678901234567|"
            "2026-04-16T11:00:00+00:00|2026-04-16T11:30:00+00:00\n"
        )

        def fake_run_git(args: list[str], cwd: object = None) -> str:
            return sample

        monkeypatch.setattr(dora_metrics, "_run_git", fake_run_git)
        result = dora_metrics.collect_deployments_from_git(
            branch="main",
            window_days=30,
            window_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert len(result.events) == 2
        assert result.events[0].sha == "abc1234567890123456789012345678901234567"
        assert result.partial is False

    def test_skips_malformed_lines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lines that are blank or have too few fields produce no events, not a crash."""

        def fake_run_git(args: list[str], cwd: object = None) -> str:
            return "abc|2026-04-15T10:00:00+00:00\nshorty\n\n"

        monkeypatch.setattr(dora_metrics, "_run_git", fake_run_git)
        result = dora_metrics.collect_deployments_from_git(
            branch="main",
            window_days=30,
            window_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert result.events == []

    def test_wrong_field_count_marks_partial(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A line with the wrong field count sets partial=True and warns (issue #575, B3).

        This used to be skipped silently. It must now set partial=True and
        emit a warning, like the malformed-timestamp branch, so a broken
        pretty-format cannot yield a silent Elite-tier report.
        """

        def fake_run_git(args: list[str], cwd: object = None) -> str:
            # Two fields instead of three (missing commit_iso).
            return "abc1234567890|2026-04-15T10:00:00+00:00\n"

        monkeypatch.setattr(dora_metrics, "_run_git", fake_run_git)
        result = dora_metrics.collect_deployments_from_git(
            branch="main",
            window_days=30,
            window_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert result.events == []
        assert result.partial is True
        assert len(result.warnings) >= 1


class TestCollectFailuresFromGh:
    """gh CLI absence and JSON parsing edge cases."""

    def test_gh_missing_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A missing `gh` binary produces an empty, partial result, not a crash."""

        def raise_missing(*args: object, **kwargs: object) -> object:
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(_sub, "run", raise_missing)
        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert result.events == []
        assert result.partial is True

    def test_parses_gh_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Well-formed gh JSON rows become FailureEvents, resolved and unresolved alike."""

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
        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert len(result.events) == 2
        assert result.events[0].resolved_at is not None
        assert result.events[1].resolved_at is None
        assert result.partial is False

    def test_invalid_json_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unparseable gh stdout produces an empty, partial result, not a crash."""

        class FakeRun:
            stdout = "not json {{{"

        def fake_run(*args: object, **kwargs: object) -> FakeRun:
            return FakeRun()

        monkeypatch.setattr(_sub, "run", fake_run)
        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert result.events == []
        assert result.partial is True


class TestRunCli:
    """End-to-end CLI smoke test with mocked collectors."""

    def test_human_report(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without --json, run_cli prints the human-readable report to stdout."""
        empty_clean = CollectionResult(events=[], partial=False, warnings=())
        monkeypatch.setattr(
            dora_metrics, "collect_deployments_from_git", lambda **kw: empty_clean
        )
        monkeypatch.setattr(
            dora_metrics, "collect_failures_from_gh", lambda **kw: empty_clean
        )
        rc = dora_metrics.run_cli(["--window", "30"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "DORA Metrics" in out

    def test_json_output(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """With --json, run_cli prints a parseable payload carrying window_days and tiers."""
        empty_clean = CollectionResult(events=[], partial=False, warnings=())
        monkeypatch.setattr(
            dora_metrics, "collect_deployments_from_git", lambda **kw: empty_clean
        )
        monkeypatch.setattr(
            dora_metrics, "collect_failures_from_gh", lambda **kw: empty_clean
        )
        rc = dora_metrics.run_cli(["--window", "30", "--json"])
        assert rc == 0
        payload = _json.loads(capsys.readouterr().out)
        assert payload["success"] is True
        assert payload["data"]["window_days"] == 30
        assert "tiers" in payload["data"]


class TestBuildParser:
    """Tests for the CLI argument parser's defaults."""

    def test_parser_has_window_default(self) -> None:
        """With no flags, --window defaults to 30 and --failure-label to "bug"."""
        parser = build_parser()
        args = parser.parse_args([])
        assert args.window == 30
        assert args.failure_label == "bug"


# =============================================================================
# Issue #526: CLI argument validation
# =============================================================================


class TestCliArgumentValidation:
    """The CLI must reject negative or zero windows and dash-prefixed branches."""

    def test_negative_window_rejected(self) -> None:
        """A negative --window would produce a future-dated window; argparse must reject it."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--window", "-5"])

    def test_zero_window_rejected(self) -> None:
        """A zero --window would divide by zero downstream; argparse must reject it."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--window", "0"])

    def test_positive_window_accepted(self) -> None:
        """A valid positive --window value parses through unchanged."""
        parser = build_parser()
        args = parser.parse_args(["--window", "7"])
        assert args.window == 7

    def test_branch_argument_separated_from_flags_in_git_log(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A branch value starting with '-' must not be interpreted by git log as a flag.

        The git log argv must place '--' before the branch.
        """
        captured: list[list[str]] = []

        def fake_run_git(args: list[str], cwd: object = None) -> str:
            captured.append(list(args))
            return ""

        monkeypatch.setattr(dora_metrics, "_run_git", fake_run_git)
        dora_metrics.collect_deployments_from_git(branch="--malicious", window_days=30)
        assert captured, "expected _run_git to be invoked"
        argv = captured[0]
        # Find the position of "--" and the branch, and ensure "--" precedes it
        # so git treats it as a positional rather than a flag.
        assert "--" in argv, "git log argv must include '--' separator"
        sep_idx = argv.index("--")
        assert "--malicious" in argv[sep_idx:], (
            "branch must follow the '--' separator, not precede it"
        )


# =============================================================================
# Issue #525: Collector partial flags and --strict and datetime resilience
# =============================================================================


class TestCollectionResult:
    """Collectors return a CollectionResult, not a bare list."""

    def test_collection_result_has_events_partial_warnings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A clean git collection returns the three-field envelope, not a bare list."""
        monkeypatch.setattr(dora_metrics, "_run_git", lambda *a, **kw: "")
        result = dora_metrics.collect_deployments_from_git(
            branch="main", window_days=30
        )
        # CollectionResult has .events, .partial, .warnings
        assert hasattr(result, "events")
        assert hasattr(result, "partial")
        assert hasattr(result, "warnings")
        assert isinstance(result.events, list)
        assert isinstance(result.partial, bool)
        assert result.partial is False  # happy path

    def test_gh_subprocess_failure_marks_partial(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing gh binary sets partial=True and adds a warning naming "gh"."""

        def raise_missing(*args: object, **kwargs: object) -> object:
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(_sub, "run", raise_missing)
        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert result.events == []
        assert result.partial is True
        assert any("gh" in w.lower() for w in result.warnings)

    def test_gh_invalid_json_marks_partial(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unparseable gh stdout sets partial=True and adds a warning naming "json"."""

        class FakeRun:
            stdout = "not json {{{"

        def fake_run(*args: object, **kwargs: object) -> FakeRun:
            return FakeRun()

        monkeypatch.setattr(_sub, "run", fake_run)
        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30
        )
        assert result.events == []
        assert result.partial is True
        assert any("json" in w.lower() for w in result.warnings)

    def test_malformed_git_timestamp_does_not_crash(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A malformed ISO timestamp on one line is skipped with a warning, not a crash."""
        # First line has a malformed ISO timestamp; second is valid.
        sample = (
            "abc1234567890123456789012345678901234567|"
            "not-a-real-date|2026-04-15T10:30:00+00:00\n"
            "def1234567890123456789012345678901234567|"
            "2026-04-16T11:00:00+00:00|2026-04-16T11:30:00+00:00\n"
        )
        monkeypatch.setattr(dora_metrics, "_run_git", lambda *a, **kw: sample)
        result = dora_metrics.collect_deployments_from_git(
            branch="main",
            window_days=30,
            window_end=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert len(result.events) == 1
        assert result.events[0].sha == "def1234567890123456789012345678901234567"
        assert result.partial is True
        assert any(
            "date" in w.lower() or "timestamp" in w.lower() for w in result.warnings
        )


class TestStrictFlag:
    """--strict makes any partial collection an exit-non-zero condition."""

    def test_strict_with_partial_exits_non_zero(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--strict turns a partial gh collection into a non-zero exit code."""
        # Force gh collector to fail

        def fake_failure_collect(**kwargs: object) -> object:
            return CollectionResult(events=[], partial=True, warnings=("gh broken",))

        def fake_deploy_collect(**kwargs: object) -> object:
            return CollectionResult(events=[], partial=False, warnings=())

        monkeypatch.setattr(
            dora_metrics, "collect_deployments_from_git", fake_deploy_collect
        )
        monkeypatch.setattr(
            dora_metrics, "collect_failures_from_gh", fake_failure_collect
        )
        rc = dora_metrics.run_cli(["--strict", "--window", "30", "--json"])
        assert rc != 0

    def test_strict_without_partial_exits_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--strict does not affect the exit code when both collectors are clean."""

        def fake_clean_collect(**kwargs: object) -> object:
            return CollectionResult(events=[], partial=False, warnings=())

        monkeypatch.setattr(
            dora_metrics, "collect_deployments_from_git", fake_clean_collect
        )
        monkeypatch.setattr(
            dora_metrics, "collect_failures_from_gh", fake_clean_collect
        )
        rc = dora_metrics.run_cli(["--strict", "--window", "30", "--json"])
        assert rc == 0


# =============================================================================
# Issue #527: Empty-window metrics should report N/A, not Elite
# =============================================================================


class TestEmptyWindowNotElite:
    """Issue #527: an empty window must report N/A, not the misleading Elite tier.

    A team that hasn't shipped anything should not look the same as a team
    that ships continuously with zero failures. Lead Time, Change Failure
    Rate, and Time to Restore Service all default to 0 when their input is
    empty. Under the previous behavior 0 classified as Elite,
    indistinguishable from "perfect quality." The fix returns None for
    these metrics when input is empty and surfaces "N/A" in the tier
    table. Deployment Frequency stays float since 0 deploys/day has a
    well-defined meaning (Low tier).
    """

    def test_empty_window_lt_is_none(self) -> None:
        """With no deploys, lead time has no samples and must be None, not 0."""
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        assert m.lead_time_hours is None

    def test_empty_window_cfr_is_none(self) -> None:
        """No deploys means CFR is undefined (no denominator), so it must be None."""
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        assert m.change_failure_rate is None

    def test_empty_window_trs_is_none(self) -> None:
        """With no failures, restore time has no samples and must be None, not 0."""
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        assert m.time_to_restore_hours is None

    def test_empty_window_df_is_zero_not_none(self) -> None:
        """DF is 0 deploys / 30 days = 0.0/day: well-defined, so it stays a float, not None."""
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        assert m.deployment_frequency == 0.0

    def test_empty_window_tier_table_reports_na(self) -> None:
        """tier() reports "N/A" for the three undefined metrics and "Low" for DF."""
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        tiers = m.tier()
        assert tiers["lead_time"] == "N/A"
        assert tiers["change_failure_rate"] == "N/A"
        assert tiers["time_to_restore"] == "N/A"
        # DF is well-defined zero -> Low, not N/A
        assert tiers["deployment_frequency"] == "Low"

    def test_empty_window_overall_tier_excludes_na(self) -> None:
        """overall_tier reports the weakest non-N/A metric, not "N/A" itself.

        DF=Low is the only computable metric here, so partial-data still
        gives the operator a tier floor for the metrics that ARE
        measurable.
        """
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        # DF=Low is the only computable metric -> Low overall
        assert m.overall_tier() == "Low"

    def test_empty_window_bottleneck_excludes_na(self) -> None:
        """Bottleneck names the weakest computable metric, not an N/A."""
        m = compute_metrics(deployments=[], failures=[], window_days=30)
        bn = m.bottleneck()
        # DF is the only computable; it's the bottleneck.
        assert bn == "deployment_frequency"

    def test_all_metrics_na_overall_is_na(self) -> None:
        """If somehow every metric is N/A, overall_tier reports N/A."""
        # Construct DORAMetrics directly with all-None to test the corner.
        metrics = DORAMetrics(
            deployment_frequency=None,
            lead_time_hours=None,
            change_failure_rate=None,
            time_to_restore_hours=None,
        )
        assert metrics.overall_tier() == "N/A"
        assert metrics.bottleneck() == "insufficient_data"

    def test_classifier_returns_na_on_none(self) -> None:
        """The four classifiers must accept None and return 'N/A'."""
        assert classify_lead_time(None) == "N/A"
        assert classify_change_failure_rate(None) == "N/A"
        assert classify_time_to_restore(None) == "N/A"
        assert classify_deployment_frequency(None) == "N/A"


# =============================================================================
# Issue #529: Type design refinements
# =============================================================================


class TestEventInvariants:
    """Issue #529: enforce datetime invariants at construction-time."""

    def test_failure_event_rejects_resolved_before_opened(self) -> None:
        """A FailureEvent with resolved_at < opened_at must raise at construction.

        A backwards pair is a data-integrity bug, not a sample to filter
        downstream.
        """
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="resolved_at"):
            FailureEvent(
                opened_at=now,
                resolved_at=now - timedelta(hours=1),  # backwards
            )

    def test_failure_event_accepts_resolved_equal_to_opened(self) -> None:
        """resolved_at == opened_at is a zero-duration but valid event."""
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        event = FailureEvent(opened_at=now, resolved_at=now)
        assert event.resolved_at == event.opened_at

    def test_failure_event_accepts_unresolved(self) -> None:
        """resolved_at=None means the incident is still open."""
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        event = FailureEvent(opened_at=now, resolved_at=None)
        assert event.resolved_at is None

    def test_failure_event_rejects_naive_opened_at(self) -> None:
        """A naive opened_at must raise at construction.

        Naive datetimes silently break window-comparison arithmetic;
        forcing tz-aware at construction catches the bug at the boundary
        instead of deep inside metric calculation.
        """
        now_naive = datetime(2026, 5, 1)  # no tzinfo
        with pytest.raises(ValueError, match="tz-aware|timezone"):
            FailureEvent(opened_at=now_naive)

    def test_failure_event_rejects_naive_resolved_at(self) -> None:
        """A naive resolved_at must raise at construction, same as a naive opened_at."""
        now = datetime(2026, 5, 1, tzinfo=timezone.utc)
        naive = datetime(2026, 5, 2)  # no tzinfo
        with pytest.raises(ValueError, match="tz-aware|timezone"):
            FailureEvent(opened_at=now, resolved_at=naive)

    def test_deployment_event_rejects_naive_datetimes(self) -> None:
        """DeploymentEvent enforces the same tz-aware invariant as FailureEvent."""
        naive = datetime(2026, 5, 1)
        with pytest.raises(ValueError, match="tz-aware|timezone"):
            DeploymentEvent(sha="a" * 40, deployed_at=naive, commit_at=naive)


class TestTierLiteral:
    """Issue #529: tier strings should be a constrained Literal type."""

    def test_tier_literal_exported(self) -> None:
        """The Tier Literal type alias must be exported.

        Without it, callers cannot type-check tier-bearing code paths.
        """
        assert hasattr(dora_metrics, "Tier")

    def test_tier_literal_values(self) -> None:
        """The Tier alias enumerates the four DORA tiers plus 'N/A'.

        Issue #527 added 'N/A' for metrics with no signal in the window.
        """
        # Resolve the Literal to its args.
        tier_alias = dora_metrics.Tier
        args = typing.get_args(tier_alias)
        assert set(args) == {"Low", "Medium", "High", "Elite", "N/A"}


class TestJsonPayloadPartialField:
    """JSON payload must surface the partial flag and warnings."""

    def test_partial_flag_present_in_json(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When the gh collector is partial, the JSON payload surfaces partial and warnings."""

        def fake_partial(**kwargs: object) -> object:
            return CollectionResult(events=[], partial=True, warnings=("gh broken",))

        def fake_clean(**kwargs: object) -> object:
            return CollectionResult(events=[], partial=False, warnings=())

        monkeypatch.setattr(dora_metrics, "collect_deployments_from_git", fake_clean)
        monkeypatch.setattr(dora_metrics, "collect_failures_from_gh", fake_partial)
        dora_metrics.run_cli(["--window", "30", "--json"])
        payload = _json.loads(capsys.readouterr().out)
        assert payload["data"]["partial"] is True
        assert "warnings" in payload["data"]
        assert any("gh" in w.lower() for w in payload["data"]["warnings"])
