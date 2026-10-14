# ruff: noqa: D101,D102,D103,PLC0415
"""The sweep must not drop entries the watcher appends while it runs."""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

HOOK_DIR = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOK_DIR))


def _file_while_watcher_appends(ledger: Path):
    """Return a capture stub that appends a new entry, as the watcher would."""

    def capture(title: str, source: str, timeout: float = 2.0) -> dict:
        entries = json.loads(ledger.read_text())
        entries.append({"title": "Arrived mid-sweep", "source": "w", "filed": False})
        ledger.write_text(json.dumps(entries))
        return {"status": "created", "number": 7}

    return capture


def test_entry_appended_during_sweep_survives_when_all_others_filed(
    tmp_path: Path,
) -> None:
    from deferred_item_sweep import process_ledger

    ledger = tmp_path / "deferred-items-session.json"
    ledger.write_text(json.dumps([{"title": "A", "source": "s", "filed": False}]))

    with patch(
        "deferred_item_sweep.call_capture_script",
        side_effect=_file_while_watcher_appends(ledger),
    ):
        process_ledger(ledger)

    assert ledger.exists()
    assert [e["title"] for e in json.loads(ledger.read_text())] == [
        "A",
        "Arrived mid-sweep",
    ]


def test_unfiled_message_counts_an_entry_appended_during_sweep(
    tmp_path: Path, capsys
) -> None:
    from deferred_item_sweep import process_ledger

    ledger = tmp_path / "deferred-items-session.json"
    ledger.write_text(json.dumps([{"title": "A", "source": "s", "filed": False}]))

    with patch(
        "deferred_item_sweep.call_capture_script",
        side_effect=_file_while_watcher_appends(ledger),
    ):
        process_ledger(ledger)

    assert "1 items remain unfiled" in capsys.readouterr().err


def test_entry_appended_during_sweep_survives_when_some_fail(tmp_path: Path) -> None:
    from deferred_item_sweep import process_ledger

    ledger = tmp_path / "deferred-items-session.json"
    ledger.write_text(
        json.dumps(
            [
                {"title": "A", "source": "s", "filed": False},
                {"title": "B", "source": "s", "filed": False},
            ]
        )
    )
    calls = {"n": 0}
    append = _file_while_watcher_appends(ledger)

    def capture(title: str, source: str, timeout: float = 2.0) -> dict:
        calls["n"] += 1
        if calls["n"] == 1:
            return append(title, source, timeout)
        return {"status": "error", "message": "gh down"}

    with patch("deferred_item_sweep.call_capture_script", side_effect=capture):
        process_ledger(ledger)

    titles = [e["title"] for e in json.loads(ledger.read_text())]
    assert titles == ["A", "B", "Arrived mid-sweep"]


def test_ledger_left_unreadable_mid_sweep_counts_as_no_late_entries(
    tmp_path: Path,
) -> None:
    """GIVEN a writer leaves the ledger half-written while the sweep files
    WHEN the sweep re-reads it for late entries
    THEN the unreadable re-read adds nothing and the filed ledger is removed.
    """
    from deferred_item_sweep import process_ledger

    ledger = tmp_path / "deferred-items-session.json"
    ledger.write_text(json.dumps([{"title": "A", "source": "t", "filed": False}]))

    def file_and_corrupt(*_args, **_kwargs):
        ledger.write_text('[{"title": "half')
        return {"status": "created", "issue_url": "u", "number": 7}

    with patch("deferred_item_sweep.call_capture_script", side_effect=file_and_corrupt):
        stats = process_ledger(ledger)

    assert stats["filed"] == 1
    assert not ledger.exists()


def test_watcher_append_racing_the_final_rewrite_survives(tmp_path: Path) -> None:
    """GIVEN the sweep has re-read the ledger for late entries
    WHEN the watcher appends before the sweep rewrites the ledger
    THEN the appended entry is still in the ledger afterwards.
    """
    import deferred_item_sweep
    from deferred_item_watcher import write_ledger_entry

    ledger = tmp_path / "deferred-items-session.json"
    ledger.write_text(json.dumps([{"title": "A", "source": "s", "filed": False}]))
    real_read = deferred_item_sweep._read_entries_after
    writers: list[threading.Thread] = []

    def read_then_race(path: Path, count: int) -> list:
        late = real_read(path, count)
        started = threading.Event()

        def append() -> None:
            started.set()
            write_ledger_entry(path, {"title": "Raced", "source": "w", "filed": False})

        writer = threading.Thread(target=append)
        writer.start()
        writers.append(writer)
        started.wait()
        # Ordering device only: give an unlocked append time to land
        # between the re-read above and the sweep's rewrite.
        time.sleep(0.05)
        return late

    capture_fails = patch(
        "deferred_item_sweep.call_capture_script",
        return_value={"status": "error", "message": "gh down"},
    )
    with patch.object(deferred_item_sweep, "_read_entries_after", read_then_race):
        with capture_fails:
            process_ledger_result = deferred_item_sweep.process_ledger(ledger)

    for writer in writers:
        writer.join(timeout=5)
    assert process_ledger_result["failed"] == 1
    titles = [e["title"] for e in json.loads(ledger.read_text())]
    assert titles == ["A", "Raced"]
