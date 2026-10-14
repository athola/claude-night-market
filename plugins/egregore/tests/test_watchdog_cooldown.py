"""The watchdog reads ``cooldown_until`` as the UTC instant it is.

``budget.py`` and ``window.record_reset`` write ``cooldown_until`` as a
UTC ISO timestamp. On macOS the watchdog parsed it with ``date -j``, which
reads the wall-clock fields in the local zone and ignores the offset:
under America/Los_Angeles a reset that had already passed still read as
seven hours away, and under Asia/Tokyo a reset an hour ahead read as eight
hours gone, so the watchdog relaunched into the same limit.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from budget import Budget
from window import record_reset

WATCHDOG = Path(__file__).resolve().parent.parent / "scripts" / "watchdog.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None, reason="watchdog.sh requires jq"
)


def _run_watchdog(tmp_path: Path, cooldown_until: str, tz: str) -> str:
    """Run one watchdog tick and return its log.

    The pidfile names this live process, so a tick that gets past the
    cooldown check exits at the "session alive" check instead of
    launching anything.
    """
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(
        json.dumps({"work_items": [{"status": "active"}]})
    )
    (egregore_dir / "budget.json").write_text(
        json.dumps({"cooldown_until": cooldown_until})
    )
    (egregore_dir / "pid").write_text(str(os.getpid()))
    subprocess.run(
        ["bash", str(WATCHDOG)],
        env={**os.environ, "EGREGORE_DIR": str(egregore_dir), "TZ": tz},
        check=True,
        cwd=tmp_path,
    )
    log = egregore_dir / "watchdog.log"
    return log.read_text() if log.exists() else ""


@pytest.mark.parametrize("microseconds", [0, 123456])
def test_a_passed_reset_is_not_a_cooldown_west_of_utc(
    tmp_path: Path, microseconds: int
) -> None:
    """An hour-old reset must not hold the watchdog in Los Angeles."""
    passed = datetime.now(timezone.utc).replace(microsecond=microseconds)
    stamp = (passed - timedelta(hours=1)).isoformat()

    assert "In cooldown" not in _run_watchdog(tmp_path, stamp, "America/Los_Angeles")


@pytest.mark.parametrize("microseconds", [0, 123456])
def test_a_future_reset_is_a_cooldown_east_of_utc(
    tmp_path: Path, microseconds: int
) -> None:
    """A reset an hour ahead must hold the watchdog in Tokyo."""
    now = datetime.now(timezone.utc).replace(microsecond=microseconds)
    stamp = (now + timedelta(hours=1)).isoformat()

    assert "In cooldown" in _run_watchdog(tmp_path, stamp, "Asia/Tokyo")


def test_record_reset_writes_the_resume_instant_in_utc() -> None:
    """The watchdog's UTC reading holds only if every writer emits UTC.

    A reset header can carry any offset; the stored string must not.
    """
    state = Budget()
    reset_at = datetime(2026, 10, 5, 21, 0, tzinfo=timezone(timedelta(hours=9)))

    record_reset(state, reset_at, now=reset_at - timedelta(hours=1))

    assert state.cooldown_until == "2026-10-05T12:00:00+00:00"


@pytest.mark.parametrize("stamp", ["garbage", "2099-13-45T99:00:00+00:00"])
def test_an_unparseable_cooldown_is_an_error_not_an_expired_cooldown(
    tmp_path: Path, stamp: str
) -> None:
    """A cooldown that does not parse stops the tick, like a bad budget.json."""
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()
    (egregore_dir / "manifest.json").write_text(
        json.dumps({"work_items": [{"status": "active"}]})
    )
    (egregore_dir / "budget.json").write_text(json.dumps({"cooldown_until": stamp}))
    # No pidfile: a tick that got past the cooldown would relaunch.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    claude = fake_bin / "claude"
    claude.write_text(f"#!/bin/sh\ntouch '{tmp_path / 'launched'}'\n")
    claude.chmod(0o755)

    proc = subprocess.run(
        ["bash", str(WATCHDOG)],
        env={
            **os.environ,
            "EGREGORE_DIR": str(egregore_dir),
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        },
        cwd=tmp_path,
        check=False,
    )

    log = (egregore_dir / "watchdog.log").read_text()
    assert proc.returncode == 1
    assert f"cooldown_until '{stamp}' does not parse" in log
    assert "Relaunching" not in log
    assert not (egregore_dir / "pid").exists()
