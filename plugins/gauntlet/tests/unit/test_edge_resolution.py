"""Tests for the provenance column that records how a CALLS target was found."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind


def _node(qn: str, file_path: str, kind: NodeKind = NodeKind.FUNCTION) -> GraphNode:
    return GraphNode(
        kind=kind, qualified_name=qn, file_path=file_path, line_start=1, line_end=5
    )


def _call(source: str, target: str, file_path: str) -> GraphEdge:
    return GraphEdge(
        kind=EdgeKind.CALLS, source_qn=source, target_qn=target, file_path=file_path
    )


def _resolution(store: GraphStore, source: str) -> list[str]:
    return [
        row["resolution"]
        for row in store._conn.execute(
            "SELECT resolution FROM edges WHERE source_qn = ?", (source,)
        )
    ]


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "graph.db")
    yield s
    s.close()


class TestEdgeResolutionProvenance:
    """
    Feature: Recording how a call target was resolved

    As a consumer of CALLS edges
    I want to tell a unique match from a bare-name guess
    So that a guessed dependency is not trusted like a declared one
    """

    @pytest.mark.unit
    def test_unique_bare_definition_is_recorded_as_exact(
        self, store: GraphStore
    ) -> None:
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_node(_node("c.py::helper", "c.py"))
        store.upsert_edge(_call("a.py::main", "helper", "a.py"))
        store.resolve_call_targets()
        assert _resolution(store, "a.py::main") == ["exact"]

    @pytest.mark.unit
    def test_module_qualified_call_is_recorded_as_exact(
        self, store: GraphStore
    ) -> None:
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_node(_node("walker.py::walk", "walker.py"))
        store.upsert_edge(_call("a.py::main", "walker.walk", "a.py"))
        store.resolve_call_targets()
        assert _resolution(store, "a.py::main") == ["exact"]

    @pytest.mark.unit
    def test_self_call_is_recorded_as_exact(self, store: GraphStore) -> None:
        store.upsert_node(_node("a.py::Job", "a.py", NodeKind.CLASS))
        store.upsert_node(_node("a.py::Job.start", "a.py"))
        store.upsert_node(_node("a.py::Job.run", "a.py"))
        store.upsert_edge(_call("a.py::Job.start", "self.run", "a.py"))
        store.resolve_call_targets()
        assert _resolution(store, "a.py::Job.start") == ["exact"]

    @pytest.mark.unit
    def test_untyped_receiver_pick_is_recorded_as_name_guess(
        self, store: GraphStore
    ) -> None:
        """`graph.upsert` has no receiver type, so the method match is a guess."""
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_node(_node("g.py::Graph", "g.py", NodeKind.CLASS))
        store.upsert_node(_node("g.py::Graph.upsert", "g.py"))
        store.upsert_edge(_call("a.py::main", "graph.upsert", "a.py"))
        store.resolve_call_targets()
        assert _resolution(store, "a.py::main") == ["name_guess"]

    @pytest.mark.unit
    def test_external_call_keeps_empty_resolution(self, store: GraphStore) -> None:
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_edge(_call("a.py::main", "os.walk", "a.py"))
        store.resolve_call_targets()
        assert _resolution(store, "a.py::main") == [""]

    @pytest.mark.unit
    def test_edge_read_back_carries_resolution(self, store: GraphStore) -> None:
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_node(_node("c.py::helper", "c.py"))
        store.upsert_edge(_call("a.py::main", "helper", "a.py"))
        store.resolve_call_targets()
        (edge,) = store.get_edges_by_source("a.py::main")
        assert edge.resolution == "exact"

    @pytest.mark.unit
    def test_duplicate_collapse_keeps_the_surviving_edge_resolution(
        self, store: GraphStore
    ) -> None:
        """Two call sites that resolve to one target leave one edge, still tagged."""
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_node(_node("c.py::helper", "c.py"))
        store.upsert_edge(_call("a.py::main", "helper", "a.py"))
        store.upsert_edge(_call("a.py::main", "c.helper", "a.py"))
        store.resolve_call_targets()
        assert _resolution(store, "a.py::main") == ["exact"]


class TestEdgeResolutionMigration:
    """An on-disk graph built before the column existed gains it on open."""

    @pytest.mark.unit
    def test_legacy_database_gains_resolution_column(self, tmp_path: Path) -> None:
        db_path = tmp_path / "old.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """CREATE TABLE edges (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   kind TEXT NOT NULL, source_qn TEXT NOT NULL,
                   target_qn TEXT NOT NULL, file_path TEXT DEFAULT '',
                   line INTEGER DEFAULT 0);
               INSERT INTO edges (kind, source_qn, target_qn, file_path)
               VALUES ('CALLS', 'a.py::main', 'helper', 'a.py');"""
        )
        conn.commit()
        conn.close()

        with GraphStore(db_path) as store:
            assert _resolution(store, "a.py::main") == [""]
            (edge,) = store.get_edges_by_source("a.py::main")
            assert edge.resolution == ""

    @pytest.mark.unit
    def test_reopening_a_migrated_database_is_a_no_op(self, tmp_path: Path) -> None:
        db_path = tmp_path / "graph.db"
        GraphStore(db_path).close()
        with GraphStore(db_path) as store:
            columns = [
                row["name"] for row in store._conn.execute("PRAGMA table_info(edges)")
            ]
        assert columns.count("resolution") == 1
