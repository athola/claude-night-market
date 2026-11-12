#!/usr/bin/env python3
"""PostToolUse hook: refresh community detection after graph builds.

Detects when gauntlet's graph_build.py completes and auto-runs
community detection to keep architectural clusters current.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from _vendored_leyline_sibling_plugins import sibling_plugin_dir


def _find_graph_db() -> Path | None:
    """Find .gauntlet/graph.db by walking up from cwd."""
    cwd = Path(os.getcwd())
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".gauntlet" / "graph.db"
        if candidate.exists():
            return candidate
    return None


# A run of graph_build.py, not a command that merely names it (rg, cat).
# Before the script or its interpreter a command may carry, in any order,
# `NAME=value` assignments, `time`, and `uv run` with its options.
_RUNS_GRAPH_BUILD = re.compile(
    r"(?:^|[;&|(])\s*"
    r"(?:(?:[A-Za-z_]\w*=\S*|time|uv\s+run(?:\s+-\S+(?:\s+[^-\s]\S*)?)*)\s+)*"
    r"(?:\S*python[\d.]*\s+(?:-\S+\s+)*)?"
    r"(?P<script>\"[^\"]*graph_build\.py\"|'[^']*graph_build\.py'"
    r"|\S*graph_build\.py\b)"
)


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Refresh communities after graph_build.py runs."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        return None

    command = tool_input.get("command", "")
    ran = _RUNS_GRAPH_BUILD.search(command)
    if ran is None:
        return None

    # PostToolUse fires only after a tool completes successfully, so reaching
    # here means graph_build.py ran. The previous check read "tool_result",
    # a key the payload has never carried, so "exitCode" always defaulted to
    # 1 and this hook returned None on every invocation since it was written.
    # The Bash tool_response has no exit code to consult in any case.

    db_path = _find_graph_db()
    if db_path is None:
        return None

    # A project that vendors gauntlet in ./src is preferred only when the
    # graph_build.py that ran is the project's own: its code has run anyway.
    # When the plugin's script ran inside some other repository, importing
    # that repository's src/gauntlet would run code the user never chose to.
    # The command is unexpanded text, so `${CLAUDE_PLUGIN_ROOT}/...`, `~/...`
    # and a quoted path all read as relative paths under the project. Only
    # an absolute path to an existing file inside the project proves it.
    gauntlet_src = None
    project = db_path.parent.parent.resolve()
    named = ran.group("script").strip("'\"")
    local_src = project / "src"
    if named.startswith("/") and "$" not in named and (local_src / "gauntlet").is_dir():
        script = Path(named).resolve()
        if script.is_file() and script.is_relative_to(project):
            gauntlet_src = local_src

    if gauntlet_src is None:
        gauntlet = sibling_plugin_dir(__file__, "gauntlet")
        candidate = (
            gauntlet or Path(__file__).resolve().parents[2] / "gauntlet"
        ) / "src"
        if (candidate / "gauntlet").is_dir():
            gauntlet_src = candidate

    if gauntlet_src and str(gauntlet_src) not in sys.path:
        sys.path.insert(0, str(gauntlet_src))

    try:
        # Cross-plugin import resolved at runtime via the sys.path injection
        # above. mypy cannot follow it statically.
        import gauntlet.communities as _gc  # type: ignore[import-not-found]  # runtime sys.path injection, not statically resolvable
        import gauntlet.graph as _gg  # type: ignore[import-not-found]  # runtime sys.path injection, not statically resolvable

        graph = _gg.GraphStore(str(db_path))
        try:
            communities = _gc.detect_communities(graph)
        finally:
            graph.close()

        names = [c.get("name", "?") for c in communities[:5]]
        msg = (
            f"Communities refreshed: {len(communities)} clusters detected"
            f" ({', '.join(names)})"
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": msg,
            }
        }
    except Exception as exc:
        sys.stderr.write(
            f"graph_community_refresh: community detection failed: "
            f"{type(exc).__name__}: {exc}\n"
        )
        return None


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    try:
        output = main(hook_input)
    except Exception as exc:
        sys.stderr.write(f"graph_community_refresh: {exc}\n")
        output = None

    if output is not None:
        print(json.dumps(output))
