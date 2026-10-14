"""Shared ledger path utilities for sanctum hooks."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows has no flock; ledger writes run unlocked there.
    fcntl = None  # type: ignore[assignment]  # None marks the platform without flock


def get_ledger_path() -> Path:
    """Return the session-scoped ledger path, respecting CLAUDE_HOME."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    return claude_dir / "deferred-items-session.json"


@contextmanager
def ledger_lock(ledger_path: Path) -> Iterator[None]:
    """Hold an exclusive lock shared by every read-modify-write of the ledger.

    The lock is a sidecar file: the sweep replaces the ledger's inode, and a
    flock taken on the replaced inode would no longer exclude anyone.
    """
    if fcntl is None:
        yield
        return
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger_path.with_name(ledger_path.name + ".lock"), "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield
