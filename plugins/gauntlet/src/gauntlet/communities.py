"""Community detection via Leiden algorithm with file-based fallback."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind

_log = logging.getLogger(__name__)

# Edge weights by type for community detection
_EDGE_WEIGHTS: dict[EdgeKind, float] = {
    EdgeKind.CALLS: 1.0,
    EdgeKind.INHERITS: 0.8,
    EdgeKind.IMPLEMENTS: 0.7,
    EdgeKind.IMPORTS_FROM: 0.5,
    EdgeKind.TESTED_BY: 0.4,
    EdgeKind.CONTAINS: 0.3,
}

_MAX_COMMUNITY_SIZE = 50


def detect_communities(
    graph: GraphStore,
    language: str | None = None,
) -> list[dict]:
    """Detect architectural communities in the graph.

    Uses Leiden algorithm if igraph is available,
    otherwise falls back to file-based grouping.
    """
    all_nodes = graph.get_all_nodes()
    if language:
        all_nodes = [n for n in all_nodes if n.language == language]

    # Filter to meaningful nodes (skip Files)
    nodes = [n for n in all_nodes if n.kind not in (NodeKind.FILE,)]

    if not nodes:
        return []

    all_edges = graph.get_all_edges()

    # Try Leiden algorithm
    try:
        communities = _leiden_communities(nodes, all_edges)
    except Exception as exc:
        _log.warning(
            "Leiden community detection failed (%s), using file-based fallback", exc
        )
        communities = _file_based_communities(nodes)

    # Subdivide large communities
    final: list[dict] = []
    for comm in communities:
        if len(comm["node_qns"]) > _MAX_COMMUNITY_SIZE:
            sub = _subdivide_community(comm, all_edges, graph)
            final.extend(sub)
        else:
            final.append(comm)

    # Calculate cohesion and store
    for comm in final:
        comm["cohesion"] = calculate_cohesion(
            set(comm["node_qns"]),
            all_edges,
        )

    graph.store_communities(final)
    return final


def _leiden_communities(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> list[dict]:
    """Detect communities using Leiden algorithm via igraph."""
    import igraph as ig  # noqa: PLC0415 - optional dep, lazy import

    qn_to_idx = {n.qualified_name: i for i, n in enumerate(nodes)}
    g = ig.Graph(n=len(nodes), directed=False)

    edge_list = []
    weights = []
    for edge in edges:
        src_idx = qn_to_idx.get(edge.source_qn)
        tgt_idx = qn_to_idx.get(edge.target_qn)
        if src_idx is not None and tgt_idx is not None and src_idx != tgt_idx:
            edge_list.append((src_idx, tgt_idx))
            weights.append(_EDGE_WEIGHTS.get(edge.kind, 0.5))

    if edge_list:
        g.add_edges(edge_list)
        partition = g.community_leiden(weights=weights, objective_function="modularity")
    else:
        partition = [[i] for i in range(len(nodes))]

    communities: list[dict] = []
    for members in partition:
        member_nodes = [nodes[i] for i in members]
        name = _generate_name(member_nodes)
        communities.append(
            {
                "name": name,
                "node_qns": [n.qualified_name for n in member_nodes],
            }
        )

    return communities


def _file_based_communities(nodes: list[GraphNode]) -> list[dict]:
    """Fallback: group nodes by file path."""
    by_file: dict[str, list[GraphNode]] = defaultdict(list)
    for node in nodes:
        by_file[node.file_path].append(node)

    communities: list[dict] = []
    for file_path, file_nodes in by_file.items():
        name = Path(file_path).stem
        communities.append(
            {
                "name": name,
                "node_qns": [n.qualified_name for n in file_nodes],
            }
        )

    return communities


def _subdivide_community(
    community: dict,
    all_edges: list[GraphEdge],
    graph: GraphStore,
) -> list[dict]:
    """Split a large community by sub-file grouping."""
    qns = set(community["node_qns"])
    by_file: dict[str, list[str]] = defaultdict(list)
    for qn in qns:
        node = graph.get_node(qn)
        if node:
            by_file[node.file_path].append(qn)

    if len(by_file) <= 1:
        return [community]

    result: list[dict] = []
    for file_path, file_qns in by_file.items():
        name = f"{community['name']}/{Path(file_path).stem}"
        result.append(
            {
                "name": name,
                "node_qns": file_qns,
            }
        )

    return result


def _generate_name(nodes: list[GraphNode]) -> str:
    """Generate a descriptive name for a community."""
    if not nodes:
        return "unknown"

    # Most common file stem
    stems = [Path(n.file_path).stem for n in nodes]
    stem_counts = Counter(stems)
    common_stem = stem_counts.most_common(1)[0][0]

    # Check for dominant class
    class_nodes = [n for n in nodes if n.kind == NodeKind.CLASS]
    if len(class_nodes) > len(nodes) * 0.4:
        class_names = Counter(n.qualified_name.rsplit("::", 1)[-1] for n in class_nodes)
        dominant = class_names.most_common(1)[0][0]
        return f"{common_stem}-{dominant}"

    return common_stem


def calculate_cohesion(
    community_qns: set[str],
    all_edges: list[GraphEdge],
) -> float:
    """Calculate cohesion: internal / (internal + external) edges."""
    internal = 0
    external = 0

    for edge in all_edges:
        src_in = edge.source_qn in community_qns
        tgt_in = edge.target_qn in community_qns
        if src_in and tgt_in:
            internal += 1
        elif src_in or tgt_in:
            external += 1

    total = internal + external
    if total == 0:
        return 0.0

    return round(internal / total, 4)


def get_architecture_overview(graph: GraphStore) -> dict:
    """Generate architecture overview with coupling warnings."""
    communities = detect_communities(graph)

    warnings: list[dict] = []
    all_edges = graph.get_all_edges()

    # Check cross-community coupling
    comm_qn_sets = [set(c["node_qns"]) for c in communities]
    for i, j in combinations(range(len(communities)), 2):
        cross_edges = sum(
            1
            for edge in all_edges
            if (edge.source_qn in comm_qn_sets[i] and edge.target_qn in comm_qn_sets[j])
            or (edge.source_qn in comm_qn_sets[j] and edge.target_qn in comm_qn_sets[i])
        )
        if cross_edges > 10:
            warnings.append(
                {
                    "communities": [communities[i]["name"], communities[j]["name"]],
                    "coupling_strength": cross_edges,
                    "severity": "high" if cross_edges > 20 else "medium",
                }
            )

    return {
        "communities": [
            {
                "name": c["name"],
                "node_count": len(c["node_qns"]),
                "cohesion": c.get("cohesion", 0.0),
            }
            for c in communities
        ],
        "warnings": warnings,
        "total_communities": len(communities),
    }
