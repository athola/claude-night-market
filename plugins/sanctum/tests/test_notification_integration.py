# ruff: noqa: D101,D102,D103,PLR2004,S603,S607
"""Additional integration tests for session_complete_notify hook.

Covers gaps in the existing test suite:
- get_session_id() for each environment priority path
- get_zellij_tab_name() subprocess behavior
- _get_tmux_session() subprocess behavior
- main() Popen dispatch and CLAUDE_NO_NOTIFICATIONS flag
- clear_notification_state() exception handler
- notify_wsl() CalledProcessError / TimeoutExpired continue paths
- notify_linux() failure modes
- notify_macos() sound-disabled path and failure modes
- notify_windows() sound-disabled path
"""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest
from session_complete_notify import (
    NotificationState,
    _get_tmux_session,
    clear_notification_state,
    get_session_id,
    get_zellij_tab_name,
    main,
    notify_linux,
    notify_macos,
    notify_windows,
    notify_wsl,
)

# ---------------------------------------------------------------------------
# 1. get_session_id(): each environment priority branch
# ---------------------------------------------------------------------------


class TestGetSessionId:
    """Test get_session_id() returns a stable, deterministic string for each
    supported environment variable priority."""

    @pytest.mark.integration
    def test_zellij_without_tab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zellij session with no resolvable tab produces
        zellij_<session>_<project>."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "work")
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/home/user/myproject",
            ),
            patch(
                "session_complete_notify.get_zellij_tab_name",
                return_value=None,
            ),
        ):
            result = get_session_id()

        assert result == "zellij_work_myproject"

    @pytest.mark.integration
    def test_zellij_with_tab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Zellij session with a custom tab includes tab name between
        session and project."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "dev")
        monkeypatch.delenv("TMUX", raising=False)

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/code/myapp",
            ),
            patch(
                "session_complete_notify.get_zellij_tab_name",
                return_value="editor",
            ),
        ):
            result = get_session_id()

        assert result == "zellij_dev_editor_myapp"

    @pytest.mark.integration
    def test_tmux_with_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """tmux env produces tmux_<session>_<window>_<project>."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,1234,0")

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/code/myapp",
            ),
            patch(
                "session_complete_notify._get_tmux_session",
                return_value="main:code",
            ),
        ):
            result = get_session_id()

        assert result == "tmux_main_code_myapp"

    @pytest.mark.integration
    def test_tmux_no_session_falls_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When _get_tmux_session() returns None, tmux branch is skipped
        and SSH_TTY is used instead."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,1234,0")
        monkeypatch.setenv("SSH_TTY", "/dev/pts/2")
        monkeypatch.delenv("TTY", raising=False)

        with (
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/code/myapp",
            ),
            patch(
                "session_complete_notify._get_tmux_session",
                return_value=None,
            ),
        ):
            result = get_session_id()

        # tmux produced no info, fallthrough to SSH_TTY priority.
        # os.path.basename("/dev/pts/2") == "2"
        assert result == "tty_2_myapp"

    @pytest.mark.integration
    def test_ssh_tty_priority(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SSH_TTY takes priority over plain TTY."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.setenv("SSH_TTY", "/dev/pts/3")
        monkeypatch.setenv("TTY", "/dev/ttys005")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/srv/proj",
        ):
            result = get_session_id()

        # os.path.basename("/dev/pts/3") == "3"
        assert result == "tty_3_proj"

    @pytest.mark.integration
    def test_tty_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When SSH_TTY is absent, TTY is used."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.setenv("TTY", "/dev/ttys007")
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/home/user/proj",
        ):
            result = get_session_id()

        assert result == "tty_ttys007_proj"

    @pytest.mark.integration
    def test_term_program_with_ppid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TERM_PROGRAM with a known PPID produces a stable id."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "WezTerm")
        monkeypatch.setenv("PPID", "12345")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/code/app",
        ):
            result = get_session_id()

        assert result == "WezTerm_12345_app"

    @pytest.mark.integration
    def test_bare_environment_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no known env vars are set, the id starts with term_<ppid>."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.setenv("PPID", "99")

        with patch(
            "session_complete_notify.os.getcwd",
            return_value="/bare/env",
        ):
            result = get_session_id()

        assert result.startswith("term_99_")
        assert result.endswith("_env")


# ---------------------------------------------------------------------------
# 2. get_zellij_tab_name(): direct subprocess calls
# ---------------------------------------------------------------------------


class TestGetZellijTabName:
    """Test get_zellij_tab_name() subprocess dispatch."""

    @pytest.mark.integration
    def test_returns_tab_name_on_success(self) -> None:
        """When zellij outputs a focused tab, the name is parsed and
        returned."""
        layout_output = 'tab name="MyTab" cwd="/home/user" focus=true { pane; }'
        mock_result = MagicMock(returncode=0, stdout=layout_output)
        with patch("session_complete_notify.subprocess.run", return_value=mock_result):
            result = get_zellij_tab_name()

        assert result == "MyTab"

    @pytest.mark.integration
    def test_returns_none_when_no_focused_tab(self) -> None:
        """Layout with no focus=true entry returns None."""
        layout_output = 'tab name="OtherTab" cwd="/home/user" { pane; }'
        mock_result = MagicMock(returncode=0, stdout=layout_output)
        with patch("session_complete_notify.subprocess.run", return_value=mock_result):
            result = get_zellij_tab_name()

        assert result is None

    @pytest.mark.integration
    def test_returns_none_on_nonzero_exit(self) -> None:
        """Nonzero returncode from zellij returns None."""
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("session_complete_notify.subprocess.run", return_value=mock_result):
            result = get_zellij_tab_name()

        assert result is None

    @pytest.mark.integration
    def test_returns_none_on_timeout(self) -> None:
        """TimeoutExpired is silently handled and returns None."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="zellij", timeout=0.5),
        ):
            result = get_zellij_tab_name()

        assert result is None

    @pytest.mark.integration
    def test_returns_none_when_zellij_not_found(self) -> None:
        """FileNotFoundError (zellij not installed) returns None."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = get_zellij_tab_name()

        assert result is None


# ---------------------------------------------------------------------------
# 3. _get_tmux_session(): direct subprocess calls
# ---------------------------------------------------------------------------


class TestGetTmuxSession:
    """Test _get_tmux_session() subprocess dispatch."""

    @pytest.mark.integration
    def test_returns_session_window_on_success(self) -> None:
        """Returns the trimmed session:window string from tmux."""
        mock_result = MagicMock(returncode=0, stdout="main:code\n")
        with patch("session_complete_notify.subprocess.run", return_value=mock_result):
            result = _get_tmux_session()

        assert result == "main:code"

    @pytest.mark.integration
    def test_returns_none_on_empty_output(self) -> None:
        """Empty stdout from tmux returns None."""
        mock_result = MagicMock(returncode=0, stdout="   \n")
        with patch("session_complete_notify.subprocess.run", return_value=mock_result):
            result = _get_tmux_session()

        assert result is None

    @pytest.mark.integration
    def test_returns_none_on_nonzero_exit(self) -> None:
        """Nonzero returncode returns None."""
        mock_result = MagicMock(returncode=1, stdout="error output\n")
        with patch("session_complete_notify.subprocess.run", return_value=mock_result):
            result = _get_tmux_session()

        assert result is None

    @pytest.mark.integration
    def test_returns_none_on_timeout(self) -> None:
        """TimeoutExpired is silently handled and returns None."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="tmux", timeout=0.5),
        ):
            result = _get_tmux_session()

        assert result is None

    @pytest.mark.integration
    def test_returns_none_when_tmux_not_found(self) -> None:
        """FileNotFoundError (tmux not installed) returns None."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = _get_tmux_session()

        assert result is None


# ---------------------------------------------------------------------------
# 4. notify_wsl(): CalledProcessError and TimeoutExpired continue paths
# ---------------------------------------------------------------------------


class TestNotifyWSLContinuePaths:
    """Test that notify_wsl() continues past CalledProcessError and
    TimeoutExpired instead of raising, and tries all three PS paths."""

    @pytest.mark.integration
    def test_called_process_error_continues_to_next_path(self) -> None:
        """CalledProcessError on path 1 continues to path 2, which succeeds."""
        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise subprocess.CalledProcessError(1, cmd)
            return MagicMock(returncode=0)

        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_wsl("Title", "Body")

        assert result is True
        assert call_count == 2

    @pytest.mark.integration
    def test_timeout_expired_continues_to_next_path(self) -> None:
        """TimeoutExpired on path 1 continues to path 2, which succeeds."""
        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=3)
            return MagicMock(returncode=0)

        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_wsl("Title", "Body")

        assert result is True
        assert call_count == 2

    @pytest.mark.integration
    def test_burnttoast_path_succeeds_after_all_toast_paths_fail(self) -> None:
        """When all 3 toast paths fail with CalledProcessError, the first
        BurntToast path succeeds and returns True."""
        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            # First 3 calls (toast paths) raise CalledProcessError
            if call_count <= 3:
                raise subprocess.CalledProcessError(1, cmd)
            # 4th call (first BurntToast path) succeeds
            return MagicMock(returncode=0)

        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_wsl("Title", "Body")

        assert result is True
        assert call_count == 4

    @pytest.mark.integration
    def test_title_quotes_escaped_for_burnttoast(self) -> None:
        """Double quotes in title and message are escaped to backtick-quote
        in the BurntToast command."""
        # Make all toast paths fail so BurntToast is attempted
        call_count = 0
        recorded_cmds: list[list[str]] = []

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            recorded_cmds.append(cmd)
            if call_count <= 3:
                raise subprocess.CalledProcessError(1, cmd)
            return MagicMock(returncode=0)

        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_wsl('Say "hello"', 'A "message"')

        assert result is True
        burnt_cmd = recorded_cmds[3][3]  # 4th call, 4th argument
        assert '`"hello`"' in burnt_cmd
        assert '`"message`"' in burnt_cmd


# ---------------------------------------------------------------------------
# 5. notify_linux(): failure modes
# ---------------------------------------------------------------------------


class TestNotifyLinuxFailureModes:
    """Test notify_linux() handles all failure modes gracefully."""

    @pytest.mark.integration
    def test_called_process_error_returns_false(self) -> None:
        """CalledProcessError from notify-send returns False."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "notify-send"),
        ):
            result = notify_linux("Title", "Body")

        assert result is False

    @pytest.mark.integration
    def test_file_not_found_returns_false(self) -> None:
        """Missing notify-send binary returns False."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = notify_linux("Title", "Body")

        assert result is False

    @pytest.mark.integration
    def test_timeout_returns_false(self) -> None:
        """TimeoutExpired from notify-send returns False."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="notify-send", timeout=1),
        ):
            result = notify_linux("Title", "Body")

        assert result is False

    @pytest.mark.integration
    def test_passes_app_name_and_urgency(self) -> None:
        """notify-send is called with --app-name and --urgency flags."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_linux("My Title", "My Body")

        cmd = mock_run.call_args[0][0]
        assert "--app-name=Claude Code" in cmd
        assert "--urgency=normal" in cmd
        assert "My Title" in cmd
        assert "My Body" in cmd


# ---------------------------------------------------------------------------
# 6. notify_macos(): sound flag and failure modes
# ---------------------------------------------------------------------------


class TestNotifyMacosDetails:
    """Test notify_macos() sound control and failure paths."""

    @pytest.mark.integration
    def test_sound_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without CLAUDE_NOTIFICATION_SOUND=0 the AppleScript includes
        sound name."""
        monkeypatch.delenv("CLAUDE_NOTIFICATION_SOUND", raising=False)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_macos("Title", "Body")

        script = mock_run.call_args[0][0][2]
        assert "sound name" in script

    @pytest.mark.integration
    def test_sound_disabled_when_env_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLAUDE_NOTIFICATION_SOUND=0 omits sound from the AppleScript."""
        monkeypatch.setenv("CLAUDE_NOTIFICATION_SOUND", "0")

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_macos("Title", "Body")

        script = mock_run.call_args[0][0][2]
        assert "sound name" not in script

    @pytest.mark.integration
    def test_special_chars_escaped_in_applescript(self) -> None:
        """Backslashes and double quotes in title/message are escaped."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_macos('Say "hi"', "A\\B")

        script = mock_run.call_args[0][0][2]
        # Backslash must be doubled; quote must be escaped
        assert '\\"hi\\"' in script
        assert "A\\\\B" in script

    @pytest.mark.integration
    def test_timeout_returns_false(self) -> None:
        """TimeoutExpired from osascript returns False."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="osascript", timeout=1),
        ):
            result = notify_macos("Title", "Body")

        assert result is False

    @pytest.mark.integration
    def test_called_process_error_returns_false(self) -> None:
        """CalledProcessError from osascript returns False."""
        with patch(
            "session_complete_notify.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "osascript"),
        ):
            result = notify_macos("Title", "Body")

        assert result is False


# ---------------------------------------------------------------------------
# 7. notify_windows(): sound-disabled path
# ---------------------------------------------------------------------------


class TestNotifyWindowsSoundControl:
    """Test notify_windows() sound control via environment variable."""

    @pytest.mark.integration
    def test_sound_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without CLAUDE_NOTIFICATION_SOUND=0 the PS script includes the
        default audio element."""
        monkeypatch.delenv("CLAUDE_NOTIFICATION_SOUND", raising=False)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_windows("Title", "Body")

        ps_script = mock_run.call_args[0][0][3]
        assert "ms-winsoundevent:Notification.Default" in ps_script

    @pytest.mark.integration
    def test_sound_disabled_when_env_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLAUDE_NOTIFICATION_SOUND=0 inserts the silent audio element."""
        monkeypatch.setenv("CLAUDE_NOTIFICATION_SOUND", "0")

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_windows("Title", "Body")

        ps_script = mock_run.call_args[0][0][3]
        assert 'audio silent="true"' in ps_script

    @pytest.mark.integration
    def test_html_escaping_in_ps_script(self) -> None:
        """HTML special characters in title/message are escaped before
        injection into the XML template."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_windows("<Title> & more", 'Body with "quotes"')

        ps_script = mock_run.call_args[0][0][3]
        assert "&lt;Title&gt;" in ps_script
        assert "&amp;" in ps_script
        assert "&quot;" in ps_script


