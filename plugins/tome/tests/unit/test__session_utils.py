"""Tests for shared session utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from hooks._session_utils import load_active_session
except ImportError:
    from _session_utils import load_active_session


class TestLoadActiveSession:
    """
    Feature: Load active research session from disk

    As a tome hook
    I want to find the most recent active session
    So that I can notify the user about ongoing research
    """

    @pytest.mark.unit
    def test_returns_none_when_dir_missing(self, tmp_path: Path) -> None:
        """
        Scenario: Sessions directory does not exist
        Given a path to a non-existent directory
        When load_active_session is called
        Then it returns None
        """
        missing = tmp_path / "no-such-dir"
        assert load_active_session(missing) is None

    @pytest.mark.unit
    def test_returns_none_when_dir_empty(self, tmp_path: Path) -> None:
        """
        Scenario: Sessions directory is empty
        Given an empty sessions directory
        When load_active_session is called
        Then it returns None
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        assert load_active_session(sessions_dir) is None

    @pytest.mark.unit
    def test_returns_topic_and_count_for_active(self, tmp_path: Path) -> None:
        """
        Scenario: Active session exists
        Given a session file with status "active" and 3 findings
        When load_active_session is called
        Then it returns (topic, 3)
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        data = {
            "topic": "caching strategies",
            "status": "active",
            "findings": [{"t": 1}, {"t": 2}, {"t": 3}],
        }
        (sessions_dir / "s1.json").write_text(json.dumps(data))
        result = load_active_session(sessions_dir)
        assert result == ("caching strategies", 3)

    @pytest.mark.unit
    def test_returns_none_for_complete_session(self, tmp_path: Path) -> None:
        """
        Scenario: Only completed sessions exist
        Given a session file with status "complete"
        When load_active_session is called
        Then it returns None
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        data = {"topic": "done", "status": "complete", "findings": []}
        (sessions_dir / "s1.json").write_text(json.dumps(data))
        assert load_active_session(sessions_dir) is None

    @pytest.mark.unit
    def test_returns_none_for_invalid_json(self, tmp_path: Path) -> None:
        """
        Scenario: Most recent file has invalid JSON
        Given a sessions directory with a corrupt JSON file
        When load_active_session is called
        Then it returns None
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        (sessions_dir / "bad.json").write_text("{not valid json")
        assert load_active_session(sessions_dir) is None

    @pytest.mark.unit
    def test_defaults_topic_to_unknown(self, tmp_path: Path) -> None:
        """
        Scenario: Active session has no topic field
        Given a session file with status "active" but no topic
        When load_active_session is called
        Then it returns ("unknown", finding_count)
        """
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        data = {"status": "active", "findings": [{"x": 1}]}
        (sessions_dir / "s1.json").write_text(json.dumps(data))
        result = load_active_session(sessions_dir)
        assert result == ("unknown", 1)
