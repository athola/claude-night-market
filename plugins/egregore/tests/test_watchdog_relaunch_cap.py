"""The watchdog stops relaunching a session that makes no progress.

Every tick with an active item and no live session relaunched, with no
count across sessions. The Stop hook's stall bound is per session and a
relaunch is a new session, so an item stuck with an unchanged manifest
(or a ``claude -p`` that fails at once on auth) was relaunched every five
minutes, indefinitely.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

WATCHDOG = Path(__file__).resolve().parent.parent / "scripts" / "watchdog.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None, reason="watchdog.sh requires jq"
)


def _setup(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(
        json.dumps({"work_items": [{"id": "wrk_001", "status": "active"}]})
    )
    launches = tmp_path / "launches"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    stub = fake_bin / "claude"
    stub.write_text(f"#!/bin/sh\nprintf 'x\\n' >> '{launches}'\n")
    stub.chmod(0o755)
    env = {
        **os.environ,
        "EGREGORE_DIR": str(egregore_dir),
        "EGREGORE_MAX_STALLED_RELAUNCHES": "3",
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
    }
    return egregore_dir, launches, env


def _launch_count(launches: Path) -> int:
    return len(launches.read_text().splitlines()) if launches.exists() else 0


def _tick(egregore_dir: Path, launches: Path, env: dict[str, str]) -> None:
    """Run one watchdog tick and wait for any session it started to exit."""
    before = _launch_count(launches)
    subprocess.run(["bash", str(WATCHDOG)], env=env, check=True, timeout=30)
    pidfile = egregore_dir / "pid"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        launched = _launch_count(launches) > before
        if not pidfile.exists() or (launched and not _alive(pidfile)):
            return
        time.sleep(0.05)
    raise AssertionError("stub session did not finish")


def _alive(pidfile: Path) -> bool:
    try:
        os.kill(int(pidfile.read_text().strip()), 0)
    except (ProcessLookupError, ValueError):
        return False
    return True


def test_watchdog_stops_relaunching_after_n_sessions_without_manifest_change(
    tmp_path: Path,
) -> None:
    egregore_dir, launches, env = _setup(tmp_path)
    for _ in range(6):
        _tick(egregore_dir, launches, env)
    assert _launch_count(launches) == 3
    log = (egregore_dir / "watchdog.log").read_text()
    assert "without manifest progress" in log
    assert str(egregore_dir / "relaunch-state") in log


def test_a_manifest_change_resets_the_relaunch_cap(tmp_path: Path) -> None:
    egregore_dir, launches, env = _setup(tmp_path)
    for _ in range(4):
        _tick(egregore_dir, launches, env)
    (egregore_dir / "manifest.json").write_text(
        json.dumps(
            {"work_items": [{"id": "wrk_001", "status": "active", "pipeline_step": 2}]}
        )
    )
    _tick(egregore_dir, launches, env)
    assert _launch_count(launches) == 4


def test_a_session_that_ended_on_a_usage_limit_is_not_a_stall(tmp_path: Path) -> None:
    """A rate-limited session writes budget.json, not the manifest, and
    three of them parked the watchdog for good.
    """
    egregore_dir, launches, env = _setup(tmp_path)
    for _ in range(3):
        _tick(egregore_dir, launches, env)
    (egregore_dir / "budget.json").write_text(
        json.dumps({"cooldown_until": "2000-01-01T00:00:00+00:00"})
    )
    _tick(egregore_dir, launches, env)
    assert _launch_count(launches) == 4
