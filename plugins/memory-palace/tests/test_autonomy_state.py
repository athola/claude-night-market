"""Unit tests for the autonomy state management helpers."""

from __future__ import annotations

import os
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


def test_interrupted_save_keeps_the_previous_state(
    temp_state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crash mid-write must not truncate the file holding the domain locks."""
    store = AutonomyStateStore(state_path=temp_state_path)
    store.set_level(1, domain="security", lock=True, reason="audit")

    def crash_before_publish(src: object, dst: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", crash_before_publish)
    with pytest.raises(OSError, match="disk full"):
        store.set_level(3)
    monkeypatch.undo()

    state = AutonomyStateStore(state_path=temp_state_path).load()
    assert state.domain_controls["security"].locked is True


def test_record_decision_leaves_an_unreadable_state_file_intact(
    temp_state_path: Path,
) -> None:
    """A parse failure must not let the metrics write destroy the bytes."""
    store = AutonomyStateStore(state_path=temp_state_path)
    temp_state_path.write_text("current_level: [unclosed\n", encoding="utf-8")

    store.record_decision(auto_approved=True, flagged=False, blocked=False)

    assert temp_state_path.read_text(encoding="utf-8") == "current_level: [unclosed\n"


@pytest.mark.parametrize(
    "corruption",
    ["\n: [unclosed\n", "- a\n- b\n"],
    ids=["bad-yaml", "non-mapping"],
)
@pytest.mark.parametrize(
    "change",
    [
        lambda store: store.promote(domain="security"),
        lambda store: store.set_level(2),
    ],
    ids=["promote-domain", "set-global-level"],
)
def test_change_after_unreadable_load_refuses_instead_of_dropping_locks(
    temp_state_path: Path, corruption: str, change: object
) -> None:
    """Every load of an unreadable file raises, and no save drops the locks."""
    store = AutonomyStateStore(state_path=temp_state_path)
    store.set_level(1, domain="security", lock=True, reason="audit")
    if corruption.startswith("- "):
        temp_state_path.write_text(corruption, encoding="utf-8")
    else:
        with temp_state_path.open("a", encoding="utf-8") as handle:
            handle.write(corruption)
    unreadable = temp_state_path.read_bytes()

    for _attempt in range(2):
        with pytest.raises(ValueError, match="unreadable"):
            change(store)  # type: ignore[operator]  # parametrized callable

    assert temp_state_path.read_bytes() == unreadable


@pytest.mark.parametrize(
    "argv",
    [
        ["autonomy", "status"],
        ["garden", "trust", "--domain", "python", "--level", "1"],
    ],
)
def test_cli_exits_with_one_line_message_on_unreadable_state(
    temp_state_path: Path, argv: list[str]
) -> None:
    temp_state_path.write_text("level: [unclosed\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exited:
        memory_palace_cli.main(argv)

    message = str(exited.value.code)
    assert "is unreadable" in message
    assert "\n" not in message


def test_save_keeps_the_umask_mode_other_readers_rely_on(
    temp_state_path: Path,
) -> None:
    """Readers under another uid keep access to the state file.

    It was written through open() before, with the umask's mode. An
    owner-only 0600 would lock those readers out without an error.
    """
    old_umask = os.umask(0o022)
    try:
        AutonomyStateStore(state_path=temp_state_path).load()
    finally:
        os.umask(old_umask)
    assert temp_state_path.stat().st_mode & 0o777 == 0o644
