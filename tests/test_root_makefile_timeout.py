"""The root Makefile's timeout fallback ends a hung check's whole group.

Stock macOS has no GNU timeout, so per-plugin checks run under a perl
alarm. The first version signalled only the process it exec'd, and a
hung check's pytest children ran on orphaned. The group fix then moved a
check run from a terminal out of the foreground group, where Ctrl-C does
not reach it, so on a terminal the check stays in the caller's group.

The non-terminal tests pin stdin to /dev/null. Inheriting fd 0 would send
them down the terminal branch under ``pytest -s``.
"""

from __future__ import annotations

import os
import pty
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("perl") is None, reason="needs perl")


def _fallback_command() -> list[str]:
    """TIMEOUT_180 as make expands it on a PATH with no timeout binary.

    make is resolved before PATH is filtered: on Linux it shares /usr/bin
    with coreutils timeout, and filtering that directory drops make too.
    """
    make = shutil.which("make")
    assert make, "make is not on PATH"
    path = ":".join(
        p for p in os.environ["PATH"].split(":") if not (Path(p) / "timeout").exists()
    )
    database = subprocess.run(
        [make, "-pn", "help"],
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
        [*_fallback_command(), "1", "sh", "-c", child],
        stdin=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    time.sleep(2.5)

    assert result.returncode == 124
    assert not marker.exists()


def test_a_finished_check_keeps_its_exit_code() -> None:
    result = subprocess.run(
        [*_fallback_command(), "5", "sh", "-c", "exit 3"],
        stdin=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    assert result.returncode == 3


@pytest.mark.parametrize(("signal_name", "expected"), [("SEGV", 139), ("KILL", 137)])
def test_a_check_killed_by_a_signal_exits_128_plus_the_signal(
    signal_name: str, expected: int
) -> None:
    result = subprocess.run(
        [*_fallback_command(), "5", "sh", "-c", f"kill -{signal_name} $$"],
        stdin=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    assert result.returncode == expected


def _child_pgid(stdin: int) -> tuple[int, int]:
    """Run the fallback around ``ps`` and return (perl pid, the check's pgid)."""
    proc = subprocess.Popen(
        [*_fallback_command(), "5", "sh", "-c", "ps -o pgid= -p $$"],
        stdin=stdin,
        stdout=subprocess.PIPE,
        text=True,
    )
    out, _ = proc.communicate(timeout=20)
    assert proc.returncode == 0
    return proc.pid, int(out.strip())


def test_a_check_without_a_terminal_leads_its_own_group() -> None:
    perl_pid, pgid = _child_pgid(subprocess.DEVNULL)
    assert pgid == perl_pid


def test_a_check_on_a_terminal_stays_in_the_callers_group() -> None:
    """Ctrl-C signals the terminal's foreground group, the caller's group."""
    master, slave = pty.openpty()
    try:
        _, pgid = _child_pgid(slave)
    finally:
        os.close(master)
        os.close(slave)
    assert pgid == os.getpgrp()


def test_the_alarm_on_a_terminal_ends_the_check_and_exits_124(
    tmp_path: Path,
) -> None:
    pid_file = tmp_path / "check.pid"
    master, slave = pty.openpty()
    try:
        result = subprocess.run(
            [
                *_fallback_command(),
                "1",
                "sh",
                "-c",
                f"echo $$ > {pid_file}; exec sleep 30",
            ],
            stdin=slave,
            check=False,
            timeout=20,
        )
    finally:
        os.close(master)
        os.close(slave)
    assert result.returncode == 124
    pid = int(pid_file.read_text())
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    os.kill(pid, 9)
    pytest.fail(f"check {pid} outlived the alarm")
