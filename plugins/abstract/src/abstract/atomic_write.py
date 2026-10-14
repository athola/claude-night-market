"""Replace a file's contents without a window where readers see partial text.

Standard library only: the improvement queue is imported by the
homeostatic hook, which runs under a bare ``python3``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_text_atomic(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` through a temp file in the same directory.

    The temp name is unique per call: a fixed sibling path let one
    process's ``os.replace`` publish or clobber another's half-written
    file. The file keeps mkstemp's 0600 mode. On any failure the temp file
    is removed and the error propagates, leaving ``path`` as it was.
    """
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
