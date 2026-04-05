"""Blast radius analysis with risk scoring for code changes."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from gauntlet.constants import SECURITY_KEYWORDS
from gauntlet.graph import GraphStore
from gauntlet.incremental import _validate_ref
from gauntlet.models import EdgeKind, GraphNode, NodeKind

_DEFAULT_WEIGHTS = {
    "test_gap": 0.30,
    "security": 0.20,
    "flow_participation": 0.25,
    "cross_community": 0.15,
    "caller_count": 0.10,
}


def load_weights(gauntlet_dir: str | Path | None = None) -> dict[str, float]:
    """Load risk scoring weights from .gauntlet/config.json.

    Falls back to defaults if the file doesn't exist or
    is missing keys. Users can override individual weights
    without specifying all five.
    """
    weights = dict(_DEFAULT_WEIGHTS)
    if gauntlet_dir is None:
        return weights
    config_path = Path(gauntlet_dir) / "config.json"
    if not config_path.exists():
        return weights
    try:
        data = json.loads(config_path.read_text())
        user_weights = data.get("risk_weights", {})
        for key in _DEFAULT_WEIGHTS:
            if key in user_weights:
                weights[key] = float(user_weights[key])
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        pass
    return weights


_HUNK_PATTERN = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_FILE_PATTERN = re.compile(r"^\+\+\+ b/(.+)$")


def parse_git_diff_ranges(
    base_ref: str = "HEAD",
) -> dict[str, list[tuple[int, int]]]:
    """Parse git diff --unified=0 for changed line ranges per file."""
    ref = _validate_ref(base_ref)
    try:
        result = subprocess.run(
            ["git", "diff", "--unified=0", ref],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}

    ranges: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None

    for line in result.stdout.splitlines():
        file_match = _FILE_PATTERN.match(line)
        if file_match:
            current_file = file_match.group(1)
            if current_file not in ranges:
                ranges[current_file] = []
            continue

        hunk_match = _HUNK_PATTERN.match(line)
        if hunk_match and current_file:
            start = int(hunk_match.group(1))
            count = int(hunk_match.group(2) or "1")
            if count == 0:
                continue
            end = start + count - 1
            ranges[current_file].append((start, end))

    return ranges


def map_changes_to_nodes(
    graph: GraphStore,
    changed_ranges: dict[str, list[tuple[int, int]]],
) -> list[GraphNode]:
    """Map changed line ranges to graph nodes."""
    affected: dict[str, GraphNode] = {}

    for file_path, line_ranges in changed_ranges.items():
        nodes = graph.get_nodes_in_file(file_path)
        for node in nodes:
            for start, end in line_ranges:
                if node.line_start <= end and node.line_end >= start:
                    affected[node.qualified_name] = node
                    break

    return list(affected.values())


def compute_risk_score(
    node: GraphNode,
    graph: GraphStore,
    weights: dict[str, float] | None = None,
) -> float:
    """Compute risk score (0.0-1.0) for a node using five weighted factors.

    Pass custom weights from load_weights() or use defaults.
    """
    w = weights or _DEFAULT_WEIGHTS
    score = 0.0

    # Factor 1: Test coverage gap
    tested_by = [
        e
        for e in graph.get_edges_by_source(node.qualified_name)
        if e.kind == EdgeKind.TESTED_BY
    ]
    if not tested_by:
        score += w["test_gap"]
    else:
        score += 0.05

    # Factor 2: Security sensitivity
    qn_lower = node.qualified_name.lower()
    if any(kw in qn_lower for kw in SECURITY_KEYWORDS):
        score += w["security"]

    # Factor 3: Flow participation
    flows = graph.get_flows_containing(node.qualified_name)
    flow_contribution = min(len(flows) * 0.05, w["flow_participation"])
    score += flow_contribution

    # Factor 4: Cross-community callers
    callers = graph.get_edges_by_target(node.qualified_name)
    caller_edges = [e for e in callers if e.kind == EdgeKind.CALLS]
    node_community = graph.get_community_for_node(node.qualified_name)
    cross_community = 0
    if node_community is not None:
        for edge in caller_edges:
            caller_comm = graph.get_community_for_node(edge.source_qn)
            if caller_comm is not None and caller_comm != node_community:
                cross_community += 1
    community_contribution = min(cross_community / 10, w["cross_community"])
    score += community_contribution

    # Factor 5: Caller count
    caller_contribution = min(len(caller_edges) / 20, w["caller_count"])
    score += caller_contribution

    return min(round(score, 4), 1.0)


def analyze_changes(
    graph: GraphStore,
    base_ref: str = "HEAD",
) -> dict[str, Any]:
    """Full blast radius analysis pipeline."""
    ranges = parse_git_diff_ranges(base_ref)
    if not ranges:
        return {
            "overall_risk": "none",
            "affected_nodes": [],
            "risk_scores": {},
            "review_priorities": [],
        }

    # Map to nodes
    direct = map_changes_to_nodes(graph, ranges)

    # BFS for downstream impact
    changed_files = list(ranges.keys())
    all_affected = graph.impact_radius(changed_files, depth=2)

    # Risk scores
    risk_scores: dict[str, float] = {}
    for node in all_affected:
        risk_scores[node.qualified_name] = compute_risk_score(node, graph)

    # Untested functions
    untested = [
        n
        for n in all_affected
        if n.kind == NodeKind.FUNCTION
        and not any(
            e.kind == EdgeKind.TESTED_BY
            for e in graph.get_edges_by_source(n.qualified_name)
        )
    ]

    # Top 10 by risk
    sorted_nodes = sorted(
        all_affected,
        key=lambda n: risk_scores.get(n.qualified_name, 0),
        reverse=True,
    )
    review_priorities = [n.to_dict() for n in sorted_nodes[:10]]

    # Overall risk
    max_risk = max(risk_scores.values()) if risk_scores else 0
    if max_risk >= 0.7:
        overall = "high"
    elif max_risk >= 0.4:
        overall = "medium"
    else:
        overall = "low"

    return {
        "overall_risk": overall,
        "affected_nodes": [n.to_dict() for n in all_affected],
        "risk_scores": risk_scores,
        "untested_functions": [n.qualified_name for n in untested],
        "review_priorities": review_priorities,
        "direct_changes": len(direct),
        "total_affected": len(all_affected),
    }
