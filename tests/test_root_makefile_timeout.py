"""The root Makefile's timeout fallback ends a hung check's whole group.

Stock macOS has no GNU timeout, so per-plugin checks run under a perl
alarm. The first version signalled only the process it exec'd, and a
hung check's pytest children ran on orphaned.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("perl") is None, reason="needs perl")


def _fallback_command() -> list[str]:
    """TIMEOUT_180 as make expands it on a PATH with no timeout binary."""
    path = ":".join(
        p for p in os.environ["PATH"].split(":") if not (Path(p) / "timeout").exists()
    )
    database = subprocess.run(
        ["make", "-pn", "help"],
        cwd=ROOT,
        env={**os.environ, "PATH": path},
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    line = next(x for x in database.splitlines() if x.startswith("TIMEOUT_180 := "))
    value = line.split(":= ", 1)[1]
    assert value.startswith("perl -e "), value
    script = re.search(r"perl -e '(.*)' 180$", value)
    assert script, value
    # make -p prints the value unexpanded, so make's $$ escape is undone here.
    return [shutil.which("perl") or "perl", "-e", script.group(1).replace("$$", "$")]


def test_the_alarm_ends_grandchildren_and_exits_124(tmp_path: Path) -> None:
    marker = tmp_path / "orphan-ran"
    child = f"sh -c 'sleep 2; touch {marker}' & wait"

    result = subprocess.run(
        [*_fallback_command(), "1", "sh", "-c", child], check=False, timeout=20
    )
    time.sleep(2.5)

    assert result.returncode == 124
    assert not marker.exists()


def test_a_finished_check_keeps_its_exit_code() -> None:
    result = subprocess.run(
        [*_fallback_command(), "5", "sh", "-c", "exit 3"], check=False, timeout=20
    )
    assert result.returncode == 3
