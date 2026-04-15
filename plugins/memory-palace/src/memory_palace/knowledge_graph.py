"""SQLite-backed knowledge graph with temporal triples and synapse mechanics.

Stores entities, residencies, triples (with validity windows), synapses
(with strength/decay), journeys, and waypoints.  Inherits connection
management, WAL mode, FTS5 fallback, and context manager protocol from
``leyline.sqlite_graph_base.SqliteGraphBase``.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any

try:
    from leyline.sqlite_graph_base import SqliteGraphBase
except ImportError:  # pragma: no cover -- standalone fallback
    # Minimal inline base when leyline is not installed.
    import sqlite3 as _sqlite3
    from pathlib import Path as _Path

    class SqliteGraphBase:  # type: ignore[no-redef]  # fallback when leyline not installed
        """Minimal fallback for connection management."""

        _schema_sql: str = ""
        _fts_create_sql: str = ""
        _batch_size: int = 450

        def __init__(self, db_path: str | _Path) -> None:
            """Open a SQLite connection with WAL mode and foreign keys."""
            self._db_path = str(db_path)
            self._conn: _sqlite3.Connection = _sqlite3.connect(self._db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = _sqlite3.Row
            self._has_fts: bool = False
            try:
                self._init_schema()
            except Exception:
                self._conn.close()
                raise

        def _init_schema(self) -> None:
            self._conn.executescript(self._schema_sql)
            if self._fts_create_sql:
                try:
                    self._conn.executescript(self._fts_create_sql)
                    self._has_fts = True
                except _sqlite3.OperationalError as exc:
                    _log.warning("FTS5 unavailable: %s", exc)
            self._conn.commit()

        def close(self) -> None:
            """Close the database connection."""
            self._conn.close()

        def __enter__(self) -> SqliteGraphBase:  # type: ignore[override]  # simpler signature for fallback
            """Enter context manager."""
            return self

        def __exit__(self, *exc: object) -> None:
            """Exit context manager and close connection."""
            self.close()

        def table_names(self) -> list[str]:
            """Return names of all tables in the database."""
            rows = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            return [r["name"] for r in rows]


_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);

CREATE TABLE IF NOT EXISTS residencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    palace_id TEXT NOT NULL,
    room_id TEXT DEFAULT '',
    role TEXT NOT NULL DEFAULT 'patron',
    status TEXT NOT NULL DEFAULT 'active',
    arrived_at TEXT NOT NULL,
    last_active TEXT NOT NULL,
    UNIQUE(entity_id, palace_id, role)
);

CREATE INDEX IF NOT EXISTS idx_res_entity ON residencies(entity_id);
CREATE INDEX IF NOT EXISTS idx_res_palace ON residencies(palace_id);
CREATE INDEX IF NOT EXISTS idx_res_role ON residencies(role);

CREATE TABLE IF NOT EXISTS triples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_id TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    valid_from TEXT DEFAULT '',
    valid_to TEXT DEFAULT '',
    source TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_triples_subj ON triples(subject_id);
CREATE INDEX IF NOT EXISTS idx_triples_obj ON triples(object_id);
CREATE INDEX IF NOT EXISTS idx_triples_pred ON triples(predicate);

CREATE TABLE IF NOT EXISTS synapses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    strength REAL DEFAULT 0.1,
    traversal_count INTEGER DEFAULT 0,
    last_traversed TEXT DEFAULT '',
    decay_curve TEXT DEFAULT 'log',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_syn_src ON synapses(source_id);
CREATE INDEX IF NOT EXISTS idx_syn_tgt ON synapses(target_id);

CREATE TABLE IF NOT EXISTS journeys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    trigger TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    completed_at TEXT DEFAULT '',
    outcome TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_journeys_entity ON journeys(entity_id);

CREATE TABLE IF NOT EXISTS waypoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journey_id INTEGER NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    palace_id TEXT NOT NULL,
    room_id TEXT DEFAULT '',
    arrived_at TEXT NOT NULL,
    departed_at TEXT DEFAULT '',
    entity_delta TEXT DEFAULT '{}',
    palace_delta TEXT DEFAULT '{}',
    synapse_id INTEGER DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_wp_journey ON waypoints(journey_id);

CREATE TABLE IF NOT EXISTS tier_assignments (
    entity_id TEXT PRIMARY KEY,
    tier INTEGER NOT NULL DEFAULT 3,
    score REAL DEFAULT 0.0,
    assigned_at TEXT NOT NULL,
    reason TEXT DEFAULT ''
);
"""

