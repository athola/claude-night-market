"""Tests for update_autonomy_state script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from memory_palace import cli as memory_palace_cli
from memory_palace.lifecycle.autonomy_state import AutonomyStateStore

GLOBAL_AFTER_TWO = 2
GLOBAL_ALERT_THRESHOLD = 0.05

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "update_autonomy_state.py"
)


def load_module():
    """Load the update_autonomy_state module."""
    spec = importlib.util.spec_from_file_location(
        "update_autonomy_state", SCRIPT_PATH.resolve()
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["update_autonomy_state"] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def build_history(total: int, regret_every: int, domain: str) -> list[dict]:
    """Build test history data."""
    events = []
    for i in range(total):
        result = "regret" if regret_every and i % regret_every == 0 else "correct"
        events.append({"result": result, "domains": [domain]})
    return events


def test_adjust_state_promotes_on_high_accuracy(tmp_path: Path) -> None:
    """Test that adjust_state promotes on high accuracy."""
    module = load_module()
    events = build_history(total=30, regret_every=0, domain="cache")
    aggregate, per_domain = module.compute_stats(events)
    store = AutonomyStateStore(state_path=tmp_path / "state.yaml")
    store.set_level(1)
    changes = module.adjust_state(store, aggregate, per_domain, dry_run=False)
    assert changes["global_after"] == GLOBAL_AFTER_TWO
    assert store.load().current_level == GLOBAL_AFTER_TWO


def test_adjust_state_demotes_when_regret_spikes(tmp_path: Path) -> None:
    """Test that adjust_state demotes when regret spikes."""
    module = load_module()
    events = build_history(total=20, regret_every=2, domain="cache")
    aggregate, per_domain = module.compute_stats(events)
    store = AutonomyStateStore(state_path=tmp_path / "state.yaml")
    store.set_level(2)
    changes = module.adjust_state(store, aggregate, per_domain, dry_run=False)
    assert changes["global_after"] == 1
    assert store.load().current_level == 1


def test_regret_alerts_fire_for_garden_commands(tmp_path: Path, monkeypatch) -> None:
    """Test that regret alerts fire for garden commands."""
    module = load_module()
    history = [{"result": "regret", "domains": ["trust"]} for _ in range(5)]
    alerts = module.compute_regret_alerts(
        history, global_threshold=GLOBAL_ALERT_THRESHOLD
    )
    assert alerts["global"]["regret_rate"] > GLOBAL_ALERT_THRESHOLD
    assert "recommended_command" in alerts["global"]
    state_path = tmp_path / "state.yaml"
    monkeypatch.setenv("MEMORY_PALACE_AUTONOMY_STATE", str(state_path))
    memory_palace_cli.main(["garden", "trust", "--domain", "cache", "--level", "2"])
    assert state_path.exists()
