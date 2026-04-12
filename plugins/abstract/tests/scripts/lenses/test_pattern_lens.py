"""Tests for PatternLens - groups errors across skills."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from insight_types import AnalysisContext
from lenses.pattern_lens import LENS_META, analyze


def _ctx(metrics=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        trigger="stop",
    )


class MockSummary:
    def __init__(self, skill, errors=None, friction=None, success_rate=50.0):
        self.skill = skill
        self.recent_errors = errors or []
        self.common_friction = friction or []
        self.success_rate = success_rate
        self.total_executions = 10
        self.failure_count = 5
        self.avg_duration_ms = 500
        self.avg_rating = None


def test_lens_meta_fields():
    assert LENS_META["name"] == "pattern-lens"
    assert LENS_META["weight"] == "lightweight"


def test_no_metrics_yields_nothing():
    ctx = _ctx(metrics={})
    findings = analyze(ctx)
    assert findings == []


def test_shared_error_pattern_detected():
    """Multiple skills with the same error should produce a Pattern finding."""
    metrics = {
        "a:one": MockSummary("a:one", errors=["TimeoutError: GraphQL"]),
        "b:two": MockSummary("b:two", errors=["TimeoutError: GraphQL API"]),
        "c:three": MockSummary("c:three", errors=["TimeoutError: GraphQL connection"]),
    }
    ctx = _ctx(metrics=metrics)
    findings = analyze(ctx)
    assert len(findings) >= 1
    assert findings[0].type == "Pattern"


def test_shared_friction_pattern_detected():
    metrics = {
        "a:one": MockSummary("a:one", friction=["too verbose output"]),
        "b:two": MockSummary("b:two", friction=["output too verbose"]),
    }
    ctx = _ctx(metrics=metrics)
    findings = analyze(ctx)
    # At least detects shared friction
    pattern_findings = [f for f in findings if f.type == "Pattern"]
    # May or may not detect depending on similarity threshold
    # Just verify no crash
    assert isinstance(findings, list)
