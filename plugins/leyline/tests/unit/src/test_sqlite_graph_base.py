# ruff: noqa: D101,D102
"""Tests for leyline.sqlite_graph_base -- shared SQLite graph infrastructure.

Feature: Reusable SQLite graph base class

As a plugin developer
I want a base class that handles SQLite connection setup, WAL mode,
foreign keys, FTS5 fallback, and context manager protocol
So that graph-backed plugins share validated, consistent storage logic
without duplicating connection boilerplate.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[4] / "src"
sys.path.insert(0, str(_SRC))

from leyline.sqlite_graph_base import SqliteGraphBase

# ---------------------------------------------------------------------------
# Minimal concrete subclass used across all tests
# ---------------------------------------------------------------------------

_TEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    value TEXT DEFAULT ''
);
"""

_TEST_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    name,
    value,
    tokenize='porter unicode61'
);
"""


class _TestGraph(SqliteGraphBase):
    """Minimal subclass for testing the base class."""

    _schema_sql = _TEST_SCHEMA
    _fts_create_sql = _TEST_FTS


class _NoFtsGraph(SqliteGraphBase):
    """Subclass without FTS DDL."""

    _schema_sql = _TEST_SCHEMA
    _fts_create_sql = ""


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------


class TestConnectionManagement:
    """Feature: SQLite connection lifecycle

    As a plugin storing graph data
    I want the base class to manage connection setup and teardown
    So that WAL mode, foreign keys, and row factory are always correct.
    """

    @pytest.mark.unit
    def test_opens_connection_with_wal_mode(self, tmp_path: Path) -> None:
        """Scenario: Connection uses WAL journal mode
        Given a new SqliteGraphBase subclass
        When it is initialized
        Then the journal mode is WAL
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        row = g._conn.execute("PRAGMA journal_mode").fetchone()
        assert row[0] == "wal"
        g.close()

    @pytest.mark.unit
    def test_enables_foreign_keys(self, tmp_path: Path) -> None:
        """Scenario: Connection enables foreign keys
        Given a new SqliteGraphBase subclass
        When it is initialized
        Then foreign keys are enabled
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        row = g._conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1
        g.close()

    @pytest.mark.unit
    def test_row_factory_set_to_row(self, tmp_path: Path) -> None:
        """Scenario: Connection uses sqlite3.Row factory
        Given a new SqliteGraphBase subclass
        When it is initialized
        Then the row factory is sqlite3.Row
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        assert g._conn.row_factory is sqlite3.Row
        g.close()

    @pytest.mark.unit
    def test_accepts_path_object(self, tmp_path: Path) -> None:
        """Scenario: Constructor accepts pathlib.Path
        Given a Path object as db_path
        When the base class is initialized
        Then it connects successfully and stores the path as a string
        """
        db = tmp_path / "test.db"
        g = _TestGraph(db)
        assert g._db_path == str(db)
        g.close()

    @pytest.mark.unit
    def test_close_closes_connection(self, tmp_path: Path) -> None:
        """Scenario: close() shuts down the connection
        Given an open graph store
        When close() is called
        Then the connection is no longer usable
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        g.close()
        with pytest.raises(sqlite3.ProgrammingError):
            g._conn.execute("SELECT 1")


# ---------------------------------------------------------------------------
# Schema initialization
# ---------------------------------------------------------------------------


class TestSchemaInit:
    """Feature: Automatic schema creation

    As a plugin developer
    I want the schema DDL applied on first connection
    So that tables are ready without manual setup.
    """

    @pytest.mark.unit
    def test_creates_tables_from_schema_sql(self, tmp_path: Path) -> None:
        """Scenario: Schema DDL creates tables
        Given a subclass with _schema_sql defining an 'items' table
        When the graph store is initialized
        Then the 'items' table exists
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        tables = g.table_names()
        assert "items" in tables
        g.close()

    @pytest.mark.unit
    def test_schema_error_closes_connection(self, tmp_path: Path) -> None:
        """Scenario: Schema failure closes connection
        Given a subclass with invalid schema DDL
        When initialization fails
        Then the connection is closed and the error propagates
        """

        class _BadSchema(SqliteGraphBase):
            _schema_sql = "CREATE TABLE INVALID SYNTAX !!!"

        db = tmp_path / "test.db"
        with pytest.raises(sqlite3.OperationalError):
            _BadSchema(str(db))


# ---------------------------------------------------------------------------
# FTS5 graceful fallback
# ---------------------------------------------------------------------------


