"""Metric definitions in abstract's self-improvement loop.

Math review findings B8, B9, B12 and B13. Each case reproduces the input
that gave the wrong number.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from abstract.improvement_memory import ImprovementMemory, ImprovementOutcome
from abstract.performance_tracker import PerformanceTracker

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "homeostatic_monitor.py"


def _record(mem: ImprovementMemory, before: float, after: float) -> None:
    mem.record_improvement_outcome(
        "p:s",
        ImprovementOutcome(
            version="1",
            change_summary="c",
            before_score=before,
            after_score=after,
            hypothesis="h",
        ),
    )


def test_trend_compares_the_last_window_with_the_one_before_it(tmp_path: Path) -> None:
    """A moving-average trend reads consecutive windows; comparing the last
    window with the first ever recorded called a skill that rose and then
    fell back "improving".
    """
    tracker = PerformanceTracker(tmp_path / "perf.json")
    for score in [0.2] * 5 + [0.9] * 5 + [0.6] * 5:
        tracker.record_generation("p:s", "1", score)
    assert tracker.get_improvement_trend("p:s", window=5) == pytest.approx(-0.3)


def test_version_comparison_without_scores_claims_nothing(tmp_path: Path) -> None:
    """An empty side averaged to 0.0, so any score at all read as improved."""
    tracker = PerformanceTracker(tmp_path / "perf.json")
    tracker.record_generation("p:s", "2", 0.4)
    result = tracker.compare_versions("p:s", "1", "2")
    assert result["improved"] is None
    assert result["improvement"] is None


def test_an_improvement_of_exactly_the_minimum_counts_as_effective(
    tmp_path: Path,
) -> None:
    """0.3 - 0.2 is 0.09999999999999998 in floating point, under 0.1."""
    mem = ImprovementMemory(tmp_path / "mem.json")
    _record(mem, 0.2, 0.3)
    assert len(mem.get_effective_strategies()) == 1


def _monitor():
    spec = importlib.util.spec_from_file_location("homeostatic_monitor_b9", HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_metacognition_counts_every_outcome_as_an_attempt(tmp_path: Path) -> None:
    """Small gains and neutral outcomes vanished from the denominator: one
    success and five +0.05 tweaks read as a 100% effectiveness rate.
    """
    skills = tmp_path / "skills"
    skills.mkdir()
    mem = ImprovementMemory(skills / "improvement_memory.json")
    _record(mem, 0.2, 0.6)
    for _ in range(5):
        _record(mem, 0.5, 0.55)
    # 1 effective of 6 attempts is under the 50% bar.
    assert _monitor()._needs_metacognition(tmp_path) is True
