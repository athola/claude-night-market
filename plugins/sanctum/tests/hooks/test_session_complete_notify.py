# ruff: noqa: D101,D102,D103,PLR2004,S603,S607
"""Integration tests for session_complete_notify hook.

Tests cross-platform notification sending, deduplication state machine,
content hashing, background mode CLI argument parsing, and terminal info
detection, all with mocked subprocess calls (no real notifications).
"""

from __future__ import annotations

import json
import platform
import runpy
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import session_complete_notify as mod
from session_complete_notify import (
    CONTENT_DEDUP_SECONDS,
    DEBOUNCE_SECONDS,
    NotificationState,
    clear_notification_state,
    content_hash,
    get_terminal_info,
    is_wsl,
    notify_windows,
    run_notification,
    send_notification,
)

HOOK_PATH = Path(mod.__file__).resolve()

# ---------------------------------------------------------------------------
# 1. Platform detection: send_notification() routes to the right command
# ---------------------------------------------------------------------------


class TestPlatformDetectionIntegration:
    """Test that send_notification() dispatches to the correct platform
    handler and that each handler invokes the expected subprocess command.
    """

    @pytest.mark.integration
    def test_linux_calls_notify_send_binary(self) -> None:
        """Linux path invokes /usr/bin/notify-send with correct args."""
        with (
            patch("session_complete_notify.platform.system", return_value="Linux"),
            patch("session_complete_notify.is_wsl", return_value=False),
            patch("session_complete_notify.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = send_notification("Title", "Body")

        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "/usr/bin/notify-send"
        assert "Title" in cmd
        assert "Body" in cmd

    @pytest.mark.integration
    def test_macos_calls_osascript(self) -> None:
        """macOS path invokes osascript with an AppleScript display
        notification command.
        """
        with (
            patch("session_complete_notify.platform.system", return_value="Darwin"),
            patch("session_complete_notify.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = send_notification("Title", "Body")

        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "osascript"
        assert cmd[1] == "-e"
        assert "display notification" in cmd[2]

    @pytest.mark.integration
    def test_windows_calls_powershell_toast(self) -> None:
        """Windows path invokes powershell with a toast notification
        script containing the title and body.
        """
        with (
            patch("session_complete_notify.platform.system", return_value="Windows"),
            patch("session_complete_notify.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = send_notification("Title", "Body")

        assert result is True
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "powershell"
        assert "-NoProfile" in cmd
        ps_script = cmd[3]
        assert "Title" in ps_script
        assert "Body" in ps_script

    @pytest.mark.integration
    def test_wsl_calls_powershell_exe_fallback(self) -> None:
        """WSL path tries powershell.exe (the Windows host binary)."""
        with (
            patch("session_complete_notify.platform.system", return_value="Linux"),
            patch("session_complete_notify.is_wsl", return_value=True),
            patch("session_complete_notify.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = send_notification("Title", "Body")

        assert result is True
        cmd = mock_run.call_args[0][0]
        # First attempt uses "powershell.exe"
        assert "powershell" in cmd[0].lower()

    @pytest.mark.integration
    def test_wsl_tries_all_paths_before_failing(self) -> None:
        """WSL exhausts all PowerShell paths and BurntToast fallback
        before returning False.
        """
        with (
            patch("session_complete_notify.platform.system", return_value="Linux"),
            patch("session_complete_notify.is_wsl", return_value=True),
            patch("session_complete_notify.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = FileNotFoundError()
            result = send_notification("Title", "Body")

        assert result is False
        # 3 toast paths + 3 BurntToast paths = 6 attempts
        assert mock_run.call_count == 6

    @pytest.mark.integration
    def test_unknown_platform_returns_false(self) -> None:
        """Unsupported platform returns False without calling subprocess."""
        with patch("session_complete_notify.platform.system", return_value="FreeBSD"):
            result = send_notification("Title", "Body")

        assert result is False


# ---------------------------------------------------------------------------
# 2. NotificationState: deduplication logic
# ---------------------------------------------------------------------------


class TestNotificationStateDeduplication:
    """Test the three-layer deduplication: per-session, content, debounce."""

    def _fresh_state(self, session_id: str = "test") -> NotificationState:
        return NotificationState(session_id=session_id)

    @pytest.mark.integration
    def test_should_notify_returns_true_on_first_call(self) -> None:
        """First call with a fresh state always returns True."""
        state = self._fresh_state()
        should, reason = state.should_notify("hash_abc")
        assert should is True
        assert reason == "ok"

    @pytest.mark.integration
    def test_should_notify_returns_false_after_notification(self) -> None:
        """After recording a notification, should_notify returns False
        because notified_since_input is True.
        """
        state = self._fresh_state()
        state.record_notification("hash_abc")

        should, reason = state.should_notify("hash_abc")
        assert should is False
        assert reason == "already_notified_since_input"

    @pytest.mark.integration
    def test_should_notify_resets_after_clear_input_flag(self, tmp_path: Path) -> None:
        """After clearing the input flag (simulating user input),
        should_notify returns True again.
        """
        state = self._fresh_state("reset_test")
        state.record_notification("hash_abc")

        # Simulate user input clearing the flag
        state.clear_input_flag()

        # Enough time must pass to avoid debounce
        state.last_notify_time = 0.0
        should, reason = state.should_notify("hash_new")
        assert should is True
        assert reason == "ok"

    @pytest.mark.integration
    def test_content_dedup_within_window(self) -> None:
        """Same content hash within CONTENT_DEDUP_SECONDS is suppressed."""
        state = self._fresh_state()
        # Simulate a prior notification with the same hash
        state.last_notify_time = time.time() - 1  # 1 second ago
        state.last_content_hash = "hash_same"
        state.notified_since_input = False  # clear layer 1

        should, reason = state.should_notify("hash_same")
        assert should is False
        assert "duplicate_content" in reason

    @pytest.mark.integration
    def test_content_dedup_expires_after_window(self) -> None:
        """Same content hash after CONTENT_DEDUP_SECONDS has elapsed is
        allowed through.
        """
        state = self._fresh_state()
        state.last_notify_time = time.time() - (CONTENT_DEDUP_SECONDS + 1)
        state.last_content_hash = "hash_same"
        state.notified_since_input = False

        should, reason = state.should_notify("hash_same")
        assert should is True

    @pytest.mark.integration
    def test_different_content_bypasses_content_dedup(self) -> None:
        """Different content hash bypasses content deduplication even
        within the time window (but may still be debounced).
        """
        state = self._fresh_state()
        state.last_notify_time = time.time() - (DEBOUNCE_SECONDS + 1)
        state.last_content_hash = "hash_old"
        state.notified_since_input = False

        should, reason = state.should_notify("hash_new")
        assert should is True

    @pytest.mark.integration
    def test_debounce_within_window(self) -> None:
        """Notification within DEBOUNCE_SECONDS of last send is suppressed,
        even with different content.
        """
        state = self._fresh_state()
        state.last_notify_time = time.time() - 1  # 1 second ago
        state.last_content_hash = "hash_old"
        state.notified_since_input = False

        should, reason = state.should_notify("hash_new")
        assert should is False
        assert "debounced" in reason

    @pytest.mark.integration
    def test_debounce_expires_after_window(self) -> None:
        """Notification after DEBOUNCE_SECONDS is allowed through."""
        state = self._fresh_state()
        state.last_notify_time = time.time() - (DEBOUNCE_SECONDS + 1)
        state.last_content_hash = "hash_old"
        state.notified_since_input = False

        should, reason = state.should_notify("hash_new")
        assert should is True

    @pytest.mark.integration
    def test_layer_priority_session_before_content(self) -> None:
        """Per-session flag (layer 1) takes priority over content dedup
        (layer 2).
        """
        state = self._fresh_state()
        state.notified_since_input = True
        state.last_content_hash = "different"
        state.last_notify_time = 0.0  # well past debounce

        should, reason = state.should_notify("brand_new_hash")
        assert should is False
        assert reason == "already_notified_since_input"


class TestNotificationStateLoadSaveRoundtrip:
    """Test state persistence to and from JSON files."""

    @pytest.mark.integration
    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """State written to disk can be loaded back identically."""
        session_id = "roundtrip_test"
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=tmp_path / "state.json",
        ):
            original = NotificationState(
                last_notify_time=1234567890.5,
                last_content_hash="abc123",
                notified_since_input=True,
                session_id=session_id,
            )
            original.save()

            loaded = NotificationState.load(session_id)

        assert loaded.last_notify_time == original.last_notify_time
        assert loaded.last_content_hash == original.last_content_hash
        assert loaded.notified_since_input == original.notified_since_input

    @pytest.mark.integration
    def test_load_returns_fresh_state_when_no_file(self, tmp_path: Path) -> None:
        """Loading from a nonexistent file returns default state."""
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=tmp_path / "nonexistent.json",
        ):
            state = NotificationState.load("no_file")

        assert state.last_notify_time == 0.0
        assert state.last_content_hash == ""
        assert state.notified_since_input is False

    @pytest.mark.integration
    def test_load_returns_fresh_state_on_corrupt_json(self, tmp_path: Path) -> None:
        """Loading from a corrupt JSON file returns default state."""
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("{invalid json!!!}")
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=corrupt_file,
        ):
            state = NotificationState.load("corrupt")

        assert state.last_notify_time == 0.0
        assert state.notified_since_input is False

    @pytest.mark.integration
    def test_load_handles_partial_json(self, tmp_path: Path) -> None:
        """Loading from JSON missing some keys uses defaults for those."""
        partial_file = tmp_path / "partial.json"
        partial_file.write_text(json.dumps({"last_notify_time": 999.0}))
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=partial_file,
        ):
            state = NotificationState.load("partial")

        assert state.last_notify_time == 999.0
        assert state.last_content_hash == ""
        assert state.notified_since_input is False

    @pytest.mark.integration
    def test_state_file_path_sanitizes_session_id(self) -> None:
        """Session IDs with special characters are sanitized for
        filesystem safety.
        """
        path = NotificationState.state_file_path("sess/with\\special:chars!")
        filename = path.name
        # Should not contain /, \, or :
        assert "/" not in filename
        assert "\\" not in filename
        assert ":" not in filename
        assert filename.startswith(".claude-notify-")

    @pytest.mark.integration
    def test_state_file_path_truncates_long_ids(self) -> None:
        """Session IDs longer than 64 characters are truncated."""
        long_id = "a" * 200
        path = NotificationState.state_file_path(long_id)
        # The sanitized part (between prefix and .json) should be <= 64 chars
        filename = path.name
        sanitized = filename.replace(".claude-notify-", "").replace(".json", "")
        assert len(sanitized) <= 64

    @pytest.mark.integration
    def test_save_silently_handles_write_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a state file path inside a directory that does not exist.

        WHEN the state is saved
        THEN nothing is raised, the failure is named on stderr, and no
            file or directory is created

        Silence on stderr would make the hook lose notifications with
        no trace; creating the directory would make a hook that is
        meant to be best-effort start writing to arbitrary paths.
        """
        target = tmp_path / "absent-dir" / "state.json"
        state = NotificationState(session_id="write_fail")

        with patch.object(NotificationState, "state_file_path", return_value=target):
            state.save()

        assert "save failed" in capsys.readouterr().err
        assert not target.parent.exists()

    @pytest.mark.integration
    def test_record_notification_persists_state(self, tmp_path: Path) -> None:
        """record_notification() updates all fields and persists to disk."""
        session_id = "record_test"
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=tmp_path / "record.json",
        ):
            state = NotificationState(session_id=session_id)
            state.record_notification("hashval")

            loaded = NotificationState.load(session_id)

        assert loaded.notified_since_input is True
        assert loaded.last_content_hash == "hashval"
        assert loaded.last_notify_time > 0


# ---------------------------------------------------------------------------
# 3. Background mode: __main__ block argument dispatch
# ---------------------------------------------------------------------------


class TestMainBlockArgumentParsing:
    """Test the if __name__ == '__main__' argument parsing logic.

    Uses runpy.run_path to execute the hook file as ``__main__``, so the
    dispatch under test is the one in the hook, not a copy of it. Only the
    outside world is faked: the state directory, the platform, and the
    notify-send and background-process launches.
    """

    @staticmethod
    def _run_as_script(
        argv: list[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> dict[str, list]:
        """Run the hook as a script and return the processes it launched."""
        launched: dict[str, list] = {"run": [], "popen": []}
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        project = tmp_path / "project"
        project.mkdir()

        for var in (
            "ZELLIJ_SESSION_NAME",
            "TMUX",
            "SSH_TTY",
            "TTY",
            "GPG_TTY",
            "TERM_PROGRAM",
            "CLAUDE_NO_NOTIFICATIONS",
        ):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("PPID", "4242")
        monkeypatch.setattr(tempfile, "tempdir", str(state_dir))
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(platform, "release", lambda: "6.1.0-generic")
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda cmd, **_kw: (
                launched["run"].append(cmd),
                subprocess.CompletedProcess(cmd, 0),
            )[1],
        )
        monkeypatch.setattr(
            subprocess, "Popen", lambda cmd, **_kw: launched["popen"].append(cmd)
        )
        monkeypatch.chdir(project)
        monkeypatch.setattr(sys, "argv", argv)

        try:
            runpy.run_path(str(HOOK_PATH), run_name="__main__")
        except SystemExit as exc:
            assert exc.code == 0
        return launched

    @staticmethod
    def _state(tmp_path: Path, session_id: str) -> dict:
        state_file = tmp_path / "state" / f".claude-notify-{session_id}.json"
        return json.loads(state_file.read_text())

    @pytest.mark.integration
    def test_clear_state_arg_calls_clear(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """--clear-state saves the session state with the input flag cleared."""
        launched = self._run_as_script(
            ["script.py", "--clear-state"], monkeypatch, tmp_path
        )

        state = self._state(tmp_path, "term_4242_project")
        assert state["notified_since_input"] is False
        assert launched == {"run": [], "popen": []}

    @pytest.mark.integration
    def test_background_with_session_and_cwd(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """--background session_id cwd notifies and records that session."""
        launched = self._run_as_script(
            ["script.py", "--background", "my_session", str(tmp_path)],
            monkeypatch,
            tmp_path,
        )

        assert len(launched["run"]) == 1
        assert launched["run"][0][-1].endswith(tmp_path.name)
        assert self._state(tmp_path, "my_session")["notified_since_input"] is True

    @pytest.mark.integration
    def test_background_legacy_fallback(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """--background without session_id/cwd derives both from the terminal."""
        launched = self._run_as_script(
            ["script.py", "--background"], monkeypatch, tmp_path
        )

        assert launched["run"][0][-1] == "Awaiting input in: project"
        state = self._state(tmp_path, "term_4242_project")
        assert state["notified_since_input"] is True

    @pytest.mark.integration
    def test_no_args_calls_main(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """No arguments relaunches the hook in the background and exits 0."""
        launched = self._run_as_script(["script.py"], monkeypatch, tmp_path)

        assert launched["popen"] == [
            [
                sys.executable,
                str(HOOK_PATH),
                "--background",
                "term_4242_project",
                str(tmp_path / "project"),
            ]
        ]
        assert launched["run"] == []

    @pytest.mark.integration
    def test_clear_notification_state_silences_os_errors(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a state load that fails with OSError.

        WHEN the UserPromptSubmit path clears the flag
        THEN nothing is raised and the cause is reported on stderr

        The companion test below pins that a RuntimeError still
        propagates, so this one has to pin more than "did not raise":
        a bare ``except OSError: pass`` would satisfy that and leave an
        operator with a hook that has quietly stopped working.
        """
        with patch(
            "session_complete_notify.NotificationState.load",
            side_effect=OSError("disk full"),
        ):
            assert clear_notification_state("any_session") is None

        captured = capsys.readouterr().err
        assert "clear_notification_state" in captured
        assert "disk full" in captured

    @pytest.mark.integration
    def test_clear_notification_state_propagates_runtime_errors(self) -> None:
        """Programming errors (RuntimeError) propagate from clear_notification_state."""
        with (
            patch(
                "session_complete_notify.NotificationState.load",
                side_effect=RuntimeError("unexpected"),
            ),
            pytest.raises(RuntimeError, match="unexpected"),
        ):
            clear_notification_state("any_session")

    @pytest.mark.integration
    def test_clear_state_clears_input_flag(self, tmp_path: Path) -> None:
        """clear_notification_state() loads state and clears the input
        flag for the current session.
        """
        with (
            patch(
                "session_complete_notify.get_session_id",
                return_value="clear_test",
            ),
            patch.object(
                NotificationState,
                "state_file_path",
                return_value=tmp_path / "clear.json",
            ),
        ):
            # Set up state with notified_since_input=True
            state = NotificationState(
                session_id="clear_test",
                notified_since_input=True,
                last_notify_time=100.0,
            )
            state.save()

            # Call clear
            clear_notification_state()

            # Verify the flag is cleared on disk
            loaded = NotificationState.load("clear_test")

        assert loaded.notified_since_input is False
        # Other state should be preserved
        assert loaded.last_notify_time == 100.0


# ---------------------------------------------------------------------------
# 4. Terminal info detection with various env vars
# ---------------------------------------------------------------------------


class TestTerminalInfoDetection:
    """Test get_terminal_info() with various environment variable
    combinations.
    """

    @pytest.mark.integration
    def test_bare_environment_returns_project_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no session env vars, returns only the project basename."""
        for var in (
            "ZELLIJ_SESSION_NAME",
            "TMUX",
            "TERM_PROGRAM",
            "SSH_TTY",
            "TTY",
            "GPG_TTY",
        ):
            monkeypatch.delenv(var, raising=False)

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/home/user/my-project",
        ):
            result = get_terminal_info()

        assert result == "my-project"

    @pytest.mark.integration
    def test_zellij_without_tab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zellij session without a resolved tab name shows only
        session.
        """
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "work")
        monkeypatch.delenv("TMUX", raising=False)

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/projects/app",
            ),
            patch(
                "session_complete_notify.get_zellij_tab_name",
                return_value=None,
            ),
        ):
            result = get_terminal_info()

        assert result == "zellij:work - app"

    @pytest.mark.integration
    def test_zellij_with_custom_tab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zellij session with a custom tab name includes both."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "dev")
        monkeypatch.delenv("TMUX", raising=False)

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/projects/app",
            ),
            patch(
                "session_complete_notify.get_zellij_tab_name",
                return_value="editor",
            ),
        ):
            result = get_terminal_info()

        assert result == "zellij:dev|editor - app"

    @pytest.mark.integration
    def test_zellij_default_tab_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default Zellij tab name 'Tab #1' is omitted from output."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "main")
        monkeypatch.delenv("TMUX", raising=False)

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/projects/app",
            ),
            patch(
                "session_complete_notify.get_zellij_tab_name",
                return_value="Tab #1",
            ),
        ):
            result = get_terminal_info()

        assert "Tab #1" not in result
        assert result == "zellij:main - app"

    @pytest.mark.integration
    def test_tmux_session_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """tmux environment includes session:window info."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,1234,0")

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/home/user/app",
            ),
            patch(
                "session_complete_notify._get_tmux_session",
                return_value="dev:code",
            ),
        ):
            result = get_terminal_info()

        assert result == "tmux:dev:code - app"

    @pytest.mark.integration
    def test_tmux_without_session_name_falls_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """tmux set but _get_tmux_session() returns None falls through
        to TERM_PROGRAM.
        """
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.delenv("GPG_TTY", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,1234,0")
        monkeypatch.setenv("TERM_PROGRAM", "Alacritty")

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/home/user/app",
            ),
            patch(
                "session_complete_notify._get_tmux_session",
                return_value=None,
            ),
        ):
            result = get_terminal_info()

        # With the refactored _detect_terminal_context(), when TMUX is set
        # but _get_tmux_session() returns None, the detection correctly
        # falls through to TERM_PROGRAM. This is the improved behavior.
        assert result == "Alacritty - app"

    @pytest.mark.integration
    def test_term_program_detection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TERM_PROGRAM shows the terminal application name."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("SSH_CONNECTION", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.delenv("GPG_TTY", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "WezTerm")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/code/project",
        ):
            result = get_terminal_info()

        assert result == "WezTerm - project"

    @pytest.mark.integration
    def test_ssh_tty_detection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SSH_TTY produces 'SSH' prefix."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.setenv("SSH_TTY", "/dev/pts/3")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/remote/project",
        ):
            result = get_terminal_info()

        assert result == "SSH - project"

    @pytest.mark.integration
    def test_tty_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TTY env var produces the tty basename as prefix."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.setenv("TTY", "/dev/ttys004")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/home/user/proj",
        ):
            result = get_terminal_info()

        assert result == "ttys004 - proj"

    @pytest.mark.integration
    def test_gpg_tty_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """GPG_TTY is used when TTY is not set."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.setenv("GPG_TTY", "/dev/ttys007")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/home/user/proj",
        ):
            result = get_terminal_info()

        assert result == "ttys007 - proj"


