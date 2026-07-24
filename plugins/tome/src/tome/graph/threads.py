"""Research threads and paths over the citation graph.

Wraps memory-palace's ``PalaceGraphAnalyzer``: community detection
surfaces "common threads" (clusters of related papers) and link
prediction surfaces "further research paths" (suggested connections).
As with the writer seam, the analyzer backend is optional and loaded
via a guarded import; its absence is an explicit failure, not a silent
no-op.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from tome.graph.palace_adapter import GraphBackendUnavailable

# memory-palace is an optional, co-installed backend. See the note in
# graph/palace_adapter.py for why the alias is declared ``Any``.
_PalaceGraphAnalyzer: Any
try:
    from memory_palace import PalaceGraphAnalyzer as _mp_graph_analyzer
except ImportError:
    _PalaceGraphAnalyzer = None
else:
    _PalaceGraphAnalyzer = _mp_graph_analyzer


@dataclass(frozen=True)
class ResearchThread:
    """A cluster of related papers: a detected community in the graph."""

    thread_id: int
    paper_ids: frozenset[str]


@dataclass(frozen=True)
class ResearchPath:
    """A suggested next connection: a predicted citation link.

    The producer (``predict_links``) scores non-existing edges by
    Adamic-Adar index and already discards anything at or below zero, so
    a non-positive score or a self-referential path means the path did
    not come from link prediction. Adamic-Adar has no upper bound, so
    none is imposed here.

    Raises:
        ValueError: When either endpoint is blank, both endpoints name
            the same node, or ``score`` is not positive.
    """

    from_id: str
    to_id: str
    score: float

    def __post_init__(self) -> None:
        if not self.from_id.strip() or not self.to_id.strip():
            raise ValueError(
                "a research path requires non-empty node IDs, got "
                f"from_id={self.from_id!r}, to_id={self.to_id!r}"
            )
        if self.from_id == self.to_id:
            raise ValueError(
                f"a research path cannot point at itself: {self.from_id!r}"
            )
        if self.score <= 0.0:
            raise ValueError(
                f"a predicted link's score must be positive, got {self.score}"
            )


@runtime_checkable
class GraphAnalyzer(Protocol):
    """The read surface tome needs for threads and paths."""

    def detect_communities(self) -> dict[int, set[str]]: ...

    def predict_links(self, top_n: int = 10) -> list[tuple[str, str, float]]: ...


def analyzer_available() -> bool:
    """Return whether the graph-analyzer backend is importable."""
    return _PalaceGraphAnalyzer is not None


def open_analyzer(graph: Any) -> GraphAnalyzer:
    """Build a ``PalaceGraphAnalyzer`` over ``graph``.

    Raises:
        GraphBackendUnavailable: When memory-palace is not installed.
    """
    if _PalaceGraphAnalyzer is None:
        raise GraphBackendUnavailable(
            "research threads require memory-palace, which is not installed"
        )
    analyzer: GraphAnalyzer = _PalaceGraphAnalyzer(graph)
    return analyzer


class ThreadFinder:
    """Derive research threads and paths from a graph analyzer."""

    def __init__(self, analyzer: GraphAnalyzer) -> None:
        self._analyzer = analyzer

    def common_threads(self) -> list[ResearchThread]:
        """Return detected communities as research threads."""
        return [
            ResearchThread(thread_id, frozenset(members))
            for thread_id, members in self._analyzer.detect_communities().items()
        ]

    def research_paths(self, top_n: int = 10) -> list[ResearchPath]:
        """Return the top predicted links as further-research paths."""
        return [
            ResearchPath(from_id=src, to_id=dst, score=score)
            for src, dst, score in self._analyzer.predict_links(top_n=top_n)
        ]
