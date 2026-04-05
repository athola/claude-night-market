"""Tests for community detection and cohesion metrics."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.communities import (
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
