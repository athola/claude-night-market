"""Unit tests for the autonomy state management helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_palace import cli as memory_palace_cli
from memory_palace.lifecycle.autonomy_state import (
    AutonomyProfile,
    AutonomyStateStore,
)


@pytest.fixture
def temp_state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated autonomy state file for each test."""
    path = tmp_path / "autonomy-state.yaml"
    monkeypatch.setenv("MEMORY_PALACE_AUTONOMY_STATE", str(path))
    return path


def test_store_creates_default_state(temp_state_path: Path) -> None:
    store = AutonomyStateStore(state_path=temp_state_path)
    state = store.load()
    assert state.current_level == 0
    assert temp_state_path.exists()


def test_set_level_updates_global_and_domain(temp_state_path: Path) -> None:
    store = AutonomyStateStore(state_path=temp_state_path)
    store.set_level(2)
    state = store.load()
    assert state.current_level == 2

    store.set_level(1, domain="Security", lock=True, reason="requires review")
    state = store.load()
    assert "security" in state.domain_controls
    control = state.domain_controls["security"]
    assert control.level == 1
    assert control.locked is True
    assert control.reason == "requires review"


def test_domain_lock_prevents_override(temp_state_path: Path) -> None:
    store = AutonomyStateStore(state_path=temp_state_path)
    store.set_level(3)
    store.set_level(0, domain="security", lock=True)

    profile = store.build_profile()
    assert isinstance(profile, AutonomyProfile)
    assert profile.effective_level_for(["security"]) == 0
    assert profile.should_auto_approve_duplicates(["security"]) is False


def test_record_decision_updates_metrics(temp_state_path: Path) -> None:
    store = AutonomyStateStore(state_path=temp_state_path)
    store.record_decision(
        auto_approved=True,
        flagged=False,
        blocked=False,
        domains=["python"],
    )
    state = store.load()
    assert state.metrics.auto_approvals == 1
    assert state.metrics.flagged_requests == 0
    assert state.metrics.last_domains == ["python"]


def test_cli_set_and_status(temp_state_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    memory_palace_cli.main(["autonomy", "set", "--level", "2"])
    memory_palace_cli.main(["autonomy", "status"])
    output = capsys.readouterr().out
    assert "Current level: 2" in output
