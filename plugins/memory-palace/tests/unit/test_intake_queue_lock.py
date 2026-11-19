"""Maintenance rewrote intake_queue.jsonl while the hook appended to it,
with no lock on either side, so an appended entry could be truncated away
(MP-10). Both now hold `intake_queue.jsonl.lock`.
"""

from __future__ import annotations

import fcntl
import threading
from pathlib import Path
from unittest.mock import MagicMock

from memory_palace.palace_maintenance import PalaceMaintenance


def _blocks_until_released(lock_path: Path, action) -> None:
    done = threading.Event()

    def run() -> None:
        action()
        done.set()

    with open(lock_path, "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        worker = threading.Thread(target=run)
        worker.start()
        assert not done.wait(0.3)
        fcntl.flock(held, fcntl.LOCK_UN)
    worker.join(5)
    assert done.is_set()


def test_sync_from_queue_waits_for_the_queue_lock(tmp_path: Path) -> None:
    queue = tmp_path / "intake_queue.jsonl"
    queue.write_text('{"query": "x"}\n')
    repo = MagicMock()
    repo.list_palaces.return_value = []
    maintenance = PalaceMaintenance(repo)

    _blocks_until_released(
        tmp_path / "intake_queue.jsonl.lock",
        lambda: maintenance.sync_from_queue(str(queue)),
    )


def test_hook_append_waits_for_the_queue_lock(tmp_path: Path, monkeypatch) -> None:
    import sys  # noqa: PLC0415 - scoped to the lock test

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "hooks"))
    from shared.hook_output import IntakeContext, queue_for_intake  # noqa: PLC0415 - hooks dir joins sys.path first

    sys.modules.pop("shared.hook_output", None)
    (tmp_path / "data").mkdir()
    decision = MagicMock(should_flag_for_intake=True)
    decision.intake_payload.to_dict.return_value = {}
    ctx = IntakeContext(query_id="q", tool_name="WebSearch", query="x", tool_input={})

    _blocks_until_released(
        tmp_path / "data" / "intake_queue.jsonl.lock",
        lambda: queue_for_intake(tmp_path, decision, ctx),
    )


def test_hook_gives_up_queueing_when_the_lock_stays_held(
    tmp_path: Path, monkeypatch
) -> None:
    """A hook must not block on a long sync; it skips queueing instead."""
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "hooks"))
    from shared import hook_output  # noqa: PLC0415 - hooks dir joins sys.path first

    monkeypatch.setattr(hook_output, "_QUEUE_LOCK_TIMEOUT_SECONDS", 0.2)
    (tmp_path / "data").mkdir()
    decision = MagicMock(should_flag_for_intake=True)
    decision.intake_payload.to_dict.return_value = {}
    ctx = hook_output.IntakeContext(
        query_id="q", tool_name="WebSearch", query="x", tool_input={}
    )
    with open(tmp_path / "data" / "intake_queue.jsonl.lock", "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        hook_output.queue_for_intake(tmp_path, decision, ctx)
        fcntl.flock(held, fcntl.LOCK_UN)

    assert not (tmp_path / "data" / "intake_queue.jsonl").exists()
