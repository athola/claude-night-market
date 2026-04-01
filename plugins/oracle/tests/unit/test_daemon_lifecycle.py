"""Tests for oracle daemon lifecycle hook."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from daemon_lifecycle import _get_event, _get_sentinel, main


class TestSentinelPath:
    """
    Feature: Opt-in sentinel controls daemon activation

    As a user who has not explicitly opted in
    I want the daemon to stay off by default
    So that oracle does not consume resources without consent
    """

    @pytest.mark.unit
    def test_sentinel_is_under_data_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: Sentinel path is derived from data directory
        Given CLAUDE_PLUGIN_DATA is set
        When _get_sentinel is called
        Then it returns data_dir / .oracle-enabled
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/oracle-data")
        result = _get_sentinel()
        assert result == Path("/tmp/oracle-data") / ".oracle-enabled"


class TestEventParsing:
    """
    Feature: Hook event parsing from stdin

    As the daemon lifecycle hook
    I want to know which event fired
    So that I can start or stop the daemon appropriately
    """

    @pytest.mark.unit
    def test_parses_session_start_event(self):
        """
        Scenario: SessionStart payload arrives on stdin
        Given a JSON payload with hook_event_name SessionStart
        When _get_event is called
        Then it returns 'SessionStart'
        """
        payload = json.dumps({"hook_event_name": "SessionStart"})
        with patch("sys.stdin", StringIO(payload)):
            assert _get_event() == "SessionStart"

    @pytest.mark.unit
    def test_parses_stop_event(self):
        """
        Scenario: Stop payload arrives on stdin
        Given a JSON payload with hook_event_name Stop
        When _get_event is called
        Then it returns 'Stop'
        """
        payload = json.dumps({"hook_event_name": "Stop"})
        with patch("sys.stdin", StringIO(payload)):
            assert _get_event() == "Stop"

    @pytest.mark.unit
    def test_returns_empty_string_on_bad_json(self):
        """
        Scenario: Stdin contains malformed JSON
        Given stdin has non-JSON content
        When _get_event is called
        Then it returns an empty string without raising
        """
        with patch("sys.stdin", StringIO("not json")):
            assert _get_event() == ""


class TestSessionStartBehavior:
    """
    Feature: Daemon does not start without opt-in

    As a user who has not run /oracle:setup
    I want the SessionStart hook to exit cleanly without starting anything
    So that the plugin is safe to install without side effects
    """

    @pytest.mark.unit
    def test_no_op_when_sentinel_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: SessionStart fires but sentinel does not exist
        Given no .oracle-enabled sentinel
        When main is called with a SessionStart event
        Then it returns without error and starts nothing
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        payload = json.dumps({"hook_event_name": "SessionStart"})
        with patch("sys.stdin", StringIO(payload)):
            main()

    @pytest.mark.unit
    def test_no_op_when_not_provisioned(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: Sentinel exists but venv is not provisioned
        Given .oracle-enabled sentinel present but no venv python
        When main is called with a SessionStart event
        Then it returns without error and starts nothing
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        (tmp_path / ".oracle-enabled").touch()
        payload = json.dumps({"hook_event_name": "SessionStart"})
        with patch("sys.stdin", StringIO(payload)):
            main()


class TestStopBehavior:
    """
    Feature: Stop event is handled gracefully

    As the Claude Code runtime
    I want the Stop hook to exit cleanly whether or not the daemon is running
    So that session teardown is never blocked
    """

    @pytest.mark.unit
    def test_stop_exits_cleanly(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: Stop event fires
        Given any daemon state
        When main is called with a Stop event
        Then it returns without error
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        payload = json.dumps({"hook_event_name": "Stop"})
        with patch("sys.stdin", StringIO(payload)):
            main()
