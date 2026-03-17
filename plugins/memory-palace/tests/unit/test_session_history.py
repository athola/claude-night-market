"""Tests for session history integration.

Feature: Persistent session history for memory-palace

As a Claude Code user
I want each session to be recorded and queryable
So that I can review what was done, discover patterns, and resume context
across sessions without relying on ephemeral memory.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from memory_palace.session_history import (
    SessionHistoryManager,
    SessionQuery,
    SessionRecord,
    _validate_session_id,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_RECORD_DEFAULTS: dict = {
    "started_at": "2026-01-01T10:00:00+00:00",
    "ended_at": "2026-01-01T10:30:00+00:00",
    "summary": "Fixed bug in parser",
    "topics": ["parsing", "debugging"],
    "skills_used": ["do-issue"],
    "tools_used": ["Read", "Edit"],
    "files_modified": ["src/parser.py"],
    "key_decisions": ["rewrote tokeniser"],
    "outcome": "completed",
    "context_usage_peak": 0.45,
    "continuation_count": 0,
    "parent_session_id": None,
    "tags": ["bugfix"],
    "metadata": {},
}


def _make_record(session_id: str = "sess-001", **overrides: object) -> SessionRecord:
    fields = {**_RECORD_DEFAULTS, **overrides}
    # Deep-copy mutable defaults so tests stay isolated
    for key in (
        "topics",
        "skills_used",
        "tools_used",
        "files_modified",
        "key_decisions",
        "tags",
        "metadata",
    ):
        val = fields[key]
        if isinstance(val, list):
            fields[key] = list(val)
        elif isinstance(val, dict):
            fields[key] = dict(val)
    return SessionRecord(session_id=session_id, **fields)


# ---------------------------------------------------------------------------
# TestSessionRecord
# ---------------------------------------------------------------------------


class TestSessionRecord:
    """Feature: SessionRecord data class.

    As a developer
    I want a typed, serialisable session record
    So that session data can be stored and restored without loss.
    """

    @pytest.mark.unit
    def test_to_dict_returns_all_fields(self) -> None:
        """Scenario: Serialise a record to a plain dict.

        Given a fully-populated SessionRecord
        When to_dict() is called
        Then every declared field appears in the result.
        """
        record = _make_record()
        result = record.to_dict()

        assert result["session_id"] == "sess-001"
        assert result["summary"] == "Fixed bug in parser"
        assert result["topics"] == ["parsing", "debugging"]
        assert result["outcome"] == "completed"
        assert result["context_usage_peak"] == 0.45

    @pytest.mark.unit
    def test_from_dict_roundtrip(self) -> None:
        """Scenario: Deserialise from dict and round-trip back.

        Given a serialised dict
        When from_dict() constructs a record and to_dict() is called again
        Then the two dicts are equal.
        """
        original = _make_record()
        restored = SessionRecord.from_dict(original.to_dict())
        assert restored.to_dict() == original.to_dict()

    @pytest.mark.unit
    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Scenario: Forward-compatibility with extra fields.

        Given a dict that contains an unrecognised key
        When from_dict() is called
        Then no exception is raised and the known fields are populated.
        """
        data = _make_record().to_dict()
        data["future_field_v2"] = "some_value"
        record = SessionRecord.from_dict(data)
        assert record.session_id == "sess-001"

    @pytest.mark.unit
    def test_defaults_are_sensible(self) -> None:
        """Scenario: Minimal construction with only required fields.

        Given only session_id and started_at are provided
        When a SessionRecord is created
        Then all optional fields have empty / zero defaults.
        """
        record = SessionRecord(
            session_id="minimal",
            started_at="2026-01-01T00:00:00+00:00",
        )
        assert record.ended_at is None
        assert record.duration_seconds == 0.0
        assert record.summary == ""
        assert record.topics == []
        assert record.skills_used == []
        assert record.tools_used == []
        assert record.files_modified == []
        assert record.key_decisions == []
        assert record.outcome == ""
        assert record.context_usage_peak == 0.0
        assert record.continuation_count == 0
        assert record.parent_session_id is None
        assert record.tags == []
        assert record.metadata == {}

    @pytest.mark.unit
    def test_mutable_defaults_are_independent(self) -> None:
        """Scenario: Dataclass mutable default isolation.

        Given two separately constructed records
        When a list on one record is modified
        Then the other record's list is unaffected.
        """
        r1 = SessionRecord(session_id="r1", started_at="2026-01-01T00:00:00+00:00")
        r2 = SessionRecord(session_id="r2", started_at="2026-01-01T00:00:00+00:00")
        r1.topics.append("python")
        assert r2.topics == []


