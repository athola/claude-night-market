"""Call chain tracing and flow criticality scoring."""

from __future__ import annotations

from collections import deque

from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphNode, NodeKind

_CONVENTIONAL_ENTRY_NAMES = {
    "main",
    "__main__",
    "run",
    "start",
    "init",
    "setup",
    "execute",
    "serve",
    "app",
    "cli",
}

_ENTRY_PREFIXES = ("test_", "handle_", "on_", "do_")

_MAX_FLOW_NODES = 1000

SECURITY_KEYWORDS = frozenset(
    {
        "auth",
        "login",
        "password",
        "token",
        "session",
        "crypt",
        "secret",
        "credential",
        "permission",
        "sql",
        "query",
        "execute",
        "sanitize",
        "encrypt",
        "decrypt",
        "hash",
        "sign",
        "verify",
        "admin",
    }
)


def detect_entry_points(graph: GraphStore) -> list[GraphNode]:
    """Find execution entry points in the graph.

    Entry points are functions that:
    1. Have no incoming CALLS edges (true roots), OR
    2. Have conventional entry point names, OR
    3. Are test functions
    """
    all_nodes = graph.get_all_nodes()

    entries: list[GraphNode] = []
    for node in all_nodes:
        if node.kind in (NodeKind.FILE, NodeKind.CLASS, NodeKind.TYPE):
            continue

        # Test functions are always entries
        if node.is_test or node.kind == NodeKind.TEST:
            entries.append(node)
            continue

        # Extract bare name from qualified name
        bare_name = node.qualified_name.rsplit("::", 1)[-1]
        if "." in bare_name:
            bare_name = bare_name.rsplit(".", 1)[-1]

        # Conventional names
        if bare_name in _CONVENTIONAL_ENTRY_NAMES:
            entries.append(node)
            continue

        # Name prefixes
        if any(bare_name.startswith(p) for p in _ENTRY_PREFIXES):
            entries.append(node)
            continue

        # True roots: no incoming CALLS
        incoming = graph.get_edges_by_target(node.qualified_name)
        has_callers = any(e.kind == EdgeKind.CALLS for e in incoming)
        if not has_callers:
            entries.append(node)

    return entries


def trace_flows(
    graph: GraphStore,
    max_depth: int = 15,
) -> list[dict]:
    """Trace execution flows from entry points via BFS on CALLS edges."""
    entry_points = detect_entry_points(graph)
    flows: list[dict] = []

    for entry in entry_points:
        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        flow_nodes: list[GraphNode] = []
        flow_files: set[str] = set()

        qn = entry.qualified_name
        visited.add(qn)
        queue.append((qn, 0))
        flow_nodes.append(entry)
        flow_files.add(entry.file_path)
        actual_max_depth = 0

        while queue and len(flow_nodes) < _MAX_FLOW_NODES:
            current_qn, depth = queue.popleft()
            if depth > actual_max_depth:
                actual_max_depth = depth
            if depth >= max_depth:
                continue

            # Follow CALLS edges
            for edge in graph.get_edges_by_source(current_qn):
                if edge.kind != EdgeKind.CALLS:
                    continue
                target = edge.target_qn
                if target in visited:
                    continue
                visited.add(target)
                target_node = graph.get_node(target)
                if target_node:
                    flow_nodes.append(target_node)
                    flow_files.add(target_node.file_path)
                    queue.append((target, depth + 1))

        # Only store non-trivial flows
        if len(flow_nodes) >= 2:
            criticality = compute_criticality(flow_nodes, graph)
            flows.append(
                {
                    "entry_point": entry.qualified_name,
                    "node_count": len(flow_nodes),
                    "file_count": len(flow_files),
                    "max_depth": actual_max_depth,
                    "criticality": criticality,
                    "node_qns": [n.qualified_name for n in flow_nodes],
                }
            )

    # Sort by criticality descending
    flows.sort(key=lambda f: f["criticality"], reverse=True)
    return flows


def compute_criticality(
    flow_nodes: list[GraphNode],
    graph: GraphStore,
) -> float:
    """Compute criticality score (0.0-1.0) for a flow."""
    if not flow_nodes:
        return 0.0

    score = 0.0

    # Factor 1: File spread (weight: 0.30)
    unique_files = len({n.file_path for n in flow_nodes})
    file_spread = min(unique_files / 5, 1.0)
    score += 0.30 * file_spread

    # Factor 2: Security sensitivity (weight: 0.25)
    security_nodes = sum(
        1
        for n in flow_nodes
        if any(kw in n.qualified_name.lower() for kw in SECURITY_KEYWORDS)
    )
    security_factor = min(security_nodes / 3, 1.0)
    score += 0.25 * security_factor

    # Factor 3: External/unresolved calls (weight: 0.20)
    unresolved = 0
    for n in flow_nodes:
        for edge in graph.get_edges_by_source(n.qualified_name):
            if edge.kind == EdgeKind.CALLS:
                target = graph.get_node(edge.target_qn)
                if target is None:
                    unresolved += 1
    external_factor = min(unresolved / 5, 1.0)
    score += 0.20 * external_factor

    # Factor 4: Test coverage gap (weight: 0.15)
    untested = sum(
        1
        for n in flow_nodes
        if not any(
            e.kind == EdgeKind.TESTED_BY
            for e in graph.get_edges_by_source(n.qualified_name)
        )
    )
    test_gap = untested / len(flow_nodes)
    score += 0.15 * test_gap

    # Factor 5: Depth (weight: 0.10)
    # Use the node count as a proxy for depth
    depth_factor = min(len(flow_nodes) / 10, 1.0)
    score += 0.10 * depth_factor

    return min(round(score, 4), 1.0)
