"""The one-writer lock on ``.gauntlet/graph.db``.

graph_build.py holds it for the life of a full or incremental build. It is
an flock, so the kernel releases it when the build exits or dies, and no
stale-lock timeout is needed. The hooks only ask whether it is held.

Standard library only: the hooks import this on the first python3 on PATH.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: no advisory locks, writers are not serialized
    _HAS_FLOCK = False
else:
    _HAS_FLOCK = True

#: EX_TEMPFAIL. graph_build.py exits with it when another writer holds the
#: lock, and the hooks' status line does not record it as a failure.
BUSY_EXIT_CODE = 75

LOCK_NAME = "graph.lock"


@contextlib.contextmanager
def writer_lock(gauntlet_dir: Path) -> Iterator[bool]:
    """Hold the writer lock; yield False when another writer has it."""
    with open(Path(gauntlet_dir) / LOCK_NAME, "a") as lock:
        if not _HAS_FLOCK:
            yield True
            return
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def writer_busy(gauntlet_dir: Path) -> bool:
    """Whether a build holds the writer lock right now."""
    if not _HAS_FLOCK:
        return False
    try:
        fd = os.open(str(Path(gauntlet_dir) / LOCK_NAME), os.O_RDWR)
    except FileNotFoundError:
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    finally:
        # Closing the descriptor drops a lock this probe took.
        os.close(fd)
    return False
