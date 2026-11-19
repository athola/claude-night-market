#!/usr/bin/env python3
"""CLI script to build or incrementally update the code graph."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
_SCRIPT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _SCRIPT_DIR.parent / "src"
sys.path.insert(0, str(_SRC_DIR))

from gauntlet.flows import trace_flows  # noqa: E402 - sys.path modified above
from gauntlet.graph import GraphStore  # noqa: E402 - sys.path modified above
from gauntlet.incremental import (  # noqa: E402 - sys.path modified above
    full_build,
    incremental_update,
)


def _head_commit(root: Path) -> str | None:
    """Commit the tree was at when this build read it, None outside git."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


#: Everything gauntlet writes under .gauntlet/ except config.
_IGNORED = ("graph.db", "*.db-wal", "*.db-shm", "rebuild.*")


def _ensure_gitignore(gitignore: Path) -> None:
    """Add any missing ignore line; a legacy file lacked the rebuild ones."""
    present = gitignore.read_text().splitlines() if gitignore.exists() else []
    missing = [line for line in _IGNORED if line not in present]
    if missing:
        gitignore.write_text("".join(f"{line}\n" for line in [*present, *missing]))


def main() -> None:
    """Build or update the code knowledge graph."""
    parser = argparse.ArgumentParser(description="Build code knowledge graph")
    parser.add_argument("root_dir", help="Root directory to scan")
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only update changed files",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Git ref for incremental diff (default: the commit of the "
        "last successful build, else HEAD)",
    )
    args = parser.parse_args()

    root = Path(args.root_dir).resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {root}"}))
        sys.exit(1)

    db_dir = root / ".gauntlet"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "graph.db"

    _ensure_gitignore(db_dir / ".gitignore")
    # Read before the build: a commit made during a long build is not in
    # it, and stamping the later HEAD meant that commit was never parsed.
    head = _head_commit(root)

    graph = GraphStore(db_path)

    try:
        if args.incremental:
            # HEAD alone covers uncommitted edits only: on a clean tree a
            # graph many commits stale reported "no changes detected".
            base_ref = (
                args.base_ref or graph.get_metadata("last_build_commit") or "HEAD"
            )
            report = incremental_update(str(root), graph, base_ref)
            if report.get("error"):
                print(json.dumps(report, indent=2))
                sys.exit(2)
        else:
            report = full_build(str(root), graph)
            if not report.get("nodes_created"):
                # An empty graph is not a built graph. Without this a
                # missing parser or a tree with no sources reported a
                # green build, and every later search read its zero
                # results as "not in the codebase".
                report["error"] = (
                    f"no nodes created under {root}: no parseable sources, "
                    "or the tree-sitter parser is unavailable"
                )
                print(json.dumps(report, indent=2))
                sys.exit(2)
        # blast_radius scores a node by the stored flows that contain it. Tracing
        # without storing left that term at zero for every node.
        if head:
            graph.set_metadata("last_build_commit", head)
        flows = trace_flows(graph)
        graph.store_flows(flows)
        report["flows_stored"] = len(flows)
        print(json.dumps(report, indent=2))
    finally:
        graph.close()


if __name__ == "__main__":
    main()
