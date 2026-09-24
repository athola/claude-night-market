"""The inline SqliteGraphBase fallback must agree with leyline (XPL-002).

``gauntlet/graph.py`` imports ``leyline.sqlite_graph_base.SqliteGraphBase``
and carries an inline copy for systems where leyline is absent. Deleting
the copy is not available: ``plugins/abstract/hooks/shared/hook_io.py``
records the standing constraint that plugin isolation forbids a
cross-plugin import, so the copies must change together. Two copies of
one contract drift silently, and the fallback is the copy nobody runs:
when this test was written the canonical had grown ``table_names()`` and
narrowed its except clause, and the copy had neither.

So the copy is pinned to the canonical by surface and by behavior over a
fixture set rather than deleted.
"""

from __future__ import annotations

import importlib
import importlib.util
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

_LEYLINE_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "leyline"
    / "src"
    / "leyline"
    / "sqlite_graph_base.py"
)


def _load_canonical() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_canonical_sqlite_base", _LEYLINE_SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fallback_base(monkeypatch: pytest.MonkeyPatch) -> Iterator[type]:
    """Yield the inline copy, forced by making the leyline import fail."""
    monkeypatch.setitem(sys.modules, "leyline.sqlite_graph_base", None)
    module = importlib.import_module("gauntlet.graph")
    reloaded = importlib.reload(module)
    yield reloaded.SqliteGraphBase
    monkeypatch.undo()
    importlib.reload(reloaded)


def _surface(cls: type) -> set[str]:
    return {
        name
        for name in vars(cls)
        if not name.startswith("__") or name in {"__init__", "__enter__", "__exit__"}
    }


def _open(base: type, path: Path, schema: str, fts: str = "") -> object:
    store_cls = type("Store", (base,), {"_schema_sql": schema, "_fts_create_sql": fts})
    return store_cls(path)


def test_fallback_exposes_the_same_surface_as_the_canonical(
    fallback_base: type,
) -> None:
    canonical = _load_canonical().SqliteGraphBase
    assert _surface(fallback_base) == _surface(canonical)


def test_fallback_and_canonical_open_a_store_identically(
    fallback_base: type, tmp_path: Path
) -> None:
    canonical = _load_canonical().SqliteGraphBase
    schema = "CREATE TABLE IF NOT EXISTS node (id TEXT PRIMARY KEY, kind TEXT)"
    fts = "CREATE VIRTUAL TABLE IF NOT EXISTS node_fts USING fts5(id, kind)"
    observed = {}
    for label, base in (("canonical", canonical), ("fallback", fallback_base)):
        with _open(base, tmp_path / f"{label}.db", schema, fts) as store:
            conn = store._conn
            observed[label] = (
                conn.execute("PRAGMA journal_mode").fetchone()[0],
                conn.execute("PRAGMA foreign_keys").fetchone()[0],
                conn.row_factory,
                store._has_fts,
                sorted(store.table_names()),
                store._batch_size,
            )
    assert observed["fallback"] == observed["canonical"]


def test_fallback_and_canonical_fail_the_same_way_on_bad_ddl(
    fallback_base: type, tmp_path: Path
) -> None:
    canonical = _load_canonical().SqliteGraphBase
    for label, base in (("canonical", canonical), ("fallback", fallback_base)):
        with pytest.raises(sqlite3.Error):
            _open(base, tmp_path / f"{label}.db", "CREATE TABL broken (x)")
