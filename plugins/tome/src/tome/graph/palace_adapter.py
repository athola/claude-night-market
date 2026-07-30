"""Citation-graph seam over memory-palace's KnowledgeGraph.

tome does not hard-depend on memory-palace: the two are isolated
plugins. This module imports the graph backend lazily and fails
explicitly when it is absent, rather than degrading to a silent no-op
that would ship dead graph features. The backend contract is expressed
as the :class:`GraphWriter` protocol, which memory-palace's
``KnowledgeGraph`` satisfies structurally, so no translation layer is
needed. A tome-native backend could implement the same protocol later.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from tome.models import CitationEdge

# memory-palace is an optional, co-installed backend. The alias is declared
# ``Any`` so this module type-checks identically whether or not the backend
# is installed; binding the imported class directly would make the absent
# branch an invalid assignment once the real types resolve.
_KnowledgeGraph: Any
try:
    from memory_palace import KnowledgeGraph as _mp_knowledge_graph
except ImportError:
    _KnowledgeGraph = None
else:
    _KnowledgeGraph = _mp_knowledge_graph

_PAPER_ENTITY = "paper"
# A citation is a definite link, so it enters the graph at full strength.
# The analyzer reads graph structure from synapses (weighted edges), not
# from temporal triples, so citation edges must be written as synapses to
# be visible to community detection and link prediction.
_CITATION_STRENGTH = 1.0


class GraphBackendUnavailable(RuntimeError):
    """Raised when no knowledge-graph backend can be loaded."""


@runtime_checkable
class GraphWriter(Protocol):
    """The minimal write surface tome needs from a knowledge graph."""

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...

    def create_synapse(
        self,
        source_id: str,
        target_id: str,
        strength: float = _CITATION_STRENGTH,
    ) -> int: ...


def memory_palace_available() -> bool:
    """Return whether the memory-palace graph backend is importable."""
    return _KnowledgeGraph is not None


def open_palace_graph(db_path: str) -> GraphWriter:
    """Open a memory-palace ``KnowledgeGraph`` at ``db_path``.

    Consumes memory-palace's public API (``KnowledgeGraph`` is exported
    from the package root), not an unexported submodule.

    Raises:
        GraphBackendUnavailable: When memory-palace is not installed.
            This is an explicit capability failure, deliberately not a
            silent fallback.
    """
    if _KnowledgeGraph is None:
        raise GraphBackendUnavailable(
            "the tome graph feature requires memory-palace, which is not installed"
        )
    graph: GraphWriter = _KnowledgeGraph(db_path)
    return graph


class CitationGraphWriter:
    """Write :class:`CitationEdge` batches into a knowledge graph.

    Each paper ID becomes a ``paper`` entity and each edge becomes a
    weighted ``citing -> cited`` synapse, the edge form the graph
    analyzer traverses for community detection and link prediction.
    Entity upserts are deduplicated within a batch; the backend upsert
    is idempotent regardless.
    """

    def __init__(self, backend: GraphWriter) -> None:
        self._backend = backend

    def write_edges(self, edges: list[CitationEdge]) -> int:
        """Write ``edges`` and return the number of edges written."""
        seen: set[str] = set()
        written = 0
        for edge in edges:
            for paper_id in (edge.citing_id, edge.cited_id):
                if paper_id not in seen:
                    self._backend.upsert_entity(paper_id, _PAPER_ENTITY, paper_id)
                    seen.add(paper_id)
            self._backend.create_synapse(
                edge.citing_id, edge.cited_id, _CITATION_STRENGTH
            )
            written += 1
        return written
