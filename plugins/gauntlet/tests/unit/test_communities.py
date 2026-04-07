"""Tests for community detection and cohesion metrics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gauntlet.communities import (
    _leiden_communities,
    calculate_cohesion,
    detect_communities,
    get_architecture_overview,
)
from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "test.db")
    yield s
    s.close()


def _build_two_clusters(store: GraphStore) -> None:
    """Create two tightly-coupled clusters with a weak cross-link."""
    # Cluster A: a1, a2, a3 all in auth/
    for i in range(3):
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"auth.py::fn_a{i}",
                file_path="auth.py",
                line_start=i * 10,
                line_end=i * 10 + 9,
            )
        )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="auth.py::fn_a0",
            target_qn="auth.py::fn_a1",
        )
    )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="auth.py::fn_a1",
            target_qn="auth.py::fn_a2",
        )
    )

    # Cluster B: b1, b2, b3 all in db/
    for i in range(3):
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"db.py::fn_b{i}",
                file_path="db.py",
                line_start=i * 10,
                line_end=i * 10 + 9,
            )
        )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="db.py::fn_b0",
            target_qn="db.py::fn_b1",
        )
    )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="db.py::fn_b1",
            target_qn="db.py::fn_b2",
        )
    )

    # Cross-cluster link
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="auth.py::fn_a2",
            target_qn="db.py::fn_b0",
        )
    )


class TestDetectCommunities:
    """
    Feature: Community detection

    As a developer
    I want to see architectural clusters
    So that I understand module boundaries
    """

    @pytest.mark.unit
    def test_detects_file_based_communities(self, store: GraphStore) -> None:
        """
        Scenario: File-based fallback groups by file path
        Given nodes in two files
        When I detect communities (fallback mode)
        Then two communities are found
        """
        _build_two_clusters(store)
        communities = detect_communities(store)
        assert len(communities) >= 2

    @pytest.mark.unit
    def test_communities_have_names(self, store: GraphStore) -> None:
        """
        Scenario: Each community has a name
        Given detected communities
        When I inspect them
        Then each has a non-empty name
        """
        _build_two_clusters(store)
        communities = detect_communities(store)
        for comm in communities:
            assert comm.get("name")

    @pytest.mark.unit
    def test_communities_have_node_lists(self, store: GraphStore) -> None:
        """
        Scenario: Each community lists its member nodes
        """
        _build_two_clusters(store)
        communities = detect_communities(store)
        for comm in communities:
            assert len(comm.get("node_qns", [])) > 0


class TestCalculateCohesion:
    """
    Feature: Community cohesion metric

    As an architect
    I want to measure how tightly coupled a community is
    So that I can identify loosely-coupled modules
    """

    @pytest.mark.unit
    def test_fully_internal_edges_high_cohesion(self) -> None:
        """
        Scenario: All edges within community
        Given 3 internal edges, 0 external
        When I calculate cohesion
        Then cohesion is 1.0
        """
        community_qns = {"a", "b", "c"}
        edges = [
            GraphEdge(kind=EdgeKind.CALLS, source_qn="a", target_qn="b"),
            GraphEdge(kind=EdgeKind.CALLS, source_qn="b", target_qn="c"),
            GraphEdge(kind=EdgeKind.CALLS, source_qn="a", target_qn="c"),
        ]
        cohesion = calculate_cohesion(community_qns, edges)
        assert cohesion == 1.0

    @pytest.mark.unit
    def test_mixed_edges_partial_cohesion(self) -> None:
        """
        Scenario: Some edges cross community boundary
        Given 2 internal edges, 1 external edge
        When I calculate cohesion
        Then cohesion is 2/3
        """
        community_qns = {"a", "b"}
        edges = [
            GraphEdge(kind=EdgeKind.CALLS, source_qn="a", target_qn="b"),
            GraphEdge(kind=EdgeKind.CALLS, source_qn="b", target_qn="a"),
            GraphEdge(kind=EdgeKind.CALLS, source_qn="a", target_qn="external"),
        ]
        cohesion = calculate_cohesion(community_qns, edges)
        assert 0.6 <= cohesion <= 0.7

    @pytest.mark.unit
    def test_no_edges_zero_cohesion(self) -> None:
        """Empty edge list gives 0.0 cohesion."""
        cohesion = calculate_cohesion({"a"}, [])
        assert cohesion == 0.0


class TestLeidenCommunities:
    """
    Feature: Leiden community detection

    As a developer
    I want communities detected via the Leiden algorithm
    So that I get modularity-optimized clusters
    """

    @pytest.mark.unit
    def test_leiden_path_with_mocked_igraph(self) -> None:
        """
        Scenario: Leiden algorithm produces communities from igraph
        Given a mock igraph module with community_leiden support
        When I call _leiden_communities
        Then communities are returned from the partition
        """
        nodes = [
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"m.py::fn{i}",
                file_path="m.py",
                line_start=i * 10,
                line_end=i * 10 + 9,
            )
            for i in range(4)
        ]
        edges = [
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn="m.py::fn0",
                target_qn="m.py::fn1",
            ),
            GraphEdge(
                kind=EdgeKind.CALLS,
                source_qn="m.py::fn2",
                target_qn="m.py::fn3",
            ),
        ]

        # Mock igraph: Graph returns object with community_leiden
        mock_graph_instance = MagicMock()
        # Partition: two groups
        mock_graph_instance.community_leiden.return_value = [[0, 1], [2, 3]]

        mock_ig = MagicMock()
        mock_ig.Graph.return_value = mock_graph_instance

        with patch.dict("sys.modules", {"igraph": mock_ig}):
            communities = _leiden_communities(nodes, edges)

        assert len(communities) == 2
        assert len(communities[0]["node_qns"]) == 2
        assert len(communities[1]["node_qns"]) == 2


class TestLeidenFallback:
    """
    Feature: Fallback when Leiden algorithm fails

    As a developer
    I want community detection to fall back gracefully
    So that non-ImportError exceptions are handled
    """

    @pytest.mark.unit
    def test_valueerror_falls_back_to_file_based(
        self, store: GraphStore, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Scenario: igraph raises ValueError during community detection
        Given a graph with nodes in two files
        And igraph raises ValueError on community_leiden
        When I detect communities
        Then file-based fallback is used and a warning is logged
        """
        _build_two_clusters(store)

        with (
            patch(
                "gauntlet.communities._leiden_communities",
                side_effect=ValueError("bad partition"),
            ),
            caplog.at_level("WARNING", logger="gauntlet.communities"),
        ):
            communities = detect_communities(store)

        # Fallback produces file-based communities
        assert len(communities) >= 2
        assert any("bad partition" in r.message for r in caplog.records)

    @pytest.mark.unit
    def test_runtimeerror_falls_back_to_file_based(
        self, store: GraphStore, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Scenario: igraph raises RuntimeError (InternalError) during community detection
        Given a graph with nodes in two files
        And igraph raises RuntimeError on community_leiden
        When I detect communities
        Then file-based fallback is used and a warning is logged
        """
        _build_two_clusters(store)

        with (
            patch(
                "gauntlet.communities._leiden_communities",
                side_effect=RuntimeError("igraph InternalError"),
            ),
            caplog.at_level("WARNING", logger="gauntlet.communities"),
        ):
            communities = detect_communities(store)

        # Fallback produces file-based communities
        assert len(communities) >= 2
        assert any("igraph InternalError" in r.message for r in caplog.records)


class TestArchitectureOverview:
    """
    Feature: Architecture coupling warnings

    As an architect
    I want warnings about tightly-coupled communities
    So that I can address architectural issues
    """

    @pytest.mark.unit
    def test_returns_communities_and_warnings(self, store: GraphStore) -> None:
        """
        Scenario: Overview includes communities and coupling data
        Given a graph with two clusters
        When I get architecture overview
        Then the result has communities and warnings keys
        """
        _build_two_clusters(store)
        overview = get_architecture_overview(store)
        assert "communities" in overview
        assert "warnings" in overview
