"""FTS5 search with BM25 ranking and query-aware kind boosting."""

from __future__ import annotations

from gauntlet.graph import GraphStore
from gauntlet.models import GraphNode


def detect_kind_boost(query: str) -> dict[str, float]:
    """Detect what node kinds a query likely targets.

    Returns a dict of kind -> boost multiplier.
    PascalCase -> Class/Type, snake_case -> Function,
    dotted path -> qualified_name boost.
    """
    boosts: dict[str, float] = {}

    if not query:
        return boosts

    # PascalCase: likely a class or type
    if query[0].isupper() and any(c.isupper() for c in query[1:]):
        boosts["Class"] = 1.5
        boosts["Type"] = 1.5

    # snake_case: likely a function
    if "_" in query and query == query.lower():
        boosts["Function"] = 1.5

    # Dotted path: qualified name
    if "." in query:
        boosts["qualified_name"] = 2.0

    return boosts


def search(
    graph: GraphStore,
    query: str,
    kind: str | None = None,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Search the graph with FTS5 and kind-aware boosting.

    Returns dicts with node data and relevance info.
    """
    if not query.strip():
        return []

    boosts = detect_kind_boost(query)
    results = graph.search_fts(query, kind=kind, limit=limit * 2)

    # Apply boosting: reorder results by boosted score
    scored: list[tuple[float, GraphNode]] = []
    for i, node in enumerate(results):
        base_score = 1.0 / (i + 1)  # rank-based score
        kind_str = str(node.kind)
        boost = boosts.get(kind_str, 1.0)
        scored.append((base_score * boost, node))

    scored.sort(key=lambda x: x[0], reverse=True)

    output: list[dict[str, object]] = []
    for score, node in scored[:limit]:
        output.append(
            {
                "qualified_name": node.qualified_name,
                "kind": str(node.kind),
                "file_path": node.file_path,
                "line_start": node.line_start,
                "line_end": node.line_end,
                "language": node.language,
                "relevance": round(score, 4),
            }
        )

    return output
