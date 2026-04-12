"""Tests for TrendLens - detects degradation/improvement over time."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from insight_types import AnalysisContext
from lenses.trend_lens import LENS_META, analyze


def _ctx(metrics=None, performance_history=None, improvement_memory=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=performance_history,
        improvement_memory=improvement_memory,
        trigger="stop",
    )


def test_lens_meta_fields():
    assert LENS_META["name"] == "trend-lens"
    assert LENS_META["weight"] == "lightweight"


def test_no_performance_history_yields_nothing():
    ctx = _ctx(performance_history=None)
    findings = analyze(ctx)
    assert findings == []


def test_degrading_skill_detected():
    """A skill with declining trend should produce a finding."""

    class MockTracker:
        def __init__(self):
            self.history = [
                {"skill_ref": "x:y", "score": 0.9},
                {"skill_ref": "x:y", "score": 0.5},
            ]

        def get_improvement_trend(self, ref):
            return -0.4  # degrading

    ctx = _ctx(performance_history=MockTracker())
    findings = analyze(ctx)
    assert len(findings) >= 1
    assert findings[0].type == "Trend"
    assert (
        "degrading" in findings[0].summary.lower()
        or "declining" in findings[0].summary.lower()
    )


def test_improving_skill_produces_positive_finding():
    class MockTracker:
        def __init__(self):
            self.history = [
                {"skill_ref": "x:y", "score": 0.5},
                {"skill_ref": "x:y", "score": 0.9},
            ]

        def get_improvement_trend(self, ref):
            return 0.4  # improving

    ctx = _ctx(performance_history=MockTracker())
    findings = analyze(ctx)
    assert len(findings) >= 1
    assert (
        "improving" in findings[0].summary.lower()
        or "recovery" in findings[0].summary.lower()
    )