class TestFts5Fallback:
    """Feature: FTS5 with graceful fallback

    As a plugin developer
    I want FTS5 tables created when available and skipped when not
    So that the graph store works on SQLite builds without FTS5.
    """

    @pytest.mark.unit
    def test_fts5_created_when_available(self, tmp_path: Path) -> None:
        """Scenario: FTS5 table created on supported builds
        Given a subclass with _fts_create_sql
        When FTS5 is supported (default CPython)
        Then _has_fts is True and the FTS table exists
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        assert g._has_fts is True
        tables = g.table_names()
        assert "items_fts" in tables
        g.close()

    @pytest.mark.unit
    def test_no_fts_sql_means_no_fts(self, tmp_path: Path) -> None:
        """Scenario: Empty FTS DDL skips FTS setup
        Given a subclass with empty _fts_create_sql
        When the graph store is initialized
        Then _has_fts is False
        """
        db = tmp_path / "test.db"
        g = _NoFtsGraph(str(db))
        assert g._has_fts is False
        g.close()

    @pytest.mark.unit
    def test_bad_fts_sql_falls_back_gracefully(self, tmp_path: Path) -> None:
        """Scenario: Invalid FTS DDL triggers fallback
        Given a subclass with broken _fts_create_sql
        When the graph store is initialized
        Then _has_fts is False and no error is raised
        """

        class _BadFts(SqliteGraphBase):
            _schema_sql = _TEST_SCHEMA
            _fts_create_sql = "CREATE VIRTUAL TABLE bad USING fts5_nope(x);"

        db = tmp_path / "test.db"
        g = _BadFts(str(db))
        assert g._has_fts is False
        # Core tables still created
        assert "items" in g.table_names()
        g.close()


# ---------------------------------------------------------------------------
# Context manager protocol
# ---------------------------------------------------------------------------


class TestContextManager:
    """Feature: Context manager protocol

    As a plugin developer
    I want to use the graph store as a context manager
    So that connections are always properly closed.
    """

    @pytest.mark.unit
    def test_enter_returns_self(self, tmp_path: Path) -> None:
        """Scenario: __enter__ returns the instance
        Given a graph store
        When used as a context manager
        Then __enter__ returns the same instance
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        result = g.__enter__()
        assert result is g
        g.close()

    @pytest.mark.unit
    def test_exit_closes_connection(self, tmp_path: Path) -> None:
        """Scenario: __exit__ closes the connection
        Given a graph store used as a context manager
        When the with block exits
        Then the connection is closed
        """
        db = tmp_path / "test.db"
        with _TestGraph(str(db)) as g:
            g._conn.execute("SELECT 1")  # Should work
        with pytest.raises(sqlite3.ProgrammingError):
            g._conn.execute("SELECT 1")  # Should fail after close

    @pytest.mark.unit
    def test_exit_closes_on_exception(self, tmp_path: Path) -> None:
        """Scenario: __exit__ closes even on exception
        Given a graph store used as a context manager
        When an exception occurs inside the with block
        Then the connection is still closed
        """
        db = tmp_path / "test.db"
        try:
            with _TestGraph(str(db)) as g:
                raise ValueError("test error")
        except ValueError:
            pass
        with pytest.raises(sqlite3.ProgrammingError):
            g._conn.execute("SELECT 1")


# ---------------------------------------------------------------------------
# table_names introspection
# ---------------------------------------------------------------------------


class TestTableNames:
    """Feature: Table introspection

    As a plugin developer
    I want to list tables in the database
    So that I can verify schema state.
    """

    @pytest.mark.unit
    def test_returns_created_tables(self, tmp_path: Path) -> None:
        """Scenario: table_names lists all user tables
        Given a graph store with schema tables
        When table_names is called
        Then it returns the table names from the schema
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        names = g.table_names()
        assert "items" in names
        g.close()


# ---------------------------------------------------------------------------
# Batch size constant
# ---------------------------------------------------------------------------


class TestBatchSize:
    """Feature: Configurable batch size

    As a plugin developer
    I want a default batch size for bulk inserts
    So that large datasets are inserted efficiently.
    """

    @pytest.mark.unit
    def test_default_batch_size_is_450(self, tmp_path: Path) -> None:
        """Scenario: Default batch size
        Given a subclass without custom _batch_size
        When the graph store is initialized
        Then _batch_size is 450
        """
        db = tmp_path / "test.db"
        g = _TestGraph(str(db))
        assert g._batch_size == 450
        g.close()

    @pytest.mark.unit
    def test_custom_batch_size(self, tmp_path: Path) -> None:
        """Scenario: Custom batch size
        Given a subclass with _batch_size = 100
        When the graph store is initialized
        Then _batch_size is 100
        """

        class _SmallBatch(SqliteGraphBase):
            _schema_sql = _TEST_SCHEMA
            _batch_size = 100

        db = tmp_path / "test.db"
        g = _SmallBatch(str(db))
        assert g._batch_size == 100
        g.close()
