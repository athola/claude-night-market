"""bin/skrills-or-fallback works when sourced, as its header documents.

Shell review S0-13 and S0-14. Sourced, `run_skrills` exec'd the binary
and replaced the caller, so nothing after it ran and the caller's EXIT
trap was skipped. Sourcing also overwrote the caller's SCRIPT_DIR and
turned on `set -euo pipefail` in the caller's shell.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[1] / "bin" / "skrills-or-fallback"


def _shim_dir(tmp_path: Path) -> Path:
    shims = tmp_path / "shims"
    shims.mkdir()
    skrills = shims / "skrills"
    skrills.write_text('#!/bin/sh\nprintf "skrills %s\\n" "$*"\nexit 3\n')
    skrills.chmod(0o755)
    return shims


def _bash(script: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", "-c", script],
        env={"PATH": f"{_shim_dir(tmp_path)}:/usr/bin:/bin", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_sourced_run_skrills_returns_to_the_caller(tmp_path: Path) -> None:
    result = _bash(
        f'trap "echo exit-trap-ran" EXIT; source "{WRAPPER}"; '
        'run_skrills validate; echo "after rc=$?"',
        tmp_path,
    )
    assert "skrills validate" in result.stdout
    assert "after rc=3" in result.stdout
    assert "exit-trap-ran" in result.stdout


def test_sourcing_leaves_the_callers_shell_alone(tmp_path: Path) -> None:
    result = _bash(
        f'SCRIPT_DIR=mine; source "{WRAPPER}"; '
        'echo "dir=$SCRIPT_DIR opts=$-"; false | true; echo "pipefail=$?"',
        tmp_path,
    )
    assert "dir=mine" in result.stdout
    assert "u" not in result.stdout.split("opts=")[1].split()[0]
    assert "pipefail=0" in result.stdout


def test_direct_invocation_still_passes_through(tmp_path: Path) -> None:
    result = subprocess.run(
        ["/bin/bash", str(WRAPPER), "validate", "--x"],
        env={"PATH": f"{_shim_dir(tmp_path)}:/usr/bin:/bin", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 3
    assert result.stdout == "skrills validate --x\n"
