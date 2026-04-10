#!/usr/bin/env python3
"""PostToolUse hook: refresh community detection after graph builds.

Detects when gauntlet's graph_build.py completes and auto-runs
community detection to keep architectural clusters current.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _find_graph_db() -> Path | None:
    """Find .gauntlet/graph.db by walking up from cwd."""
    cwd = Path(os.getcwd())
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".gauntlet" / "graph.db"
        if candidate.exists():
            return candidate
    return None


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Refresh communities after graph_build.py runs."""
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        return None

    command = tool_input.get("command", "")
    if "graph_build.py" not in command:
        return None

    # Check success
    tool_result = hook_input.get("tool_result", {})
    if tool_result.get("exitCode", 1) != 0:
        return None

    db_path = _find_graph_db()
    if db_path is None:
        return None

    # Add gauntlet src to path for imports
    gauntlet_src = None
    for search in [
        db_path.parent.parent / "src",  # .gauntlet/../src
    ]:
        if (search / "gauntlet").is_dir():
            gauntlet_src = search
            break

    if gauntlet_src is None:
        # Try finding via plugin directories
        plugins_dir = Path(__file__).resolve().parents[2]
        candidate = plugins_dir / "gauntlet" / "src"
        if (candidate / "gauntlet").is_dir():
            gauntlet_src = candidate

    if gauntlet_src and str(gauntlet_src) not in sys.path:
        sys.path.insert(0, str(gauntlet_src))

    try:
        import gauntlet.communities as _gc
        import gauntlet.graph as _gg

        graph = _gg.GraphStore(str(db_path))
        communities = _gc.detect_communities(graph)
        graph.close()

        names = [c.get("name", "?") for c in communities[:5]]
        msg = (
            f"Communities refreshed: {len(communities)} clusters detected"
            f" ({', '.join(names)})"
        )
        return {"additionalContext": msg}
    except Exception:
        sys.stderr.write("graph_community_refresh: community detection failed\n")
        return None


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
