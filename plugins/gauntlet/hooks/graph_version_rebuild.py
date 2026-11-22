#!/usr/bin/env python3
"""SessionStart hook: rebuild a code graph that an older gauntlet built.

A release can change what extraction writes (new columns, new edge
resolution), and an existing graph keeps the old shape until each file is
re-parsed. When the graph's recorded ``gauntlet_version`` is older than
the installed plugin, or missing, start one full build in the background. The build
needs tree-sitter, which the system python running hooks may lack, so it
runs through ``uv run --project`` in the plugin's own environment.

Opt out with ``{"rebuild_on_upgrade": false}`` in ``.gauntlet/config.json``.
"""

from __future__ import annotations

import fcntl
import json
import os
import shlex
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from _graph_hook_common import (
    PLUGIN_ROOT,
    context,
    graph_build_argv,
    last_run_failed,
    launch,
    status_command,
)

# A full build of a large repository takes minutes; a lock older than this
# belongs to a build that died, and blocking every later session on it
# would leave the graph stale for good.
_LOCK_TTL_SECONDS = 2 * 60 * 60


def _installed_version() -> str:
    """Version of the installed plugin, as the release bump writes it."""
    manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])


def _graph_version(db_path: Path) -> str | None:
    """Version that built the graph, None when it was never recorded."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT value FROM metadata WHERE key = 'gauntlet_version'"
        ).fetchone()
    except sqlite3.OperationalError as exc:
        # A graph without the table predates version stamps. Any other
        # error, such as a lock held by a running build, must not read
        # as "never recorded" and start a second build.
        if "no such table" not in str(exc):
            raise
        return None
    finally:
        conn.close()
    return row[0] if row else None


def _older(built: str | None, installed: str) -> bool:
    """Whether the graph predates the installed plugin.

    A graph newer than the plugin is left alone: the release runbook builds
    with the bumped version before the installed plugin is updated.
    """
    if built is None:
        return True
    # update_versions.py writes only X.Y.Z, so both sides parse.
    return tuple(map(int, built.split("."))) < tuple(map(int, installed.split(".")))


def _opted_out(gauntlet_dir: Path) -> bool:
    config = gauntlet_dir / "config.json"
    if not config.exists():
        return False
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # An unreadable opt-out is not consent to a multi-minute rebuild.
        return True
    return isinstance(data, dict) and data.get("rebuild_on_upgrade") is False


def _guard_path(lock: Path) -> Path:
    return lock.with_name(lock.name + ".guard")


def _take_lock(lock: Path) -> bool:
    """Create the lock, replacing one a dead build left behind.

    The stale check, unlink and create run under an exclusive flock on a
    guard file. Without it, two sessions could both find the lock stale,
    and the second would unlink the first's fresh lock and build again.
    A taker that finds the guard held gives way: someone else is deciding.
    """
    with open(_guard_path(lock), "a") as guard:
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        try:
            if time.time() - lock.stat().st_mtime > _LOCK_TTL_SECONDS:
                lock.unlink()
        except FileNotFoundError:
            pass
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return False
        os.write(fd, str(time.time()).encode("ascii"))
        os.close(fd)
        return True


def _session_context(message: str) -> dict[str, Any]:
    return context("SessionStart", message)


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Start a background rebuild when the graph predates the plugin."""
    root = Path(os.getcwd())
    gauntlet_dir = root / ".gauntlet"
    db_path = gauntlet_dir / "graph.db"
    if not db_path.exists() or _opted_out(gauntlet_dir):
        return None

    installed = _installed_version()
    try:
        built = _graph_version(db_path)
    except sqlite3.OperationalError:
        # Locked by a build in progress: wait rather than start a second.
        return None
    except sqlite3.DatabaseError:
        return _session_context(
            f"gauntlet graph at {db_path} is unreadable, so it was not "
            "rebuilt. Run /gauntlet-graph build to replace it."
        )
    if not _older(built, installed):
        return None
    built_label = built or "an unrecorded version"

    uv = shutil.which("uv")
    if uv is None:
        return _session_context(
            f"gauntlet graph was built by {built_label}, plugin is {installed}. "
            "uv is not on PATH, so it was not rebuilt. Install uv "
            "(https://docs.astral.sh/uv/), then run /gauntlet-graph build."
        )

    lock = gauntlet_dir / "rebuild.lock"
    status = gauntlet_dir / "rebuild.status"
    log_path = gauntlet_dir / "rebuild.log"
    if not _take_lock(lock):
        if last_run_failed(status):
            return _session_context(
                f"gauntlet graph rebuild failed (log: {log_path}). It is "
                f"retried once {lock} is removed or two hours old."
            )
        return None

    # A failed build keeps the lock, so sessions do not relaunch it until
    # the lock goes stale; the status file and the log say it failed.
    status.unlink(missing_ok=True)
    script = (
        f"{status_command(graph_build_argv(uv, root), status)}; "
        f'[ "$(cat {shlex.quote(str(status))})" = 0 ] '
        f"&& rm -f {shlex.quote(str(lock))}"
    )
    argv = ["sh", "-c", script]
    nice = shutil.which("nice")
    if nice:
        argv = [nice, "-n", "10", *argv]

    try:
        launch(argv, root, log_path)
    except OSError:
        # Nothing was started, so nothing will release the lock.
        lock.unlink(missing_ok=True)
        raise
    return _session_context(
        f"gauntlet graph was built by {built_label}, plugin is {installed}: "
        f"rebuilding in the background (log: {log_path})."
    )


if __name__ == "__main__":
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, OSError):
        payload = {}
    output = main(payload)
    if output is not None:
        print(json.dumps(output))
