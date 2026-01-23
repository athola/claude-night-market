# ruff: noqa: D101,D102,D103,PLR2004,S603,S607
"""Tests for session_complete_notify hook - cross-platform toast notifications.

Tests the notification system that alerts users when Claude session
awaits input, supporting Linux, macOS, Windows, and WSL platforms.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from session_complete_notify import (
    get_terminal_info,
    get_zellij_tab_name,
    is_wsl,
    main,
    notify_linux,
    notify_macos,
    notify_windows,
    notify_wsl,
    run_notification,
    send_notification,
)


class TestTerminalInfoDetection:
    """Tests for terminal/session information detection."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_project_name_without_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given no session environment, returns project name from cwd."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.delenv("SSH_TTY", raising=False)
        monkeypatch.delenv("TTY", raising=False)
        monkeypatch.delenv("GPG_TTY", raising=False)

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/myproject"
        ):
            result = get_terminal_info()

        assert result == "myproject"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_zellij_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given ZELLIJ_SESSION_NAME, includes it in terminal info."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "dev-session")
        monkeypatch.delenv("TMUX", raising=False)

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/project"
        ):
            with patch(
                "session_complete_notify.get_zellij_tab_name", return_value=None
            ):
                result = get_terminal_info()

        assert "zellij:dev-session" in result
        assert "project" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_zellij_tab_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given Zellij session with custom tab, includes tab name."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "dev")
        monkeypatch.delenv("TMUX", raising=False)

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/project"
        ):
            with patch(
                "session_complete_notify.get_zellij_tab_name", return_value="my-tab"
            ):
                result = get_terminal_info()

        assert "zellij:dev|my-tab" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skips_default_zellij_tab(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given default Zellij tab name, skips it."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "dev")
        monkeypatch.delenv("TMUX", raising=False)

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/project"
        ):
            with patch(
                "session_complete_notify.get_zellij_tab_name", return_value="Tab #1"
            ):
                result = get_terminal_info()

        assert "Tab #1" not in result
        assert "zellij:dev" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_tmux_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given TMUX environment, includes tmux session info."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/project"
        ):
            with patch(
                "session_complete_notify._get_tmux_session", return_value="main:editor"
            ):
                result = get_terminal_info()

        assert "tmux:main:editor" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_term_program(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given TERM_PROGRAM, includes terminal name."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/project"
        ):
            result = get_terminal_info()

        assert "iTerm.app" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_ssh_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given SSH_TTY, identifies SSH session."""
        monkeypatch.delenv("ZELLIJ_SESSION_NAME", raising=False)
        monkeypatch.delenv("TMUX", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)
        monkeypatch.setenv("SSH_TTY", "/dev/pts/0")

        with patch(
            "session_complete_notify.os.getcwd", return_value="/home/user/project"
        ):
            result = get_terminal_info()

        assert "SSH" in result


class TestZellijTabDetection:
    """Tests for Zellij tab name detection."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_parses_focused_tab_from_layout(self) -> None:
        """Given Zellij layout with focused tab, extracts tab name."""
        mock_layout = 'tab name="my-work" focus=true'

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_layout)
            result = get_zellij_tab_name()

        assert result == "my-work"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_on_no_focused_tab(self) -> None:
        """Given layout without focus=true, returns None."""
        mock_layout = 'tab name="other"'

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_layout)
            result = get_zellij_tab_name()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_none_on_command_failure(self) -> None:
        """Given zellij command failure, returns None."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = get_zellij_tab_name()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_timeout(self) -> None:
        """Given command timeout, returns None gracefully."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired("zellij", 0.5)
            result = get_zellij_tab_name()

        assert result is None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_missing_zellij(self) -> None:
        """Given zellij not installed, returns None gracefully."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = get_zellij_tab_name()

        assert result is None


class TestWSLDetection:
    """Tests for Windows Subsystem for Linux detection."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_wsl_from_microsoft_release(self) -> None:
        """Given 'microsoft' in platform release, identifies as WSL."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.90.1-microsoft-standard-WSL2",
        ):
            assert is_wsl() is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_wsl_from_wsl_release(self) -> None:
        """Given 'wsl' in platform release, identifies as WSL."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.90.1-wsl2",
        ):
            assert is_wsl() is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_not_wsl_on_regular_linux(self) -> None:
        """Given regular Linux kernel, not identified as WSL."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.0-91-generic",
        ):
            assert is_wsl() is False


class TestPlatformNotifications:
    """Tests for platform-specific notification functions."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_linux_notify_calls_notify_send(self) -> None:
        """Given Linux platform, uses notify-send command."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = notify_linux("Test Title", "Test Message")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/usr/bin/notify-send" in call_args
        assert "Test Title" in call_args
        assert "Test Message" in call_args

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_linux_notify_handles_missing_notifysend(self) -> None:
        """Given notify-send not found, returns False gracefully."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = notify_linux("Title", "Message")

        assert result is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_macos_notify_calls_osascript(self) -> None:
        """Given macOS platform, uses osascript command."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = notify_macos("Test Title", "Test Message")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "osascript" in call_args
        assert "-e" in call_args

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_macos_escapes_special_characters(self) -> None:
        """Given special characters in message, escapes them properly."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_macos('Title with "quotes"', "Message with \\backslash")

        # Should have escaped the quotes and backslashes
        call_args = mock_run.call_args[0][0]
        script = call_args[2]  # The -e argument
        assert '\\"' in script or "\\\\" in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_windows_notify_calls_powershell(self) -> None:
        """Given Windows platform, uses PowerShell toast."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = notify_windows("Test Title", "Test Message")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "powershell" in call_args

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_windows_escapes_xml_characters(self) -> None:
        """Given HTML/XML characters in message, escapes them."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_windows("Title <script>", "Message with & ampersand")

        call_args = mock_run.call_args[0][0]
        script = call_args[3]  # The -Command argument
        # Should have escaped < > and &
        assert "&lt;" in script or "&amp;" in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_wsl_tries_multiple_powershell_paths(self) -> None:
        """Given WSL environment, tries multiple PowerShell paths."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            # First path fails, second succeeds
            mock_run.side_effect = [FileNotFoundError(), MagicMock(returncode=0)]
            result = notify_wsl("Test", "Message")

        # Should have tried at least 2 paths
        assert mock_run.call_count >= 2
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_wsl_returns_false_when_all_paths_fail(self) -> None:
        """Given no working PowerShell path, returns False."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = notify_wsl("Test", "Message")

        assert result is False


