"""Regression tests for the vitality decay script."""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "update_vitality_scores.py"
)


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "update_vitality_scores", SCRIPT_PATH.resolve()
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_decay_skips_evergreen_and_emits_queue(tmp_path: Path) -> None:
    """Validate evergreen entries are preserved while other entries decay."""
    module = _load_script()
    vitality = {
        "metadata": {"decay_per_day": 2, "stale_threshold": 5},
        "entries": {
            "evergreen-note": {"vitality": 10, "maturity": "evergreen"},
            "probation-note": {
                "vitality": 6,
                "maturity": "probation",
                "last_accessed": "2025-11-20T00:00:00+00:00",
                "state": "probation",
            },
        },
    }

    queue = module.decay_entries(vitality, decay=2)

    assert vitality["entries"]["evergreen-note"]["vitality"] == VITALITY_EVERGREEN
    assert vitality["entries"]["probation-note"]["vitality"] == VITALITY_PROBATION
    assert queue["stale"] == ["probation-note"]
    assert vitality["metadata"]["last_recomputed"]


VITALITY_EVERGREEN = 10
VITALITY_PROBATION = 4


class TestEffectiveDecay:
    """Time-based decay: scale by elapsed days since last recompute.

    Commits in this repo arrive in bursts then go quiet, so decay must
    track wall-clock time, not invocation count. Within a burst (same
    day) elapsed days is zero, so re-running is a no-op; after a gap the
    next run decays proportionally.
    """

    def test_no_last_recomputed_yields_zero(self) -> None:
        """A first run (no baseline timestamp) decays nothing."""
        module = _load_script()
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)
        assert module.effective_decay(2, None, now) == 0

    def test_same_day_yields_zero(self) -> None:
        """Bursty same-day commits accrue no decay (idempotent)."""
        module = _load_script()
        now = dt.datetime(2026, 5, 28, 18, 0, tzinfo=dt.timezone.utc)
        earlier = "2026-05-28T09:00:00+00:00"
        assert module.effective_decay(2, earlier, now) == 0

    def test_scales_with_elapsed_days(self) -> None:
        """Three days at rate 2 decays by 6."""
        module = _load_script()
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)
        three_days_ago = "2026-05-25T00:00:00+00:00"
        assert module.effective_decay(2, three_days_ago, now) == 6

    def test_handles_z_suffix_and_garbage(self) -> None:
        """Z-suffixed timestamps parse; unparsable ones decay nothing."""
        module = _load_script()
        now = dt.datetime(2026, 5, 28, tzinfo=dt.timezone.utc)
        assert module.effective_decay(1, "2026-05-26T00:00:00Z", now) == 2
        assert module.effective_decay(1, "not-a-date", now) == 0
