"""Write a command's report to stdout or to its ``--output`` file.

Lives in ``src/`` because the wheel ships only ``abstract``: the wrapper
scripts and ``cli_framework`` both import it from here.
"""

from __future__ import annotations

import sys
from pathlib import Path


def write_output(text: str, output_path: Path | None) -> bool:
    """Return False after reporting on stderr when the file cannot be written.

    A bad path is a user error, so it gets one line and a non-zero exit from
    the caller rather than a traceback. File content is ``text`` unchanged.
    """
    if output_path is None:
        print(text)
        return True
    try:
        output_path.write_text(text)
    except OSError as e:
        print(f"Error: cannot write {output_path}: {e}", file=sys.stderr)
        return False
    return True
