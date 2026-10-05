"""Stability gap over a skill's per-run pass/fail outcomes.

ADR-0006 flags a skill as degrading when its stability gap passes 0.3
and critical past 0.5. The term comes from Avalanche's continual
evaluation, which watches worst-case accuracy over time. Each run here is
a single pass (1) or fail (0), so the worst single run is 0 after any
failure, and "average minus worst run" collapsed into the success rate: a
99%-reliable skill scored 0.99 and an always-failing one 0.0.

Accuracy is measured over sliding windows of runs instead, and the gap is
the worst window's shortfall from perfect, ``1 - worst window rate``. One
stray failure costs 0.2, a skill whose worst stretch drops below 70%
success is degrading, and one that fails half the time or always is
critical. Mean minus worst window was rejected: it measures only
variability, so a skill that failed consistently never registered.

Standard library only: the hooks run under the operator's bare python3.
"""

from __future__ import annotations

from collections.abc import Sequence

# Runs per window. Five is the fewest that turns one stray failure into a
# 0.2 dip rather than a full drop.
WINDOW = 5


def _checked(outcomes: Sequence[float]) -> Sequence[float]:
    for outcome in outcomes:
        if not isinstance(outcome, (int, float)):
            raise TypeError(f"run outcome must be a number, got {outcome!r}")
    return outcomes


def _window_rates(outcomes: Sequence[float], window: int) -> list[float]:
    if len(outcomes) < window:
        return [sum(outcomes) / len(outcomes)]
    return [
        sum(outcomes[i : i + window]) / window
        for i in range(len(outcomes) - window + 1)
    ]


def worst_window_rate(outcomes: Sequence[float], window: int = WINDOW) -> float:
    """Lowest success rate over any ``window`` consecutive runs."""
    if not _checked(outcomes):
        return 0.0
    return min(_window_rates(outcomes, window))


def stability_gap(outcomes: Sequence[float], window: int = WINDOW) -> float:
    """Shortfall of the worst window: ``1 - worst_window_rate``.

    0.0 until there is a full window of runs to judge.
    """
    if len(_checked(outcomes)) < window:
        return 0.0
    return 1.0 - min(_window_rates(outcomes, window))
