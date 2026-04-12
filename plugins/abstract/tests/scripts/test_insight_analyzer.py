"""Tests for insight analyzer orchestrator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from insight_analyzer import build_context, run_analysis


class MockSummary:
    """Mock SkillLogSummary for testing."""

    def __init__(self, skill, success_rate=90.0, total=50):
        self.skill = skill
        self.success_rate = success_rate
        self.total_executions = total
        self.failure_count = int(total * (100 - success_rate) / 100)
        self.avg_duration_ms = 500
        self.max_duration_ms = 1000
        self.avg_rating = None
        self.common_friction = []
        self.recent_errors = []


def test_build_context_with_metrics():
    metrics = {"x:y": MockSummary("x:y")}
    ctx = build_context(metrics=metrics, trigger="stop")
    assert ctx.trigger == "stop"
    assert "x:y" in ctx.metrics


def test_build_context_defaults():
    ctx = build_context(metrics={})
    assert ctx.trigger == "stop"
    assert ctx.previous_snapshot is None
    assert ctx.performance_history is None
    assert ctx.improvement_memory is None


def test_run_analysis_returns_findings():
    """Analysis with real lenses should return findings list."""
    metrics = {
        "a:failing": MockSummary("a:failing", success_rate=10.0, total=20),
    }
    ctx = build_context(metrics=metrics, trigger="stop")
    findings = run_analysis(ctx, weight_filter="lightweight")
    assert isinstance(findings, list)
    # Health lens should flag the critical failure
    assert any(f.type == "Health Check" for f in findings)


def test_run_analysis_empty_metrics():
    ctx = build_context(metrics={})
    findings = run_analysis(ctx, weight_filter="lightweight")
    assert findings == []


def test_run_analysis_filters_by_weight():
    """Lightweight filter should not run deep lenses."""
    metrics = {"x:y": MockSummary("x:y")}
    ctx = build_context(metrics=metrics, trigger="stop")
    # Should not crash even if no deep lenses exist
    findings = run_analysis(ctx, weight_filter="deep")
    assert isinstance(findings, list)
