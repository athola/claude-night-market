"""Valid JSON of the wrong shape raised past sanctum's hook readers (ARCH-1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

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