_FTS_CREATE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    entity_id,
    name,
    entity_type,
    tokenize='porter unicode61'
);
"""

_FTS_SYNC_SQL = """
INSERT OR REPLACE INTO entities_fts(entity_id, name, entity_type)
VALUES (?, ?, ?);
"""

_FTS_DELETE_SQL = """
DELETE FROM entities_fts WHERE entity_id = ?;
"""


class KnowledgeGraph(SqliteGraphBase):
    """Persistent knowledge graph backed by SQLite."""

    _schema_sql = _SCHEMA_SQL
    _fts_create_sql = _FTS_CREATE_SQL

    # ------------------------------------------------------------------
    # Entity CRUD
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Insert or update an entity."""
        now = self._now()
        meta_json = json.dumps(metadata or {})
        self._conn.execute(
            """INSERT INTO entities (entity_id, entity_type, name, metadata,
                                     created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(entity_id) DO UPDATE SET
                 entity_type=excluded.entity_type,
                 name=excluded.name,
                 metadata=excluded.metadata,
                 updated_at=excluded.updated_at""",
            (entity_id, entity_type, name, meta_json, now, now),
        )
        if self._has_fts:
            self._conn.execute(_FTS_SYNC_SQL, (entity_id, name, entity_type))
        self._conn.commit()

    def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """Fetch a single entity by ID."""
        row = self._conn.execute(
            "SELECT * FROM entities WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_entities_by_type(self, entity_type: str) -> list[dict[str, Any]]:
        """Fetch all entities of a given type."""
        rows = self._conn.execute(
            "SELECT * FROM entities WHERE entity_type = ?", (entity_type,)
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_entity(self, entity_id: str) -> None:
        """Delete an entity and its FTS entry."""
        self._conn.execute("DELETE FROM entities WHERE entity_id = ?", (entity_id,))
        if self._has_fts:
            self._conn.execute(_FTS_DELETE_SQL, (entity_id,))
        self._conn.commit()

    def entity_count(self) -> int:
        """Return total entity count."""
        row = self._conn.execute("SELECT COUNT(*) FROM entities").fetchone()
        return row[0] if row else 0

    def bulk_upsert_entities(self, entities: list[dict[str, Any]]) -> None:
        """Batch-insert entities for performance."""
        now = self._now()
        for i in range(0, len(entities), self._batch_size):
            batch = entities[i : i + self._batch_size]
            for e in batch:
                meta_json = json.dumps(e.get("metadata", {}))
                self._conn.execute(
                    """INSERT INTO entities
                       (entity_id, entity_type, name, metadata,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(entity_id) DO UPDATE SET
                         entity_type=excluded.entity_type,
                         name=excluded.name,
                         metadata=excluded.metadata,
                         updated_at=excluded.updated_at""",
                    (
                        e["entity_id"],
                        e["entity_type"],
                        e["name"],
                        meta_json,
                        now,
                        now,
                    ),
                )
                if self._has_fts:
                    self._conn.execute(
                        _FTS_SYNC_SQL,
                        (e["entity_id"], e["name"], e["entity_type"]),
                    )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Residencies
    # ------------------------------------------------------------------

    def add_residency(
        self,
        entity_id: str,
        palace_id: str,
        room_id: str = "",
        role: str = "patron",
        status: str = "active",
    ) -> None:
        """Add an entity residency in a palace. Duplicates are ignored."""
        now = self._now()
        self._conn.execute(
            """INSERT INTO residencies
               (entity_id, palace_id, room_id, role, status,
                arrived_at, last_active)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(entity_id, palace_id, role) DO UPDATE SET
                 room_id=excluded.room_id,
                 status=excluded.status,
                 last_active=excluded.last_active""",
            (entity_id, palace_id, room_id, role, status, now, now),
        )
        self._conn.commit()

    def get_residencies(self, entity_id: str) -> list[dict[str, Any]]:
        """Get all residencies for an entity."""
        rows = self._conn.execute(
            "SELECT * FROM residencies WHERE entity_id = ?", (entity_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_residents_in_palace(self, palace_id: str) -> list[dict[str, Any]]:
        """Get all entities residing in a palace."""
        rows = self._conn.execute(
            "SELECT * FROM residencies WHERE palace_id = ?", (palace_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_messengers(self) -> list[dict[str, Any]]:
        """Get entities with messenger role in multiple palaces."""
        rows = self._conn.execute(
            """SELECT entity_id, COUNT(DISTINCT palace_id) as palace_count
               FROM residencies
               WHERE role = 'messenger'
               GROUP BY entity_id
               HAVING palace_count >= 2"""
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Triples (temporal facts)
    # ------------------------------------------------------------------

    def add_triple(  # noqa: PLR0913 - triple requires subject, predicate, object plus metadata
        self,
        subject_id: str,
        predicate: str,
        object_id: str,
        confidence: float = 1.0,
        valid_from: str = "",
        valid_to: str = "",
        source: str = "",
    ) -> int:
        """Add a temporal triple. Returns the triple ID."""
        now = self._now()
        cur = self._conn.execute(
            """INSERT INTO triples
               (subject_id, predicate, object_id, confidence,
                valid_from, valid_to, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                subject_id,
                predicate,
                object_id,
                confidence,
                valid_from,
                valid_to,
                source,
                now,
            ),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_triples_from(self, subject_id: str) -> list[dict[str, Any]]:
        """Get all triples where entity is the subject."""
        rows = self._conn.execute(
            "SELECT * FROM triples WHERE subject_id = ?", (subject_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_active_triples_from(self, subject_id: str) -> list[dict[str, Any]]:
        """Get currently active triples (no valid_to set)."""
        rows = self._conn.execute(
            """SELECT * FROM triples
               WHERE subject_id = ? AND (valid_to = '' OR valid_to IS NULL)""",
            (subject_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def invalidate_triple(self, triple_id: int, valid_to: str = "") -> None:
        """Mark a triple as no longer valid."""
        if not valid_to:
            valid_to = self._now()
        self._conn.execute(
            "UPDATE triples SET valid_to = ? WHERE id = ?",
            (valid_to, triple_id),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Synapses (weighted links)
    # ------------------------------------------------------------------

    def create_synapse(
        self,
        source_id: str,
        target_id: str,
        strength: float = 0.1,
        decay_curve: str = "log",
    ) -> int:
        """Create a synapse between two entities. Returns synapse ID."""
        now = self._now()
        cur = self._conn.execute(
            """INSERT INTO synapses
               (source_id, target_id, strength, decay_curve, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (source_id, target_id, strength, decay_curve, now),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_synapse(self, synapse_id: int) -> dict[str, Any] | None:
        """Fetch a synapse by ID."""
        row = self._conn.execute(
            "SELECT * FROM synapses WHERE id = ?", (synapse_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_synapses_from(self, source_id: str) -> list[dict[str, Any]]:
        """Get all outgoing synapses from an entity."""
        rows = self._conn.execute(
            "SELECT * FROM synapses WHERE source_id = ?", (source_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def strengthen_synapse(self, synapse_id: int, delta: float) -> None:
        """Increase synapse strength (capped at 1.0) and bump traversal count."""
        now = self._now()
        self._conn.execute(
            """UPDATE synapses SET
                 strength = MIN(1.0, strength + ?),
                 traversal_count = traversal_count + 1,
                 last_traversed = ?
               WHERE id = ?""",
            (delta, now, synapse_id),
        )
        self._conn.commit()

    def synapse_count(self) -> int:
        """Return total synapse count."""
        row = self._conn.execute("SELECT COUNT(*) FROM synapses").fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Journeys and Waypoints
    # ------------------------------------------------------------------

    def create_journey(
        self,
        entity_id: str,
        trigger: str = "",
    ) -> int:
        """Start a new journey. Returns journey ID."""
        now = self._now()
        cur = self._conn.execute(
            """INSERT INTO journeys (entity_id, trigger, started_at)
               VALUES (?, ?, ?)""",
            (entity_id, trigger, now),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_journey(self, journey_id: int) -> dict[str, Any] | None:
        """Fetch a journey by ID."""
        row = self._conn.execute(
            "SELECT * FROM journeys WHERE id = ?", (journey_id,)
        ).fetchone()
        return dict(row) if row else None

    def complete_journey(self, journey_id: int, outcome: str) -> None:
        """Mark a journey as completed with an outcome."""
        now = self._now()
        self._conn.execute(
            "UPDATE journeys SET completed_at = ?, outcome = ? WHERE id = ?",
            (now, outcome, journey_id),
        )
        self._conn.commit()

    def add_waypoint(  # noqa: PLR0913 - waypoint requires all graph context fields
        self,
        journey_id: int,
        sequence: int,
        palace_id: str,
        room_id: str = "",
        entity_delta: str = "{}",
        palace_delta: str = "{}",
        synapse_id: int | None = None,
    ) -> int:
        """Add a waypoint to a journey. Returns waypoint ID."""
        now = self._now()
        cur = self._conn.execute(
            """INSERT INTO waypoints
               (journey_id, sequence, palace_id, room_id,
                arrived_at, entity_delta, palace_delta, synapse_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                journey_id,
                sequence,
                palace_id,
                room_id,
                now,
                entity_delta,
                palace_delta,
                synapse_id,
            ),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_waypoints(self, journey_id: int) -> list[dict[str, Any]]:
        """Get all waypoints for a journey, ordered by sequence."""
        rows = self._conn.execute(
            """SELECT * FROM waypoints
               WHERE journey_id = ?
               ORDER BY sequence""",
            (journey_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Tier Assignments
    # ------------------------------------------------------------------

    def assign_tier(
        self,
        entity_id: str,
        tier: int,
        score: float = 0.0,
        reason: str = "",
    ) -> None:
        """Assign or update an entity's tier."""
        now = self._now()
        self._conn.execute(
            """INSERT INTO tier_assignments
               (entity_id, tier, score, assigned_at, reason)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(entity_id) DO UPDATE SET
                 tier=excluded.tier,
                 score=excluded.score,
                 assigned_at=excluded.assigned_at,
                 reason=excluded.reason""",
            (entity_id, tier, score, now, reason),
        )
        self._conn.commit()

    def get_tier(self, entity_id: str) -> dict[str, Any] | None:
        """Get the tier assignment for an entity."""
        row = self._conn.execute(
            "SELECT * FROM tier_assignments WHERE entity_id = ?",
            (entity_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_entities_by_tier(self, tier: int) -> list[dict[str, Any]]:
        """Get all entities assigned to a given tier."""
        rows = self._conn.execute(
            "SELECT * FROM tier_assignments WHERE tier = ?", (tier,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # FTS5 Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Full-text search over entity names. Returns matching entities."""
        if not query or not query.strip():
            return []
        if not self._has_fts:
            return self._fallback_search(query, limit)
        try:
            rows = self._conn.execute(
                """SELECT entity_id, name, entity_type,
                          rank
                   FROM entities_fts
                   WHERE entities_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return self._fallback_search(query, limit)

    def _fallback_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """LIKE-based search when FTS5 is unavailable."""
        rows = self._conn.execute(
            """SELECT entity_id, name, entity_type
               FROM entities
               WHERE name LIKE ?
               LIMIT ?""",
            (f"%{query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]
