"""Tests for NetworkX-based graph analysis."""

from __future__ import annotations

import pytest

from memory_palace.graph_analyzer import PalaceGraphAnalyzer
from memory_palace.knowledge_graph import KnowledgeGraph


@pytest.fixture
def graph() -> KnowledgeGraph:
    """In-memory graph with a connected knowledge network."""
    g = KnowledgeGraph(":memory:")
    # Create a small network: A -> B -> C -> D, A -> C (shortcut)
    for eid in ("a", "b", "c", "d", "e"):
        g.upsert_entity(eid, "concept", f"Entity {eid.upper()}")

    g.create_synapse("a", "b", strength=0.8)
    g.create_synapse("b", "c", strength=0.6)
    g.create_synapse("c", "d", strength=0.4)
    g.create_synapse("a", "c", strength=0.3)  # shortcut
    g.create_synapse("d", "e", strength=0.2)

    yield g
    g.close()


@pytest.fixture
def analyzer(graph: KnowledgeGraph) -> PalaceGraphAnalyzer:
    return PalaceGraphAnalyzer(graph)


class TestGraphLoading:
    """Loading SQLite graph into NetworkX."""

    def test_loads_nodes(self, analyzer: PalaceGraphAnalyzer) -> None:
        nx_graph = analyzer.build_graph()
        assert len(nx_graph.nodes) == 5

    def test_loads_edges(self, analyzer: PalaceGraphAnalyzer) -> None:
        nx_graph = analyzer.build_graph()
        assert len(nx_graph.edges) == 5

    def test_edge_weights(self, analyzer: PalaceGraphAnalyzer) -> None:
        nx_graph = analyzer.build_graph()
        assert nx_graph["a"]["b"]["weight"] == pytest.approx(0.8)


class TestPageRank:
    """PageRank for entity importance."""

    def test_pagerank_returns_all_entities(self, analyzer: PalaceGraphAnalyzer) -> None:
        ranks = analyzer.pagerank()
        assert len(ranks) == 5
        assert all(0.0 <= v <= 1.0 for v in ranks.values())

    def test_well_connected_node_ranks_higher(
        self, analyzer: PalaceGraphAnalyzer
    ) -> None:
        ranks = analyzer.pagerank()
        # a is the source with no incoming edges, should rank lowest
        assert ranks["a"] < ranks["d"]


class TestBetweenness:
    """Betweenness centrality for bridge importance."""

    def test_betweenness_returns_scores(self, analyzer: PalaceGraphAnalyzer) -> None:
        scores = analyzer.betweenness_centrality()
        assert len(scores) == 5

    def test_bridge_node_has_higher_betweenness(
        self, analyzer: PalaceGraphAnalyzer
    ) -> None:
        scores = analyzer.betweenness_centrality()
        # b and c are on many shortest paths
        assert scores["c"] > scores["e"] or scores["b"] > scores["e"]


class TestCommunityDetection:
    """Community detection via Louvain or greedy modularity."""

    def test_detects_communities(self, analyzer: PalaceGraphAnalyzer) -> None:
        communities = analyzer.detect_communities()
        assert len(communities) >= 1
        # All entities should be assigned to some community
        all_members = set()
        for members in communities.values():
            all_members.update(members)
        assert len(all_members) == 5


class TestBridgesAndArticulationPoints:
    """Structural analysis."""

    def test_find_bridges(self, analyzer: PalaceGraphAnalyzer) -> None:
        bridges = analyzer.find_bridges()
        # Should find at least some bridges
        assert isinstance(bridges, list)

    def test_find_keystones(self, analyzer: PalaceGraphAnalyzer) -> None:
        keystones = analyzer.find_keystones()
        assert isinstance(keystones, list)

    def test_connected_components(self, analyzer: PalaceGraphAnalyzer) -> None:
        components = analyzer.connected_components()
        assert len(components) >= 1
        # All 5 entities should be in components
        total = sum(len(c) for c in components)
        assert total == 5


class TestShortestPath:
    """Weighted shortest path for knowledge navigation."""

    def test_shortest_path_exists(self, analyzer: PalaceGraphAnalyzer) -> None:
        path = analyzer.shortest_path("a", "e")
        assert path is not None
        assert path[0] == "a"
        assert path[-1] == "e"

    def test_shortest_path_no_connection(self, graph: KnowledgeGraph) -> None:
        # Add an isolated node
        graph.upsert_entity("isolated", "concept", "Isolated")
        analyzer = PalaceGraphAnalyzer(graph)
        path = analyzer.shortest_path("a", "isolated")
        assert path is None


class TestEmptyGraph:
    """Algorithms on empty graphs."""

    def test_pagerank_empty(self) -> None:
        g = KnowledgeGraph(":memory:")
        analyzer = PalaceGraphAnalyzer(g)
        assert analyzer.pagerank() == {}
        g.close()

    def test_betweenness_empty(self) -> None:
        g = KnowledgeGraph(":memory:")
        analyzer = PalaceGraphAnalyzer(g)
        assert analyzer.betweenness_centrality() == {}
        g.close()

    def test_communities_empty(self) -> None:
        g = KnowledgeGraph(":memory:")
        analyzer = PalaceGraphAnalyzer(g)
        assert analyzer.detect_communities() == {}
        g.close()

    def test_predict_links_too_few_nodes(self) -> None:
        g = KnowledgeGraph(":memory:")
        g.upsert_entity("solo", "concept", "Solo")
        analyzer = PalaceGraphAnalyzer(g)
        assert analyzer.predict_links() == []
        g.close()


class TestLinkPrediction:
    """Adamic-Adar link prediction for synapse suggestions."""

    def test_suggests_links(self, analyzer: PalaceGraphAnalyzer) -> None:
        suggestions = analyzer.predict_links(top_n=5)
        assert isinstance(suggestions, list)
        for u, v, score in suggestions:
            assert isinstance(score, float)

    def test_does_not_suggest_existing_links(
        self, analyzer: PalaceGraphAnalyzer
    ) -> None:
        suggestions = analyzer.predict_links(top_n=10)
        existing = {("a", "b"), ("b", "c"), ("c", "d"), ("a", "c"), ("d", "e")}
        for u, v, _ in suggestions:
            assert (u, v) not in existing
