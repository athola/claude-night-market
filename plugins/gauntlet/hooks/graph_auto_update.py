#!/usr/bin/env python3
"""PostToolUse hook: auto-update the code graph after git commits.

Runs an incremental graph update when a git commit succeeds.
Opt-in via .gauntlet/config.json: {"auto_update": true}
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from _gauntlet_config import load_config
from _graph_hook_common import (
    context,
    graph_build_argv,
    last_run_failed,
    launch,
    status_command,
)

from gauntlet._vendored_leyline_shell_command import is_git_commit
from gauntlet.build_lock import BUSY_EXIT_CODE, writer_busy


def _get_gauntlet_dir() -> Path | None:
    cwd = Path(os.getcwd())
    candidate = cwd / ".gauntlet"
    if candidate.is_dir():
        return candidate
    return None


def _is_auto_update_enabled(gauntlet_dir: Path) -> bool:
    """Check if auto_update is enabled in config."""
    config = load_config(gauntlet_dir)
    return bool(config and config.get("auto_update", False))


def _update_in_plugin_env(gauntlet_dir: Path) -> dict[str, Any] | None:
    """Run the incremental update where tree-sitter is installed.

    This hook runs on the first python3 on PATH, which usually lacks
    tree-sitter; the plugin's own environment has it. graph_build.py is the
    one path even where this python3 has a parser, because only it diffs
    from the last stamped build and stamps the new one. The update is
    detached because the hook has a five-second timeout.
    """
    uv = shutil.which("uv")
    if uv is None:
        return _context(
            "Graph not updated: uv is not on PATH, so the plugin environment "
            "cannot run the build. Run /gauntlet-graph build."
        )
    if writer_busy(gauntlet_dir):
        # A running build reads HEAD itself, and the next update diffs from
        # the commit that build stamps, so this commit is not lost.
        return None
    # The graph the hook found, which may sit above the cwd.
    root = gauntlet_dir.parent
    log_path = gauntlet_dir / "update.log"
    status = gauntlet_dir / "update.status"
    failed = last_run_failed(status)
    status.unlink(missing_ok=True)
    # No --base-ref: the build diffs from the last commit it stamped, so a
    # commit an earlier update missed is still parsed.
    build = graph_build_argv(uv, root, "--incremental")
    script = status_command(build, status, BUSY_EXIT_CODE)
    launch(["sh", "-c", script], root, log_path)
    if failed:
        return _context(
            "Graph not updated: the last background update failed (log: "
            f"{log_path}). Retrying in the background."
        )
    return _context(f"Graph updating in the background (log: {log_path}).")


def _context(message: str) -> dict[str, Any]:
    return context("PostToolUse", message)


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Process a PostToolUse hook event after git commit."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        return None

    command = tool_input.get("command", "")
    if not is_git_commit(command):
        return None

    # PostToolUse fires only after a tool completes successfully, so there is
    # no success test to make here and no exit code to read: the Bash entry
    # of tool_response carries stdout, stderr, interrupted and isImage only.
    # This read used the key "tool_result", which the payload has never
    # contained, so the dict was always empty, "exitCode" always defaulted to
    # 1, and the hook returned None on every invocation since it was written.
    tool_response = hook_input.get("tool_response", {})
    stdout = tool_response.get("stdout", "")
    if "nothing to commit" in stdout:
        return None

    gauntlet_dir = _get_gauntlet_dir()
    if gauntlet_dir is None:
        return None

    if not _is_auto_update_enabled(gauntlet_dir):
        return None

    db_path = gauntlet_dir / "graph.db"
    if not db_path.exists():
        return None

    return _update_in_plugin_env(gauntlet_dir)


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
