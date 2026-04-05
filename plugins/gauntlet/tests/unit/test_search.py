"""Tests for FTS5 search with kind boosting."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.graph import GraphStore
from gauntlet.models import GraphNode, NodeKind
from gauntlet.search import detect_kind_boost, search


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "test.db")
    yield s
    s.close()


def _insert_and_index(store: GraphStore, nodes: list[GraphNode]) -> None:
    for n in nodes:
        store.upsert_node(n)
    store.rebuild_fts()


class TestDetectKindBoost:
    """
    Feature: Query-aware kind boosting

    As a search system
    I want to detect likely node kinds from query patterns
    So that results are more relevant
    """

    @pytest.mark.unit
    def test_pascal_case_boosts_class(self) -> None:
        """PascalCase queries boost Class and Type."""
        boosts = detect_kind_boost("MyClass")
        assert boosts.get("Class") == 1.5
        assert boosts.get("Type") == 1.5

    @pytest.mark.unit
    def test_snake_case_boosts_function(self) -> None:
        """snake_case queries boost Function."""
        boosts = detect_kind_boost("get_users")
        assert boosts.get("Function") == 1.5

    @pytest.mark.unit
    def test_dotted_path_boosts_qualified_name(self) -> None:
        """Dotted queries boost qualified_name matches."""
        boosts = detect_kind_boost("app.models.User")
        assert boosts.get("qualified_name") == 2.0

    @pytest.mark.unit
    def test_single_lowercase_word_no_boost(self) -> None:
        """Plain lowercase words get no special boost."""
        boosts = detect_kind_boost("users")
        assert boosts == {}

    @pytest.mark.unit
    def test_empty_query_no_boost(self) -> None:
        boosts = detect_kind_boost("")
        assert boosts == {}


class TestSearch:
    """
    Feature: Full-text search with boosting

    As a developer
    I want to search the graph by name
    So that I can find code without reading every file
    """

    @pytest.mark.unit
    def test_finds_node_by_name(self, store: GraphStore) -> None:
        """
        Scenario: Search returns matching nodes
        Given a graph with a UserService class
        When I search for "UserService"
        Then the result includes that node
        """
        _insert_and_index(
            store,
            [
                GraphNode(
                    kind=NodeKind.CLASS,
                    qualified_name="app.py::UserService",
                    file_path="app.py",
                    line_start=1,
                    line_end=50,
                    language="python",
                ),
            ],
        )
        results = search(store, "UserService")
        assert len(results) >= 1
        assert results[0]["qualified_name"] == "app.py::UserService"

    @pytest.mark.unit
    def test_empty_query_returns_empty(self, store: GraphStore) -> None:
        """
        Scenario: Empty query returns no results
        Given any graph state
        When I search with an empty string
        Then an empty list is returned
        """
        results = search(store, "")
        assert results == []

    @pytest.mark.unit
    def test_results_include_metadata(self, store: GraphStore) -> None:
        """
        Scenario: Results include file path and line numbers
        Given a node in the graph
        When I search and find it
        Then the result dict has file_path, line_start, line_end
        """
        _insert_and_index(
            store,
            [
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name="lib.py::calculate",
                    file_path="lib.py",
                    line_start=10,
                    line_end=25,
                    language="python",
                ),
            ],
        )
        results = search(store, "calculate")
        assert len(results) >= 1
        r = results[0]
        assert r["file_path"] == "lib.py"
        assert r["line_start"] == 10
        assert r["line_end"] == 25
        assert "relevance" in r

    @pytest.mark.unit
    def test_kind_filter(self, store: GraphStore) -> None:
        """
        Scenario: Filter results by kind
        Given a Class and Function with similar names
        When I search with kind="Function"
        Then only the Function is returned
        """
        _insert_and_index(
            store,
            [
                GraphNode(
                    kind=NodeKind.CLASS,
                    qualified_name="a.py::User",
                    file_path="a.py",
                    line_start=1,
                    line_end=20,
                ),
                GraphNode(
                    kind=NodeKind.FUNCTION,
                    qualified_name="a.py::get_user",
                    file_path="a.py",
                    line_start=22,
                    line_end=30,
                ),
            ],
        )
        results = search(store, "user", kind="Function")
        kinds = {r["kind"] for r in results}
        assert "Class" not in kinds

    @pytest.mark.unit
    def test_respects_limit(self, store: GraphStore) -> None:
        """
        Scenario: Limit caps result count
        Given 10 matching nodes
        When I search with limit=3
        Then at most 3 results are returned
        """
        nodes = [
            GraphNode(
                kind=NodeKind.FUNCTION,
                qualified_name=f"f.py::func_{i}",
                file_path="f.py",
                line_start=i,
                line_end=i + 5,
            )
            for i in range(10)
        ]
        _insert_and_index(store, nodes)
        results = search(store, "func", limit=3)
        assert len(results) <= 3
