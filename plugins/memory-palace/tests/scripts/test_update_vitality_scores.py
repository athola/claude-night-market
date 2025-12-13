"""Regression tests for the vitality decay script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "update_vitality_scores.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("update_vitality_scores", SCRIPT_PATH.resolve())
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_decay_skips_evergreen_and_emits_queue(tmp_path: Path) -> None:
    """Ensure evergreen entries are preserved while other entries decay."""
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
