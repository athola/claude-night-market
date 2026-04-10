"""Tests for Mermaid and ASCII palace rendering."""

from __future__ import annotations

import pytest

from memory_palace.knowledge_graph import KnowledgeGraph
from memory_palace.palace_renderer import PalaceRenderer


@pytest.fixture
def graph() -> KnowledgeGraph:
    """In-memory knowledge graph with sample data."""
    g = KnowledgeGraph(":memory:")
    # Create a small palace structure
    g.upsert_entity("p1", "palace", "Architecture Palace")
    g.upsert_entity("r1", "room", "Design Patterns")
    g.upsert_entity("r2", "room", "Data Structures")
    g.upsert_entity("e1", "concept", "Dependency Injection")
    g.upsert_entity("e2", "concept", "Observer Pattern")
    g.upsert_entity("e3", "concept", "Binary Tree")

    # Residencies
    g.add_residency("r1", palace_id="p1", role="curator")
    g.add_residency("r2", palace_id="p1", role="curator")
    g.add_residency("e1", palace_id="p1", room_id="r1", role="patron")
    g.add_residency("e2", palace_id="p1", room_id="r1", role="patron")
    g.add_residency("e3", palace_id="p1", room_id="r2", role="patron")

    # Synapses
    g.create_synapse("e1", "e2", strength=0.7)
    g.create_synapse("e2", "e3", strength=0.3)

    yield g
    g.close()


@pytest.fixture
def renderer(graph: KnowledgeGraph) -> PalaceRenderer:
    return PalaceRenderer(graph)


class TestMermaidPalaceMap:
    """Palace map as Mermaid flowchart."""

    def test_generates_valid_mermaid(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.palace_map("p1")
        assert mermaid.startswith("flowchart TD")
        assert "Architecture Palace" in mermaid

    def test_includes_rooms_as_subgraphs(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.palace_map("p1")
        assert "subgraph" in mermaid
        assert "Design Patterns" in mermaid
        assert "Data Structures" in mermaid

    def test_includes_entities_in_rooms(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.palace_map("p1")
        assert "Dependency Injection" in mermaid
        assert "Binary Tree" in mermaid

    def test_includes_synapse_edges(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.palace_map("p1")
        # Synapses should render as edges between entities
        assert "-->" in mermaid or "---" in mermaid

    def test_empty_palace_returns_minimal(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity("p_empty", "palace", "Empty Palace")
        renderer = PalaceRenderer(graph)
        mermaid = renderer.palace_map("p_empty")
        assert "flowchart TD" in mermaid
        assert "Empty Palace" in mermaid

    def test_nonexistent_palace_returns_empty(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.palace_map("nonexistent")
        assert mermaid == ""


class TestMermaidEntityGraph:
    """Single entity's relationships as Mermaid graph."""

    def test_entity_relationship_graph(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.entity_graph("e1")
        assert "flowchart LR" in mermaid
        assert "Dependency Injection" in mermaid

    def test_includes_connected_entities(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.entity_graph("e1")
        # e1 has a synapse to e2
        assert "Observer Pattern" in mermaid


class TestMermaidSynapseHeatmap:
    """Synapse strength visualization."""

    def test_heatmap_renders_edges(self, renderer: PalaceRenderer) -> None:
        mermaid = renderer.synapse_heatmap("p1")
        assert "flowchart LR" in mermaid
        # Strong synapse (0.7) and weak synapse (0.3) should render differently
        assert "==>" in mermaid or "-->" in mermaid


class TestEntityGraphTriples:
    """Entity graph with triples and incoming synapses."""

    def test_entity_graph_with_triples(self, graph: KnowledgeGraph) -> None:
        graph.add_triple(subject_id="e1", predicate="uses", object_id="e3")
        renderer = PalaceRenderer(graph)
        mermaid = renderer.entity_graph("e1")
        assert "uses" in mermaid
        assert "Binary Tree" in mermaid

    def test_entity_graph_with_incoming(self, graph: KnowledgeGraph) -> None:
        # e2 has a synapse TO e1 (incoming for e1 perspective is
        # from e2->e3 perspective, but let's add one directly)
        graph.create_synapse("e3", "e1", strength=0.5)
        renderer = PalaceRenderer(graph)
        mermaid = renderer.entity_graph("e1")
        assert "Binary Tree" in mermaid

    def test_nonexistent_entity_returns_empty(self, graph: KnowledgeGraph) -> None:
        renderer = PalaceRenderer(graph)
        assert renderer.entity_graph("nonexistent") == ""

    def test_synapse_heatmap_nonexistent(self, graph: KnowledgeGraph) -> None:
        renderer = PalaceRenderer(graph)
        assert renderer.synapse_heatmap("nonexistent") == ""


class TestASCIIOverview:
    """ASCII box-drawing palace overview."""

    def test_ascii_overview(self, renderer: PalaceRenderer) -> None:
        ascii_art = renderer.ascii_overview("p1")
        assert "Architecture Palace" in ascii_art
        assert "Design Patterns" in ascii_art
        assert "Data Structures" in ascii_art

    def test_ascii_includes_entity_counts(self, renderer: PalaceRenderer) -> None:
        ascii_art = renderer.ascii_overview("p1")
        # Should show entity counts per room
        assert "2" in ascii_art  # Design Patterns has 2 entities
        assert "1" in ascii_art  # Data Structures has 1 entity

    def test_ascii_empty_palace(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity("p_empty", "palace", "Empty")
        renderer = PalaceRenderer(graph)
        ascii_art = renderer.ascii_overview("p_empty")
        assert "Empty" in ascii_art

    def test_nonexistent_palace_returns_empty(self, renderer: PalaceRenderer) -> None:
        assert renderer.ascii_overview("nonexistent") == ""
