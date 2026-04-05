#!/usr/bin/env python3
"""CLI script to query the code knowledge graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _SCRIPT_DIR.parent / "src"
sys.path.insert(0, str(_SRC_DIR))

from gauntlet.blast_radius import (
    analyze_changes,  # noqa: E402 - sys.path modified above
)
from gauntlet.communities import (
    get_architecture_overview,  # noqa: E402 - sys.path modified above
)
from gauntlet.flows import trace_flows  # noqa: E402 - sys.path modified above
from gauntlet.graph import GraphStore  # noqa: E402 - sys.path modified above
from gauntlet.search import search  # noqa: E402 - sys.path modified above


def _find_db(start_dir: str | None = None) -> Path | None:
    """Find graph.db by walking up from start_dir or cwd."""
    base = Path(start_dir) if start_dir else Path.cwd()
    for parent in [base, *base.parents]:
        candidate = parent / ".gauntlet" / "graph.db"
        if candidate.exists():
            return candidate
    return None


def main() -> None:
    """Query the code knowledge graph."""
    parser = argparse.ArgumentParser(description="Query code knowledge graph")
    parser.add_argument(
        "--action",
        required=True,
        choices=["search", "impact", "flows", "communities", "status"],
        help="Query action to perform",
    )
    parser.add_argument("--query", help="Search query string")
    parser.add_argument("--kind", help="Filter by node kind")
    parser.add_argument("--files", help="Comma-separated file paths")
    parser.add_argument("--depth", type=int, default=2, help="BFS depth")
    parser.add_argument("--entry", help="Entry point for flow tracing")
    parser.add_argument("--limit", type=int, default=20, help="Result limit")
    parser.add_argument("--base-ref", default="HEAD", help="Git base ref")
    parser.add_argument("--db", help="Path to graph.db")
    args = parser.parse_args()

    # Find database
    db_path = Path(args.db) if args.db else _find_db()
    if not db_path or not db_path.exists():
        print(json.dumps({"error": "graph.db not found. Run graph_build.py first."}))
        sys.exit(1)

    graph = GraphStore(db_path)

    try:
        result = _dispatch(args, graph)
        print(json.dumps(result, indent=2, default=str))
    finally:
        graph.close()


def _dispatch(args: argparse.Namespace, graph: GraphStore) -> dict:
    """Route to the appropriate query handler."""
    if args.action == "search":
        if not args.query:
            return {"error": "--query required for search action"}
        results = search(graph, args.query, kind=args.kind, limit=args.limit)
        return {"results": results, "count": len(results)}

    if args.action == "impact":
        return analyze_changes(graph, base_ref=args.base_ref)

    if args.action == "flows":
        flows = trace_flows(graph, max_depth=args.depth)
        if args.entry:
            flows = [f for f in flows if args.entry in f["entry_point"]]
        return {"flows": flows, "count": len(flows)}

    if args.action == "communities":
        return get_architecture_overview(graph)

    if args.action == "status":
        return {
            "node_count": graph.node_count(),
            "edge_count": graph.edge_count(),
            "last_build_type": graph.get_metadata("last_build_type"),
            "last_build_duration": graph.get_metadata("last_build_duration"),
            "last_build_files": graph.get_metadata("last_build_files"),
        }

    return {"error": f"unknown action: {args.action}"}


if __name__ == "__main__":
    main()
