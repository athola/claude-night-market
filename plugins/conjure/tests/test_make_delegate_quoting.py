"""`make delegate-*` passes PROMPT and FILES as data, never as shell text.

The recipes pasted PROMPT into a double-quoted shell string and FILES
unquoted, so `$(...)` in a prompt ran and `;` in FILES started a command
(CNJ-8). The Python layer below already used list argv.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="needs make")


def test_make_delegate_target_passes_prompt_as_single_literal_argv(
    tmp_path: Path,
) -> None:
    """Backticks, quotes and `;` reach the program as text and run nothing."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    argv_log = tmp_path / "argv"
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        f'#!/bin/sh\nfor a in "$@"; do printf "%s\\n" "$a"; done > "{argv_log}"\n'
    )
    fake_uv.chmod(0o755)
    marker = tmp_path / "marker"
    # make expands `$` in a variable value itself, so a literal `$` must be
    # written `$$`; the shell never sees `$(...)` as a command either way.
    prompt = f'`touch {marker}`; "q" $(touch {marker})'
    literal = f'`touch {marker}`; "q" '

    subprocess.run(
        [
            "make",
            "-s",
            "-C",
            str(PLUGIN),
            "delegate-gemini",
            f"PROMPT={prompt}",
            f"FILES=a.py;touch {marker}",
        ],
        env={**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
        check=True,
        capture_output=True,
        timeout=60,
    )

    assert not marker.exists()
    args = argv_log.read_text().splitlines()
    assert args[args.index("gemini") + 1] == literal
    assert "a.py;touch" in args  # FILES splits on spaces, never on ;
