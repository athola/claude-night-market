"""Tests for oracle daemon lifecycle hook."""

from __future__ import annotations

import json
import os
import signal
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from daemon_lifecycle import (
    _get_event,
    _get_models_dir,
    _get_pid_file,
    _get_port_file,
    _get_sentinel,
    _is_daemon_running,
    _start_daemon,
    _stop_daemon,
    main,
)


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


class TestPathHelpers:
    """
    Feature: Data directory path derivation

    As the lifecycle hook
    I want consistent paths for pid, port, and model files
    So that the daemon and its clients agree on file locations
    """

    @pytest.mark.unit
    def test_pid_file_is_under_data_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: PID file path derived from CLAUDE_PLUGIN_DATA
        Given CLAUDE_PLUGIN_DATA is set
        When _get_pid_file is called
        Then it returns data_dir / daemon.pid
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/oracle-data")
        result = _get_pid_file()
        assert result == Path("/tmp/oracle-data") / "daemon.pid"

    @pytest.mark.unit
    def test_port_file_is_under_data_dir(self, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: Port file path derived from CLAUDE_PLUGIN_DATA
        Given CLAUDE_PLUGIN_DATA is set
        When _get_port_file is called
        Then it returns data_dir / daemon.port
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "/tmp/oracle-data")
        result = _get_port_file()
        assert result == Path("/tmp/oracle-data") / "daemon.port"

    @pytest.mark.unit
    def test_models_dir_is_under_plugin_root(self):
        """
        Scenario: Models directory is relative to the plugin root
        Given the plugin root is known
        When _get_models_dir is called
        Then it returns PLUGIN_ROOT / models
        """
        result = _get_models_dir()
        assert result.name == "models"
        assert result.parent.name == "oracle"


class TestIsDaemonRunning:
    """
    Feature: PID-based daemon liveness check

    As the lifecycle hook
    I want to check whether the daemon process is still alive
    So that I avoid starting a second instance
    """

    @pytest.mark.unit
    def test_returns_true_when_process_exists(self, tmp_path: Path):
        """
        Scenario: PID file contains a live process ID
        Given a pid file with the current process PID
        When _is_daemon_running is called
        Then it returns True
        """
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text(str(os.getpid()))
        assert _is_daemon_running(pid_file) is True

    @pytest.mark.unit
    def test_returns_false_when_pid_file_missing(self, tmp_path: Path):
        """
        Scenario: No PID file exists
        Given a non-existent pid file path
        When _is_daemon_running is called
        Then it returns False
        """
        assert _is_daemon_running(tmp_path / "nonexistent.pid") is False

    @pytest.mark.unit
    def test_returns_false_when_pid_file_has_garbage(self, tmp_path: Path):
        """
        Scenario: PID file contains non-integer content
        Given a pid file with garbage text
        When _is_daemon_running is called
        Then it returns False
        """
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text("not-a-number")
        assert _is_daemon_running(pid_file) is False

    @pytest.mark.unit
    def test_returns_false_when_process_does_not_exist(self, tmp_path: Path):
        """
        Scenario: PID file references a dead process
        Given a pid file with PID 99999999
        When _is_daemon_running is called
        Then it returns False (no such process)
        """
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text("99999999")
        assert _is_daemon_running(pid_file) is False


class TestStartDaemon:
    """
    Feature: Daemon process launch

    As the lifecycle hook on SessionStart
    I want to spawn the daemon as a detached subprocess
    So that inference is available for the session
    """

    @pytest.mark.unit
    def test_skips_launch_when_already_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: Daemon is already running
        Given _is_daemon_running returns True
        When _start_daemon is called
        Then subprocess.Popen is not called
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text(str(os.getpid()))

        with patch("daemon_lifecycle.subprocess.Popen") as mock_popen:
            _start_daemon()

        mock_popen.assert_not_called()

    @pytest.mark.unit
    def test_launches_daemon_subprocess(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: No daemon running, launch a new one
        Given no existing daemon process
        When _start_daemon is called
        Then subprocess.Popen is called with the daemon script
        And a PID file is written
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))

        mock_proc = MagicMock()
        mock_proc.pid = 42

        with patch(
            "daemon_lifecycle.subprocess.Popen",
            return_value=mock_proc,
        ) as mock_popen:
            _start_daemon()

        mock_popen.assert_called_once()
        args = mock_popen.call_args
        cmd = args[0][0]
        assert "daemon.py" in cmd[1]
        assert "--host" in cmd
        assert "--port" in cmd

        pid_file = tmp_path / "daemon.pid"
        assert pid_file.exists()
        assert pid_file.read_text() == "42"

    @pytest.mark.unit
    def test_cleans_stale_files_before_launch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: Stale port and pid files from a crashed run
        Given stale pid and port files exist but no live process
        When _start_daemon is called
        Then stale files are removed before launching
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        pid_file = tmp_path / "daemon.pid"
        port_file = tmp_path / "daemon.port"
        pid_file.write_text("99999999")
        port_file.write_text("12345")

        mock_proc = MagicMock()
        mock_proc.pid = 100

        with patch("daemon_lifecycle.subprocess.Popen", return_value=mock_proc):
            _start_daemon()

        # PID file should have the new PID, not the stale one.
        assert pid_file.read_text() == "100"


class TestStopDaemon:
    """
    Feature: Daemon graceful shutdown

    As the lifecycle hook on Stop
    I want to send SIGTERM to the daemon
    So that it shuts down cleanly when the session ends
    """

    @pytest.mark.unit
    def test_sends_sigterm_to_daemon(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: Daemon is running with a valid PID file
        Given a pid file containing a PID
        When _stop_daemon is called
        Then os.kill is called with SIGTERM
        And pid and port files are cleaned up
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        pid_file = tmp_path / "daemon.pid"
        port_file = tmp_path / "daemon.port"
        pid_file.write_text("12345")
        port_file.write_text("9000")

        with patch("daemon_lifecycle.os.kill") as mock_kill:
            _stop_daemon()

        mock_kill.assert_called_once_with(12345, signal.SIGTERM)
        assert not pid_file.exists()
        assert not port_file.exists()

    @pytest.mark.unit
    def test_handles_missing_pid_file_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: No PID file exists (daemon was never started)
        Given no pid file
        When _stop_daemon is called
        Then it completes without error
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        _stop_daemon()

    @pytest.mark.unit
    def test_handles_dead_process_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: PID file exists but process is already dead
        Given a pid file with a dead process PID
        When _stop_daemon is called
        Then os.kill raises OSError and _stop_daemon still cleans up files
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text("99999999")

        with patch("daemon_lifecycle.os.kill", side_effect=OSError("No such process")):
            _stop_daemon()

        assert not pid_file.exists()
