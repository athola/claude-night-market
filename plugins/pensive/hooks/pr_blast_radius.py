#!/usr/bin/env python3
"""PreToolUse hook: surface blast radius context on PR creation.

When `gh pr create` is run, analyze the blast radius of the
branch's changes and add risk context as additionalContext.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _find_graph_db() -> Path | None:
    cwd = Path(os.getcwd())
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".gauntlet" / "graph.db"
        if candidate.exists():
            return candidate
    return None


def _find_gauntlet_src() -> Path | None:
    """Find the gauntlet src directory for imports."""
    # Try via plugin directory structure
    plugins_dir = Path(__file__).resolve().parents[2]
    candidate = plugins_dir / "gauntlet" / "src"
    if (candidate / "gauntlet").is_dir():
        return candidate
    return None


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Surface blast radius analysis when creating a PR."""
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if "gh pr create" not in command and "gh pr submit" not in command:
        return None

    db_path = _find_graph_db()
    if db_path is None:
        return None

    gauntlet_src = _find_gauntlet_src()
    if gauntlet_src and str(gauntlet_src) not in sys.path:
        sys.path.insert(0, str(gauntlet_src))

    try:
        import gauntlet.blast_radius as _br
        import gauntlet.graph as _gg

        graph = _gg.GraphStore(str(db_path))
        report = _br.analyze_changes(graph, base_ref="HEAD")
        graph.close()
    except Exception:
        return None

    overall = report.get("overall_risk", "none")
    total = report.get("total_affected", 0)
    untested = report.get("untested_functions", [])
    priorities = report.get("review_priorities", [])[:5]

    lines = [f"PR blast radius: {overall} risk, {total} nodes affected"]

    if priorities:
        lines.append("Top risk nodes:")
        scores = report.get("risk_scores", {})
        for node_dict in priorities:
            qn = node_dict.get("qualified_name", "?")
            short = qn.rsplit("::", 1)[-1] if "::" in qn else qn
            risk = scores.get(qn, 0)
            lines.append(f"  {risk:.2f} {short}")

    if untested:
        lines.append(f"{len(untested)} untested function(s) in blast radius")

    return {"additionalContext": "\n".join(lines)}


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
