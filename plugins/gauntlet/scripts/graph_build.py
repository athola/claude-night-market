#!/usr/bin/env python3
"""CLI script to build or incrementally update the code graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
_SCRIPT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _SCRIPT_DIR.parent / "src"
sys.path.insert(0, str(_SRC_DIR))

from gauntlet.graph import GraphStore  # noqa: E402 - sys.path modified above
from gauntlet.incremental import (  # noqa: E402 - sys.path modified above
    full_build,
    incremental_update,
)


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
        default="HEAD",
        help="Git ref for incremental diff (default: HEAD)",
    )
    args = parser.parse_args()

    root = Path(args.root_dir).resolve()
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {root}"}))
        sys.exit(1)

    db_dir = root / ".gauntlet"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "graph.db"

    # Write .gitignore if missing
    gitignore = db_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("graph.db\n*.db-wal\n*.db-shm\n")

    graph = GraphStore(db_path)

    try:
        if args.incremental:
            report = incremental_update(str(root), graph, args.base_ref)
        else:
            report = full_build(str(root), graph)
        print(json.dumps(report, indent=2))
    finally:
        graph.close()


if __name__ == "__main__":
    main()
