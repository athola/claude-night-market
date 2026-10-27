"""Register an intake document in the knowledge graph from a hook."""

from __future__ import annotations

import sys
from pathlib import Path


def try_register_graph_entity(  # noqa: PLR0913 - four entity fields plus the log label
    palaces_dir: Path,
    entity_id: str,
    name: str,
    entity_type: str,
    *,
    source: str,
) -> None:
    """Create a graph entity and run link prediction. Never raises.

    Runs silently if the graph DB or package is unavailable. ``source``
    labels what reaches stderr, so a skipped write names its hook.
    """
    try:
        from memory_palace.knowledge_graph import (
            KnowledgeGraph,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
        )

        db_path = palaces_dir / "knowledge_graph.db"
        graph = KnowledgeGraph(str(db_path))
        try:
            graph.upsert_entity(
                entity_id=entity_id,
                entity_type=entity_type,
                name=name,
            )
            try:
                from memory_palace.graph_analyzer import (
                    PalaceGraphAnalyzer,  # noqa: PLC0415 - deferred import inside try/except for graceful degradation
                )

                analyzer = PalaceGraphAnalyzer(graph)
                suggestions = analyzer.predict_links(top_n=5)
                if suggestions:
                    sys.stderr.write(f"{source}: link predictions: {suggestions[:3]}\n")
            except Exception:  # noqa: BLE001, S110 - link prediction is optional; entity write already succeeded
                pass
        finally:
            graph.close()
    except Exception as exc:  # noqa: BLE001 - hooks must never crash; log and continue
        sys.stderr.write(f"{source}: graph wiring skipped: {exc}\n")
