"""Stability gap over per-run pass/fail outcomes.

The hooks record each run as 1 or 0, so the worst single run is 0 after
any failure and "average minus worst" collapsed into the success rate: a
99%-reliable skill scored 0.99 (critical) and an always-failing one 0.0.
The gap is now the worst five-run window's shortfall from perfect.
"""

from __future__ import annotations

import pytest
from hooks.shared.stability import WINDOW, stability_gap, worst_window_rate


def test_no_runs_means_no_gap() -> None:
    assert stability_gap([]) == 0.0


def test_fewer_runs_than_a_window_carry_no_evidence_of_a_gap() -> None:
    assert stability_gap([1, 0, 1]) == 0.0


def test_one_failure_in_a_hundred_runs_is_stable() -> None:
    runs = [1] * 50 + [0] + [1] * 49
    assert stability_gap(runs) < 0.3


def test_a_recent_run_of_failures_is_a_gap() -> None:
    runs = [1] * 20 + [0] * WINDOW
    assert stability_gap(runs) > 0.3


def test_a_reliable_skill_has_no_gap() -> None:
    assert stability_gap([1] * 20) == pytest.approx(0.0)


def test_a_skill_that_always_fails_is_critical() -> None:
    assert stability_gap([0] * 20) > 0.5


def test_a_skill_that_fails_half_the_time_is_critical() -> None:
    assert stability_gap([1, 0] * 10) > 0.5


def test_gap_is_never_negative() -> None:
    assert stability_gap([0, 1, 1, 1, 1, 1, 0]) >= 0.0


def test_a_non_numeric_outcome_is_rejected_not_skipped() -> None:
    """A short history must not hide corrupt data behind the window check."""
    with pytest.raises(TypeError):
        stability_gap([1.0, "x"])


def test_worst_window_rate_is_the_lowest_windowed_success_rate() -> None:
    assert worst_window_rate([1] * 20 + [0] * WINDOW) == 0.0
    assert worst_window_rate([1, 1, 1]) == 1.0
