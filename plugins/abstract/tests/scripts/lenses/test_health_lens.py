"""Tests for HealthLens - identifies unused/orphaned components."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

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
