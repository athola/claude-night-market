"""entrypoint.sh waits for Xvfb instead of assuming it started.

Shell review S2-21. Xvfb ran in the background with its exit status
ignored. After a fixed `sleep 1` the script printed "Display environment
ready" and exec'd the task, even when Xvfb had already died (a stale
/tmp/.X1-lock, say).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ENTRYPOINT = Path(__file__).resolve().parents[2] / "scripts" / "entrypoint.sh"


def _run(tmp_path: Path, xvfb_body: str) -> subprocess.CompletedProcess[str]:
    shims = tmp_path / "shims"
    shims.mkdir()
    for name, body in {
        "Xvfb": xvfb_body,
        "mutter": "exit 0",
        "tint2": "exit 0",
    }.items():
        shim = shims / name
        shim.write_text(f"#!/bin/sh\n{body}\n")
        shim.chmod(0o755)
    return subprocess.run(
        ["/bin/bash", str(ENTRYPOINT), "echo", "task-ran"],
        env={**os.environ, "PATH": f"{shims}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_a_dead_xvfb_stops_the_entrypoint(tmp_path: Path) -> None:
    result = _run(tmp_path, "echo 'Server is already active' >&2; exit 1")
    assert result.returncode != 0
    assert "ready" not in result.stdout
    assert "task-ran" not in result.stdout


def test_a_ready_xvfb_runs_the_task(tmp_path: Path) -> None:
    """-displayfd: Xvfb writes the display number once it accepts clients."""
    result = _run(tmp_path, 'printf "1\\n" >&3; sleep 5')
    assert result.returncode == 0, result.stderr
    assert "task-ran" in result.stdout
