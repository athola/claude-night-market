"""Insight analyzer orchestrator.

Builds an AnalysisContext from available data sources,
runs matching lenses, and returns deduplicated findings.
This is the main entry point for both the Stop hook
(lightweight lenses) and the insight-engine agent
(all lenses).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from insight_types import AnalysisContext, Finding
from lenses import run_lenses

# Optional modules (may not be installed)
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

try:
    from abstract.improvement_memory import ImprovementMemory

    _HAS_IMPROVEMENT_MEMORY = True
except ImportError:
    _HAS_IMPROVEMENT_MEMORY = False

try:
    from abstract.performance_tracker import PerformanceTracker

    _HAS_PERFORMANCE_TRACKER = True
except ImportError:
    _HAS_PERFORMANCE_TRACKER = False


def build_context(
    metrics: dict[str, Any],
    trigger: str = "stop",
    previous_snapshot: dict[str, Any] | None = None,
    code_paths: list[Path] | None = None,
    pr_diff: str | None = None,
) -> AnalysisContext:
    """Build an AnalysisContext from available data sources.

    Loads PerformanceTracker and ImprovementMemory if the
    modules and data files are available. Falls back to None
    for unavailable sources.

    Args:
        metrics: Skill metrics from aggregate_skill_logs.
        trigger: What triggered this analysis.
        previous_snapshot: Last-posted metrics snapshot.
        code_paths: File paths for LLM lenses.
        pr_diff: Git diff for PR-scoped analysis.

    Returns:
        Populated AnalysisContext.

    """
    performance_history = None
    improvement_memory = None

    if _HAS_PERFORMANCE_TRACKER:
        tracker_file = Path.home() / ".claude" / "skills" / "performance_history.json"
        if tracker_file.exists():
            try:
                performance_history = PerformanceTracker(tracker_file)
            except (OSError, KeyError):
                pass

    if _HAS_IMPROVEMENT_MEMORY:
        mem_file = Path.home() / ".claude" / "skills" / "improvement_memory.json"
        if mem_file.exists():
            try:
                improvement_memory = ImprovementMemory(mem_file)
            except (OSError, KeyError):
                pass

    return AnalysisContext(
        metrics=metrics,
        previous_snapshot=previous_snapshot,
        performance_history=performance_history,
        improvement_memory=improvement_memory,
        code_paths=code_paths or [],
        pr_diff=pr_diff,
        trigger=trigger,
    )


def run_analysis(
    context: AnalysisContext,
    weight_filter: str | None = None,
) -> list[Finding]:
    """Run all matching lenses and return findings.

    Args:
        context: Analysis context with metrics and history.
        weight_filter: Only run lenses of this weight
            ("lightweight" for hooks, None for all).

    Returns:
        List of findings from all lenses.

    """
    return run_lenses(context, weight_filter=weight_filter)
