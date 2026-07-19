"""
Feature: Citation graph seam (build increment 2)

As the tome research engine
I want to write citation edges into a knowledge graph
So that papers become linked entities instead of a flat list,
reusing memory-palace's KnowledgeGraph without a hard dependency.
"""

from __future__ import annotations

from typing import Any

import pytest

from tome.graph.palace_adapter import (
    CitationGraphWriter,
    GraphBackendUnavailable,
    GraphWriter,
    memory_palace_available,
    open_palace_graph,
)
from tome.models import CitationEdge


class FakeGraph:
    """In-memory stand-in satisfying the GraphWriter protocol."""

    def __init__(self) -> None:
        self.entities: dict[str, tuple[str, str]] = {}
        self.triples: list[tuple[str, str, str]] = []
        self.upsert_calls: list[str] = []

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.upsert_calls.append(entity_id)
        self.entities[entity_id] = (entity_type, name)

    def add_triple(
        self,
        subject_id: str,
        predicate: str,
        object_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> int:
        self.triples.append((subject_id, predicate, object_id))
        return len(self.triples)


class TestCitationGraphWriter:
    @pytest.mark.unit
    def test_writes_paper_entities_and_cites_triple(self) -> None:
        """
        Given one citation edge A -> B
        When it is written to the graph
        Then A and B are paper entities and A cites B
        """
        graph = FakeGraph()
        writer = CitationGraphWriter(graph)

        writer.write_edges([CitationEdge(citing_id="A", cited_id="B")])

        assert graph.entities == {"A": ("paper", "A"), "B": ("paper", "B")}
        assert graph.triples == [("A", "cites", "B")]

    @pytest.mark.unit
    def test_returns_edge_count(self) -> None:
        graph = FakeGraph()
        writer = CitationGraphWriter(graph)

        count = writer.write_edges(
            [
                CitationEdge(citing_id="A", cited_id="B"),
                CitationEdge(citing_id="A", cited_id="C"),
            ]
        )

        assert count == 2

    @pytest.mark.unit
    def test_shared_paper_upserted_once_per_batch(self) -> None:
        """A appears in two edges but is upserted a single time."""
        graph = FakeGraph()
        writer = CitationGraphWriter(graph)

        writer.write_edges(
            [
                CitationEdge(citing_id="A", cited_id="B"),
                CitationEdge(citing_id="A", cited_id="C"),
            ]
        )

        assert graph.upsert_calls.count("A") == 1

    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        assert isinstance(FakeGraph(), GraphWriter)


class TestBackendCapability:
    @pytest.mark.unit
    def test_availability_is_boolean(self) -> None:
        assert isinstance(memory_palace_available(), bool)

    @pytest.mark.unit
    def test_open_raises_explicitly_when_unavailable(self) -> None:
        """
        The absence of memory-palace is an explicit failure, not a
        silent no-op that ships dead graph features.
        """
        if memory_palace_available():
            pytest.skip("memory-palace is installed; cannot test the absent path")
        with pytest.raises(GraphBackendUnavailable, match="memory-palace"):
            open_palace_graph(":memory:")


class TestRealBackendContract:
    """Runs only where memory-palace is installed (combined CI)."""

    @pytest.mark.integration
    def test_real_knowledge_graph_satisfies_writer(self, tmp_path: Any) -> None:
        mp = pytest.importorskip("memory_palace")
        graph = mp.KnowledgeGraph(str(tmp_path / "g.db"))
        assert isinstance(graph, GraphWriter)

        writer = CitationGraphWriter(graph)
        written = writer.write_edges([CitationEdge(citing_id="P1", cited_id="P2")])

        assert written == 1