# ---------------------------------------------------------------------------
# 5. Content hashing: consistent and deterministic
# ---------------------------------------------------------------------------


class TestContentHashing:
    """Test that content_hash() produces stable, deterministic results."""

    @pytest.mark.integration
    def test_same_input_same_hash(self) -> None:
        """Identical title+message always produce the same hash."""
        h1 = content_hash("Title", "Message")
        h2 = content_hash("Title", "Message")
        assert h1 == h2

    @pytest.mark.integration
    def test_different_title_different_hash(self) -> None:
        """Different titles produce different hashes."""
        h1 = content_hash("Title A", "Message")
        h2 = content_hash("Title B", "Message")
        assert h1 != h2

    @pytest.mark.integration
    def test_different_message_different_hash(self) -> None:
        """Different messages produce different hashes."""
        h1 = content_hash("Title", "Message A")
        h2 = content_hash("Title", "Message B")
        assert h1 != h2

    @pytest.mark.integration
    def test_hash_length_is_16(self) -> None:
        """Hash is truncated to 16 hex characters."""
        h = content_hash("Any Title", "Any Message")
        assert len(h) == 16
        # Should be valid hex
        int(h, 16)

    @pytest.mark.integration
    def test_hash_is_hex_string(self) -> None:
        """Hash contains only hexadecimal characters."""
        h = content_hash("Test", "Content")
        assert all(c in "0123456789abcdef" for c in h)

    @pytest.mark.integration
    def test_empty_strings_produce_valid_hash(self) -> None:
        """Empty title and message still produce a valid hash."""
        h = content_hash("", "")
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)

    @pytest.mark.integration
    def test_special_characters_handled(self) -> None:
        """Special characters in content do not cause errors."""
        h = content_hash(
            'Title "with" <special> & chars',
            "Message\nwith\ttabs\rand\0nulls",
        )
        assert len(h) == 16

    @pytest.mark.integration
    def test_unicode_handled(self) -> None:
        """Unicode content produces a valid hash."""
        h = content_hash("Titre", "Le message est pret")
        assert len(h) == 16


