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


# ── build_context conditional path tests ───────────────────

from unittest.mock import MagicMock, patch

_MODULE = "insight_analyzer"


def test_build_context_loads_performance_tracker(tmp_path):
    """GIVEN a valid performance_history.json file exists,
    WHEN build_context is called,
    THEN performance_history is populated.
    """
    tracker_file = tmp_path / "performance_history.json"
    tracker_file.write_text("[]")

    mock_tracker = MagicMock()

    with (
        patch(f"{_MODULE}._HAS_PERFORMANCE_TRACKER", True),
        patch(f"{_MODULE}.PerformanceTracker", return_value=mock_tracker),
        patch(f"{_MODULE}.Path.home", return_value=tmp_path),
        patch(f"{_MODULE}._HAS_IMPROVEMENT_MEMORY", False),
        patch(f"{_MODULE}._HAS_PALACE_BRIDGE", False),
    ):
        # Create the expected file path
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "performance_history.json").write_text("[]")

        ctx = build_context(metrics={}, trigger="test")

    assert ctx.performance_history is mock_tracker


def test_build_context_loads_improvement_memory(tmp_path):
    """GIVEN a valid improvement_memory.json file exists,
    WHEN build_context is called,
    THEN improvement_memory is populated.
    """
    mock_memory = MagicMock()

    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "improvement_memory.json").write_text("{}")

    with (
        patch(f"{_MODULE}._HAS_PERFORMANCE_TRACKER", False),
        patch(f"{_MODULE}._HAS_IMPROVEMENT_MEMORY", True),
        patch(f"{_MODULE}.ImprovementMemory", return_value=mock_memory),
        patch(f"{_MODULE}.Path.home", return_value=tmp_path),
        patch(f"{_MODULE}._HAS_PALACE_BRIDGE", False),
    ):
        ctx = build_context(metrics={}, trigger="test")

    assert ctx.improvement_memory is mock_memory


def test_build_context_handles_tracker_error(tmp_path):
    """GIVEN PerformanceTracker constructor raises,
    WHEN build_context is called,
    THEN performance_history remains None (graceful fallback).
    """
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "performance_history.json").write_text("bad json")

    with (
        patch(f"{_MODULE}._HAS_PERFORMANCE_TRACKER", True),
        patch(f"{_MODULE}.PerformanceTracker", side_effect=ValueError("bad")),
        patch(f"{_MODULE}.Path.home", return_value=tmp_path),
        patch(f"{_MODULE}._HAS_IMPROVEMENT_MEMORY", False),
        patch(f"{_MODULE}._HAS_PALACE_BRIDGE", False),
    ):
        ctx = build_context(metrics={}, trigger="test")

    assert ctx.performance_history is None


def test_build_context_handles_memory_error(tmp_path):
    """GIVEN ImprovementMemory constructor raises,
    WHEN build_context is called,
    THEN improvement_memory remains None (graceful fallback).
    """
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    (skills_dir / "improvement_memory.json").write_text("bad json")

    with (
        patch(f"{_MODULE}._HAS_PERFORMANCE_TRACKER", False),
        patch(f"{_MODULE}._HAS_IMPROVEMENT_MEMORY", True),
        patch(f"{_MODULE}.ImprovementMemory", side_effect=OSError("bad")),
        patch(f"{_MODULE}.Path.home", return_value=tmp_path),
        patch(f"{_MODULE}._HAS_PALACE_BRIDGE", False),
    ):
        ctx = build_context(metrics={}, trigger="test")

    assert ctx.improvement_memory is None


def test_build_context_with_palace_bridge():
    """GIVEN palace bridge is available and returns insights,
    WHEN build_context is called,
    THEN palace_insights is populated.
    """
    mock_insights = [{"type": "pattern", "content": "foo"}]

    with (
        patch(f"{_MODULE}._HAS_PERFORMANCE_TRACKER", False),
        patch(f"{_MODULE}._HAS_IMPROVEMENT_MEMORY", False),
        patch(f"{_MODULE}._HAS_PALACE_BRIDGE", True),
        patch(f"{_MODULE}.query_palace_insights", return_value=mock_insights),
    ):
        ctx = build_context(metrics={}, trigger="test")

    assert ctx.palace_insights == mock_insights


def test_build_context_palace_bridge_error_fallback():
    """GIVEN palace bridge raises an exception,
    WHEN build_context is called,
    THEN palace_insights defaults to empty list.
    """
    with (
        patch(f"{_MODULE}._HAS_PERFORMANCE_TRACKER", False),
        patch(f"{_MODULE}._HAS_IMPROVEMENT_MEMORY", False),
        patch(f"{_MODULE}._HAS_PALACE_BRIDGE", True),
        patch(
            f"{_MODULE}.query_palace_insights",
            side_effect=RuntimeError("palace down"),
        ),
    ):
        ctx = build_context(metrics={}, trigger="test")

    assert ctx.palace_insights == []


def test_build_context_passes_optional_args():
    """GIVEN optional args (previous_snapshot, code_paths, pr_diff),
    WHEN build_context is called,
    THEN they appear in the context.
    """
    from pathlib import Path as RealPath

    ctx = build_context(
        metrics={"a": "b"},
        trigger="agent",
        previous_snapshot={"x": 1},
        code_paths=[RealPath("foo.py")],
        pr_diff="diff content",
    )
    assert ctx.trigger == "agent"
    assert ctx.previous_snapshot == {"x": 1}
    assert len(ctx.code_paths) == 1
    assert ctx.pr_diff == "diff content"
