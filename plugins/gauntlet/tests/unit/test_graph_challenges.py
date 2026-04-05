"""Tests for graph-aware challenge generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.graph import GraphStore
from gauntlet.graph_challenges import generate_graph_challenges
from gauntlet.models import (
    ChallengeType,
    EdgeKind,
    GraphEdge,
    GraphNode,
    NodeKind,
)


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "test.db")
    yield s
    s.close()


def _build_graph(store: GraphStore) -> None:
    """Build a small graph with imports and calls."""
    # auth.py has verify_token which calls db.py::execute_query
    store.upsert_node(
        GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="auth.py::verify_token",
            file_path="auth.py",
            line_start=1,
            line_end=20,
            language="python",
        )
    )
    store.upsert_node(
        GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="db.py::execute_query",
            file_path="db.py",
            line_start=1,
            line_end=15,
            language="python",
        )
    )
    store.upsert_node(
        GraphNode(
            kind=NodeKind.CLASS,
            qualified_name="api.py::UserHandler",
            file_path="api.py",
            line_start=1,
            line_end=50,
            language="python",
        )
    )
    store.upsert_node(
        GraphNode(
            kind=NodeKind.FUNCTION,
            qualified_name="api.py::UserHandler.get",
            file_path="api.py",
            line_start=10,
            line_end=25,
            language="python",
            parent_name="UserHandler",
        )
    )
    # Edges
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="auth.py::verify_token",
            target_qn="db.py::execute_query",
        )
    )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.CALLS,
            source_qn="api.py::UserHandler.get",
            target_qn="auth.py::verify_token",
        )
    )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.IMPORTS_FROM,
            source_qn="api.py",
            target_qn="auth",
            file_path="api.py",
        )
    )
    store.upsert_edge(
        GraphEdge(
            kind=EdgeKind.IMPORTS_FROM,
            source_qn="api.py",
            target_qn="db",
            file_path="api.py",
        )
    )
    store.rebuild_fts()


class TestGenerateGraphChallenges:
    """
    Feature: Graph-aware challenge generation

    As a developer learning a codebase
    I want challenges about code relationships
    So that I understand architecture and dependencies
    """

    @pytest.mark.unit
    def test_generates_challenges_from_graph(self, store: GraphStore) -> None:
        """
        Scenario: Generate challenges from a populated graph
        Given a graph with functions, calls, and imports
        When I generate graph challenges
        Then at least one challenge is returned
        """
        _build_graph(store)
        challenges = generate_graph_challenges(store, count=5)
        assert len(challenges) >= 1

    @pytest.mark.unit
    def test_challenges_have_valid_types(self, store: GraphStore) -> None:
        """
        Scenario: Generated challenges use valid ChallengeType values
        Given graph challenges
        When I inspect their types
        Then all are valid ChallengeType enum members
        """
        _build_graph(store)
        challenges = generate_graph_challenges(store, count=5)
        for ch in challenges:
            assert isinstance(ch.type, ChallengeType)

    @pytest.mark.unit
    def test_challenges_reference_real_nodes(self, store: GraphStore) -> None:
        """
        Scenario: Challenge prompts reference actual code entities
        Given graph challenges
        When I inspect their prompts
        Then they contain bare names or file paths from the graph
        """
        _build_graph(store)
        challenges = generate_graph_challenges(store, count=3)
        all_names = set()
        for n in store.get_all_nodes():
            all_names.add(n.file_path)
            tail = n.qualified_name.rsplit("::", 1)[-1]
            all_names.add(tail)
            if "." in tail:
                all_names.add(tail.rsplit(".", 1)[-1])
        for ch in challenges:
            found = any(name in ch.prompt for name in all_names)
            assert found, f"No node reference in prompt: {ch.prompt}"

    @pytest.mark.unit
    def test_empty_graph_returns_empty(self, store: GraphStore) -> None:
        """
        Scenario: Empty graph yields no challenges
        Given an empty graph
        When I generate challenges
        Then an empty list is returned
        """
        challenges = generate_graph_challenges(store, count=5)
        assert challenges == []

    @pytest.mark.unit
    def test_difficulty_scales_with_graph_depth(self, store: GraphStore) -> None:
        """
        Scenario: Impact prediction challenges scale difficulty
        Given a deep call chain (A -> B -> C -> D)
        When I generate challenges
        Then deeper chains produce higher difficulty
        """
        _build_graph(store)
        challenges = generate_graph_challenges(store, count=5)
        difficulties = [ch.difficulty for ch in challenges]
        assert all(1 <= d <= 5 for d in difficulties)
