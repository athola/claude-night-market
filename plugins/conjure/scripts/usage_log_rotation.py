"""Size-capped JSONL usage log with one rotated backup.

Shared by ``usage_logger`` and ``delegation_executor``, which both keep a
``usage.jsonl`` log and its ``usage.jsonl.1`` backup. Standard library only
and Python 3.9 compatible: ``bin/status.sh`` imports ``usage_logger`` under
the operator's bare ``python3`` with only ``scripts/`` on the path.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: no flock, appends run unlocked
    fcntl = None  # type: ignore[assignment]  # None sentinel checked at the lock site

logger = logging.getLogger(__name__)

# The live log rotates to a single backup at this size, replacing the
# previous backup, so the pair holds at most about twice this on disk.
MAX_LOG_BYTES = 5 * 1024 * 1024


def append_line(log: Path, backup: Path, line: str, max_bytes: int) -> None:
    """Append ``line`` to ``log``, first rotating it to ``backup`` if full.

    The size check, rotation and append share one lock. Without it, two
    processes that both saw a full log rotated twice, and the second rename
    replaced the full backup with the other process's one-line log. Where
    ``fcntl`` is missing (Windows) the same steps run unlocked.

    A failed rotation is logged and the append goes ahead, since an
    oversized log beats a lost entry. A failed append raises ``OSError``.
    """
    lock_fd = os.open(log.with_name(log.name + ".lock"), os.O_CREAT | os.O_WRONLY)
    try:
        if fcntl is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            full = log.stat().st_size >= max_bytes
        except FileNotFoundError:
            full = False
        if full:
            try:
                log.replace(backup)
            except OSError as e:
                logger.warning("Could not rotate usage log %s: %s", log, e)
        with open(log, "a") as f:
            f.write(line + "\n")
    finally:
        os.close(lock_fd)  # closing the descriptor releases the lock


def read_lines(log: Path, backup: Path) -> Iterator[str]:
    """Yield log lines oldest first: the backup, then the live log."""
    for path in (backup, log):
        try:
            with open(path) as f:
                yield from f
        except FileNotFoundError:
            continue