# ---------------------------------------------------------------------------
# 6. End-to-end integration: run_notification with deduplication
# ---------------------------------------------------------------------------


class TestRunNotificationIntegration:
    """Test run_notification() end-to-end including state machine
    interactions.
    """

    @pytest.mark.integration
    def test_first_call_sends_notification(self, tmp_path: Path) -> None:
        """First run_notification() call with fresh state sends a
        notification.
        """
        state_file = tmp_path / "state.json"
        with (
            patch.object(
                NotificationState,
                "state_file_path",
                return_value=state_file,
            ),
            patch(
                "session_complete_notify.get_terminal_info",
                return_value="test-term",
            ),
            patch(
                "session_complete_notify.send_notification",
                return_value=True,
            ) as mock_send,
        ):
            run_notification("fresh_session", str(tmp_path))

        mock_send.assert_called_once()
        assert json.loads(state_file.read_text())["notified_since_input"] is True

    @pytest.mark.integration
    def test_second_call_is_deduplicated(self, tmp_path: Path) -> None:
        """Second immediate run_notification() call is suppressed by
        deduplication.
        """
        state_file = tmp_path / "state.json"
        with (
            patch.object(
                NotificationState,
                "state_file_path",
                return_value=state_file,
            ),
            patch(
                "session_complete_notify.get_terminal_info",
                return_value="test-term",
            ),
            patch(
                "session_complete_notify.send_notification",
                return_value=True,
            ) as mock_send,
        ):
            run_notification("dedup_session", str(tmp_path))
            run_notification("dedup_session", str(tmp_path))

        # Only the first call should send
        assert mock_send.call_count == 1

    @pytest.mark.integration
    def test_skips_when_should_notify_false(self, tmp_path: Path) -> None:
        """When should_notify returns False, no notification is sent."""
        state_file = tmp_path / "state.json"
        # Pre-populate state as already notified
        pre_state = NotificationState(
            session_id="skip_test",
            notified_since_input=True,
            last_notify_time=time.time(),
        )
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=state_file,
        ):
            pre_state.save()

        with (
            patch.object(
                NotificationState,
                "state_file_path",
                return_value=state_file,
            ),
            patch(
                "session_complete_notify.get_terminal_info",
                return_value="test-term",
            ),
            patch(
                "session_complete_notify.send_notification",
            ) as mock_send,
        ):
            run_notification("skip_test", str(tmp_path))

        mock_send.assert_not_called()

    @pytest.mark.integration
    def test_failed_notification_does_not_record_state(self, tmp_path: Path) -> None:
        """When send_notification returns False, state is not recorded."""
        state_file = tmp_path / "state.json"
        with (
            patch.object(
                NotificationState,
                "state_file_path",
                return_value=state_file,
            ),
            patch(
                "session_complete_notify.get_terminal_info",
                return_value="test-term",
            ),
            patch(
                "session_complete_notify.send_notification",
                return_value=False,
            ),
        ):
            run_notification("fail_session", str(tmp_path))

        # Load state and verify notification was not recorded
        with patch.object(
            NotificationState,
            "state_file_path",
            return_value=state_file,
        ):
            state = NotificationState.load("fail_session")

        assert state.notified_since_input is False

    @pytest.mark.integration
    def test_exception_in_run_notification_is_silent(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a chdir to the caller's cwd that fails with OSError.

        WHEN the background notification runs
        THEN nothing is raised, no notification is sent, and the cause
            is reported on stderr

        chdir is the first statement in the try, so a notification
        reaching the user here would mean it was built from the wrong
        directory's terminal info.
        """
        with (
            patch(
                "session_complete_notify.os.chdir",
                side_effect=OSError("bad dir"),
            ),
            patch("session_complete_notify.send_notification") as mock_send,
        ):
            run_notification("err_session", "/nonexistent/path")

        mock_send.assert_not_called()
        assert "bad dir" in capsys.readouterr().err

    @pytest.mark.integration
    def test_run_notification_propagates_unexpected_errors(self) -> None:
        """Programming errors (RuntimeError) are NOT swallowed by the handler."""
        with (
            patch(
                "session_complete_notify.os.chdir",
                side_effect=RuntimeError("unexpected"),
            ),
            pytest.raises(RuntimeError, match="unexpected"),
        ):
            run_notification("runtime_err_session", "/some/path")


# ---------------------------------------------------------------------------
# 7. Windows BurntToast fallback
# ---------------------------------------------------------------------------


class TestWindowsBurntToastFallback:
    """Test the BurntToast fallback path on Windows."""

    @pytest.mark.integration
    def test_windows_falls_back_to_burnttoast(self) -> None:
        """When primary toast fails, Windows tries BurntToast cmdlet."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            # First call (primary toast) fails, second (BurntToast) succeeds
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "powershell"),
                MagicMock(returncode=0),
            ]
            result = notify_windows("Test", "Message")

        assert result is True
        assert mock_run.call_count == 2
        # Second call should contain BurntToast command
        second_call_cmd = mock_run.call_args_list[1][0][0]
        assert "BurntToast" in second_call_cmd[3]

    @pytest.mark.unit
    @pytest.mark.parametrize("quote", ["\u201c", "\u201d", "\u201e"])
    def test_burnttoast_escapes_curly_double_quotes(self, quote: str) -> None:
        """PowerShell ends a double-quoted string on a curly quote too."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mod._try_burnt_toast(f"a{quote}; calc; {quote}b", "msg", ["powershell"])

        burnt_cmd = mock_run.call_args[0][0][3]
        assert burnt_cmd.count(quote) == 2
        assert burnt_cmd.count("`" + quote) == 2

    @pytest.mark.integration
    def test_windows_returns_false_when_both_fail(self) -> None:
        """When both primary toast and BurntToast fail, returns False."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "powershell"),
                subprocess.CalledProcessError(1, "powershell"),
            ]
            result = notify_windows("Test", "Message")

        assert result is False


# ---------------------------------------------------------------------------
# 8. WSL detection edge cases
# ---------------------------------------------------------------------------


class TestWSLDetectionEdgeCases:
    """Additional WSL detection edge cases."""

    @pytest.mark.integration
    def test_wsl_case_insensitive(self) -> None:
        """WSL detection is case-insensitive."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.90.1-MICROSOFT-standard",
        ):
            assert is_wsl() is True

    @pytest.mark.integration
    def test_macos_kernel_not_wsl(self) -> None:
        """macOS Darwin kernel is not WSL."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="23.4.0",
        ):
            assert is_wsl() is False

    @pytest.mark.integration
    def test_empty_release_not_wsl(self) -> None:
        """Empty platform release is not WSL."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="",
        ):
            assert is_wsl() is False
