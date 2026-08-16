"""Regression tests for the vitality decay script."""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path

import yaml

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
VITALITY_DECAYED_FROM = 40


class TestPersistenceGate:
    """Persist on a real change, not merely on elapsed time.

    The pre-commit maintenance hook re-stages this file whenever its
    bytes move, so a rewrite that only advances ``last_recomputed``
    attaches an unrelated one-line diff to whatever commit happens to
    run first that day. Discussions #605 and #611 are that diff: a
    timestamp-only bump of an auto-generated index, landing in PRs that
    never touched memory-palace, and unstable to revert because the hook
    regenerates it.

    Elapsed days is the wrong question. The right one is whether any
    entry actually decayed.
    """

    @staticmethod
    def _run(module, tmp_path: Path, entries: dict, monkeypatch) -> tuple[str, str]:
        """Run ``main`` over ``entries`` and return the bytes before/after."""
        path = tmp_path / "vitality-scores.yaml"
        stale = "2026-05-20T00:00:00+00:00"
        path.write_text(
            yaml.safe_dump(
                {
                    "entries": entries,
                    "metadata": {"decay_per_day": 1, "last_recomputed": stale},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        before = path.read_text(encoding="utf-8")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "update_vitality_scores.py",
                "--file",
                str(path),
                "--queue-file",
                str(tmp_path / "queue.json"),
            ],
        )
        module.main()
        return before, path.read_text(encoding="utf-8")

    def test_empty_entries_does_not_rewrite(self, tmp_path: Path, monkeypatch) -> None:
        """Nothing to decay means nothing to persist.

        This is the committed state of the real file: ``entries: {}``.
        Every day-boundary commit currently rewrites it for a timestamp.
        """
        module = _load_script()
        before, after = self._run(module, tmp_path, {}, monkeypatch)
        assert after == before, (
            "an empty index was rewritten for a timestamp-only bump; "
            "the pre-commit hook re-stages that into an unrelated commit"
        )

    def test_all_evergreen_does_not_rewrite(self, tmp_path: Path, monkeypatch) -> None:
        """Evergreen entries are skipped, so a run over only them changes nothing."""
        module = _load_script()
        entries = {"pinned": {"vitality": 40, "maturity": "evergreen"}}
        before, after = self._run(module, tmp_path, entries, monkeypatch)
        assert after == before, "a file of only evergreen entries was rewritten"

    def test_real_decay_still_persists(self, tmp_path: Path, monkeypatch) -> None:
        """The gate must not swallow a decay that actually happened."""
        module = _load_script()
        entries = {"note": {"vitality": 40, "maturity": "growing"}}
        before, after = self._run(module, tmp_path, entries, monkeypatch)
        assert after != before, "a real decay was not persisted"
        assert (
            yaml.safe_load(after)["entries"]["note"]["vitality"] < VITALITY_DECAYED_FROM
        )


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
