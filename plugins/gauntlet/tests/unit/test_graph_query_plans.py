"""Query plans for the lookups a graph build repeats once per edge.

``resolve_call_targets`` checks every resolved call for an existing
duplicate. SQLite planned that lookup on the ``kind`` index, and most
edges are CALLS, so each check scanned them all: 12.7 ms a lookup on
this repository's 123k-edge graph, or about 380 s of a 459 s build.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from gauntlet import graph as graph_mod
from gauntlet.graph import GraphStore

if TYPE_CHECKING:
    from pathlib import Path


def _plan(conn: sqlite3.Connection) -> str:
    rows = conn.execute(
        "EXPLAIN QUERY PLAN " + graph_mod._DUPLICATE_CALL_SQL,
        ("CALLS", "a.f", "b.g"),
    ).fetchall()
    return " ".join(str(row[-1]) for row in rows)


def test_duplicate_call_lookup_seeks_on_source_and_target(tmp_path: Path) -> None:
    store = GraphStore(tmp_path / "graph.db")
    try:
        plan = _plan(store._conn)
    finally:
        store.close()
    assert "source_qn=? AND target_qn=?" in plan, plan


def test_a_graph_built_before_the_index_gets_it_on_open(tmp_path: Path) -> None:
    db = tmp_path / "graph.db"
    GraphStore(db).close()
    with sqlite3.connect(db) as conn:
        conn.execute("DROP INDEX IF EXISTS idx_edges_kind_src_tgt")
    store = GraphStore(db)
    try:
        plan = _plan(store._conn)
    finally:
        store.close()
    assert "source_qn=? AND target_qn=?" in plan, plan
