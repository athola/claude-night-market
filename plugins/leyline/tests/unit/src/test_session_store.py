# ruff: noqa: D101,D102
"""Tests for leyline.session_store — shared JSON session store base class.

Feature: Reusable JSON-file session store

As a plugin developer
I want a base class that handles file-backed session CRUD
So that tome and memory-palace share validated, consistent storage logic
without duplicating ID validation, JSON I/O, or corrupt-file handling.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_SRC = Path(__file__).resolve().parents[4] / "src"
sys.path.insert(0, str(_SRC))

from leyline.session_store import SessionStore, validate_session_id

# ---------------------------------------------------------------------------
# Minimal concrete subclass used across all tests
# ---------------------------------------------------------------------------


class _SimpleStore(SessionStore):
    """Stores plain dicts verbatim — no transformation."""

    def _serialize(self, record: Any) -> dict:  # type: ignore[type-arg]
        return dict(record)

    def _deserialize(self, data: dict) -> Any:  # type: ignore[type-arg]
        return dict(data)


# ---------------------------------------------------------------------------
# validate_session_id
# ---------------------------------------------------------------------------


class TestValidateSessionId:
    """
    Feature: Session ID safety validation

    As a plugin persisting session files
    I want IDs validated before use as filenames
    So that path-traversal and shell-injection attacks are prevented.
    """

    @pytest.mark.unit
    def test_accepts_alphanumeric(self) -> None:
        """
        Scenario: Simple alphanumeric ID passes
        Given a session ID of 'abc123'
        When validate_session_id is called
        Then it returns True
        """
        assert validate_session_id("abc123") is True

    @pytest.mark.unit
    def test_accepts_allowed_punctuation(self) -> None:
        """
        Scenario: Underscores, dots, and dashes are valid
        Given a session ID containing '_', '.', and '-'
        When validate_session_id is called
        Then it returns True
        """
        assert validate_session_id("my-session_v1.0") is True

    @pytest.mark.unit
    def test_rejects_leading_special_char(self) -> None:
        """
        Scenario: ID starting with '-' is invalid
        Given a session ID '-bad'
        When validate_session_id is called
        Then it returns False
        """
        assert validate_session_id("-bad") is False

    @pytest.mark.unit
    def test_rejects_path_traversal(self) -> None:
        """
        Scenario: Path traversal sequence '..' is rejected
        Given a session ID '../etc/passwd'
        When validate_session_id is called
        Then it returns False
        """
        assert validate_session_id("../etc/passwd") is False

    @pytest.mark.unit
    def test_rejects_slash(self) -> None:
        """
        Scenario: Forward slash is rejected
        Given a session ID 'a/b'
        When validate_session_id is called
        Then it returns False
        """
        assert validate_session_id("a/b") is False

    @pytest.mark.unit
    def test_rejects_overly_long_id(self) -> None:
        """
        Scenario: ID longer than 128 characters is rejected
        Given a session ID of 129 'a' characters
        When validate_session_id is called
        Then it returns False
        """
        assert validate_session_id("a" * 129) is False

    @pytest.mark.unit
    def test_accepts_exactly_128_chars(self) -> None:
        """
        Scenario: ID of exactly 128 characters is accepted
        Given a session ID of 128 'a' characters
        When validate_session_id is called
        Then it returns True
        """
        assert validate_session_id("a" * 128) is True


# ---------------------------------------------------------------------------
# SessionStore.save / load round-trip
# ---------------------------------------------------------------------------


class TestSessionStoreSaveLoad:
    """
    Feature: Save and load session records

    As a plugin persisting structured data
    I want save() to write JSON and load() to return the same data
    So that session state survives process restarts.
    """

    @pytest.mark.unit
    def test_save_creates_json_file(self, tmp_path: Path) -> None:
        """
        Scenario: save() writes a .json file
        Given a fresh store directory
        When save() is called with a valid ID and a dict
        Then a .json file exists at sessions_dir/<id>.json
        """
        store = _SimpleStore(tmp_path / "sessions")
        store.save("sess1", {"key": "value"})
        assert (tmp_path / "sessions" / "sess1.json").exists()

    @pytest.mark.unit
    def test_save_returns_path(self, tmp_path: Path) -> None:
        """
        Scenario: save() returns the written file path
        Given a fresh store
        When save() is called
        Then the returned path points to the written file
        """
        store = _SimpleStore(tmp_path / "sessions")
        path = store.save("sess1", {"x": 1})
        assert path == tmp_path / "sessions" / "sess1.json"
        assert path.exists()

    @pytest.mark.unit
    def test_load_returns_saved_record(self, tmp_path: Path) -> None:
        """
        Scenario: load() retrieves what save() wrote
        Given a record saved under 'sess1'
        When load('sess1') is called
        Then the original dict is returned
        """
        store = _SimpleStore(tmp_path / "sessions")
        store.save("sess1", {"name": "test", "value": 42})
        result = store.load("sess1")
        assert result == {"name": "test", "value": 42}

    @pytest.mark.unit
    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        """
        Scenario: load() returns None for a non-existent session
        Given an empty store
        When load('no-such-id') is called
        Then None is returned
        """
        store = _SimpleStore(tmp_path / "sessions")
        assert store.load("no-such-id") is None

    @pytest.mark.unit
    def test_load_corrupt_json_returns_none_and_warns(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """
        Scenario: load() handles corrupt JSON gracefully
        Given a session file containing invalid JSON
        When load() is called
        Then None is returned and a warning is printed to stderr
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        (sessions_dir / "bad.json").write_text("{not valid json", encoding="utf-8")

        store = _SimpleStore(sessions_dir)
        result = store.load("bad")
        assert result is None
        captured = capsys.readouterr()
        assert "bad" in captured.err

    @pytest.mark.unit
    def test_save_invalid_id_raises(self, tmp_path: Path) -> None:
        """
        Scenario: save() rejects an invalid session ID
        Given a session ID containing '/'
        When save() is called
        Then ValueError is raised
        """
        store = _SimpleStore(tmp_path / "sessions")
        with pytest.raises(ValueError, match="Invalid session ID"):
            store.save("bad/id", {"x": 1})

    @pytest.mark.unit
    def test_json_is_pretty_printed(self, tmp_path: Path) -> None:
        """
        Scenario: saved JSON uses indent=2 for readability
        Given a record saved to disk
        When the raw file content is read
        Then it contains newlines (confirming indent formatting)
        """
        store = _SimpleStore(tmp_path / "sessions")
        store.save("sess1", {"a": 1})
        raw = (tmp_path / "sessions" / "sess1.json").read_text(encoding="utf-8")
        assert "\n" in raw


