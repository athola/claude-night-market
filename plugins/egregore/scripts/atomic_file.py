"""Replace a state file in one rename, so a reader never sees half of it.

The watchdog, the Stop hook and the night runner read manifest.json and
budget.json at any moment. Each write goes to a temporary file beside the
target and is renamed over it; a write that fails midway leaves the last
good copy in place.

Standard library only: the rate-limit hook imports this through budget.py
under the operator's bare python3.
"""

from __future__ import annotations

import contextlib
import os
import stat
import sys
import tempfile
from pathlib import Path


def write_text_atomic(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` through a temporary file and a rename.

    mkstemp creates its file 0600. The result keeps the mode the target
    already had, or for a new file the mode ``open`` would have given it,
    so a save never narrows who may read the state.
    """
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except FileNotFoundError:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp_name = tempfile.mkstemp(
        suffix=".tmp", prefix=path.name + ".", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise
    _fsync_directory(path.parent)


def _fsync_directory(directory: str | os.PathLike[str]) -> None:
    """Sync ``directory`` so a rename inside it survives a crash.

    Windows cannot open a directory for fsync, and NTFS journals
    metadata changes such as a rename. The sync is skipped there.
    """
    if sys.platform == "win32":
        return
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
