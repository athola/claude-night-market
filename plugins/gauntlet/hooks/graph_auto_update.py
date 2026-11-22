#!/usr/bin/env python3
"""PostToolUse hook: auto-update the code graph after git commits.

Runs an incremental graph update when a git commit succeeds.
Opt-in via .gauntlet/config.json: {"auto_update": true}
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from _graph_hook_common import (
    context,
    graph_build_argv,
    last_run_failed,
    launch,
    status_command,
)

from gauntlet.git_commands import is_git_commit
from gauntlet.treesitter_parser import parser_available


def _get_gauntlet_dir() -> Path | None:
    cwd = Path(os.getcwd())
    candidate = cwd / ".gauntlet"
    if candidate.is_dir():
        return candidate
    return None


def _is_auto_update_enabled(gauntlet_dir: Path) -> bool:
    """Check if auto_update is enabled in config."""
    for name in ("config.json", "config.yaml"):
        config_path = gauntlet_dir / name
        if config_path.exists():
            try:
                if name.endswith(".json"):
                    data = json.loads(config_path.read_text())
                else:
                    try:
                        from yaml import (
                            safe_load,
                        )

                        data = safe_load(config_path.read_text())
                    except ImportError:
                        print(
                            f"warning: PyYAML is not installed for {sys.executable}; "
                            f"{config_path} is ignored",
                            file=sys.stderr,
                        )
                        continue
                if not isinstance(data, dict):
                    continue
                return bool(data.get("auto_update", False))
            except (json.JSONDecodeError, OSError, TypeError):
                continue
    return False


def _update_in_plugin_env(gauntlet_dir: Path) -> dict[str, Any] | None:
    """Run the incremental update where tree-sitter is installed.

    This hook runs on the first python3 on PATH, which usually lacks
    tree-sitter, so every commit reported "Graph not updated". The plugin's
    own environment has it. The update is detached because the hook has a
    five-second timeout, the same way the version-rebuild hook launches.
    """
    uv = shutil.which("uv")
    if uv is None:
        return _context(
            "Graph not updated: this python3 has no tree-sitter and uv is not "
            "on PATH. Run /gauntlet-graph build."
        )
    if (gauntlet_dir / "rebuild.lock").exists():
        # A version rebuild is already rewriting this graph, or failed and
        # still holds the lock.
        if last_run_failed(gauntlet_dir / "rebuild.status"):
            return _context(
                "Graph not updated: the background rebuild failed (log: "
                f"{gauntlet_dir / 'rebuild.log'})."
            )
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
    launch(["sh", "-c", status_command(build, status)], root, log_path)
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

    if not parser_available():
        return _update_in_plugin_env(gauntlet_dir)

    try:
        from gauntlet.graph import (
            GraphStore,
        )
        from gauntlet.incremental import (
            incremental_update,
        )

        start = time.monotonic()
        graph = GraphStore(str(db_path))
        try:
            report = incremental_update(
                str(Path(os.getcwd())), graph, base_ref="HEAD~1"
            )
        finally:
            graph.close()
        duration = round(time.monotonic() - start, 2)

        # An error or skipped report did no work. Its counters are zeros
        # that would otherwise read as a successful update.
        reason = report.get("error") or report.get("skipped")
        if reason:
            msg = f"Graph not updated: {reason}"
        else:
            files = report.get("files_parsed", 0)
            nodes = report.get("nodes_created", 0)
            msg = f"Graph updated: {files} files, {nodes} nodes in {duration}s"
        return _context(msg)
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "graph_auto_update failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return None


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
