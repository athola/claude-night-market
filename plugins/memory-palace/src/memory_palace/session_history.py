"""Session history integration for memory-palace.

Persists session summaries and enables cross-session queries.
Stores session records in the palace data directory under a `sessions/`
subdirectory so they are co-located with palace data but clearly separated.
"""

from __future__ import annotations

import contextlib
import fcntl
import fnmatch
import json
import logging
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from memory_palace.palace_repository import _atomic_write_json
from memory_palace.paths import user_data_dir

try:
    from leyline.session_store import (
        SessionStore,
        validate_session_id,
    )
except ImportError:  # pragma: no cover — standalone fallback
    from memory_palace._vendored_leyline_session_store import (
        SessionStore,
        validate_session_id,
    )


# Storage location within the plugin data directory
SESSIONS_DIR = "sessions"
SESSION_INDEX = "session_index.json"

logger = logging.getLogger(__name__)


UNIT_TYPES: frozenset[str] = frozenset({"finding", "decision", "open-thread", "state"})


@dataclass
class SessionUnit:
    """One thread of work from a session, typed by how fast it ages.

    The type is what lets a durable finding and the transient action that
    produced it live on separate decay curves. A unit whose ``open`` field
    is non-empty carries the state of thinking rather than a binary marker.
    """

    thread: str
    type: str
    date: str
    state: str
    why: str = ""
    open: str = ""
    ref: str = ""
    # Paths this claim rests on, declared by the writer. The reader
    # cannot infer them, which is why they are stated at capture time.
    files: list[str] = field(default_factory=list)
    # Content fingerprints of those paths, filled in by the capture
    # path rather than by the writer. A change here is a staleness
    # signal that does not depend on elapsed time.
    file_digests: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reject units the recall path could not rank or supersede.

        Raises TypeError rather than ValueError because both session-store
        loaders catch (JSONDecodeError, KeyError, TypeError); a corrupt
        stored unit then degrades exactly like any other malformed record.
        """
        if self.type not in UNIT_TYPES:
            raise TypeError(
                f"type must be one of {sorted(UNIT_TYPES)}, got {self.type!r}"
            )
        if not self.thread:
            raise TypeError("thread must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the unit to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionUnit:
        """Deserialize a unit, ignoring unknown keys."""
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in known})


def merge_handoff_units(
    existing: list[SessionUnit], incoming: list[SessionUnit]
) -> list[SessionUnit]:
    """Supersede by (thread, type); append anything new, preserving order.

    The Stop hook fires repeatedly and ``record_session`` overwrites by
    session_id, so merging is what keeps captured units from being erased
    on the next turn. A new unit for the same thread AND type replaces the
    old one; the same thread under a different type stays separate, which
    is what the split rule requires.
    """
    merged = list(existing)
    index = {(u.thread, u.type): i for i, u in enumerate(merged)}
    for unit in incoming:
        key = (unit.thread, unit.type)
        if key in index:
            merged[index[key]] = unit
        else:
            index[key] = len(merged)
            merged.append(unit)
    return merged


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
    handoff_units: list[SessionUnit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionRecord:
        """Deserialize a record from a plain dictionary.

        Unknown keys are silently ignored for forward-compatibility.
        """
        known = set(cls.__dataclass_fields__)
        filtered = {k: v for k, v in data.items() if k in known}
        units = filtered.get("handoff_units") or []
        filtered["handoff_units"] = [
            u if isinstance(u, SessionUnit) else SessionUnit.from_dict(u) for u in units
        ]
        return cls(**filtered)


def _started_on_or_before(started_at: str, until: str) -> bool:
    """Compare a start timestamp against an inclusive ISO upper bound.

    A bare date bound ("2026-10-07") covers that whole day, so a session
    that started at 10:00 that day must not sort after it.
    """
    if len(until) == len("YYYY-MM-DD"):
        return started_at[: len(until)] <= until
    return started_at <= until


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


class _SessionRecordStore(SessionStore):
    """SessionStore subclass that serializes/deserializes SessionRecord objects."""

    def _serialize(self, record: Any) -> Any:
        return record.to_dict()

    def _deserialize(self, data: Any) -> Any:
        return SessionRecord.from_dict(data)


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
            # src/memory_palace/ -> the plugin root, then through the
            # persistent root: session records are user data and an
            # install's plugin root is version scoped, so deriving the
            # directory from __file__ alone stranded them on every
            # update (issue #661). Identity in a source checkout.
            data_dir = user_data_dir(Path(__file__).resolve().parents[2])
        self.sessions_dir = data_dir / SESSIONS_DIR
        self.index_path = self.sessions_dir / SESSION_INDEX
        self._store = _SessionRecordStore(self.sessions_dir)

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
                # Corrupted index: the session files are the source of truth.
                # Saved, or every later load would rescan them all.
                rebuilt = self._rebuild_index()
                try:
                    self._save_index(rebuilt)
                except OSError as exc:
                    # The index is a cache; a read must not fail on its write.
                    logger.warning(
                        "session index %s rebuilt but not saved: %s",
                        self.index_path,
                        exc,
                    )
                return rebuilt
        return {"sessions": [], "stats": {"total": 0, "last_updated": None}}

    @staticmethod
    def _index_entry(record: SessionRecord) -> dict[str, Any]:
        """Build the summary row the index keeps for a record."""
        return {
            "session_id": record.session_id,
            "started_at": record.started_at,
            "ended_at": record.ended_at,
            "summary": record.summary[:200],  # truncated for index
            "topics": record.topics,
            "outcome": record.outcome,
            "tags": record.tags,
            "parent_session_id": record.parent_session_id,
        }

    def _rebuild_index(self) -> dict[str, Any]:
        """Rebuild the index by scanning the stored session files."""
        index_stem = Path(SESSION_INDEX).stem
        records = []
        for sid in self._store.list_sessions():
            if sid == index_stem:
                continue
            # The store catches only JSON and shape errors; one file with
            # bad bytes or an unparsable field must not fail every load.
            try:
                records.append(self._store.load(sid))
            except (OSError, ValueError) as exc:
                logger.warning("skipping unreadable session %s: %s", sid, exc)
        loaded = sorted(
            (rec for rec in records if rec is not None),
            key=lambda rec: rec.started_at,
        )
        return {
            "sessions": [self._index_entry(rec) for rec in loaded],
            "stats": {"total": len(loaded), "last_updated": None},
        }

    def _load_record(self, session_id: str) -> SessionRecord | None:
        """Load a record, treating an unsafe stored id as absent."""
        if not validate_session_id(session_id):
            return None
        result: SessionRecord | None = self._store.load(session_id)
        return result

    @contextlib.contextmanager
    def _locked_index(self) -> Iterator[dict[str, Any]]:
        """Load, yield for mutation, and save the index under a file lock.

        Parallel Stop hooks each record a session. An unlocked
        load-modify-save let one writer's stale copy drop the row another
        had just added, and the index is only rebuilt when it is corrupt.
        """
        self._ensure_dirs()
        lock_path = self.index_path.with_name(SESSION_INDEX + ".lock")
        with open(lock_path, "a", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            index = self._load_index()
            yield index
            self._save_index(index)

    def _save_index(self, index: dict[str, Any]) -> None:
        """Persist the session index atomically."""
        index["stats"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        # A per-call temp name: with a fixed one, concurrent writers clobber
        # each other's half-written file before the rename.
        _atomic_write_json(str(self.index_path), index)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_session(self, record: SessionRecord) -> Path:
        """Persist a session record and update the index.

        Args:
            record: The session record to store.

        Returns:
            The path to the written session file.

        Raises:
            ValueError: If the session_id contains unsafe characters.

        """
        if not validate_session_id(record.session_id):
            raise ValueError(f"Invalid session_id: {record.session_id!r}")
        session_file: Path = self._store.save(record.session_id, record)

        with self._locked_index() as index:
            # Remove any stale entry for this session before appending
            index["sessions"] = [
                s for s in index["sessions"] if s.get("session_id") != record.session_id
            ]
            index["sessions"].append(self._index_entry(record))
            index["stats"]["total"] = len(index["sessions"])
        return session_file

    def get_session(self, session_id: str) -> SessionRecord | None:
        """Retrieve a specific session record by ID.

        Args:
            session_id: The identifier of the session to retrieve.

        Returns:
            The ``SessionRecord``, or ``None`` if no such session exists.

        Raises:
            ValueError: If the session_id contains unsafe characters.

        """
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session_id: {session_id!r}")
        return self._load_record(session_id)

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

            if query.until and not _started_on_or_before(
                entry.get("started_at", ""), query.until
            ):
                continue

            # Load full record for deeper filters
            record = self._load_record(entry["session_id"])
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
            Ordered list of ``SessionRecord`` objects from root to leaf,
            or an empty list if no such session exists.

        Raises:
            ValueError: If the session_id contains unsafe characters.

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
            parent = self._load_record(current.parent_session_id)
            if parent is None:
                break
            visited.add(parent.session_id)
            current = parent

        # current is now the chain root; walk forward collecting children.
        # Build a single-pass parent->child index from the stored index so
        # the forward walk is O(n) rather than O(n^2).
        index = self._load_index()
        parent_to_child: dict[str, str] = {}
        for entry in index["sessions"]:
            pid = entry.get("parent_session_id")
            if pid:
                parent_to_child[pid] = entry["session_id"]

        chain: list[SessionRecord] = [current]
        current_id = current.session_id
        seen: set[str] = {current_id}
        while current_id in parent_to_child:
            child_id = parent_to_child[current_id]
            if child_id in seen:
                # Guard against cycles in the index
                break
            child = self._load_record(child_id)
            if child is None:
                break
            chain.append(child)
            seen.add(child_id)
            current_id = child_id

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

        topics: Counter[str] = Counter()
        outcomes: Counter[str] = Counter()
        for s in sessions:
            topics.update(s.get("topics", []))
            outcomes[s.get("outcome", "unknown") or "unknown"] += 1

        return {
            "total": len(sessions),
            "topics": dict(topics.most_common(20)),
            "outcomes": dict(outcomes),
            "first_session": sessions[0].get("started_at"),
            "last_session": sessions[-1].get("started_at"),
        }

    def delete_session(self, session_id: str) -> bool:
        """Delete a session record from storage.

        Args:
            session_id: The identifier of the session to delete.

        Returns:
            ``True`` if the session was deleted, ``False`` if it was
            not found.

        Raises:
            ValueError: If the session_id contains unsafe characters.

        """
        if not validate_session_id(session_id):
            raise ValueError(f"Invalid session_id: {session_id!r}")
        deleted = self._store.delete(session_id)
        if not deleted:
            return False

        with self._locked_index() as index:
            index["sessions"] = [
                s for s in index["sessions"] if s.get("session_id") != session_id
            ]
            index["stats"]["total"] = len(index["sessions"])
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

        with self._locked_index() as index:
            to_remove = [
                s["session_id"]
                for s in index["sessions"]
                if s.get("started_at", "") < cutoff_str
            ]

            for sid in to_remove:
                self._store.delete(sid)

            index["sessions"] = [
                s for s in index["sessions"] if s.get("session_id") not in to_remove
            ]
            index["stats"]["total"] = len(index["sessions"])
        return len(to_remove)
