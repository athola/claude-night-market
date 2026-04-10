"""Tests for community detection and cohesion metrics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gauntlet.communities import (
    _leiden_communities,
    _subdivide_community,
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
        """Scenario: Each community lists its member nodes."""
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


class TestLanguageFilter:
    """
    Feature: Language-filtered community detection

    As a developer
    I want to detect communities for a specific language
    So that I can isolate cross-language noise
    """

    @pytest.mark.unit
    def test_filters_by_language(self, store: GraphStore) -> None:
        """
        Scenario: Only Python nodes are included
        Given nodes with language='python' and language='javascript'
        When I detect communities with language='python'
        Then only Python nodes appear
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.py::main",
                file_path="app.py",
                line_start=1,
                line_end=5,
                language="python",
            )
        )
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="app.js::init",
                file_path="app.js",
                line_start=1,
                line_end=5,
                language="javascript",
            )
        )
        communities = detect_communities(store, language="python")
        all_qns = [qn for c in communities for qn in c["node_qns"]]
        assert "app.py::main" in all_qns
        assert "app.js::init" not in all_qns

    @pytest.mark.unit
    def test_empty_after_language_filter(self, store: GraphStore) -> None:
        """
        Scenario: No nodes match the language filter
        Given only Python nodes exist
        When I detect communities with language='rust'
        Then an empty list is returned
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name="lib.py::fn",
                file_path="lib.py",
                line_start=1,
                line_end=5,
                language="python",
            )
        )
        communities = detect_communities(store, language="rust")
        assert communities == []


class TestEmptyGraph:
    """
    Feature: Community detection on degenerate graphs

    As a developer
    I want community detection to handle edge cases
    So that it never crashes on empty or file-only graphs
    """

    @pytest.mark.unit
    def test_only_file_nodes_returns_empty(self, store: GraphStore) -> None:
        """
        Scenario: Graph only has FILE-kind nodes
        Given nodes are all NodeKind.FILE
        When I detect communities
        Then an empty list is returned (FILE nodes are filtered out)
        """
        store.upsert_node(
            GraphNode(
                kind=NodeKind.FILE,
                qualified_name="src/app.py",
                file_path="src/app.py",
                line_start=0,
                line_end=100,
            )
        )
        communities = detect_communities(store)
        assert communities == []


class TestSubdivideCommunity:
    """
    Feature: Large community subdivision

    As an architect
    I want oversized communities split by file
    So that each sub-community is manageable
    """

    @pytest.mark.unit
    def test_splits_by_file(self, store: GraphStore) -> None:
        """
        Scenario: A community spans two files
        Given a community with nodes from auth.py and db.py
        When I subdivide it
        Then two sub-communities are returned, one per file
        """
        for i in range(3):
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=f"auth.py::fn{i}",
                    file_path="auth.py",
                    line_start=i * 10,
                    line_end=i * 10 + 9,
                )
            )
        for i in range(2):
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=f"db.py::fn{i}",
                    file_path="db.py",
                    line_start=i * 10,
                    line_end=i * 10 + 9,
                )
            )

        community = {
            "name": "big-cluster",
            "node_qns": [
                "auth.py::fn0",
                "auth.py::fn1",
                "auth.py::fn2",
                "db.py::fn0",
                "db.py::fn1",
            ],
        }
        all_edges = list(store.get_all_edges())
        result = _subdivide_community(community, all_edges, store)

        assert len(result) == 2
        names = {r["name"] for r in result}
        assert "big-cluster/auth" in names
        assert "big-cluster/db" in names

    @pytest.mark.unit
    def test_single_file_not_split(self, store: GraphStore) -> None:
        """
        Scenario: A community is all in one file
        Given all nodes belong to the same file
        When I subdivide it
        Then the original community is returned unchanged
        """
        for i in range(3):
            store.upsert_node(
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name=f"single.py::fn{i}",
                    file_path="single.py",
                    line_start=i * 10,
                    line_end=i * 10 + 9,
                )
            )

        community = {
            "name": "mono",
            "node_qns": ["single.py::fn0", "single.py::fn1", "single.py::fn2"],
        }
        result = _subdivide_community(community, [], store)
        assert len(result) == 1
        assert result[0]["name"] == "mono"
