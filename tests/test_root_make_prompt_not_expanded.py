"""A command-line PROMPT is text to the root Makefile too.

GNU make 4 expands an exported command-line variable each time a
`$(shell ...)` builds its environment. The root Makefile calls
`$(shell command -v timeout ...)` while it parses, so
`make conjure-delegate-gemini PROMPT='$(shell touch x)'` ran the command
before the conjure sub-make, which already guards against it, started.
make 3.81 does not do this, so the test needs a make 4.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _gnu_make_4() -> str | None:
    for name in ("gmake", "make"):
        path = shutil.which(name)
        if path is None:
            continue
        version = subprocess.run(
            [path, "--version"], capture_output=True, text=True, check=False
        ).stdout
        if version.startswith("GNU Make") and not version.startswith("GNU Make 3"):
            return path
    return None


MAKE = _gnu_make_4()

pytestmark = pytest.mark.skipif(MAKE is None, reason="needs GNU make 4 or later")


@pytest.mark.parametrize("variable", ["PROMPT", "FILES"])
def test_shell_function_in_a_command_line_variable_does_not_run(
    tmp_path: Path, variable: str
) -> None:
    marker = tmp_path / "pwned"

    subprocess.run(
        [MAKE, "-n", "-C", str(ROOT), "help", f"{variable}=$(shell touch {marker})"],
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert not marker.exists()
