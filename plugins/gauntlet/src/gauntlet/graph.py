"""SQLite-backed code knowledge graph with BFS traversal and FTS5 search."""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import deque
from pathlib import Path
from typing import Any

from gauntlet.models import EdgeKind, GraphEdge, GraphNode, NodeKind

_log = logging.getLogger(__name__)

_BATCH_SIZE = 450
_MAX_BFS_NODES = 10_000

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    qualified_name TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    language TEXT DEFAULT '',
    parent_name TEXT DEFAULT '',
    params TEXT DEFAULT '',
    return_type TEXT DEFAULT '',
    modifiers TEXT DEFAULT '',
    is_test INTEGER DEFAULT 0,
    file_hash TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file_path);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_qn ON nodes(qualified_name);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    source_qn TEXT NOT NULL,
    target_qn TEXT NOT NULL,
    file_path TEXT DEFAULT '',
    line INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(source_qn);
CREATE INDEX IF NOT EXISTS idx_edges_tgt ON edges(target_qn);
CREATE INDEX IF NOT EXISTS idx_edges_kind ON edges(kind);

CREATE TABLE IF NOT EXISTS flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_point TEXT NOT NULL,
    node_count INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    max_depth INTEGER DEFAULT 0,
    criticality REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS flow_members (
    flow_id INTEGER REFERENCES flows(id) ON DELETE CASCADE,
    node_qn TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fm_flow ON flow_members(flow_id);
CREATE INDEX IF NOT EXISTS idx_fm_node ON flow_members(node_qn);

CREATE TABLE IF NOT EXISTS communities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT '',
    cohesion REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS community_members (
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    node_qn TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cm_comm ON community_members(community_id);
CREATE INDEX IF NOT EXISTS idx_cm_node ON community_members(node_qn);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

_FTS_CREATE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    qualified_name,
    kind,
    file_path,
    language,
    tokenize='porter unicode61'
);
"""


class GraphStore:
    """Persistent code knowledge graph backed by SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(_SCHEMA_SQL)
        try:
            self._conn.executescript(_FTS_CREATE_SQL)
        except sqlite3.OperationalError:
            _log.warning("FTS5 unavailable -- full-text search disabled")
        self._conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> GraphStore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Node CRUD
    # ------------------------------------------------------------------

    def upsert_node(self, node: GraphNode) -> None:
        """Insert or update a single node."""
        self._conn.execute(
            """INSERT INTO nodes
               (kind, qualified_name, file_path, line_start, line_end,
                language, parent_name, params, return_type, modifiers,
                is_test, file_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(qualified_name) DO UPDATE SET
                 kind=excluded.kind,
                 file_path=excluded.file_path,
                 line_start=excluded.line_start,
                 line_end=excluded.line_end,
                 language=excluded.language,
                 parent_name=excluded.parent_name,
                 params=excluded.params,
                 return_type=excluded.return_type,
                 modifiers=excluded.modifiers,
                 is_test=excluded.is_test,
                 file_hash=excluded.file_hash""",
            (
                str(node.kind),
                node.qualified_name,
                node.file_path,
                node.line_start,
                node.line_end,
                node.language,
                node.parent_name,
                node.params_json(),
                node.return_type,
                node.modifiers_json(),
                int(node.is_test),
                node.file_hash,
            ),
        )
        self._conn.commit()

    def get_node(self, qualified_name: str) -> GraphNode | None:
        """Fetch a single node by qualified name."""
        row = self._conn.execute(
            "SELECT * FROM nodes WHERE qualified_name = ?",
            (qualified_name,),
        ).fetchone()
        return self._row_to_node(row) if row else None

    def get_nodes_in_file(self, file_path: str) -> list[GraphNode]:
        """Fetch all nodes in a file."""
        rows = self._conn.execute(
            "SELECT * FROM nodes WHERE file_path = ?",
            (file_path,),
        ).fetchall()
        return [self._row_to_node(r) for r in rows]

    def get_all_nodes(self) -> list[GraphNode]:
        """Fetch all nodes."""
        rows = self._conn.execute("SELECT * FROM nodes").fetchall()
        return [self._row_to_node(r) for r in rows]

    def node_count(self) -> int:
        """Return total node count."""
        row = self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()
        return row[0] if row else 0

    def delete_nodes_in_file(self, file_path: str) -> int:
        """Delete all nodes for a file. Returns count deleted."""
        cur = self._conn.execute("DELETE FROM nodes WHERE file_path = ?", (file_path,))
        self._conn.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Edge CRUD
    # ------------------------------------------------------------------

    def upsert_edge(self, edge: GraphEdge) -> None:
        """Insert an edge, skipping duplicates."""
        self._conn.execute(
            """INSERT INTO edges (kind, source_qn, target_qn, file_path, line)
               SELECT ?, ?, ?, ?, ?
               WHERE NOT EXISTS (
                 SELECT 1 FROM edges
                 WHERE kind = ? AND source_qn = ? AND target_qn = ?
               )""",
            (
                str(edge.kind),
                edge.source_qn,
                edge.target_qn,
                edge.file_path,
                edge.line,
                str(edge.kind),
                edge.source_qn,
                edge.target_qn,
            ),
        )
        self._conn.commit()

    def get_edges_by_source(self, qualified_name: str) -> list[GraphEdge]:
        """Fetch all outgoing edges from a node."""
        rows = self._conn.execute(
            "SELECT * FROM edges WHERE source_qn = ?",
            (qualified_name,),
        ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    def get_edges_by_target(self, qualified_name: str) -> list[GraphEdge]:
        """Fetch all incoming edges to a node."""
        rows = self._conn.execute(
            "SELECT * FROM edges WHERE target_qn = ?",
            (qualified_name,),
        ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    def get_all_edges(self) -> list[GraphEdge]:
        """Fetch all edges."""
        rows = self._conn.execute("SELECT * FROM edges").fetchall()
        return [self._row_to_edge(r) for r in rows]

    def edge_count(self) -> int:
        """Return total edge count."""
        row = self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()
        return row[0] if row else 0

    def delete_edges_in_file(self, file_path: str) -> int:
        """Delete all edges originating from a file."""
        cur = self._conn.execute("DELETE FROM edges WHERE file_path = ?", (file_path,))
        self._conn.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Atomic file storage
    # ------------------------------------------------------------------

    def store_file(
        self,
        file_path: str,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> None:
        """Atomically replace all nodes/edges for a file.

        Maintains the FTS index incrementally: stale entries are removed
        before the node delete and new entries are inserted after the
        batch insert.  If the FTS virtual table does not exist the
        inserts are silently skipped.
        """
        with self._conn:
            # Remove stale FTS entries before deleting nodes
            try:
                self._conn.execute(
                    "DELETE FROM nodes_fts WHERE file_path = ?", (file_path,)
                )
            except sqlite3.OperationalError:
                pass  # FTS unavailable
            self._conn.execute("DELETE FROM nodes WHERE file_path = ?", (file_path,))
            self._conn.execute("DELETE FROM edges WHERE file_path = ?", (file_path,))
            self._batch_insert_nodes(nodes)
            self._batch_insert_edges(edges)
            # Update FTS index incrementally for the new nodes
            for i, node in enumerate(nodes):
                try:
                    self._conn.execute(
                        "INSERT INTO nodes_fts"
                        "(qualified_name, kind, file_path, language)"
                        " VALUES (?, ?, ?, ?)",
                        (
                            node.qualified_name,
                            str(node.kind),
                            node.file_path,
                            node.language,
                        ),
                    )
                except sqlite3.OperationalError:
                    if i == 0:
                        break  # FTS table likely missing, skip all
                    continue  # Individual entry failed, keep going

    def _batch_insert_nodes(self, nodes: list[GraphNode]) -> None:
        for i in range(0, len(nodes), _BATCH_SIZE):
            batch = nodes[i : i + _BATCH_SIZE]
            self._conn.executemany(
                """INSERT OR REPLACE INTO nodes
                   (kind, qualified_name, file_path, line_start, line_end,
                    language, parent_name, params, return_type, modifiers,
                    is_test, file_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        str(n.kind),
                        n.qualified_name,
                        n.file_path,
                        n.line_start,
                        n.line_end,
                        n.language,
                        n.parent_name,
                        n.params_json(),
                        n.return_type,
                        n.modifiers_json(),
                        int(n.is_test),
                        n.file_hash,
                    )
                    for n in batch
                ],
            )

    def _batch_insert_edges(self, edges: list[GraphEdge]) -> None:
        for i in range(0, len(edges), _BATCH_SIZE):
            batch = edges[i : i + _BATCH_SIZE]
            self._conn.executemany(
                """INSERT INTO edges
                   (kind, source_qn, target_qn, file_path, line)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (
                        str(e.kind),
                        e.source_qn,
                        e.target_qn,
                        e.file_path,
                        e.line,
                    )
                    for e in batch
                ],
            )

    # ------------------------------------------------------------------
    # BFS impact radius
    # ------------------------------------------------------------------

    def impact_radius(
        self,
        changed_files: list[str],
        depth: int = 2,
    ) -> list[GraphNode]:
        """BFS from nodes in changed files to find affected nodes."""
        seed_nodes = []
        for fp in changed_files:
            seed_nodes.extend(self.get_nodes_in_file(fp))

        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()

        for node in seed_nodes:
            qn = node.qualified_name
            if qn not in visited:
                visited.add(qn)
                queue.append((qn, 0))

        while queue and len(visited) < _MAX_BFS_NODES:
            current_qn, current_depth = queue.popleft()
            if current_depth >= depth:
                continue

            # Forward edges (things this node calls)
            for edge in self.get_edges_by_source(current_qn):
                if edge.target_qn not in visited:
                    visited.add(edge.target_qn)
                    queue.append((edge.target_qn, current_depth + 1))

            # Reverse edges (things that depend on this node)
            for edge in self.get_edges_by_target(current_qn):
                if edge.source_qn not in visited:
                    visited.add(edge.source_qn)
                    queue.append((edge.source_qn, current_depth + 1))

        result: list[GraphNode] = []
        for qn in visited:
            found = self.get_node(qn)
            if found:
                result.append(found)
        return result

    # ------------------------------------------------------------------
    # FTS5 search
    # ------------------------------------------------------------------

    def rebuild_fts(self) -> int:
        """Drop and rebuild the FTS5 index. Returns indexed count."""
        try:
            self._conn.execute("DROP TABLE IF EXISTS nodes_fts")
            self._conn.executescript(_FTS_CREATE_SQL)
        except sqlite3.OperationalError:
            return 0

        rows = self._conn.execute(
            "SELECT qualified_name, kind, file_path, language FROM nodes"
        ).fetchall()

        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i : i + _BATCH_SIZE]
            self._conn.executemany(
                "INSERT INTO nodes_fts (qualified_name, kind, file_path, language) "
                "VALUES (?, ?, ?, ?)",
                [(r[0], r[1], r[2], r[3]) for r in batch],
            )
        self._conn.commit()
        return len(rows)

    def search_fts(
        self,
        query: str,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[GraphNode]:
        """Search nodes via FTS5 with BM25 ranking."""
        sanitized = _sanitize_fts_query(query)
        if not sanitized:
            return []

        try:
            rows = self._conn.execute(
                """SELECT qualified_name, rank
                   FROM nodes_fts
                   WHERE nodes_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (sanitized, limit * 3),
            ).fetchall()
        except sqlite3.OperationalError:
            return self._fallback_like_search(query, kind, limit)

        results = []
        for row in rows:
            node = self.get_node(row[0])
            if node and (kind is None or str(node.kind) == kind):
                results.append(node)
                if len(results) >= limit:
                    break
        return results

    def _fallback_like_search(
        self,
        query: str,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[GraphNode]:
        """LIKE-based fallback when FTS5 fails."""
        pattern = f"%{query}%"
        if kind:
            rows = self._conn.execute(
                "SELECT * FROM nodes WHERE qualified_name LIKE ? AND kind = ? LIMIT ?",
                (pattern, kind, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM nodes WHERE qualified_name LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
        return [self._row_to_node(r) for r in rows]

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, key: str) -> str | None:
        """Get a metadata value."""
        row = self._conn.execute(
            "SELECT value FROM metadata WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata value."""
        self._conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Flow storage
    # ------------------------------------------------------------------

    def store_flows(self, flows: list[dict[str, Any]]) -> None:
        """Replace all stored flows."""
        with self._conn:
            self._conn.execute("DELETE FROM flow_members")
            self._conn.execute("DELETE FROM flows")
            for flow in flows:
                cur = self._conn.execute(
                    """INSERT INTO flows
                       (entry_point, node_count, file_count,
                        max_depth, criticality)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        flow["entry_point"],
                        flow["node_count"],
                        flow["file_count"],
                        flow["max_depth"],
                        flow["criticality"],
                    ),
                )
                flow_id = cur.lastrowid
                for qn in flow.get("node_qns", []):
                    self._conn.execute(
                        "INSERT INTO flow_members (flow_id, node_qn) VALUES (?, ?)",
                        (flow_id, qn),
                    )

    def get_flows_containing(self, qualified_name: str) -> list[dict[str, Any]]:
        """Get flows that contain a given node."""
        rows = self._conn.execute(
            """SELECT f.* FROM flows f
               JOIN flow_members fm ON f.id = fm.flow_id
               WHERE fm.node_qn = ?""",
            (qualified_name,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Community storage
    # ------------------------------------------------------------------

    def store_communities(self, communities: list[dict[str, Any]]) -> None:
        """Replace all stored communities."""
        with self._conn:
            self._conn.execute("DELETE FROM community_members")
            self._conn.execute("DELETE FROM communities")
            for comm in communities:
                cur = self._conn.execute(
                    "INSERT INTO communities (name, cohesion) VALUES (?, ?)",
                    (comm.get("name", ""), comm.get("cohesion", 0.0)),
                )
                comm_id = cur.lastrowid
                for qn in comm.get("node_qns", []):
                    self._conn.execute(
                        "INSERT INTO community_members (community_id, node_qn) "
                        "VALUES (?, ?)",
                        (comm_id, qn),
                    )

    def get_community_for_node(self, qualified_name: str) -> int | None:
        """Get the community ID for a node, or None."""
        row = self._conn.execute(
            "SELECT community_id FROM community_members WHERE node_qn = ?",
            (qualified_name,),
        ).fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Row conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> GraphNode:
        params_raw = row["params"]
        params = json.loads(params_raw) if params_raw else {}
        mods_raw = row["modifiers"]
        modifiers = json.loads(mods_raw) if mods_raw else []

        return GraphNode(
            kind=NodeKind(row["kind"]),
            qualified_name=row["qualified_name"],
            file_path=row["file_path"],
            line_start=row["line_start"],
            line_end=row["line_end"],
            language=row["language"] or "",
            parent_name=row["parent_name"] or "",
            params=params,
            return_type=row["return_type"] or "",
            modifiers=modifiers,
            is_test=bool(row["is_test"]),
            file_hash=row["file_hash"] or "",
        )

    @staticmethod
    def _row_to_edge(row: sqlite3.Row) -> GraphEdge:
        return GraphEdge(
            kind=EdgeKind(row["kind"]),
            source_qn=row["source_qn"],
            target_qn=row["target_qn"],
            file_path=row["file_path"] or "",
            line=row["line"] or 0,
        )


def _sanitize_fts_query(query: str) -> str:
    """Escape FTS5 special characters."""
    for ch in '+-*()"':
        query = query.replace(ch, " ")
    return " ".join(query.split())