class TestSendNotification:
    """Tests for platform-aware notification dispatch."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_routes_to_linux(self) -> None:
        """Given Linux platform (not WSL), routes to Linux notifier."""
        with patch("session_complete_notify.platform.system", return_value="Linux"):
            with patch("session_complete_notify.is_wsl", return_value=False):
                with patch("session_complete_notify.notify_linux") as mock_linux:
                    mock_linux.return_value = True
                    result = send_notification("Test", "Message")

        mock_linux.assert_called_once_with("Test", "Message")
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_routes_to_wsl_on_linux_with_wsl(self) -> None:
        """Given Linux platform with WSL detected, routes to WSL notifier."""
        with patch("session_complete_notify.platform.system", return_value="Linux"):
            with patch("session_complete_notify.is_wsl", return_value=True):
                with patch("session_complete_notify.notify_wsl") as mock_wsl:
                    mock_wsl.return_value = True
                    result = send_notification("Test", "Message")

        mock_wsl.assert_called_once_with("Test", "Message")
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_routes_to_macos(self) -> None:
        """Given macOS platform, routes to macOS notifier."""
        with patch("session_complete_notify.platform.system", return_value="Darwin"):
            with patch("session_complete_notify.notify_macos") as mock_macos:
                mock_macos.return_value = True
                result = send_notification("Test", "Message")

        mock_macos.assert_called_once_with("Test", "Message")
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_routes_to_windows(self) -> None:
        """Given Windows platform, routes to Windows notifier."""
        with patch("session_complete_notify.platform.system", return_value="Windows"):
            with patch("session_complete_notify.notify_windows") as mock_win:
                mock_win.return_value = True
                result = send_notification("Test", "Message")

        mock_win.assert_called_once_with("Test", "Message")
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_false_for_unknown_platform(self) -> None:
        """Given unknown platform, returns False."""
        with patch("session_complete_notify.platform.system", return_value="AIX"):
            result = send_notification("Test", "Message")

        assert result is False


class TestMainEntryPoint:
    """Tests for hook main entry point."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exits_when_notifications_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given CLAUDE_NO_NOTIFICATIONS=1, exits without spawning."""
        monkeypatch.setenv("CLAUDE_NO_NOTIFICATIONS", "1")

        with patch("session_complete_notify.subprocess.Popen") as mock_popen:
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_popen.assert_not_called()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_spawns_background_process(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given notifications enabled, spawns background process."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with patch("session_complete_notify.subprocess.Popen") as mock_popen:
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert "--background" in call_args

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_spawns_detached_process(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given spawn request, creates detached session."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with patch("session_complete_notify.subprocess.Popen") as mock_popen:
            with pytest.raises(SystemExit):
                main()

        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs.get("start_new_session") is True

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fails_silently_on_spawn_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given Popen failure, exits cleanly without error."""
        monkeypatch.delenv("CLAUDE_NO_NOTIFICATIONS", raising=False)

        with patch("session_complete_notify.subprocess.Popen") as mock_popen:
            mock_popen.side_effect = OSError("spawn failed")
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Should still exit 0 (notifications are non-critical)
        assert exc_info.value.code == 0


class TestRunNotification:
    """Tests for background notification execution."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_sends_notification_with_terminal_info(self) -> None:
        """Given background mode, sends notification with terminal context."""
        with patch(
            "session_complete_notify.get_terminal_info",
            return_value="iTerm - myproject",
        ):
            with patch("session_complete_notify.send_notification") as mock_send:
                mock_send.return_value = True
                run_notification()

        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "Claude Code Ready"
        assert "iTerm - myproject" in args[1]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_fails_silently_on_error(self) -> None:
        """Given notification error, does not raise exception."""
        with patch("session_complete_notify.get_terminal_info") as mock_info:
            mock_info.side_effect = RuntimeError("failed to get info")
            # Should not raise
            run_notification()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_notification_message_format(self) -> None:
        """Given successful detection, formats message correctly."""
        with patch(
            "session_complete_notify.get_terminal_info", return_value="tmux:dev:main"
        ):
            with patch("session_complete_notify.send_notification") as mock_send:
                mock_send.return_value = True
                run_notification()

        args = mock_send.call_args[0]
        assert "Awaiting input in:" in args[1]
        assert "tmux:dev:main" in args[1]


class TestNotificationSoundToggle:
    """Tests for CLAUDE_NOTIFICATION_SOUND environment variable."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_macos_sound_enabled_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given no sound env var, macOS notification includes sound by default."""
        monkeypatch.delenv("CLAUDE_NOTIFICATION_SOUND", raising=False)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_macos("Test", "Message")

        call_args = mock_run.call_args[0][0]
        script = call_args[2]  # The osascript script
        assert 'sound name "Glass"' in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_macos_sound_disabled_when_env_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given CLAUDE_NOTIFICATION_SOUND=0, macOS notification is silent."""
        monkeypatch.setenv("CLAUDE_NOTIFICATION_SOUND", "0")

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_macos("Test", "Message")

        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert 'sound name "Glass"' not in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_windows_sound_enabled_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given no sound env var, Windows notification includes sound by default."""
        monkeypatch.delenv("CLAUDE_NOTIFICATION_SOUND", raising=False)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_windows("Test", "Message")

        call_args = mock_run.call_args[0][0]
        script = call_args[3]  # The PowerShell script
        assert "ms-winsoundevent:Notification.Default" in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_windows_sound_disabled_when_env_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given CLAUDE_NOTIFICATION_SOUND=0, Windows notification is silent."""
        monkeypatch.setenv("CLAUDE_NOTIFICATION_SOUND", "0")

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_windows("Test", "Message")

        call_args = mock_run.call_args[0][0]
        script = call_args[3]
        assert 'silent="true"' in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_wsl_sound_enabled_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given no sound env var, WSL notification includes sound by default."""
        monkeypatch.delenv("CLAUDE_NOTIFICATION_SOUND", raising=False)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_wsl("Test", "Message")

        # Should call powershell.exe first
        call_args = mock_run.call_args[0][0]
        script = call_args[3]  # The PowerShell script
        assert "ms-winsoundevent:Notification.Default" in script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_wsl_sound_disabled_when_env_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given CLAUDE_NOTIFICATION_SOUND=0, WSL notification is silent."""
        monkeypatch.setenv("CLAUDE_NOTIFICATION_SOUND", "0")

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_wsl("Test", "Message")

        call_args = mock_run.call_args[0][0]
        script = call_args[3]
        assert 'silent="true"' in script


@pytest.mark.requires_notify_send
class TestIntegrationWithNotifySend:
    """Integration tests requiring notify-send command.

    These tests only run when notify-send is available on the system.
    Use pytest -m "requires_notify_send" to run these tests.
    """

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_actual_linux_notification(self) -> None:
        """Given notify-send installed, sends actual notification."""
        import shutil

        if not shutil.which("notify-send"):
            pytest.skip("notify-send not found on system")

        result = notify_linux("Integration Test", "This is a test notification")
        assert result is True

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_notify_send_not_installed_returns_false(self) -> None:
        """Given notify-send missing, notification returns False gracefully."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = notify_linux("Test", "Message")

        assert result is False