# ---------------------------------------------------------------------------
# 8. main(): CLAUDE_NO_NOTIFICATIONS and Popen dispatch
# ---------------------------------------------------------------------------


class TestMainFunction:
    """Test main() environment guard and Popen invocation."""

    @pytest.mark.integration
    def test_claude_no_notifications_exits_early(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLAUDE_NO_NOTIFICATIONS=1 causes main() to sys.exit(0) without
        spawning a subprocess."""
        monkeypatch.setenv("CLAUDE_NO_NOTIFICATIONS", "1")

        with (
            patch("session_complete_notify.subprocess.Popen") as mock_popen,
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        mock_popen.assert_not_called()
        assert exc_info.value.code == 0

    @pytest.mark.integration
    def test_main_spawns_background_process(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without the disable flag, main() calls Popen with --background
        and then exits."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with (
            patch(
                "session_complete_notify.get_session_id",
                return_value="test_session",
            ),
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/test/cwd",
            ),
            patch("session_complete_notify.subprocess.Popen") as mock_popen,
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        mock_popen.assert_called_once()
        popen_cmd = mock_popen.call_args[0][0]
        assert popen_cmd[1] == sys.executable or "--background" in popen_cmd
        assert "--background" in popen_cmd
        assert "test_session" in popen_cmd
        assert "/test/cwd" in popen_cmd
        assert exc_info.value.code == 0

    @pytest.mark.integration
    def test_main_popen_failure_is_silent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When Popen raises, main() prints to stderr but still exits 0."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with (
            patch(
                "session_complete_notify.get_session_id",
                return_value="err_session",
            ),
            patch(
                "session_complete_notify.os.getcwd",
                return_value="/test/cwd",
            ),
            patch(
                "session_complete_notify.subprocess.Popen",
                side_effect=OSError("cannot fork"),
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 0


# ---------------------------------------------------------------------------
# 9. clear_notification_state(): exception handler
# ---------------------------------------------------------------------------


class TestClearNotificationStateExceptionHandler:
    """Test the BLE001 exception handler in clear_notification_state()."""

    @pytest.mark.integration
    def test_exception_in_get_session_id_is_caught(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """If get_session_id() raises, the error is printed to stderr and
        does not propagate."""
        with patch(
            "session_complete_notify.get_session_id",
            side_effect=RuntimeError("boom"),
        ):
            clear_notification_state()  # must not raise

        captured = capsys.readouterr()
        assert "clear_notification_state" in captured.err
        assert "boom" in captured.err

    @pytest.mark.integration
    def test_exception_in_load_is_caught(self, capsys: pytest.CaptureFixture) -> None:
        """If NotificationState.load() raises, the error is caught and
        printed to stderr."""
        with (
            patch(
                "session_complete_notify.get_session_id",
                return_value="ex_session",
            ),
            patch.object(
                NotificationState,
                "load",
                side_effect=PermissionError("no access"),
            ),
        ):
            clear_notification_state()  # must not raise

        captured = capsys.readouterr()
        assert "clear_notification_state" in captured.err
