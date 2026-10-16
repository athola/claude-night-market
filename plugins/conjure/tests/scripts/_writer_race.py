"""Two-writer interleaving shared by the usage-log rotation race tests.

usage_logger and delegation_executor append through the same rotation
code, so both test modules drive it with this one harness.
"""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from pathlib import Path

import pytest


def race_two_writers(
    monkeypatch: pytest.MonkeyPatch,
    live_log: Path,
    write_a: Callable[[], None],
    write_b: Callable[[], None],
) -> list[OSError]:
    """Run two appends where both see the full log before either rotates.

    Writer B's rename waits until writer A has rotated and appended, which
    is the interleaving that renamed A's fresh log over the full backup.
    Only ``OSError`` is collected, because that is what a failed append
    raises. Anything else escapes the thread, and the writer's line is then
    missing from the log the caller checks.

    With the rotation lock in place writer B blocks on the lock before it
    can stat the log, so the barrier never fills and every run waits out
    its timeout. The timeout is kept short for that reason; unlocked, both
    writers reach the barrier in well under it.
    """
    barrier = threading.Barrier(2, timeout=0.2)
    a_done = threading.Event()
    seen: set[str] = set()
    real_stat = Path.stat
    real_replace = Path.replace

    def stat(path: Path, *args: object, **kwargs: object) -> object:
        info = real_stat(path, *args, **kwargs)
        name = threading.current_thread().name
        if path == live_log and name not in seen:
            seen.add(name)
            with contextlib.suppress(threading.BrokenBarrierError):
                barrier.wait()
        return info

    def replace(path: Path, target: Path) -> Path:
        if threading.current_thread().name == "writer-b":
            a_done.wait(timeout=1)
        return real_replace(path, target)

    monkeypatch.setattr(Path, "stat", stat)
    monkeypatch.setattr(Path, "replace", replace)
    errors: list[OSError] = []

    def run(write: Callable[[], None], done: threading.Event | None) -> None:
        try:
            write()
        except OSError as exc:
            errors.append(exc)
        if done is not None:
            done.set()

    threads = [
        threading.Thread(target=run, args=(write_a, a_done), name="writer-a"),
        threading.Thread(target=run, args=(write_b, None), name="writer-b"),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive(), f"{thread.name} still running after 10s"
    return errors
