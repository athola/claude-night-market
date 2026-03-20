"""Unit tests for SessionManager persistence."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from tome.models import Finding, ResearchSession
from tome.session import SessionManager


class TestSessionManagerCreate:
    """
    Feature: Session creation

    As a research orchestrator
    I want to create a new session with a stable ID and timestamp
    So that the session can be retrieved and updated later
    """

    @pytest.mark.unit
    def test_create_returns_research_session(self, tmp_path: Path) -> None:
        """
        Scenario: Create returns a ResearchSession
        Given a SessionManager pointed at a temp directory
        When create is called with valid parameters
        Then a ResearchSession instance is returned
        """
        manager = SessionManager(tmp_path)
        session = manager.create("async python", "algorithm", "medium", ["code"])

        assert isinstance(session, ResearchSession)

    @pytest.mark.unit
    def test_create_generates_uuid_id(self, tmp_path: Path) -> None:
        """
        Scenario: Auto-generated UUID
        Given a new session created without an explicit id
        When inspecting the returned session
        Then id is a 36-character UUID string
        """
        manager = SessionManager(tmp_path)
        session = manager.create("topic", "domain", "light", [])

        assert isinstance(session.id, str)
        assert len(session.id) == 36

    @pytest.mark.unit
    def test_create_sets_created_at_timestamp(self, tmp_path: Path) -> None:
        """
        Scenario: Timestamp stamped on creation
        Given a freshly created session
        When created_at is inspected
        Then it is a timezone-aware datetime
        """
        manager = SessionManager(tmp_path)
        session = manager.create("topic", "domain", "light", [])

        assert isinstance(session.created_at, datetime)
        assert session.created_at.tzinfo is not None

    @pytest.mark.unit
    def test_create_sets_status_active(self, tmp_path: Path) -> None:
        """
        Scenario: Status is active after creation
        Given a new session from SessionManager.create
        When status is inspected
        Then it equals 'active'
        """
        manager = SessionManager(tmp_path)
        session = manager.create("topic", "domain", "light", [])

        assert session.status == "active"

    @pytest.mark.unit
    def test_create_persists_file_immediately(self, tmp_path: Path) -> None:
        """
        Scenario: File written on creation
        Given a SessionManager
        When create is called
        Then a JSON file exists for the new session
        """
        manager = SessionManager(tmp_path)
        session = manager.create("topic", "domain", "light", ["code"])

        expected_path = tmp_path / ".tome" / "sessions" / f"{session.id}.json"
        assert expected_path.exists()


class TestSessionManagerSave:
    """
    Feature: Session saving

    As a research orchestrator
    I want to persist a modified session back to disk
    So that progress is not lost between tool calls
    """

    @pytest.mark.unit
    def test_save_writes_json_to_correct_path(self, tmp_path: Path) -> None:
        """
        Scenario: Save writes to the expected path
        Given a session with a known id
        When save is called
        Then a file exists at .tome/sessions/{id}.json
        """
        manager = SessionManager(tmp_path)
        session = ResearchSession(
            id="fixed-id-001",
            topic="t",
            domain="d",
            triz_depth="light",
            channels=[],
            created_at=datetime.now(tz=timezone.utc),
        )
        path = manager.save(session)

        assert path == tmp_path / ".tome" / "sessions" / "fixed-id-001.json"
        assert path.exists()

    @pytest.mark.unit
    def test_save_writes_valid_json(self, tmp_path: Path) -> None:
        """
        Scenario: Saved file contains parseable JSON
        Given a session
        When save is called
        Then the file content is valid JSON
        """
        manager = SessionManager(tmp_path)
        session = ResearchSession(
            id="json-test-001",
            topic="t",
            domain="d",
            triz_depth="light",
            channels=["code"],
            created_at=datetime.now(tz=timezone.utc),
        )
        path = manager.save(session)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["id"] == "json-test-001"
        assert data["topic"] == "t"

    @pytest.mark.unit
    def test_save_overwrites_previous_version(self, tmp_path: Path) -> None:
        """
        Scenario: Re-saving a modified session replaces the file
        Given a session saved once with status 'active'
        When status is changed and save is called again
        Then the file reflects the updated status
        """
        manager = SessionManager(tmp_path)
        session = ResearchSession(
            id="overwrite-001",
            topic="t",
            domain="d",
            triz_depth="light",
            channels=[],
            created_at=datetime.now(tz=timezone.utc),
        )
        manager.save(session)

        session.mark_complete()
        manager.save(session)

        path = tmp_path / ".tome" / "sessions" / "overwrite-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["status"] == "complete"


class TestSessionManagerLoad:
    """
    Feature: Session loading

    As a research orchestrator
    I want to reload a previously saved session by ID
    So that I can resume work or inspect results
    """

    @pytest.mark.unit
    def test_load_returns_equivalent_session(self, tmp_path: Path) -> None:
        """
        Scenario: Load round-trips through the file system
        Given a saved session
        When load is called with the same id
        Then the returned session has identical fields
        """
        manager = SessionManager(tmp_path)
        original = manager.create("async python", "algorithm", "medium", ["code"])

        restored = manager.load(original.id)

        assert restored.id == original.id
        assert restored.topic == original.topic
        assert restored.domain == original.domain
        assert restored.triz_depth == original.triz_depth
        assert restored.channels == original.channels
        assert restored.status == original.status

    @pytest.mark.unit
    def test_load_restores_findings(self, tmp_path: Path) -> None:
        """
        Scenario: Findings survive save/load
        Given a session with one finding that is saved
        When load is called
        Then the returned session has one finding with matching fields
        """
        manager = SessionManager(tmp_path)
        session = manager.create("topic", "domain", "light", ["code"])
        finding = Finding(
            source="github",
            channel="code",
            title="test-repo",
            url="https://github.com/test/repo",
            relevance=0.9,
            summary="A test repo",
            metadata={"stars": 42},
        )
        session.add_finding(finding)
        manager.save(session)

        restored = manager.load(session.id)

        assert len(restored.findings) == 1
        assert restored.findings[0].title == "test-repo"
        assert restored.findings[0].metadata == {"stars": 42}

    @pytest.mark.unit
    def test_load_nonexistent_raises_file_not_found(self, tmp_path: Path) -> None:
        """
        Scenario: Loading a missing session raises FileNotFoundError
        Given no session with id 'does-not-exist'
        When load is called
        Then FileNotFoundError is raised
        """
        manager = SessionManager(tmp_path)

        with pytest.raises(FileNotFoundError):
            manager.load("does-not-exist")


class TestSessionManagerLoadLatest:
    """
    Feature: Loading the most recent session

    As a user resuming work
    I want to retrieve the latest session without knowing its id
    So that common workflows require less bookkeeping
    """

    @pytest.mark.unit
    def test_load_latest_returns_none_when_empty(self, tmp_path: Path) -> None:
        """
        Scenario: No sessions exist
        Given a fresh SessionManager with no saved sessions
        When load_latest is called
        Then None is returned
        """
        manager = SessionManager(tmp_path)

        assert manager.load_latest() is None

    @pytest.mark.unit
    def test_load_latest_returns_most_recent(self, tmp_path: Path) -> None:
        """
        Scenario: Multiple sessions, most recent is returned
        Given two sessions saved sequentially
        When load_latest is called
        Then the second (most recently written) session is returned
        """
        manager = SessionManager(tmp_path)
        manager.create("first topic", "algorithm", "light", [])
        second = manager.create("second topic", "algorithm", "light", [])

        latest = manager.load_latest()

        assert latest is not None
        assert latest.id == second.id


class TestSessionManagerListAll:
    """
    Feature: Listing all sessions

    As a user browsing research history
    I want a sorted list of session summaries
    So that the most recent work appears first
    """

    @pytest.mark.unit
    def test_list_all_empty_when_no_sessions(self, tmp_path: Path) -> None:
        """
        Scenario: No sessions returns empty list
        Given a fresh SessionManager
        When list_all is called
        Then an empty list is returned
        """
        manager = SessionManager(tmp_path)

        assert manager.list_all() == []

    @pytest.mark.unit
    def test_list_all_returns_one_summary_per_session(self, tmp_path: Path) -> None:
        """
        Scenario: Count of summaries matches sessions created
        Given three sessions created via the manager
        When list_all is called
        Then exactly three summaries are returned
        """
        manager = SessionManager(tmp_path)
        manager.create("topic a", "domain", "light", [])
        manager.create("topic b", "domain", "light", [])
        manager.create("topic c", "domain", "light", [])

        summaries = manager.list_all()

        assert len(summaries) == 3

    @pytest.mark.unit
    def test_list_all_sorted_by_created_at_descending(self, tmp_path: Path) -> None:
        """
        Scenario: Summaries arrive newest-first
        Given three sessions with distinct created_at timestamps
        When list_all is called
        Then summaries are ordered most-recent first
        """
        manager = SessionManager(tmp_path)
        base = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)

        for minutes_offset in [0, 5, 10]:
            s = ResearchSession(
                topic=f"topic-{minutes_offset}",
                domain="d",
                triz_depth="light",
                channels=[],
                created_at=base + timedelta(minutes=minutes_offset),
                status="active",
            )
            manager.save(s)

        summaries = manager.list_all()

        assert summaries[0].created_at == base + timedelta(minutes=10)
        assert summaries[1].created_at == base + timedelta(minutes=5)
        assert summaries[2].created_at == base

    @pytest.mark.unit
    def test_list_all_summary_fields_match_session(self, tmp_path: Path) -> None:
        """
        Scenario: Summary fields reflect session state accurately
        Given a session with known topic, domain, and status
        When list_all is called
        Then the returned summary matches those fields
        """
        manager = SessionManager(tmp_path)
        session = manager.create(
            "known topic", "algorithm", "deep", ["code", "academic"]
        )
        session.mark_complete()
        manager.save(session)

        summaries = manager.list_all()

        assert len(summaries) == 1
        s = summaries[0]
        assert s.id == session.id
        assert s.topic == "known topic"
        assert s.domain == "algorithm"
        assert s.status == "complete"
        assert s.finding_count == 0
