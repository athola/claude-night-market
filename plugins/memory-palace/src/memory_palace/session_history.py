"""Session history integration for memory-palace.

Persists session summaries and enables cross-session queries.
Stores session records in the palace data directory under a `sessions/`
subdirectory so they are co-located with palace data but clearly separated.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Storage location within the plugin data directory
SESSIONS_DIR = "sessions"
SESSION_INDEX = "session_index.json"


@dataclass
class SessionRecord:
    """A record of a single Claude Code session."""

    session_id: str
    started_at: str  # ISO format
    ended_at: str | None = None
    duration_seconds: float = 0.0
    summary: str = ""
    topics: list[str] = field(default_factory=list)
    skills_used: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)
    outcome: str = ""  # completed, interrupted, continued
    context_usage_peak: float = 0.0  # 0.0-1.0
    continuation_count: int = 0
    parent_session_id: str | None = None  # for continuation chains
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionRecord:
        """Deserialize a record from a plain dictionary.

        Unknown keys are silently ignored for forward-compatibility.
        """
        known = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class SessionQuery:
    """Query parameters for searching session history."""

    topic: str | None = None
    skill: str | None = None
    tag: str | None = None
    since: str | None = None  # ISO date string (inclusive lower bound)
    until: str | None = None  # ISO date string (inclusive upper bound)
    file_pattern: str | None = None  # fnmatch glob applied to files_modified
    limit: int = 20
    offset: int = 0


class SessionHistoryManager:
    """Manage persistent session history records.

    Records are stored as individual JSON files under ``data/sessions/``.
    A lightweight index file (``session_index.json``) holds summary data
    for quick filtering without loading every record.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize the manager.

        Args:
            data_dir: Base data directory for the plugin.  Defaults to the
                ``data/`` directory co-located with the installed package.

        """
        if data_dir is None:
            # Resolve relative to this source file: src/memory_palace/ -> data/
            data_dir = Path(__file__).resolve().parents[2] / "data"
        self.sessions_dir = data_dir / SESSIONS_DIR
        self.index_path = self.sessions_dir / SESSION_INDEX
        self._ensure_dirs()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        """Create the sessions storage directory if it does not exist."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, Any]:
        """Load the session index from disk, returning a default if absent."""
        if self.index_path.exists():
            try:
                result: dict[str, Any] = json.loads(
                    self.index_path.read_text(encoding="utf-8")
                )
                return result
            except (json.JSONDecodeError, OSError):
                # Corrupted index: return a clean default and let it be rebuilt
                return {"sessions": [], "stats": {"total": 0, "last_updated": None}}
        return {"sessions": [], "stats": {"total": 0, "last_updated": None}}

    def _save_index(self, index: dict[str, Any]) -> None:
        """Persist the session index to disk."""
        index["stats"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_session(self, record: SessionRecord) -> Path:
        """Persist a session record and update the index.

        Args:
            record: The session record to store.

        Returns:
            The path to the written session file.

        """
        session_file = self.sessions_dir / f"{record.session_id}.json"
        session_file.write_text(
            json.dumps(record.to_dict(), indent=2), encoding="utf-8"
        )

        index = self._load_index()
        # Remove any stale entry for this session before appending
        index["sessions"] = [
            s for s in index["sessions"] if s.get("session_id") != record.session_id
        ]
        index["sessions"].append(
            {
                "session_id": record.session_id,
                "started_at": record.started_at,
                "ended_at": record.ended_at,
                "summary": record.summary[:200],  # truncated for index
                "topics": record.topics,
                "outcome": record.outcome,
                "tags": record.tags,
            }
        )
        index["stats"]["total"] = len(index["sessions"])
        self._save_index(index)
        return session_file

    def get_session(self, session_id: str) -> SessionRecord | None:
        """Retrieve a specific session record by ID.

        Args:
            session_id: The identifier of the session to retrieve.

        Returns:
            The ``SessionRecord``, or ``None`` if not found.

        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            return SessionRecord.from_dict(data)
        except (json.JSONDecodeError, TypeError):
            return None

    def query_sessions(self, query: SessionQuery) -> list[SessionRecord]:
        """Search session history with flexible filters.

        Index entries are checked first for cheap filters (topic, tag,
        date range).  The full record is loaded only when deeper checks are
        needed (skill, file pattern).

        Args:
            query: Filter and pagination parameters.

        Returns:
            A list of matching ``SessionRecord`` objects, most recent first.

        """
        index = self._load_index()
        results: list[SessionRecord] = []

        for entry in reversed(index["sessions"]):  # most recent first
            # Cheap index-level filters
            if query.topic:
                topics_text = " ".join(entry.get("topics", [])).lower()
                if query.topic.lower() not in topics_text:
                    continue

            if query.tag and query.tag not in entry.get("tags", []):
                continue

            if query.since and entry.get("started_at", "") < query.since:
                continue

            if query.until and entry.get("started_at", "") > query.until:
                continue

            # Load full record for deeper filters
            record = self.get_session(entry["session_id"])
            if record is None:
                continue

            if query.skill and query.skill not in record.skills_used:
                continue

            if query.file_pattern and not any(
                fnmatch.fnmatch(f, query.file_pattern) for f in record.files_modified
            ):
                continue

            results.append(record)

        # Apply pagination
        return results[query.offset : query.offset + query.limit]

    def get_recent_sessions(self, count: int = 10) -> list[SessionRecord]:
        """Return the N most recent sessions.

        Args:
            count: Maximum number of sessions to return.

        Returns:
            A list of ``SessionRecord`` objects, most recent first.

        """
        return self.query_sessions(SessionQuery(limit=count))

    def get_session_chain(self, session_id: str) -> list[SessionRecord]:
        """Return a session and all its continuations in chronological order.

        Walks ``parent_session_id`` links backward to find the root of the
        chain, then traverses forward through child sessions.

        Args:
            session_id: Any session in the chain.

        Returns:
            Ordered list of ``SessionRecord`` objects from root to leaf.

        """
        root = self.get_session(session_id)
        if root is None:
            return []

        # Walk backward to find the chain root
        current = root
        visited: set[str] = {current.session_id}
        while current.parent_session_id:
            if current.parent_session_id in visited:
                # Guard against cycles
                break
            parent = self.get_session(current.parent_session_id)
            if parent is None:
                break
            visited.add(parent.session_id)
            current = parent

        # current is now the chain root; walk forward collecting children
        chain: list[SessionRecord] = [current]
        index = self._load_index()
        all_ids = {s["session_id"] for s in index["sessions"]}

        current_id = current.session_id
        seen: set[str] = {current_id}
        while True:
            found_child = False
            for sid in all_ids:
                if sid in seen:
                    continue
                record = self.get_session(sid)
                if record and record.parent_session_id == current_id:
                    chain.append(record)
                    seen.add(sid)
                    current_id = record.session_id
                    found_child = True
                    break
            if not found_child:
                break

        return chain

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate statistics across all stored sessions.

        Returns:
            A dictionary with ``total``, ``topics`` (frequency map),
            ``outcomes`` (frequency map), ``first_session``, and
            ``last_session`` keys.

        """
        index = self._load_index()
        sessions = index.get("sessions", [])

        if not sessions:
            return {
                "total": 0,
                "topics": {},
                "outcomes": {},
                "first_session": None,
                "last_session": None,
            }

        topics: dict[str, int] = {}
        outcomes: dict[str, int] = {}
        for s in sessions:
            for topic in s.get("topics", []):
                topics[topic] = topics.get(topic, 0) + 1
            outcome = s.get("outcome", "unknown") or "unknown"
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

        return {
            "total": len(sessions),
            "topics": dict(sorted(topics.items(), key=lambda x: -x[1])[:20]),
            "outcomes": outcomes,
            "first_session": sessions[0].get("started_at"),
            "last_session": sessions[-1].get("started_at"),
        }

    def delete_session(self, session_id: str) -> bool:
        """Delete a session record from storage.

        Args:
            session_id: The identifier of the session to delete.

        Returns:
            ``True`` if the session was deleted, ``False`` if it was not found.

        """
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return False

        session_file.unlink()

        index = self._load_index()
        index["sessions"] = [
            s for s in index["sessions"] if s.get("session_id") != session_id
        ]
        index["stats"]["total"] = len(index["sessions"])
        self._save_index(index)
        return True

    def prune_old_sessions(self, max_age_days: int = 90) -> int:
        """Remove session records older than ``max_age_days``.

        Args:
            max_age_days: Sessions with ``started_at`` older than this many
                days will be removed.

        Returns:
            The number of sessions pruned.

        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()

        index = self._load_index()
        to_remove = [
            s["session_id"]
            for s in index["sessions"]
            if s.get("started_at", "") < cutoff_str
        ]

        for sid in to_remove:
            session_file = self.sessions_dir / f"{sid}.json"
            if session_file.exists():
                session_file.unlink()

        index["sessions"] = [
            s for s in index["sessions"] if s.get("session_id") not in to_remove
        ]
        index["stats"]["total"] = len(index["sessions"])
        self._save_index(index)
        return len(to_remove)
