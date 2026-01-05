"""Unit tests for the autonomy state management helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_palace import cli as memory_palace_cli
from memory_palace.lifecycle.autonomy_state import (
    AutonomyProfile,
    AutonomyStateStore,
)

LEVEL_ZERO = 0
LEVEL_ONE = 1
LEVEL_TWO = 2
LEVEL_THREE = 3


@pytest.fixture
def temp_state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated autonomy state file for each test."""
    path = tmp_path / "autonomy-state.yaml"
    monkeypatch.setenv("MEMORY_PALACE_AUTONOMY_STATE", str(path))
    return path


def test_store_creates_default_state(temp_state_path: Path) -> None:
    """Store should create default state file with level zero."""
    store = AutonomyStateStore(state_path=temp_state_path)
    state = store.load()
    assert state.current_level == LEVEL_ZERO
    assert temp_state_path.exists()


def test_set_level_updates_global_and_domain(temp_state_path: Path) -> None:
    """Setting levels updates both global and domain-specific controls."""
    store = AutonomyStateStore(state_path=temp_state_path)
    store.set_level(LEVEL_TWO)
    state = store.load()
    assert state.current_level == LEVEL_TWO

    store.set_level(LEVEL_ONE, domain="Security", lock=True, reason="requires review")
    state = store.load()
    assert "security" in state.domain_controls
    control = state.domain_controls["security"]
    assert control.level == LEVEL_ONE
    assert control.locked is True
    assert control.reason == "requires review"


def test_domain_lock_prevents_override(temp_state_path: Path) -> None:
    """Locked domain levels cannot be overridden."""
    store = AutonomyStateStore(state_path=temp_state_path)
    store.set_level(LEVEL_THREE)
    store.set_level(LEVEL_ZERO, domain="security", lock=True)

    profile = store.build_profile()
    assert isinstance(profile, AutonomyProfile)
    assert profile.effective_level_for(["security"]) == LEVEL_ZERO
    assert profile.should_auto_approve_duplicates(["security"]) is False


def test_record_decision_updates_metrics(temp_state_path: Path) -> None:
    """Recording decisions should update metrics counters."""
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


def test_cli_set_and_status(
    temp_state_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI set and status commands should reflect updated level."""
    memory_palace_cli.main(["autonomy", "set", "--level", str(LEVEL_TWO)])
    memory_palace_cli.main(["autonomy", "status"])
    output = capsys.readouterr().out
    assert f"Current level: {LEVEL_TWO}" in output


def test_garden_commands_emit_transcripts(
    temp_state_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Garden commands should emit transcript data."""
    memory_palace_cli.main(
        [
            "garden",
            "trust",
            "--domain",
            "cache",
            "--level",
            str(LEVEL_TWO),
            "--lock",
            "--reason",
            "autonomy review",
        ]
    )
    trust_output = capsys.readouterr().out
    assert "Garden command transcript" in trust_output
    assert "action: trust" in trust_output
    assert "domain: cache" in trust_output
    assert f"level: {LEVEL_TWO}" in trust_output
    assert "lock: yes" in trust_output
    assert str(temp_state_path) in trust_output

    memory_palace_cli.main(
        [
            "garden",
            "demote",
            "--domain",
            "cache",
            "--unlock",
            "--reason",
            "regret spike",
        ]
    )
    demote_output = capsys.readouterr().out
    assert "Garden command transcript" in demote_output
    assert "action: demote" in demote_output
    assert "domain: cache" in demote_output
    assert "unlock: yes" in demote_output
    assert "reason: regret spike" in demote_output
    assert str(temp_state_path) in demote_output
