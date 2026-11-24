"""Tests for DeltaLens - surfaces changes since last snapshot."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from insight_types import AnalysisContext
from lenses.delta_lens import LENS_META, analyze


def _ctx(metrics, previous_snapshot=None, **kw):
    return AnalysisContext(
        metrics=metrics,
        previous_snapshot=previous_snapshot,
        performance_history=None,
        improvement_memory=None,
        trigger="stop",
        **kw,
    )


def test_lens_meta_fields():
    assert LENS_META["name"] == "delta-lens"
    assert LENS_META["weight"] == "lightweight"
    assert "insight_types" in LENS_META


def test_no_previous_snapshot_yields_nothing():
    ctx = _ctx(metrics={"x:y": _skill(90.0, 100)}, previous_snapshot=None)
    findings = analyze(ctx)
    assert findings == []


def test_stable_metrics_yield_nothing():
    snap = {"x:y": {"success_rate": 90.0, "avg_duration_ms": 500}}
    ctx = _ctx(
        metrics={"x:y": _skill(90.0, 100, avg_duration_ms=500)},
        previous_snapshot=snap,
    )
    findings = analyze(ctx)
    assert findings == []


def test_success_rate_drop_detected():
    snap = {"x:y": {"success_rate": 90.0, "avg_duration_ms": 500}}
    ctx = _ctx(
        metrics={"x:y": _skill(70.0, 100, avg_duration_ms=500)},
        previous_snapshot=snap,
    )
    findings = analyze(ctx)
    assert len(findings) >= 1
    assert findings[0].type == "Trend"
    assert "70" in findings[0].summary or "dropped" in findings[0].summary.lower()


def test_new_skill_detected():
    snap = {}  # empty previous
    ctx = _ctx(
        metrics={"new:skill": _skill(50.0, 10)},
        previous_snapshot=snap,
    )
    findings = analyze(ctx)
    # New skill with 50% success rate should be flagged
    assert any("new:skill" in f.skill for f in findings)


def _skill(success_rate, total, avg_duration_ms=500):
    """Helper to create a mock SkillLogSummary-like dict."""

    class MockSummary:
        def __init__(self):
            self.success_rate = success_rate
            self.total_executions = total
            self.avg_duration_ms = avg_duration_ms
            self.max_duration_ms = avg_duration_ms * 2
            self.failure_count = int(total * (100 - success_rate) / 100)
            self.avg_rating = None
            self.common_friction = []
            self.recent_errors = []
            self.skill = "x:y"

    return MockSummary()


def test_zero_run_previous_window_is_not_a_recovery():
    """A window with no runs scores 0.0, which is no rate at all (#1071)."""
    snap = {"x:y": {"success_rate": 0.0, "avg_duration_ms": 0, "total_executions": 0}}
    ctx = _ctx(
        metrics={"x:y": _skill(100.0, 3, avg_duration_ms=0)},
        previous_snapshot=snap,
    )
    assert analyze(ctx) == []


def test_zero_run_current_window_is_not_a_collapse():
    snap = {"x:y": {"success_rate": 100.0, "avg_duration_ms": 0, "total_executions": 4}}
    ctx = _ctx(
        metrics={"x:y": _skill(0.0, 0, avg_duration_ms=0)},
        previous_snapshot=snap,
    )
    assert analyze(ctx) == []


def test_shift_between_windows_with_runs_is_still_reported():
    snap = {
        "x:y": {"success_rate": 90.0, "avg_duration_ms": 500, "total_executions": 5}
    }
    ctx = _ctx(
        metrics={"x:y": _skill(50.0, 4, avg_duration_ms=500)},
        previous_snapshot=snap,
    )
    assert [f.summary for f in analyze(ctx)] == ["success rate dropped from 90% to 50%"]
