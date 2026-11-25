"""Valid JSON of the wrong shape raised past sanctum's hook readers (ARCH-1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "hooks"))

import deferred_item_sweep  # noqa: E402 - hooks dir joins sys.path above
import session_complete_notify  # noqa: E402 - hooks dir joins sys.path above


def test_notification_state_from_a_list_is_fresh(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state.json"
    state.write_text("[]")
    monkeypatch.setattr(
        session_complete_notify.NotificationState,
        "state_file_path",
        classmethod(lambda cls, session_id: state),
    )
    loaded = session_complete_notify.NotificationState.load("s1")
    assert loaded.last_notify_time == 0.0


def test_dict_shaped_ledger_is_left_alone(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps({"entries": []}))
    stats = deferred_item_sweep.process_ledger(ledger)
    assert stats["filed"] == 0
    assert ledger.exists()


def test_notification_state_with_null_fields_is_usable(
    tmp_path: Path, monkeypatch
) -> None:
    """A null field reached ``should_notify`` and raised TypeError, and every
    save wrote the same null back, so the session never notified again.
    """
    state = tmp_path / "state.json"
    state.write_text(
        json.dumps(
            {
                "last_notify_time": None,
                "last_content_hash": 7,
                "notified_since_input": "yes",
            }
        )
    )
    monkeypatch.setattr(
        session_complete_notify.NotificationState,
        "state_file_path",
        classmethod(lambda cls, session_id: state),
    )
    loaded = session_complete_notify.NotificationState.load("s1")
    assert loaded.last_notify_time == 0.0
    assert loaded.last_content_hash == ""
    assert loaded.notified_since_input is False
    assert loaded.should_notify("h")[0] is True


def test_entry_with_a_null_title_does_not_stop_the_sweep(
    tmp_path: Path, monkeypatch
) -> None:
    """``entry.get("title", default)`` returned None, argv raised TypeError,
    and the entries filed before it were never marked.
    """
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            [
                {"title": "first ok", "source": "a"},
                {"title": None, "source": "b"},
                {"title": "third", "source": "c"},
            ]
        )
    )
    called: list[str] = []

    def capture(title: str, source: str, timeout: float) -> dict:
        assert isinstance(title, str) and isinstance(source, str)
        called.append(title)
        return {"status": "created", "number": len(called)}

    monkeypatch.setattr(deferred_item_sweep, "call_capture_script", capture)
    stats = deferred_item_sweep.process_ledger(ledger)

    assert called == ["first ok", "third"]
    assert stats["filed"] == 2
    assert stats["failed"] == 1
    kept = json.loads(ledger.read_text())
    assert [e.get("filed") for e in kept] == [True, None, True]


@pytest.mark.parametrize(
    "stored",
    ["Infinity", "-Infinity", "NaN", "1" + "0" * 400, "1e300", "1" + "0" * 5000],
)
def test_a_non_finite_notify_time_does_not_debounce_forever(
    tmp_path: Path, monkeypatch, stored: str
) -> None:
    """json loads `Infinity` as inf, so every Stop fell inside the debounce
    and the bad value was saved back unchanged (F5).
    """
    state = tmp_path / "state.json"
    state.write_text(f'{{"last_notify_time": {stored}}}')
    monkeypatch.setattr(
        session_complete_notify.NotificationState,
        "state_file_path",
        classmethod(lambda cls, session_id: state),
    )
    loaded = session_complete_notify.NotificationState.load("s1")
    assert loaded.last_notify_time == 0.0
    assert loaded.should_notify("h")[0] is True
