"""Tests for the provenance column that records how a CALLS target was found."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest import mock

import pytest

from gauntlet.graph import GraphStore
from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind, Resolution


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


class TestVendoredCopyResolution:
    """
    Feature: Resolving a bare call among vendored copies of one module

    As a reader of blast radius
    I want a call to reach the copy inside the caller's own plugin
    So that the dependency is not lost to a three-way name collision
    """

    _CALLER = "plugins/herald/hooks/latte.py"

    def _seed_copies(self, store: GraphStore, *paths: str) -> None:
        store.upsert_node(_node(f"{self._CALLER}::main", self._CALLER))
        for path in paths:
            store.upsert_node(_node(f"{path}::write_atomic", path))
        store.upsert_edge(_call(f"{self._CALLER}::main", "write_atomic", self._CALLER))

    @pytest.mark.unit
    def test_bare_call_prefers_own_plugin_copy_as_name_guess(
        self, store: GraphStore
    ) -> None:
        own = "plugins/herald/hooks/_vendored_leyline_atomic_file.py"
        self._seed_copies(
            store,
            "plugins/leyline/src/leyline/atomic_file.py",
            own,
            "plugins/sanctum/hooks/_vendored_leyline_atomic_file.py",
        )
        store.resolve_call_targets()
        edge = store.get_edges_by_source(f"{self._CALLER}::main")[0]
        assert edge.target_qn == f"{own}::write_atomic"
        assert _resolution(store, f"{self._CALLER}::main") == ["name_guess"]

    @pytest.mark.unit
    def test_absolute_paths_resolve_to_own_plugin_copy(self, store: GraphStore) -> None:
        root = "/home/dev/night-market"
        caller = f"{root}/plugins/herald/hooks/latte.py"
        own = f"{root}/plugins/herald/hooks/_vendored_leyline_atomic_file.py"
        store.upsert_node(_node(f"{caller}::main", caller))
        for path in (
            f"{root}/plugins/leyline/src/leyline/atomic_file.py",
            own,
            f"{root}/plugins/sanctum/hooks/_vendored_leyline_atomic_file.py",
        ):
            store.upsert_node(_node(f"{path}::write_atomic", path))
        store.upsert_edge(_call(f"{caller}::main", "write_atomic", caller))
        store.resolve_call_targets()
        edge = store.get_edges_by_source(f"{caller}::main")[0]
        assert edge.target_qn == f"{own}::write_atomic"

    @pytest.mark.unit
    def test_caller_plugin_without_copy_stays_unresolved(
        self, store: GraphStore
    ) -> None:
        self._seed_copies(
            store,
            "plugins/leyline/src/leyline/atomic_file.py",
            "plugins/sanctum/hooks/_vendored_leyline_atomic_file.py",
        )
        assert store.resolve_call_targets() == 0
        assert _resolution(store, f"{self._CALLER}::main") == [""]

    @pytest.mark.unit
    def test_two_copies_in_own_plugin_stay_unresolved(self, store: GraphStore) -> None:
        self._seed_copies(
            store,
            "plugins/herald/hooks/_vendored_leyline_atomic_file.py",
            "plugins/herald/src/_vendored_leyline_atomic_file.py",
            "plugins/leyline/src/leyline/atomic_file.py",
        )
        assert store.resolve_call_targets() == 0

    @pytest.mark.unit
    def test_single_cross_plugin_definition_still_resolves_exact(
        self, store: GraphStore
    ) -> None:
        self._seed_copies(store, "plugins/leyline/src/leyline/atomic_file.py")
        store.resolve_call_targets()
        assert _resolution(store, f"{self._CALLER}::main") == ["exact"]


@pytest.mark.unit
def test_object_receiver_sharing_module_name_is_a_name_guess(store: GraphStore) -> None:
    """`config.load()` on a parameter named like config.py was labelled exact,
    so it never reached name_guess_callers (GAU-4).
    """
    store.upsert_node(_node("config.py::load", "config.py"))
    store.upsert_node(_node("store.py::Store", "store.py", NodeKind.CLASS))
    store.upsert_node(_node("store.py::Store.load", "store.py"))
    store.upsert_node(_node("main.py::run", "main.py"))
    store.upsert_edge(_call("main.py::run", "config.load", "main.py"))
    store.resolve_call_targets()
    assert _resolution(store, "main.py::run") == ["name_guess"]


@pytest.mark.unit
def test_init_schema_tolerates_column_added_concurrently(tmp_path: Path) -> None:
    """Two processes upgrading one legacy graph: the second ALTER raised
    "duplicate column name" and failed that process (GAU-8).
    """
    db = tmp_path / "graph.db"
    GraphStore(db).close()  # the column exists now
    real_execute = sqlite3.Connection.execute

    class StaleConnection(sqlite3.Connection):
        def execute(self, sql, *args):  # type: ignore[override] - narrows sqlite3 execute to fake a stale schema
            if sql.startswith("PRAGMA table_info(edges)"):
                return iter([(0, "id"), (1, "source_qn")])  # column looks absent
            return real_execute(self, sql, *args)

    original_connect = sqlite3.connect

    def connect(*args, **kwargs):
        return original_connect(*args, factory=StaleConnection, **kwargs)

    with mock.patch("sqlite3.connect", connect):
        GraphStore(db).close()


class TestResolutionIsOneOfThreeValues:
    """An unknown resolution read as a confirmed caller in blast radius."""

    @staticmethod
    def _edge_dict(resolution: str) -> dict[str, object]:
        return {
            "kind": "CALLS",
            "source_qn": "a.py::main",
            "target_qn": "c.py::helper",
            "resolution": resolution,
        }

    @pytest.mark.unit
    def test_edge_from_dict_rejects_an_unknown_resolution(self) -> None:
        with pytest.raises(ValueError, match="nam_guess"):
            GraphEdge.from_dict(self._edge_dict("nam_guess"))

    @pytest.mark.unit
    def test_edge_from_dict_parses_a_known_resolution(self) -> None:
        edge = GraphEdge.from_dict(self._edge_dict("name_guess"))
        assert edge.resolution is Resolution.NAME_GUESS
        assert edge.to_dict()["resolution"] == "name_guess"

    @pytest.mark.unit
    def test_stored_edge_with_an_unknown_resolution_is_rejected(
        self, store: GraphStore
    ) -> None:
        store.upsert_node(_node("a.py::main", "a.py"))
        store.upsert_edge(_call("a.py::main", "helper", "a.py"))
        store._conn.execute("UPDATE edges SET resolution = 'guessed'")
        with pytest.raises(ValueError, match="guessed"):
            store.get_edges_by_source("a.py::main")
