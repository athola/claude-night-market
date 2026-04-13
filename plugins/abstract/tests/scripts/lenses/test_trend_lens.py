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


# ── _analyze_improvement_memory tests ──────────────────────


def test_no_improvement_memory_yields_nothing():
    """GIVEN no improvement memory, WHEN analyzed, THEN no findings."""
    ctx = _ctx(improvement_memory=None)
    findings = analyze(ctx)
    assert findings == []


def test_improvement_memory_attribute_error_yields_nothing():
    """GIVEN a memory object that lacks expected methods,
    WHEN analyzed, THEN graceful fallback returns no findings.
    """

    class BrokenMemory:
        pass  # no get_effective_strategies / get_failed_strategies

    ctx = _ctx(improvement_memory=BrokenMemory())
    findings = analyze(ctx)
    assert findings == []


def test_improvement_memory_empty_strategies_yields_nothing():
    """GIVEN a memory with no effective or failed strategies,
    WHEN analyzed, THEN no findings produced.
    """

    class EmptyMemory:
        def get_effective_strategies(self):
            return []

        def get_failed_strategies(self):
            return []

    ctx = _ctx(improvement_memory=EmptyMemory())
    findings = analyze(ctx)
    assert findings == []


def test_low_success_rate_produces_high_finding():
    """GIVEN low improvement success rate with enough attempts,
    WHEN analyzed, THEN a high-severity finding is produced.
    """

    class LowSuccessMemory:
        def get_effective_strategies(self):
            return [{"change_summary": "good change", "improvement": 0.1}]

        def get_failed_strategies(self):
            # 5 failures + 1 success = 6 total, rate = 1/6 ≈ 17%
            return [
                {"change_summary": f"bad change {i}", "improvement": -0.05}
                for i in range(5)
            ]

    ctx = _ctx(improvement_memory=LowSuccessMemory())
    findings = analyze(ctx)
    low_rate = [f for f in findings if "success rate" in f.summary]
    assert len(low_rate) == 1
    assert low_rate[0].severity == "high"


def test_below_min_attempts_skips_rate_finding():
    """GIVEN a low success rate but fewer than MIN_ATTEMPTS_FOR_RATE,
    WHEN analyzed, THEN no low-rate finding is produced.
    """

    class FewAttemptsMemory:
        def get_effective_strategies(self):
            return [{"change_summary": "ok", "improvement": 0.1}]

        def get_failed_strategies(self):
            # 3 failures + 1 success = 4 total (below threshold of 5)
            return [
                {"change_summary": f"fail {i}", "improvement": -0.05} for i in range(3)
            ]

    ctx = _ctx(improvement_memory=FewAttemptsMemory())
    findings = analyze(ctx)
    low_rate = [f for f in findings if "success rate" in f.summary]
    assert len(low_rate) == 0


def test_failed_strategies_summary_produced():
    """GIVEN 3+ failed strategies, WHEN analyzed,
    THEN a summary of worst failures is produced.
    """

    class FailedMemory:
        def get_effective_strategies(self):
            return [
                {"change_summary": f"good {i}", "improvement": 0.1} for i in range(10)
            ]

        def get_failed_strategies(self):
            return [
                {"change_summary": f"bad approach {i}", "improvement": -(0.1 * (i + 1))}
                for i in range(4)
            ]

    ctx = _ctx(improvement_memory=FailedMemory())
    findings = analyze(ctx)
    regression = [f for f in findings if "regression" in f.summary.lower()]
    assert len(regression) == 1
    assert regression[0].type == "Improvement"
    assert regression[0].severity == "medium"
    assert "bad approach" in regression[0].evidence


def test_fewer_than_min_failed_skips_summary():
    """GIVEN < 3 failed strategies, WHEN analyzed,
    THEN no regression summary is produced.
    """

    class FewFailsMemory:
        def get_effective_strategies(self):
            return [
                {"change_summary": f"good {i}", "improvement": 0.1} for i in range(10)
            ]

        def get_failed_strategies(self):
            return [
                {"change_summary": "one bad", "improvement": -0.05},
                {"change_summary": "two bad", "improvement": -0.03},
            ]

    ctx = _ctx(improvement_memory=FewFailsMemory())
    findings = analyze(ctx)
    regression = [f for f in findings if "regression" in f.summary.lower()]
    assert len(regression) == 0


def test_tracker_without_history_attr_yields_nothing():
    """GIVEN a tracker object without a history attribute,
    WHEN analyzed, THEN returns empty findings.
    """

    class NoHistoryTracker:
        pass

    ctx = _ctx(performance_history=NoHistoryTracker())
    findings = analyze(ctx)
    assert findings == []


def test_tracker_with_empty_history_yields_nothing():
    """GIVEN a tracker with an empty history list,
    WHEN analyzed, THEN returns empty findings.
    """

    class EmptyHistoryTracker:
        def __init__(self):
            self.history = []

    ctx = _ctx(performance_history=EmptyHistoryTracker())
    findings = analyze(ctx)
    assert findings == []


def test_tracker_none_trend_skipped():
    """GIVEN a skill whose trend returns None,
    WHEN analyzed, THEN that skill is skipped.
    """

    class NullTrendTracker:
        def __init__(self):
            self.history = [{"skill_ref": "x:y"}]

        def get_improvement_trend(self, ref):
            return None

    ctx = _ctx(performance_history=NullTrendTracker())
    findings = analyze(ctx)
    assert findings == []


def test_severe_degradation_is_high_severity():
    """GIVEN a trend <= -0.3 (SEVERE_DEGRADATION),
    WHEN analyzed, THEN finding has high severity.
    """

    class SevereTracker:
        def __init__(self):
            self.history = [{"skill_ref": "x:y"}]

        def get_improvement_trend(self, ref):
            return -0.35

    ctx = _ctx(performance_history=SevereTracker())
    findings = analyze(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "high"


def test_moderate_degradation_is_medium_severity():
    """GIVEN a trend between -0.3 and -0.1,
    WHEN analyzed, THEN finding has medium severity.
    """

    class ModerateTracker:
        def __init__(self):
            self.history = [{"skill_ref": "x:y"}]

        def get_improvement_trend(self, ref):
            return -0.15

    ctx = _ctx(performance_history=ModerateTracker())
    findings = analyze(ctx)
    assert len(findings) == 1
    assert findings[0].severity == "medium"


def test_duplicate_skill_refs_deduplicated():
    """GIVEN multiple history entries for the same skill,
    WHEN analyzed, THEN only one finding per skill.
    """

    class DupTracker:
        def __init__(self):
            self.history = [
                {"skill_ref": "x:y"},
                {"skill_ref": "x:y"},
                {"skill_ref": "x:y"},
            ]

        def get_improvement_trend(self, ref):
            return -0.2

    ctx = _ctx(performance_history=DupTracker())
    findings = analyze(ctx)
    assert len(findings) == 1
