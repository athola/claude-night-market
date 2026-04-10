"""Graph-aware challenge generation from code knowledge graph."""

from __future__ import annotations

import random
import uuid

from gauntlet.graph import GraphStore
from gauntlet.models import (
    Challenge,
    ChallengeType,
    EdgeKind,
    GraphNode,
    NodeKind,
)


def _make_id() -> str:
    return "gch-" + uuid.uuid4().hex[:12]


def _bare_name(qualified_name: str) -> str:
    """Extract the short name from a qualified name."""
    tail = (
        qualified_name.rsplit("::", 1)[-1] if "::" in qualified_name else qualified_name
    )
    return tail.rsplit(".", 1)[-1] if "." in tail else tail


def generate_graph_challenges(
    graph: GraphStore,
    count: int = 5,
) -> list[Challenge]:
    """Generate challenges from graph structural relationships.

    Produces two types:
    - IMPACT_PREDICTION: "What is affected if you change X?"
    - DEPENDENCY_TRACE: "What does X depend on / what depends on X?"
    """
    all_nodes = graph.get_all_nodes()
    # Filter to interesting nodes (functions and classes, not files)
    candidates = [
        n
        for n in all_nodes
        if n.kind in (NodeKind.FUNCTION, NodeKind.CLASS, NodeKind.TEST)
    ]

    if not candidates:
        return []

    # Shuffle and pick up to count * 2 candidates (we'll generate from best)
    random.shuffle(candidates)
    challenges: list[Challenge] = []

    for node in candidates:
        if len(challenges) >= count:
            break

        outgoing = graph.get_edges_by_source(node.qualified_name)
        incoming = graph.get_edges_by_target(node.qualified_name)
        call_targets = [e.target_qn for e in outgoing if e.kind == EdgeKind.CALLS]
        callers = [e.source_qn for e in incoming if e.kind == EdgeKind.CALLS]

        # Need at least some edges to make an interesting challenge
        if not call_targets and not callers:
            continue

        # Alternate between challenge types
        if len(challenges) % 2 == 0 and call_targets:
            ch = _impact_prediction(node, call_targets, graph)
        elif callers:
            ch = _dependency_trace(node, callers, graph)
        elif call_targets:
            ch = _impact_prediction(node, call_targets, graph)
        else:
            continue

        challenges.append(ch)

    return challenges


def _impact_prediction(
    node: GraphNode,
    call_targets: list[str],
    graph: GraphStore,
) -> Challenge:
    """Generate: 'If you change X, what downstream code is affected?'"""
    name = _bare_name(node.qualified_name)

    # BFS to find full downstream impact
    affected = graph.impact_radius([node.file_path], depth=2)
    affected_names = sorted(
        {
            _bare_name(n.qualified_name)
            for n in affected
            if n.qualified_name != node.qualified_name
        }
    )[:8]

    # Difficulty scales with number of affected nodes
    difficulty = min(max(1, len(affected_names) // 2), 4)

    answer = ", ".join(affected_names) if affected_names else "no downstream impact"
    direct_targets = [_bare_name(t) for t in call_targets[:3]]

    return Challenge(
        id=_make_id(),
        type=ChallengeType.IMPACT_PREDICTION,
        knowledge_entry_id=f"graph:{node.qualified_name}",
        difficulty=difficulty,
        prompt=(
            f"If you change `{name}` in `{node.file_path}`, "
            f"what other code is affected? "
            f"List the functions/classes that would need review."
        ),
        context=(
            f"{name} directly calls: {', '.join(direct_targets)}. "
            f"It lives in {node.file_path} (lines {node.line_start}-{node.line_end})."
        ),
        answer=answer,
        hints=[
            f"{name} calls {len(call_targets)} function(s) directly",
            f"Think about what depends on {node.file_path}",
        ],
        scope_files=[node.file_path],
    )


def _dependency_trace(
    node: GraphNode,
    callers: list[str],
    graph: GraphStore,
) -> Challenge:
    """Generate: 'What calls X? / What does X depend on?'"""
    name = _bare_name(node.qualified_name)
    caller_names = sorted({_bare_name(c) for c in callers})[:5]

    # Difficulty scales with caller count
    difficulty = min(max(1, len(caller_names)), 4)

    answer = ", ".join(caller_names)

    return Challenge(
        id=_make_id(),
        type=ChallengeType.DEPENDENCY_TRACE,
        knowledge_entry_id=f"graph:{node.qualified_name}",
        difficulty=difficulty,
        prompt=(
            f"Name the functions or modules that call `{name}`. "
            f"How many callers does it have?"
        ),
        context=(
            f"{name} is a {node.kind.value} in {node.file_path} "
            f"(lines {node.line_start}-{node.line_end})."
        ),
        answer=f"{len(caller_names)} caller(s): {answer}",
        hints=[
            f"Look at what imports or calls {name}",
            f"Check {node.file_path} for incoming edges",
        ],
        scope_files=[node.file_path],
    )