# ---------------------------------------------------------------------------
# TestSessionHistoryManager
# ---------------------------------------------------------------------------


class TestSessionHistoryManager:
    """Feature: SessionHistoryManager persistence.

    As a Claude Code plugin
    I want session records written to disk and retrievable later
    So that history survives across processes and restarts.
    """

    # ------------------------------------------------------------------
    # record_session / get_session
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_record_session_creates_file(self, tmp_path: Path) -> None:
        """Scenario: Store a session record.

        Given a fresh SessionHistoryManager
        When record_session() is called with a valid record
        Then a JSON file named <session_id>.json exists in the sessions dir.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        record = _make_record()
        path = mgr.record_session(record)

        assert path.exists()
        assert path.name == "sess-001.json"

    @pytest.mark.unit
    def test_get_session_returns_record(self, tmp_path: Path) -> None:
        """Scenario: Retrieve a stored session.

        Given a session that has been recorded
        When get_session() is called with its ID
        Then the returned record matches the original.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        original = _make_record()
        mgr.record_session(original)

        retrieved = mgr.get_session("sess-001")
        assert isinstance(retrieved, SessionRecord)
        assert retrieved.session_id == "sess-001"
        assert retrieved.summary == "Fixed bug in parser"

    @pytest.mark.unit
    def test_record_session_updates_index(self, tmp_path: Path) -> None:
        """Scenario: Index is updated after recording.

        Given a fresh SessionHistoryManager
        When two sessions are recorded
        Then the index file exists and contains both session IDs.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1"))
        mgr.record_session(_make_record("s2"))

        index = mgr._load_index()
        ids = [s["session_id"] for s in index["sessions"]]
        assert "s1" in ids
        assert "s2" in ids
        assert index["stats"]["total"] == 2

    @pytest.mark.unit
    def test_record_session_overwrites_existing(self, tmp_path: Path) -> None:
        """Scenario: Re-recording an existing session ID updates the entry.

        Given a session already recorded
        When record_session() is called again with the same ID but different data
        Then the index contains only one entry for that ID with the updated data.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("sess-dup", summary="first"))
        mgr.record_session(_make_record("sess-dup", summary="updated"))

        index = mgr._load_index()
        entries = [s for s in index["sessions"] if s["session_id"] == "sess-dup"]
        assert len(entries) == 1

        retrieved = mgr.get_session("sess-dup")
        assert isinstance(retrieved, SessionRecord)
        assert retrieved.summary == "updated"

    @pytest.mark.unit
    def test_get_session_missing_returns_none(self, tmp_path: Path) -> None:
        """Scenario: Requesting a non-existent session.

        Given an empty SessionHistoryManager
        When get_session() is called with an unknown ID
        Then None is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        assert mgr.get_session("does-not-exist") is None

    # ------------------------------------------------------------------
    # query_sessions — individual filters
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_query_by_topic(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by topic keyword.

        Given two sessions with different topics
        When querying with topic='refactor'
        Then only the session that includes 'refactor' is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", topics=["refactor", "python"]))
        mgr.record_session(_make_record("s2", topics=["bugfix", "rust"]))

        results = mgr.query_sessions(SessionQuery(topic="refactor"))
        assert len(results) == 1
        assert results[0].session_id == "s1"

    @pytest.mark.unit
    def test_query_topic_is_case_insensitive(self, tmp_path: Path) -> None:
        """Scenario: Topic filter ignores case.

        Given a session with topic 'Python'
        When querying with topic='python'
        Then the session is included in results.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", topics=["Python", "Testing"]))

        results = mgr.query_sessions(SessionQuery(topic="python"))
        assert len(results) == 1

    @pytest.mark.unit
    def test_query_by_skill(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by skill used.

        Given two sessions with different skills
        When querying with skill='scribe'
        Then only sessions using 'scribe' are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", skills_used=["scribe", "do-issue"]))
        mgr.record_session(_make_record("s2", skills_used=["do-issue"]))

        results = mgr.query_sessions(SessionQuery(skill="scribe"))
        assert len(results) == 1
        assert results[0].session_id == "s1"

    @pytest.mark.unit
    def test_query_by_tag(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by tag.

        Given sessions with different tags
        When querying with tag='release'
        Then only sessions tagged 'release' are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", tags=["release", "v2"]))
        mgr.record_session(_make_record("s2", tags=["bugfix"]))

        results = mgr.query_sessions(SessionQuery(tag="release"))
        assert len(results) == 1
        assert results[0].session_id == "s1"

    @pytest.mark.unit
    def test_query_by_date_since(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by start date lower bound.

        Given sessions started on different dates
        When querying with since='2026-02-01T00:00:00+00:00'
        Then only sessions on or after that date are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("old", started_at="2026-01-15T00:00:00+00:00"))
        mgr.record_session(_make_record("new", started_at="2026-02-10T00:00:00+00:00"))

        results = mgr.query_sessions(SessionQuery(since="2026-02-01T00:00:00+00:00"))
        ids = [r.session_id for r in results]
        assert "new" in ids
        assert "old" not in ids

    @pytest.mark.unit
    def test_query_by_date_until(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by start date upper bound.

        Given sessions started on different dates
        When querying with until='2026-01-31T23:59:59+00:00'
        Then only sessions on or before that date are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("old", started_at="2026-01-15T00:00:00+00:00"))
        mgr.record_session(_make_record("new", started_at="2026-02-10T00:00:00+00:00"))

        results = mgr.query_sessions(SessionQuery(until="2026-01-31T23:59:59+00:00"))
        ids = [r.session_id for r in results]
        assert "old" in ids
        assert "new" not in ids

    @pytest.mark.unit
    def test_query_by_date_range(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by both since and until.

        Given three sessions at different times
        When querying with a date window that includes only the middle one
        Then exactly that session is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(
            _make_record("early", started_at="2026-01-01T00:00:00+00:00")
        )
        mgr.record_session(_make_record("mid", started_at="2026-03-15T00:00:00+00:00"))
        mgr.record_session(_make_record("late", started_at="2026-06-01T00:00:00+00:00"))

        results = mgr.query_sessions(
            SessionQuery(
                since="2026-02-01T00:00:00+00:00",
                until="2026-04-30T00:00:00+00:00",
            )
        )
        assert len(results) == 1
        assert results[0].session_id == "mid"

    @pytest.mark.unit
    def test_query_by_file_pattern(self, tmp_path: Path) -> None:
        """Scenario: Filter sessions by modified file pattern.

        Given two sessions that modified different files
        When querying with file_pattern='*.py'
        Then only sessions that modified a .py file are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(
            _make_record("s1", files_modified=["src/parser.py", "README.md"])
        )
        mgr.record_session(_make_record("s2", files_modified=["docs/guide.md"]))

        results = mgr.query_sessions(SessionQuery(file_pattern="*.py"))
        assert len(results) == 1
        assert results[0].session_id == "s1"

    @pytest.mark.unit
    def test_query_by_file_pattern_nested_glob(self, tmp_path: Path) -> None:
        """Scenario: File pattern matching with fnmatch semantics.

        Given a session that modified 'plugins/foo/bar.py'
        When querying with file_pattern='plugins/*.py'
        Then the session IS returned (fnmatch's * matches any chars including /).
        When querying with file_pattern='*.md'
        Then the session is NOT returned (no .md files were modified).
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", files_modified=["plugins/foo/bar.py"]))

        # fnmatch * crosses path separators, so plugins/*.py matches plugins/foo/bar.py
        match = mgr.query_sessions(SessionQuery(file_pattern="plugins/*.py"))
        assert len(match) == 1

        no_match = mgr.query_sessions(SessionQuery(file_pattern="*.md"))
        assert len(no_match) == 0

    # ------------------------------------------------------------------
    # query_sessions — pagination
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_query_pagination_limit(self, tmp_path: Path) -> None:
        """Scenario: Limit the number of returned results.

        Given five stored sessions
        When querying with limit=3
        Then exactly 3 records are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        for i in range(5):
            mgr.record_session(_make_record(f"s{i}"))

        results = mgr.query_sessions(SessionQuery(limit=3))
        assert len(results) == 3

    @pytest.mark.unit
    def test_query_pagination_offset(self, tmp_path: Path) -> None:
        """Scenario: Skip the first N results.

        Given five stored sessions recorded in chronological order
        When querying with offset=3, limit=10
        Then 2 records are returned (the oldest two).
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        for i in range(5):
            ts = f"2026-01-0{i + 1}T00:00:00+00:00"
            mgr.record_session(_make_record(f"s{i}", started_at=ts))

        results = mgr.query_sessions(SessionQuery(offset=3, limit=10))
        assert len(results) == 2

    @pytest.mark.unit
    def test_results_are_most_recent_first(self, tmp_path: Path) -> None:
        """Scenario: Default ordering is most recent first.

        Given sessions recorded with ascending timestamps
        When get_recent_sessions() is called
        Then the first result has the latest started_at.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        dates = [
            "2026-01-01T00:00:00+00:00",
            "2026-02-01T00:00:00+00:00",
            "2026-03-01T00:00:00+00:00",
        ]
        for i, d in enumerate(dates):
            mgr.record_session(_make_record(f"s{i}", started_at=d))

        results = mgr.get_recent_sessions(count=3)
        assert results[0].started_at == "2026-03-01T00:00:00+00:00"
        assert results[-1].started_at == "2026-01-01T00:00:00+00:00"

    # ------------------------------------------------------------------
    # get_recent_sessions
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_get_recent_sessions_count(self, tmp_path: Path) -> None:
        """Scenario: Retrieve the N most recent sessions.

        Given 7 stored sessions
        When get_recent_sessions(count=4) is called
        Then exactly 4 records are returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        for i in range(7):
            mgr.record_session(_make_record(f"s{i}"))

        results = mgr.get_recent_sessions(count=4)
        assert len(results) == 4

    @pytest.mark.unit
    def test_get_recent_sessions_empty_store(self, tmp_path: Path) -> None:
        """Scenario: No sessions stored.

        Given an empty SessionHistoryManager
        When get_recent_sessions() is called
        Then an empty list is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        assert mgr.get_recent_sessions() == []

    # ------------------------------------------------------------------
    # get_session_chain
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_get_session_chain_single(self, tmp_path: Path) -> None:
        """Scenario: Chain of one session with no parent or child.

        Given a standalone session
        When get_session_chain() is called
        Then a list containing only that session is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("root"))

        chain = mgr.get_session_chain("root")
        assert len(chain) == 1
        assert chain[0].session_id == "root"

    @pytest.mark.unit
    def test_get_session_chain_continuation(self, tmp_path: Path) -> None:
        """Scenario: A two-session continuation chain.

        Given root -> child (parent_session_id=root)
        When get_session_chain() is called with the child's ID
        Then [root, child] is returned in order.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("root"))
        mgr.record_session(_make_record("child", parent_session_id="root"))

        chain = mgr.get_session_chain("child")
        assert [r.session_id for r in chain] == ["root", "child"]

    @pytest.mark.unit
    def test_get_session_chain_three_levels(self, tmp_path: Path) -> None:
        """Scenario: Three-level chain accessed from the middle.

        Given root -> mid -> leaf
        When get_session_chain() is called with mid's ID
        Then [root, mid, leaf] is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("root"))
        mgr.record_session(_make_record("mid", parent_session_id="root"))
        mgr.record_session(_make_record("leaf", parent_session_id="mid"))

        chain = mgr.get_session_chain("mid")
        assert [r.session_id for r in chain] == ["root", "mid", "leaf"]

    @pytest.mark.unit
    def test_get_session_chain_missing_id(self, tmp_path: Path) -> None:
        """Scenario: Non-existent session ID.

        Given an empty SessionHistoryManager
        When get_session_chain() is called with an unknown ID
        Then an empty list is returned.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        assert mgr.get_session_chain("ghost") == []

    @pytest.mark.unit
    def test_get_session_chain_long_chain(self, tmp_path: Path) -> None:
        """Scenario: Chain correctness at scale.

        Given a linear chain of 120 sessions
        When get_session_chain() is called from the middle
        Then the full chain is returned in order from root to leaf.
        """
        chain_length = 120
        mgr = SessionHistoryManager(data_dir=tmp_path)

        prev_id: str | None = None
        session_ids: list[str] = []
        for i in range(chain_length):
            sid = f"s{i:04d}"
            session_ids.append(sid)
            mgr.record_session(_make_record(sid, parent_session_id=prev_id))
            prev_id = sid

        # Query from the middle of the chain -- should still return the full chain
        mid_id = session_ids[chain_length // 2]
        chain = mgr.get_session_chain(mid_id)

        assert len(chain) == chain_length
        assert [r.session_id for r in chain] == session_ids

    # ------------------------------------------------------------------
    # get_stats
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_get_stats_empty(self, tmp_path: Path) -> None:
        """Scenario: Statistics on an empty store.

        Given no sessions recorded
        When get_stats() is called
        Then total is 0 and aggregates are empty.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        stats = mgr.get_stats()
        assert stats["total"] == 0
        assert stats["topics"] == {}
        assert stats["outcomes"] == {}
        assert stats["first_session"] is None
        assert stats["last_session"] is None

    @pytest.mark.unit
    def test_get_stats_counts_topics(self, tmp_path: Path) -> None:
        """Scenario: Topic frequency aggregation.

        Given sessions with overlapping topics
        When get_stats() is called
        Then each topic's count reflects how many sessions included it.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", topics=["python", "testing"]))
        mgr.record_session(_make_record("s2", topics=["python", "refactor"]))
        mgr.record_session(_make_record("s3", topics=["rust"]))

        stats = mgr.get_stats()
        assert stats["topics"]["python"] == 2
        assert stats["topics"]["testing"] == 1
        assert stats["topics"]["rust"] == 1

    @pytest.mark.unit
    def test_get_stats_counts_outcomes(self, tmp_path: Path) -> None:
        """Scenario: Outcome frequency aggregation.

        Given sessions with different outcomes
        When get_stats() is called
        Then outcomes dict maps outcome -> count.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", outcome="completed"))
        mgr.record_session(_make_record("s2", outcome="completed"))
        mgr.record_session(_make_record("s3", outcome="interrupted"))

        stats = mgr.get_stats()
        assert stats["outcomes"]["completed"] == 2
        assert stats["outcomes"]["interrupted"] == 1

    @pytest.mark.unit
    def test_get_stats_first_and_last(self, tmp_path: Path) -> None:
        """Scenario: First and last session timestamps.

        Given sessions recorded with different start times
        When get_stats() is called
        Then first_session and last_session match the earliest and latest started_at.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("s1", started_at="2026-01-01T00:00:00+00:00"))
        mgr.record_session(_make_record("s2", started_at="2026-06-01T00:00:00+00:00"))

        stats = mgr.get_stats()
        assert stats["first_session"] == "2026-01-01T00:00:00+00:00"
        assert stats["last_session"] == "2026-06-01T00:00:00+00:00"

    # ------------------------------------------------------------------
    # delete_session
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_delete_session_removes_file_and_index(self, tmp_path: Path) -> None:
        """Scenario: Delete a recorded session.

        Given a session that exists
        When delete_session() is called
        Then the file is gone and the index no longer references the session.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("to-delete"))

        result = mgr.delete_session("to-delete")

        assert result is True
        assert mgr.get_session("to-delete") is None
        index = mgr._load_index()
        ids = [s["session_id"] for s in index["sessions"]]
        assert "to-delete" not in ids

    @pytest.mark.unit
    def test_delete_session_returns_false_when_missing(self, tmp_path: Path) -> None:
        """Scenario: Deleting a session that does not exist.

        Given an empty store
        When delete_session() is called
        Then False is returned and no exception is raised.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        assert mgr.delete_session("ghost") is False

    @pytest.mark.unit
    def test_delete_session_leaves_others_intact(self, tmp_path: Path) -> None:
        """Scenario: Deleting one session does not affect others.

        Given two sessions recorded
        When only one is deleted
        Then the other is still retrievable.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(_make_record("keep"))
        mgr.record_session(_make_record("remove"))

        mgr.delete_session("remove")

        assert isinstance(mgr.get_session("keep"), SessionRecord)
        assert mgr.get_session("remove") is None

    # ------------------------------------------------------------------
    # prune_old_sessions
    # ------------------------------------------------------------------

    @pytest.mark.unit
    def test_prune_removes_old_sessions(self, tmp_path: Path) -> None:
        """Scenario: Age-based pruning removes stale sessions.

        Given a session started 100 days ago and one started today
        When prune_old_sessions(max_age_days=90) is called
        Then the old session is removed and the recent one is kept.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        new_ts = datetime.now(timezone.utc).isoformat()

        mgr.record_session(_make_record("old-sess", started_at=old_ts))
        mgr.record_session(_make_record("new-sess", started_at=new_ts))

        pruned = mgr.prune_old_sessions(max_age_days=90)

        assert pruned == 1
        assert mgr.get_session("old-sess") is None
        assert isinstance(mgr.get_session("new-sess"), SessionRecord)

    @pytest.mark.unit
    def test_prune_returns_count_of_removed(self, tmp_path: Path) -> None:
        """Scenario: Prune return value.

        Given three sessions all older than the threshold
        When prune_old_sessions() is called
        Then the return value equals 3.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        for i in range(3):
            mgr.record_session(_make_record(f"old-{i}", started_at=old_ts))

        pruned = mgr.prune_old_sessions(max_age_days=90)
        assert pruned == 3

    @pytest.mark.unit
    def test_prune_empty_store_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Pruning an empty store.

        Given no sessions recorded
        When prune_old_sessions() is called
        Then 0 is returned and no exception is raised.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        assert mgr.prune_old_sessions(max_age_days=90) == 0

    @pytest.mark.unit
    def test_prune_updates_index_total(self, tmp_path: Path) -> None:
        """Scenario: Index total is updated after pruning.

        Given two old sessions and one new session
        When prune_old_sessions() is called
        Then the index total reflects only the surviving sessions.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        new_ts = datetime.now(timezone.utc).isoformat()
        mgr.record_session(_make_record("old1", started_at=old_ts))
        mgr.record_session(_make_record("old2", started_at=old_ts))
        mgr.record_session(_make_record("new1", started_at=new_ts))

        mgr.prune_old_sessions(max_age_days=90)

        index = mgr._load_index()
        assert index["stats"]["total"] == 1


# ---------------------------------------------------------------------------
# TestSessionIdSanitization
# ---------------------------------------------------------------------------


class TestSessionIdSanitization:
    """Feature: Session ID path-traversal prevention.

    As a security-conscious system
    I want session IDs validated before use in file paths
    So that malicious IDs cannot escape the sessions directory.
    """

    @pytest.mark.unit
    def test_normal_session_id_accepted(self, tmp_path: Path) -> None:
        """Scenario: A well-formed session ID works normally.

        Given a session ID with alphanumerics, hyphens, and dots
        When record_session and get_session are called
        Then the record is stored and retrieved successfully.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)
        record = _make_record("sess-001.abc_XYZ")
        path = mgr.record_session(record)
        assert path.exists()

        retrieved = mgr.get_session("sess-001.abc_XYZ")
        assert retrieved is not None
        assert retrieved.session_id == "sess-001.abc_XYZ"

    @pytest.mark.unit
    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        """Scenario: Classic path-traversal attack is blocked.

        Given a session ID of '../../../etc/passwd'
        When record_session is called
        Then a ValueError is raised
        And get_session returns None
        And delete_session returns False.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)

        with pytest.raises(ValueError, match="Invalid session_id"):
            mgr.record_session(_make_record("../../../etc/passwd"))

        assert mgr.get_session("../../../etc/passwd") is None
        assert mgr.delete_session("../../../etc/passwd") is False

    @pytest.mark.unit
    def test_encoded_traversal_rejected(self, tmp_path: Path) -> None:
        """Scenario: URL-encoded path-traversal variant is blocked.

        Given a session ID of '..%2F..%2Fetc'
        When record_session is called
        Then a ValueError is raised.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)

        with pytest.raises(ValueError, match="Invalid session_id"):
            mgr.record_session(_make_record("..%2F..%2Fetc"))

        assert mgr.get_session("..%2F..%2Fetc") is None

    @pytest.mark.unit
    def test_empty_session_id_rejected(self, tmp_path: Path) -> None:
        """Scenario: Empty string session ID is blocked.

        Given an empty session ID
        When record_session is called
        Then a ValueError is raised
        And get_session returns None.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)

        with pytest.raises(ValueError, match="Invalid session_id"):
            mgr.record_session(_make_record(""))

        assert mgr.get_session("") is None

    @pytest.mark.unit
    def test_session_id_with_path_separators_rejected(self, tmp_path: Path) -> None:
        """Scenario: Session IDs containing slashes are blocked.

        Given session IDs with forward or backward slashes
        When record_session is called
        Then a ValueError is raised for each.
        """
        mgr = SessionHistoryManager(data_dir=tmp_path)

        with pytest.raises(ValueError, match="Invalid session_id"):
            mgr.record_session(_make_record("foo/bar"))

        with pytest.raises(ValueError, match="Invalid session_id"):
            mgr.record_session(_make_record("foo\\bar"))

        assert mgr.get_session("foo/bar") is None
        assert mgr.get_session("foo\\bar") is None

    @pytest.mark.unit
    def test_validate_session_id_helper(self) -> None:
        """Scenario: The _validate_session_id helper covers edge cases.

        Given various valid and invalid IDs
        Then the helper returns the correct boolean.
        """
        # Valid
        assert _validate_session_id("sess-001") is True
        assert _validate_session_id("a") is True
        assert _validate_session_id("ABC.def-123_ghi") is True

        # Invalid
        assert _validate_session_id("") is False
        assert _validate_session_id("..") is False
        assert _validate_session_id("../etc") is False
        assert _validate_session_id("/absolute") is False
        assert _validate_session_id(".hidden") is False
        assert _validate_session_id("-start") is False
        assert _validate_session_id("_start") is False
        assert _validate_session_id("has space") is False
        assert _validate_session_id("a/../b") is False
