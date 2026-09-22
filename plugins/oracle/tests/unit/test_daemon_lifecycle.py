"""Tests for oracle daemon lifecycle hook."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
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


@contextmanager
def _fake_daemon(tmp_path: Path) -> Iterator[subprocess.Popen]:
    """Spawn a live process whose command line names daemon.py, like the real one."""
    script = tmp_path / "daemon.py"
    script.write_text("import time; time.sleep(30)\n")
    proc = subprocess.Popen([sys.executable, str(script)])
    try:
        yield proc
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()


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
        # The body used to be main() and nothing else: zero assertions, so
        # the test passed whether or not the sentinel was honoured.
        #
        # is_provisioned is forced True so the sentinel is the only thing
        # that can stop the launch. Without that, the missing venv stops it
        # anyway and removing the sentinel check leaves this test green,
        # which is the same blind spot in a new place.
        with (
            patch("sys.stdin", StringIO(payload)),
            patch("daemon_lifecycle.is_provisioned", return_value=True),
            patch("daemon_lifecycle._start_daemon") as mock_start,
        ):
            main()
        mock_start.assert_not_called()

    @pytest.mark.unit
    def test_no_op_when_not_provisioned(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: Sentinel exists but venv is not provisioned
        GIVEN a .oracle-enabled sentinel present but no venv python
        WHEN main is called with a SessionStart event
        THEN it returns without error and leaves no daemon state behind

        The sentinel is the only file the data dir should hold after
        this: a pid or port file here would mean a daemon was launched
        against an interpreter that does not exist.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        (tmp_path / ".oracle-enabled").touch()
        payload = json.dumps({"hook_event_name": "SessionStart"})

        with patch("sys.stdin", StringIO(payload)):
            main()

        assert not (tmp_path / "daemon.pid").exists()
        assert not (tmp_path / "daemon.port").exists()


class TestStopBehavior:
    """
    Feature: Stop event is handled gracefully

    As the Claude Code runtime
    I want the Stop hook to exit cleanly whether or not the daemon is running
    So that session teardown is never blocked
    """

    @pytest.mark.unit
    def test_stop_does_not_signal_a_process_that_reused_the_pid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: Stale pid file after a crash or reboot
        Given daemon.pid names a live process the hook did not spawn
        When main is called with a Stop event
        Then that process is still alive afterward
        And the stale pid file is removed
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        bystander = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"]
        )
        try:
            (tmp_path / "daemon.pid").write_text(str(bystander.pid))
            with patch("sys.stdin", StringIO(json.dumps({"hook_event_name": "Stop"}))):
                main()
            assert bystander.poll() is None, (
                "Stop killed a process that is not the daemon"
            )
            assert not (tmp_path / "daemon.pid").exists()
        finally:
            bystander.kill()
            bystander.wait()

    @pytest.mark.unit
    def test_stop_exits_cleanly(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """
        Scenario: Stop event fires over state left by a dead daemon
        GIVEN a pid file naming a process that is not the oracle daemon
            and a port file beside it
        WHEN main is called with a Stop event
        THEN both files are gone

        Stop's whole job is reaching _stop_daemon; routing the event
        anywhere else leaves the stale pair on disk, and the next
        SessionStart reads a port nothing is listening on.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        pid_file = tmp_path / "daemon.pid"
        port_file = tmp_path / "daemon.port"
        # PID 1 exists on every POSIX host and is never the oracle
        # daemon, so _pid_is_daemon declines to signal it.
        pid_file.write_text("1")
        port_file.write_text("9000")
        payload = json.dumps({"hook_event_name": "Stop"})

        with patch("sys.stdin", StringIO(payload)):
            main()

        assert not pid_file.exists()
        assert not port_file.exists()


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
    def test_returns_true_when_pid_runs_the_daemon_script(self, tmp_path: Path):
        """
        Scenario: PID file names a live process running daemon.py
        Given a pid file naming a process whose command line is daemon.py
        When _is_daemon_running is called
        Then it returns True
        """
        pid_file = tmp_path / "daemon.pid"
        with _fake_daemon(tmp_path) as daemon:
            pid_file.write_text(str(daemon.pid))
            assert _is_daemon_running(pid_file) is True

    @pytest.mark.unit
    def test_returns_false_when_pid_belongs_to_another_process(self, tmp_path: Path):
        """
        Scenario: PID file names a live process that is not the daemon
        Given a pid file with this test's own PID
        When _is_daemon_running is called
        Then it returns False, because PIDs are reused after a crash
        """
        pid_file = tmp_path / "daemon.pid"
        pid_file.write_text(str(os.getpid()))
        assert _is_daemon_running(pid_file) is False

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
        with _fake_daemon(tmp_path) as daemon:
            pid_file.write_text(str(daemon.pid))
            # wraps= keeps the ps probe inside _pid_is_daemon working; the
            # assertion is that no launch happened, not that nothing ran.
            with patch(
                "daemon_lifecycle.subprocess.Popen", wraps=subprocess.Popen
            ) as spy:
                _start_daemon()

        launches = [c for c in spy.call_args_list if "--port-file" in str(c)]
        assert launches == []

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
        with _fake_daemon(tmp_path) as daemon:
            pid_file.write_text(str(daemon.pid))
            port_file.write_text("9000")
            _stop_daemon()
            assert daemon.wait(timeout=5) == -signal.SIGTERM

        assert not pid_file.exists()
        assert not port_file.exists()

    @pytest.mark.unit
    def test_handles_missing_pid_file_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """
        Scenario: No PID file exists (daemon was never started)
        GIVEN an empty data dir with no pid file
        WHEN _stop_daemon is called
        THEN it completes without error and creates nothing

        The unlink loop runs unconditionally, so a version that opened
        the files for writing before removing them would leave two
        empty files behind on a host that never ran the daemon.
        """
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))

        assert _stop_daemon() is None

        assert list(tmp_path.iterdir()) == []

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