# ---------------------------------------------------------------------------
# SessionStore.list_sessions
# ---------------------------------------------------------------------------


class TestSessionStoreListSessions:
    """
    Feature: List available session IDs

    As a plugin enumerating stored sessions
    I want list_sessions() to return valid IDs
    So that sessions can be shown to users or batch-processed.
    """

    @pytest.mark.unit
    def test_list_empty_store(self, tmp_path: Path) -> None:
        """
        Scenario: list_sessions() on empty directory returns []
        Given a fresh sessions directory with no files
        When list_sessions() is called
        Then an empty list is returned
        """
        store = _SimpleStore(tmp_path / "sessions")
        assert store.list_sessions() == []

    @pytest.mark.unit
    def test_list_returns_saved_ids(self, tmp_path: Path) -> None:
        """
        Scenario: list_sessions() reflects what was saved
        Given two sessions saved under 'alpha' and 'beta'
        When list_sessions() is called
        Then both IDs appear in the result (sorted)
        """
        store = _SimpleStore(tmp_path / "sessions")
        store.save("beta", {"v": 2})
        store.save("alpha", {"v": 1})
        assert store.list_sessions() == ["alpha", "beta"]

    @pytest.mark.unit
    def test_list_excludes_invalid_stems(self, tmp_path: Path) -> None:
        """
        Scenario: list_sessions() skips files with invalid ID stems
        Given a .json file whose stem contains '/' (path traversal simulation)
        When list_sessions() is called
        Then the invalid stem is excluded
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        # A stem with a leading '-' is invalid per validate_session_id
        (sessions_dir / "-bad.json").write_text("{}", encoding="utf-8")
        store = _SimpleStore(sessions_dir)
        assert store.list_sessions() == []


# ---------------------------------------------------------------------------
# SessionStore.delete
# ---------------------------------------------------------------------------


class TestSessionStoreDelete:
    """
    Feature: Delete session records

    As a plugin managing session lifecycle
    I want delete() to remove session files
    So that old sessions can be pruned.
    """

    @pytest.mark.unit
    def test_delete_existing_returns_true(self, tmp_path: Path) -> None:
        """
        Scenario: delete() removes an existing session file
        Given a session saved under 'sess1'
        When delete('sess1') is called
        Then True is returned and the file is gone
        """
        store = _SimpleStore(tmp_path / "sessions")
        store.save("sess1", {"x": 1})
        result = store.delete("sess1")
        assert result is True
        assert not (tmp_path / "sessions" / "sess1.json").exists()

    @pytest.mark.unit
    def test_delete_missing_returns_false(self, tmp_path: Path) -> None:
        """
        Scenario: delete() returns False for a non-existent session
        Given an empty store
        When delete('no-such-id') is called
        Then False is returned
        """
        store = _SimpleStore(tmp_path / "sessions")
        assert store.delete("no-such-id") is False

    @pytest.mark.unit
    def test_load_after_delete_returns_none(self, tmp_path: Path) -> None:
        """
        Scenario: load() after delete() returns None
        Given a session saved and then deleted
        When load() is called
        Then None is returned
        """
        store = _SimpleStore(tmp_path / "sessions")
        store.save("sess1", {"x": 1})
        store.delete("sess1")
        assert store.load("sess1") is None


# ---------------------------------------------------------------------------
# SessionStore subclassing contract
# ---------------------------------------------------------------------------


class TestSessionStoreAbstractContract:
    """
    Feature: Subclass must implement _serialize/_deserialize

    As a framework author
    I want unimplemented _serialize/_deserialize to raise NotImplementedError
    So that partial subclasses fail loudly rather than silently.
    """

    @pytest.mark.unit
    def test_bare_subclass_serialize_raises(self, tmp_path: Path) -> None:
        """
        Scenario: calling save() on a bare subclass raises NotImplementedError
        Given a SessionStore subclass that does not override _serialize
        When save() is called
        Then NotImplementedError is raised
        """

        class _Bare(SessionStore):
            pass

        store = _Bare(tmp_path / "sessions")
        with pytest.raises(NotImplementedError):
            store.save("sess1", {"x": 1})
