"""Tests for HealthLens - identifies unused/orphaned components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from insight_registry import InsightRegistry
from insight_types import AnalysisContext
from lenses.health_lens import LENS_META, analyze


def _ctx(metrics=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        trigger="stop",
    )


class MockSummary:
    """Stand-in for the aggregate-log summary row the health lens scores."""

    def __init__(self, skill, total=0, success_rate=100.0, failure_count=0):
        self.skill = skill
        self.total_executions = total
        self.success_rate = success_rate
        self.failure_count = failure_count
        self.avg_duration_ms = 100
        self.avg_rating = None
        self.common_friction = []
        self.recent_errors = []


def test_lens_meta_fields():
    assert LENS_META["name"] == "health-lens"
    assert LENS_META["weight"] == "lightweight"


def test_no_metrics_yields_nothing():
    ctx = _ctx(metrics={})
    findings = analyze(ctx)
    assert findings == []


def test_zero_execution_skills_detected():
    """Skills with 0 executions in 30 days should produce a Health Check."""
    metrics = {
        "a:active": MockSummary("a:active", total=50),
        "b:unused": MockSummary("b:unused", total=0),
        "c:unused2": MockSummary("c:unused2", total=0),
    }
    ctx = _ctx(metrics=metrics)
    findings = analyze(ctx)
    health_checks = [f for f in findings if f.type == "Health Check"]
    assert len(health_checks) >= 1
    assert (
        "unused" in health_checks[0].summary.lower()
        or "0 execution" in health_checks[0].summary.lower()
    )


def test_high_failure_ratio_detected():
    """Skills with extremely high failure counts should be flagged."""
    metrics = {
        "a:failing": MockSummary(
            "a:failing", total=100, success_rate=10.0, failure_count=90
        ),
    }
    ctx = _ctx(metrics=metrics)
    findings = analyze(ctx)
    assert len(findings) >= 1


def test_unused_skills_finding_posts_once_as_the_count_moves(tmp_path):
    """A new unused-skill count must not open a new Discussion (#1306)."""
    registry = InsightRegistry(state_path=tmp_path / "insights_posted.json")

    def unused(n):
        metrics = {f"p:s{i}": MockSummary(f"p:s{i}", total=0) for i in range(n)}
        return analyze(_ctx(metrics=metrics))[0]

    first, later = unused(27), unused(40)
    registry.record_posted(first, "https://example.com/1")

    assert first.summary != later.summary
    assert registry.check_local(later) == "skip"
