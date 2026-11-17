#!/usr/bin/env python3
"""SessionStart hook: rebuild a code graph that an older gauntlet built.

A release can change what extraction writes (new columns, new edge
resolution), and an existing graph keeps the old shape until each file is
re-parsed. When the graph's recorded ``gauntlet_version`` differs from
the installed plugin, start one full build in the background. The build
needs tree-sitter, which the system python running hooks may lack, so it
runs through ``uv run --project`` in the plugin's own environment.

Opt out with ``{"rebuild_on_upgrade": false}`` in ``.gauntlet/config.json``.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent

# A full build of a large repository takes minutes; a lock older than this
# belongs to a build that died, and blocking every later session on it
# would leave the graph stale for good.
_LOCK_TTL_SECONDS = 2 * 60 * 60


def _installed_version() -> str:
    """Version of the installed plugin, as the release bump writes it."""
    manifest = _PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
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


def _take_lock(lock: Path) -> bool:
    """Create the lock, replacing one a dead build left behind."""
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


def _context(message: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": message,
        }
    }


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Start a background rebuild when the graph predates the plugin."""
    root = Path(os.getcwd())
    gauntlet_dir = root / ".gauntlet"
    db_path = gauntlet_dir / "graph.db"
    if not db_path.exists() or _opted_out(gauntlet_dir):
        return None

    installed = _installed_version()
    built = _graph_version(db_path)
    if not _older(built, installed):
        return None
    built_label = built or "an unrecorded version"

    uv = shutil.which("uv")
    if uv is None:
        return _context(
            f"gauntlet graph was built by {built_label}, plugin is {installed}. "
            "uv is not on PATH, so it was not rebuilt. Install uv "
            "(https://docs.astral.sh/uv/), then run /gauntlet-graph build."
        )

    lock = gauntlet_dir / "rebuild.lock"
    if not _take_lock(lock):
        return None

    build = shlex.join(
        [
            uv,
            "run",
            "--project",
            str(_PLUGIN_ROOT),
            "python",
            str(_PLUGIN_ROOT / "scripts" / "graph_build.py"),
            str(root),
        ]
    )
    # A failed build keeps the lock, so sessions do not relaunch it until
    # the lock goes stale; the log says why it failed.
    script = f"{build} && rm -f {shlex.quote(str(lock))}"
    argv = ["sh", "-c", script]
    nice = shutil.which("nice")
    if nice:
        argv = [nice, "-n", "10", *argv]

    log_path = gauntlet_dir / "rebuild.log"
    with open(log_path, "ab") as log:
        subprocess.Popen(
            argv,
            cwd=str(root),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return _context(
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
