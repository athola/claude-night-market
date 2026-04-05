"""Tests for the SQLite-backed code knowledge graph."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.graph import GraphStore, _sanitize_fts_query
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_graph.db"


@pytest.fixture()
def store(db_path: Path) -> GraphStore:
    s = GraphStore(db_path)
    yield s
    s.close()


def _make_node(
    qn: str = "app.py::main",
    kind: NodeKind = NodeKind.FUNCTION,
    file_path: str = "app.py",
    line_start: int = 1,
    line_end: int = 10,
    **kwargs: object,
) -> GraphNode:
    return GraphNode(
        kind=kind,
        qualified_name=qn,
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        language=kwargs.get("language", "python"),
        is_test=kwargs.get("is_test", False),
        file_hash=kwargs.get("file_hash", "abc123"),
    )


def _make_edge(
    kind: EdgeKind = EdgeKind.CALLS,
    source: str = "app.py::main",
    target: str = "app.py::helper",
    file_path: str = "app.py",
) -> GraphEdge:
    return GraphEdge(
        kind=kind,
        source_qn=source,
        target_qn=target,
        file_path=file_path,
    )


class TestGraphStoreNodeCrud:
    """
    Feature: Node CRUD operations

    As a graph consumer
    I want to create, read, update, and delete nodes
    So that the graph reflects the current codebase state
    """

    @pytest.mark.unit
    def test_upsert_and_retrieve_node(self, store: GraphStore) -> None:
        """
        Scenario: Insert a node and retrieve it by qualified name
        Given an empty graph
        When I upsert a function node
        Then I can retrieve it by qualified name
        """
        node = _make_node()
        store.upsert_node(node)
        result = store.get_node("app.py::main")
        assert result is not None
        assert result.qualified_name == "app.py::main"
        assert result.kind == NodeKind.FUNCTION
        assert result.file_path == "app.py"

    @pytest.mark.unit
    def test_upsert_updates_existing_node(self, store: GraphStore) -> None:
        """
        Scenario: Upserting a node with the same qualified name updates it
        Given a node exists in the graph
        When I upsert with the same qualified name but different data
        Then the node is updated, not duplicated
        """
        store.upsert_node(_make_node(line_end=10))
        store.upsert_node(_make_node(line_end=20))
        assert store.node_count() == 1
        result = store.get_node("app.py::main")
        assert result is not None
        assert result.line_end == 20

    @pytest.mark.unit
    def test_get_nodes_in_file(self, store: GraphStore) -> None:
        """
        Scenario: Retrieve all nodes belonging to a file
        Given multiple nodes across two files
        When I query by file path
        Then only nodes from that file are returned
        """
        store.upsert_node(_make_node("a.py::foo", file_path="a.py"))
        store.upsert_node(_make_node("a.py::bar", file_path="a.py"))
        store.upsert_node(_make_node("b.py::baz", file_path="b.py"))

        results = store.get_nodes_in_file("a.py")
        assert len(results) == 2
        qns = {n.qualified_name for n in results}
        assert qns == {"a.py::foo", "a.py::bar"}

    @pytest.mark.unit
    def test_delete_nodes_in_file(self, store: GraphStore) -> None:
        """
        Scenario: Delete all nodes for a file
        Given nodes exist for a file
        When I delete by file path
        Then those nodes are removed and others remain
        """
        store.upsert_node(_make_node("a.py::foo", file_path="a.py"))
        store.upsert_node(_make_node("b.py::bar", file_path="b.py"))
        deleted = store.delete_nodes_in_file("a.py")
        assert deleted == 1
        assert store.node_count() == 1
        assert store.get_node("b.py::bar") is not None

    @pytest.mark.unit
    def test_node_count(self, store: GraphStore) -> None:
        """
        Scenario: Count nodes in the graph
        Given three nodes inserted
        When I check node count
        Then it returns 3
        """
        for i in range(3):
            store.upsert_node(_make_node(f"f.py::fn{i}"))
        assert store.node_count() == 3


class TestGraphStoreEdgeCrud:
    """
    Feature: Edge CRUD operations

    As a graph consumer
    I want to create and query edges between nodes
    So that I can traverse code relationships
    """

    @pytest.mark.unit
    def test_upsert_and_query_edge_by_source(self, store: GraphStore) -> None:
        """
        Scenario: Insert an edge and query by source
        Given an empty graph
        When I insert a CALLS edge
        Then I can find it by source qualified name
        """
        store.upsert_edge(_make_edge())
        results = store.get_edges_by_source("app.py::main")
        assert len(results) == 1
        assert results[0].target_qn == "app.py::helper"
        assert results[0].kind == EdgeKind.CALLS

    @pytest.mark.unit
    def test_upsert_edge_deduplicates(self, store: GraphStore) -> None:
        """
        Scenario: Duplicate edges are not inserted
        Given an edge exists
        When I insert the same edge again
        Then edge count remains 1
        """
        store.upsert_edge(_make_edge())
        store.upsert_edge(_make_edge())
        assert store.edge_count() == 1

    @pytest.mark.unit
    def test_query_edges_by_target(self, store: GraphStore) -> None:
        """
        Scenario: Find all incoming edges to a node
        Given two edges targeting the same node
        When I query by target
        Then both edges are returned
        """
        store.upsert_edge(_make_edge(source="a.py::fn1", target="b.py::shared"))
        store.upsert_edge(_make_edge(source="a.py::fn2", target="b.py::shared"))
        results = store.get_edges_by_target("b.py::shared")
        assert len(results) == 2

    @pytest.mark.unit
    def test_delete_edges_in_file(self, store: GraphStore) -> None:
        """
        Scenario: Delete edges by file path
        Given edges from two files
        When I delete edges for one file
        Then only edges from the other file remain
        """
        store.upsert_edge(_make_edge(file_path="a.py"))
        store.upsert_edge(
            _make_edge(source="b.py::x", target="b.py::y", file_path="b.py")
        )
        deleted = store.delete_edges_in_file("a.py")
        assert deleted == 1
        assert store.edge_count() == 1


class TestGraphStoreAtomicFileStorage:
    """
    Feature: Atomic per-file storage

    As a graph builder
    I want to atomically replace all nodes/edges for a file
    So that partial updates don't corrupt the graph
    """

    @pytest.mark.unit
    def test_store_file_replaces_existing(self, store: GraphStore) -> None:
        """
        Scenario: store_file replaces old data for a file
        Given nodes/edges exist for app.py
        When I call store_file with new data
        Then old data is gone and new data is present
        """
        store.upsert_node(_make_node("app.py::old_fn", file_path="app.py"))
        store.upsert_edge(
            _make_edge(source="app.py::old_fn", target="x", file_path="app.py")
        )

        new_nodes = [_make_node("app.py::new_fn", file_path="app.py")]
        new_edges = [
            _make_edge(source="app.py::new_fn", target="y", file_path="app.py")
        ]
        store.store_file("app.py", new_nodes, new_edges)

        assert store.get_node("app.py::old_fn") is None
        assert store.get_node("app.py::new_fn") is not None
        assert store.edge_count() == 1

    @pytest.mark.unit
    def test_store_file_does_not_affect_other_files(self, store: GraphStore) -> None:
        """
        Scenario: store_file only touches the specified file
        Given nodes in two files
        When I store_file for one
        Then the other file's nodes are untouched
        """
        store.upsert_node(_make_node("b.py::keep", file_path="b.py"))
        store.store_file("a.py", [_make_node("a.py::new", file_path="a.py")], [])
        assert store.get_node("b.py::keep") is not None


class TestGraphStoreBfsImpactRadius:
    """
    Feature: BFS impact radius

    As a code reviewer
    I want to find all nodes affected by changes in specific files
    So that I know what code to review
    """

    @pytest.mark.unit
    def test_impact_radius_depth_zero(self, store: GraphStore) -> None:
        """
        Scenario: Depth 0 returns only seed nodes
        Given nodes and edges in the graph
        When I compute impact radius with depth=0
        Then only nodes in the changed files are returned
        """
        store.upsert_node(_make_node("a.py::fn", file_path="a.py"))
        store.upsert_node(_make_node("b.py::fn", file_path="b.py"))
        store.upsert_edge(
            _make_edge(source="a.py::fn", target="b.py::fn", file_path="a.py")
        )

        result = store.impact_radius(["a.py"], depth=0)
        qns = {n.qualified_name for n in result}
        assert "a.py::fn" in qns
        assert "b.py::fn" not in qns

    @pytest.mark.unit
    def test_impact_radius_follows_forward_edges(self, store: GraphStore) -> None:
        """
        Scenario: BFS follows outgoing CALLS edges
        Given A calls B calls C
        When I compute impact radius from A's file with depth=2
        Then A, B, and C are all in the result
        """
        store.upsert_node(_make_node("a.py::A", file_path="a.py"))
        store.upsert_node(_make_node("b.py::B", file_path="b.py"))
        store.upsert_node(_make_node("c.py::C", file_path="c.py"))
        store.upsert_edge(
            _make_edge(source="a.py::A", target="b.py::B", file_path="a.py")
        )
        store.upsert_edge(
            _make_edge(source="b.py::B", target="c.py::C", file_path="b.py")
        )

        result = store.impact_radius(["a.py"], depth=2)
        qns = {n.qualified_name for n in result}
        assert qns == {"a.py::A", "b.py::B", "c.py::C"}

    @pytest.mark.unit
    def test_impact_radius_follows_reverse_edges(self, store: GraphStore) -> None:
        """
        Scenario: BFS follows incoming edges (dependents)
        Given B depends on A (B imports A)
        When I compute impact radius from A's file
        Then B is in the result
        """
        store.upsert_node(_make_node("a.py::A", file_path="a.py"))
        store.upsert_node(_make_node("b.py::B", file_path="b.py"))
        store.upsert_edge(
            _make_edge(
                kind=EdgeKind.IMPORTS_FROM,
                source="b.py::B",
                target="a.py::A",
                file_path="b.py",
            )
        )

        result = store.impact_radius(["a.py"], depth=1)
        qns = {n.qualified_name for n in result}
        assert "b.py::B" in qns

    @pytest.mark.unit
    def test_impact_radius_respects_depth_limit(self, store: GraphStore) -> None:
        """
        Scenario: BFS stops at the depth limit
        Given a chain A -> B -> C -> D
        When I compute with depth=1
        Then D is not in the result
        """
        for name, fp in [("A", "a.py"), ("B", "b.py"), ("C", "c.py"), ("D", "d.py")]:
            store.upsert_node(_make_node(f"{fp}::{name}", file_path=fp))
        store.upsert_edge(_make_edge(source="a.py::A", target="b.py::B"))
        store.upsert_edge(_make_edge(source="b.py::B", target="c.py::C"))
        store.upsert_edge(_make_edge(source="c.py::C", target="d.py::D"))

        result = store.impact_radius(["a.py"], depth=1)
        qns = {n.qualified_name for n in result}
        assert "a.py::A" in qns
        assert "b.py::B" in qns
        assert "d.py::D" not in qns


class TestGraphStoreFts5Search:
    """
    Feature: FTS5 full-text search

    As a developer
    I want to search the graph by function/class name
    So that I can find code without reading every file
    """

    @pytest.mark.unit
    def test_fts_search_finds_matching_node(self, store: GraphStore) -> None:
        """
        Scenario: FTS5 search returns nodes matching a query
        Given a node with qualified name "app.py::UserService"
        When I search for "UserService"
        Then the node is returned
        """
        store.upsert_node(
            _make_node("app.py::UserService", kind=NodeKind.CLASS, file_path="app.py")
        )
        store.rebuild_fts()
        results = store.search_fts("UserService")
        assert len(results) >= 1
        assert results[0].qualified_name == "app.py::UserService"

    @pytest.mark.unit
    def test_fts_search_with_kind_filter(self, store: GraphStore) -> None:
        """
        Scenario: FTS5 search can filter by node kind
        Given a Class and Function with similar names
        When I search with kind="Class"
        Then only the Class is returned
        """
        store.upsert_node(
            _make_node("a.py::User", kind=NodeKind.CLASS, file_path="a.py")
        )
        store.upsert_node(
            _make_node("a.py::get_user", kind=NodeKind.FUNCTION, file_path="a.py")
        )
        store.rebuild_fts()
        results = store.search_fts("user", kind="Class")
        kinds = {str(r.kind) for r in results}
        assert "Function" not in kinds

    @pytest.mark.unit
    def test_fts_fallback_on_broken_index(self, store: GraphStore) -> None:
        """
        Scenario: Search falls back to LIKE when FTS5 index is broken
        Given nodes exist but the FTS5 table is dropped
        When I search
        Then LIKE-based fallback finds matching results
        """
        store.upsert_node(_make_node("app.py::calculate_total"))
        # Drop FTS table to trigger OperationalError fallback
        store._conn.execute("DROP TABLE IF EXISTS nodes_fts")
        results = store.search_fts("calculate_total")
        assert len(results) == 1
        assert results[0].qualified_name == "app.py::calculate_total"


class TestGraphStoreMetadata:
    """
    Feature: Metadata key-value storage

    As a graph manager
    I want to store build metadata (timestamp, commit SHA)
    So that I know when the graph was last updated
    """

    @pytest.mark.unit
    def test_set_and_get_metadata(self, store: GraphStore) -> None:
        store.set_metadata("build_time", "2026-04-04T12:00:00")
        assert store.get_metadata("build_time") == "2026-04-04T12:00:00"

    @pytest.mark.unit
    def test_get_missing_metadata_returns_none(self, store: GraphStore) -> None:
        assert store.get_metadata("nonexistent") is None

    @pytest.mark.unit
    def test_metadata_upsert(self, store: GraphStore) -> None:
        store.set_metadata("version", "1")
        store.set_metadata("version", "2")
        assert store.get_metadata("version") == "2"


class TestSanitizeFtsQuery:
    """Unit tests for FTS5 query sanitization."""

    @pytest.mark.unit
    def test_strips_operators(self) -> None:
        assert (
            _sanitize_fts_query('hello+world-foo*bar("baz")')
            == "hello world foo bar baz"
        )

    @pytest.mark.unit
    def test_collapses_whitespace(self) -> None:
        assert _sanitize_fts_query("  hello   world  ") == "hello world"

    @pytest.mark.unit
    def test_empty_query(self) -> None:
        assert _sanitize_fts_query("") == ""
