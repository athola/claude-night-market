"""Shared SQLite graph infrastructure for plugins that store graph data.

Provides connection management (WAL mode, foreign keys, row factory),
FTS5 table creation with graceful fallback, batch insert sizing, and
context manager protocol.  Subclasses supply their own schema DDL and
FTS DDL via the ``_schema_sql`` and ``_fts_create_sql`` class
attributes (or constructor overrides).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Self

_log = logging.getLogger(__name__)

_BATCH_SIZE = 450


class SqliteGraphBase:
    """Base class for SQLite-backed graph stores.

    Handles the boilerplate every graph store repeats:

    * Open a connection with WAL journal mode and foreign keys.
    * Execute the main schema DDL (``_schema_sql``).
    * Attempt to create FTS5 virtual tables (``_fts_create_sql``),
      falling back silently when the extension is unavailable.
    * Expose ``close()``, ``__enter__``, and ``__exit__``.

    Subclasses **must** set ``_schema_sql`` (the core DDL) and
    *may* set ``_fts_create_sql`` (the FTS5 virtual table DDL).
    """

    _schema_sql: str = ""
    _fts_create_sql: str = ""

    # Subclasses can override with a smaller or larger value.
    _batch_size: int = _BATCH_SIZE

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = sqlite3.Row
        self._has_fts: bool = False
        try:
            self._init_schema()
        except Exception:
            self._conn.close()
            raise

    def _init_schema(self) -> None:
        """Create core tables then attempt FTS5 tables."""
        self._conn.executescript(self._schema_sql)
        if self._fts_create_sql:
            try:
                self._conn.executescript(self._fts_create_sql)
                self._has_fts = True
            except sqlite3.OperationalError as exc:
                _log.warning("FTS5 unavailable: %s", exc)
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager and close connection."""
        self.close()

    def table_names(self) -> list[str]:
        """Return all table names in the database."""
        rows = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return [r["name"] for r in rows]
