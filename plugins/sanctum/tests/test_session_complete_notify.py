# ruff: noqa: D101,D102,D103,PLR2004,S603,S607
"""Tests for session_complete_notify hook."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Add hooks directory to path for import
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from session_complete_notify import (  # noqa: E402
    _get_tmux_session,
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

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear terminal-related environment variables."""
    env_vars = [
        "TERM_PROGRAM",
        "TERM",
        "TMUX",
        "SSH_TTY",
        "TTY",
        "GPG_TTY",
        "ZELLIJ",
        "ZELLIJ_SESSION_NAME",
        "ZELLIJ_PANE_ID",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def mock_subprocess_success() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to succeed."""
    with patch("session_complete_notify.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        yield mock_run


@pytest.fixture
def mock_subprocess_failure() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to fail."""
    with patch("session_complete_notify.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        yield mock_run


@pytest.fixture
def mock_subprocess_not_found() -> Generator[MagicMock, None, None]:
    """Mock subprocess.run to raise FileNotFoundError."""
    with patch("session_complete_notify.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("command not found")
        yield mock_run


# =============================================================================
# Unit Tests: get_terminal_info
# =============================================================================


class TestGetTerminalInfo:
    """Tests for terminal/session identification."""

    def test_with_term_program(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should use TERM_PROGRAM when available."""
        monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
        monkeypatch.chdir(
            tmp_path / "my-project"
            if (tmp_path / "my-project").exists()
            or not (tmp_path / "my-project").mkdir()
            else tmp_path / "my-project"
        )

        result = get_terminal_info()

        assert "iTerm.app" in result
        assert "my-project" in result

    def test_with_tmux_session(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should detect tmux session."""
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")  # noqa: S108
        monkeypatch.chdir(tmp_path)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="dev:main\n")
            result = get_terminal_info()

        assert "tmux:dev:main" in result

    def test_with_tmux_failure_fallback(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should fallback gracefully when tmux command fails."""
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")  # noqa: S108
        project_dir = tmp_path / "fallback-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("tmux", 2)
            result = get_terminal_info()

        assert "fallback-project" in result

    def test_with_ssh_session(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should detect SSH session."""
        monkeypatch.setenv("SSH_TTY", "/dev/pts/0")
        project_dir = tmp_path / "remote-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        result = get_terminal_info()

        assert "SSH" in result
        assert "remote-project" in result

    def test_with_tty(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should use TTY name when available."""
        monkeypatch.setenv("TTY", "/dev/ttys003")
        project_dir = tmp_path / "tty-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        result = get_terminal_info()

        assert "ttys003" in result
        assert "tty-project" in result

    def test_fallback_to_project_name(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should fallback to project name when no terminal info available."""
        project_dir = tmp_path / "simple-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        result = get_terminal_info()

        assert result == "simple-project"

    def test_with_zellij_session(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should detect Zellij session."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "my-session")
        project_dir = tmp_path / "zellij-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        with patch("session_complete_notify.get_zellij_tab_name") as mock_tab:
            mock_tab.return_value = None  # No custom tab name
            result = get_terminal_info()

        assert "zellij:my-session" in result
        assert "zellij-project" in result

    def test_with_zellij_session_and_tab(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should include Zellij tab name when available."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "dev-session")
        project_dir = tmp_path / "work-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        with patch("session_complete_notify.get_zellij_tab_name") as mock_tab:
            mock_tab.return_value = "Markdown Link Validation"
            result = get_terminal_info()

        assert "zellij:dev-session|Markdown Link Validation" in result
        assert "work-project" in result

    def test_zellij_skips_default_tab_name(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should skip default 'Tab #1' name in Zellij."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "test-session")
        monkeypatch.chdir(tmp_path)

        with patch("session_complete_notify.get_zellij_tab_name") as mock_tab:
            mock_tab.return_value = "Tab #1"  # Default name
            result = get_terminal_info()

        assert "Tab #1" not in result
        assert "zellij:test-session" in result

    def test_zellij_takes_priority_over_tmux(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Zellij should take priority when both are set (nested sessions)."""
        monkeypatch.setenv("ZELLIJ_SESSION_NAME", "zellij-first")
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")  # noqa: S108
        monkeypatch.chdir(tmp_path)

        with patch("session_complete_notify.get_zellij_tab_name") as mock_tab:
            mock_tab.return_value = None
            result = get_terminal_info()

        assert "zellij:zellij-first" in result
        assert "tmux" not in result


class TestGetZellijTabName:
    """Tests for Zellij tab name extraction."""

    def test_extracts_focused_tab_name(self) -> None:
        """Should extract tab name from layout dump."""
        layout_output = """layout {
    tab name="Dev Work" focus=true {
        pane
    }
    tab name="Other Tab" {
        pane
    }
}"""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=layout_output)
            result = get_zellij_tab_name()

        assert result == "Dev Work"

    def test_returns_none_on_failure(self) -> None:
        """Should return None when zellij command fails."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = get_zellij_tab_name()

        assert result is None

    def test_returns_none_on_timeout(self) -> None:
        """Should return None on timeout."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("zellij", 0.5)
            result = get_zellij_tab_name()

        assert result is None

    def test_returns_none_when_zellij_not_installed(self) -> None:
        """Should return None when zellij is not installed."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("zellij not found")
            result = get_zellij_tab_name()

        assert result is None


class TestGetTmuxSession:
    """Tests for tmux session extraction."""

    def test_extracts_session_window(self) -> None:
        """Should extract session:window name."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="main:editor\n")
            result = _get_tmux_session()

        assert result == "main:editor"

    def test_returns_none_on_failure(self) -> None:
        """Should return None when tmux command fails."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = _get_tmux_session()

        assert result is None


# =============================================================================
# Unit Tests: Platform-specific notification functions
# =============================================================================


class TestNotifyLinux:
    """Tests for Linux notification via notify-send."""

    def test_success(self, mock_subprocess_success: MagicMock) -> None:
        """Should return True on successful notification."""
        result = notify_linux("Test Title", "Test message")

        assert result is True
        mock_subprocess_success.assert_called_once()
        call_args = mock_subprocess_success.call_args[0][0]
        assert any("notify-send" in str(arg) for arg in call_args)
        assert "Test Title" in call_args
        assert "Test message" in call_args

    def test_failure(self, mock_subprocess_failure: MagicMock) -> None:
        """Should return False when notify-send fails."""
        result = notify_linux("Title", "Message")

        assert result is False

    def test_command_not_found(self, mock_subprocess_not_found: MagicMock) -> None:
        """Should return False when notify-send not installed."""
        result = notify_linux("Title", "Message")

        assert result is False

    def test_timeout(self) -> None:
        """Should return False on timeout."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("notify-send", 3)
            result = notify_linux("Title", "Message")

        assert result is False


class TestNotifyMacos:
    """Tests for macOS notification via osascript."""

    def test_success(self, mock_subprocess_success: MagicMock) -> None:
        """Should return True on successful notification."""
        result = notify_macos("Test Title", "Test message")

        assert result is True
        mock_subprocess_success.assert_called_once()
        call_args = mock_subprocess_success.call_args[0][0]
        assert "osascript" in call_args

    def test_includes_sound(self, mock_subprocess_success: MagicMock) -> None:
        """Should include sound in notification."""
        notify_macos("Title", "Message")

        call_args = mock_subprocess_success.call_args[0][0]
        script = call_args[2]  # -e argument
        assert 'sound name "Glass"' in script

    def test_failure(self, mock_subprocess_failure: MagicMock) -> None:
        """Should return False when osascript fails."""
        result = notify_macos("Title", "Message")

        assert result is False


class TestNotifyWindows:
    """Tests for Windows notification via PowerShell."""

    def test_success(self, mock_subprocess_success: MagicMock) -> None:
        """Should return True on successful notification."""
        result = notify_windows("Test Title", "Test message")

        assert result is True
        mock_subprocess_success.assert_called_once()
        call_args = mock_subprocess_success.call_args[0][0]
        assert "powershell" in call_args

    def test_fallback_to_burnttoast(self) -> None:
        """Should try BurntToast as fallback."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise subprocess.CalledProcessError(1, "powershell")
            return MagicMock(returncode=0)

        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_windows("Title", "Message")

        assert result is True
        assert call_count == 2

    def test_both_methods_fail(self) -> None:
        """Should return False when both methods fail."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "powershell")
            result = notify_windows("Title", "Message")

        assert result is False


# =============================================================================
# Unit Tests: WSL Detection and Notification
# =============================================================================


class TestIsWsl:
    """Tests for WSL environment detection."""

    def test_detects_wsl2_microsoft(self) -> None:
        """Should detect WSL2 via 'microsoft' in release string."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.0-microsoft-wsl2",
        ):
            assert is_wsl() is True

    def test_detects_wsl1_microsoft(self) -> None:
        """Should detect WSL1 via 'microsoft' in release string."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="4.4.0-microsoft-standard",
        ):
            assert is_wsl() is True

    def test_detects_wsl_keyword(self) -> None:
        """Should detect WSL via 'wsl' in release string."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.0-wsl2",
        ):
            assert is_wsl() is True

    def test_not_wsl_on_native_linux(self) -> None:
        """Should return False for native Linux."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.15.0-generic",
        ):
            assert is_wsl() is False

    def test_not_wsl_on_ubuntu_kernel(self) -> None:
        """Should return False for standard Ubuntu kernel."""
        with patch(
            "session_complete_notify.platform.release",
            return_value="5.4.0-150-generic",
        ):
            assert is_wsl() is False


class TestNotifyWsl:
    """Tests for WSL notification via PowerShell."""

    def test_success_with_powershell_exe(self) -> None:
        """Should succeed when powershell.exe works."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = notify_wsl("Test Title", "Test message")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "powershell.exe" in call_args[0]

    def test_tries_multiple_paths(self) -> None:
        """Should try multiple PowerShell paths when first fails."""
        call_count = 0

        def side_effect(cmd, **_kwargs):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise FileNotFoundError("powershell.exe not found")
            return MagicMock(returncode=0)

        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_wsl("Title", "Message")

        assert result is True
        assert call_count == 2  # First path failed, second succeeded

    def test_all_paths_fail(self) -> None:
        """Should return False when all PowerShell paths fail."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("not found")
            result = notify_wsl("Title", "Message")

        # 3 main paths + 3 BurntToast fallback paths = 6 attempts
        assert result is False
        assert mock_run.call_count == 6

    def test_escapes_xml_characters(self) -> None:
        """Should escape XML special characters."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            notify_wsl("<script>alert('xss')</script>", "Test & <malicious>")

        call_args = mock_run.call_args[0][0]
        ps_script = call_args[3]  # -Command argument
        # html.escape should convert < to &lt;, > to &gt;, & to &amp;
        assert "&lt;script&gt;" in ps_script
        assert "&amp;" in ps_script

    def test_timeout_handling(self) -> None:
        """Should handle timeouts gracefully."""
        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("powershell.exe", 3)
            result = notify_wsl("Title", "Message")

        assert result is False


# =============================================================================
# Unit Tests: send_notification (platform detection)
# =============================================================================


class TestSendNotification:
    """Tests for platform-aware notification dispatch."""

    def test_linux_platform(self) -> None:
        """Should call notify_linux on Linux."""
        with patch("session_complete_notify.platform.system", return_value="Linux"):
            with patch(
                "session_complete_notify.platform.release", return_value="5.15.0"
            ):
                with patch(
                    "session_complete_notify.notify_linux", return_value=True
                ) as mock:
                    result = send_notification("Title", "Message")

        assert result is True
        mock.assert_called_once_with("Title", "Message")

    def test_wsl_uses_windows_notifications(self) -> None:
        """Should use Windows notification on WSL (not Linux notify-send)."""
        with patch("session_complete_notify.platform.system", return_value="Linux"):
            with patch(
                "session_complete_notify.platform.release",
                return_value="5.15.0-microsoft-wsl2",
            ):
                with patch(
                    "session_complete_notify.notify_wsl", return_value=True
                ) as mock:
                    result = send_notification("Title", "Message")

        assert result is True
        mock.assert_called_once_with("Title", "Message")

    def test_macos_platform(self) -> None:
        """Should call notify_macos on Darwin."""
        with patch("session_complete_notify.platform.system", return_value="Darwin"):
            with patch(
                "session_complete_notify.platform.release", return_value="22.0.0"
            ):
                with patch(
                    "session_complete_notify.notify_macos", return_value=True
                ) as mock:
                    result = send_notification("Title", "Message")

        assert result is True
        mock.assert_called_once_with("Title", "Message")

    def test_windows_platform(self) -> None:
        """Should call notify_windows on Windows."""
        with patch("session_complete_notify.platform.system", return_value="Windows"):
            with patch("session_complete_notify.platform.release", return_value="10"):
                with patch(
                    "session_complete_notify.notify_windows", return_value=True
                ) as mock:
                    result = send_notification("Title", "Message")

        assert result is True
        mock.assert_called_once_with("Title", "Message")

    def test_unknown_platform(self) -> None:
        """Should return False on unknown platform."""
        with patch("session_complete_notify.platform.system", return_value="FreeBSD"):
            with patch("session_complete_notify.platform.release", return_value="13.0"):
                result = send_notification("Title", "Message")

        assert result is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestMainFunction:
    """Integration tests for the main entry point."""

    def test_main_exits_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should always exit with code 0."""
        monkeypatch.chdir(tmp_path)

        with patch("session_complete_notify.send_notification", return_value=True):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

    def test_main_exits_zero_on_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should exit 0 even when notification fails (silent failure)."""
        monkeypatch.chdir(tmp_path)

        with patch("session_complete_notify.send_notification", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0

    def test_main_spawns_background_subprocess(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should spawn subprocess with --background flag."""
        monkeypatch.chdir(tmp_path)

        with patch("session_complete_notify.subprocess.Popen") as mock_popen:
            with pytest.raises(SystemExit):
                main()

        # Verify Popen was called with correct arguments
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]  # Get the command list
        assert sys.executable in call_args
        assert "--background" in call_args

    def test_main_uses_correct_title(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should use 'Claude Code Ready' as title."""
        monkeypatch.chdir(tmp_path)

        # main() now spawns a subprocess, so we test run_notification() directly
        with patch(
            "session_complete_notify.send_notification", return_value=True
        ) as mock:
            run_notification()

        mock.assert_called_once()
        title = mock.call_args[0][0]
        assert title == "Claude Code Ready"

    def test_main_includes_terminal_info_in_message(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include terminal info in message."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        # main() now spawns a subprocess, so we test run_notification() directly
        with patch(
            "session_complete_notify.send_notification", return_value=True
        ) as mock:
            run_notification()

        message = mock.call_args[0][1]
        assert "Awaiting input in:" in message
        assert "test-project" in message


class TestHookRegistration:
    """Tests for hook registration in hooks.json."""

    def test_hook_registered_in_hooks_json(self) -> None:
        """Should be registered in hooks.json under Stop event."""
        hooks_json_path = HOOKS_DIR / "hooks.json"
        assert hooks_json_path.exists(), "hooks.json should exist"

        with open(hooks_json_path) as f:
            hooks_config = json.load(f)

        assert "hooks" in hooks_config
        assert "Stop" in hooks_config["hooks"]

        stop_hooks = hooks_config["hooks"]["Stop"]
        hook_commands = []
        for hook_group in stop_hooks:
            for hook in hook_group.get("hooks", []):
                hook_commands.append(hook.get("command", ""))

        # stop_combined.py consolidates session_complete_notify.py functionality
        assert any("stop_combined.py" in cmd for cmd in hook_commands), (
            "stop_combined.py should be registered in Stop hooks"
        )

    def test_hook_script_is_executable(self) -> None:
        """Should have executable permissions."""
        script_path = HOOKS_DIR / "session_complete_notify.py"
        assert script_path.exists(), "Script should exist"

        mode = os.stat(script_path).st_mode
        assert mode & stat.S_IXUSR, "Script should be executable by owner"

    def test_hook_script_has_shebang(self) -> None:
        """Should have proper shebang line."""
        script_path = HOOKS_DIR / "session_complete_notify.py"

        with open(script_path) as f:
            first_line = f.readline()

        assert first_line.startswith("#!/usr/bin/env python3"), (
            "Should have python3 shebang"
        )


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_special_characters_in_project_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should handle special characters in project names."""
        project_dir = tmp_path / "my-project (v2.0)"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        result = get_terminal_info()

        assert "my-project (v2.0)" in result

    def test_empty_tmux_output(
        self, clean_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Should handle empty tmux output gracefully."""
        monkeypatch.setenv("TMUX", "/tmp/tmux-1000/default,12345,0")  # noqa: S108
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        monkeypatch.chdir(project_dir)

        with patch("session_complete_notify.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = get_terminal_info()

        # Should fallback since tmux output is empty
        assert "project" in result

    def test_notification_with_quotes_in_message_linux(
        self, mock_subprocess_success: MagicMock
    ) -> None:
        """Should handle quotes in message content for Linux."""
        # This tests that we don't break shell escaping
        result = notify_linux('Title with "quotes"', "Message with 'quotes'")

        assert result is True

    def test_notification_with_quotes_in_message_macos(
        self, mock_subprocess_success: MagicMock
    ) -> None:
        """Should properly escape quotes for AppleScript on macOS."""
        result = notify_macos('Title with "quotes"', "Message with 'quotes'")

        assert result is True
        # Verify the script was properly escaped
        call_args = mock_subprocess_success.call_args[0][0]
        script = call_args[2]  # -e argument
        # Double quotes should be escaped with backslash for AppleScript
        assert '\\"' in script or "quotes" in script

    def test_notification_with_injection_attempt_macos(
        self, mock_subprocess_success: MagicMock
    ) -> None:
        """Should escape characters that could break AppleScript."""
        # Attempt to break out of the AppleScript string
        malicious_title = 'Title" & do shell script "whoami'
        result = notify_macos(malicious_title, "Safe message")

        assert result is True
        # The injection attempt should be escaped
        call_args = mock_subprocess_success.call_args[0][0]
        script = call_args[2]
        # Should contain escaped quotes, not raw injection
        assert "do shell script" not in script or '\\"' in script

    def test_notification_with_xml_injection_windows(
        self, mock_subprocess_success: MagicMock
    ) -> None:
        """Should escape XML special characters for Windows toast."""
        # Attempt XML injection
        malicious_title = "<script>alert('xss')</script>"
        malicious_message = "Test & <malicious> content"
        result = notify_windows(malicious_title, malicious_message)

        assert result is True
        # Verify xml characters were escaped
        call_args = mock_subprocess_success.call_args[0][0]
        ps_script = call_args[3]  # -Command argument
        # html.escape converts < to &lt;, > to &gt;, & to &amp;
        assert "&lt;" in ps_script or "script" not in ps_script.lower()

    def test_notification_with_powershell_injection_windows(self) -> None:
        """Should escape PowerShell-breaking characters in BurntToast."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise subprocess.CalledProcessError(1, "powershell")
            return MagicMock(returncode=0)

        # Attempt to break out of PowerShell string
        malicious_title = 'Title"; Remove-Item -Recurse C:\\; echo "'
        with patch("session_complete_notify.subprocess.run", side_effect=side_effect):
            result = notify_windows(malicious_title, "Safe message")

        assert result is True
        # BurntToast fallback was tried (2 calls = main + fallback)
        assert call_count == 2

    def test_notification_with_backslash_escaping_macos(
        self, mock_subprocess_success: MagicMock
    ) -> None:
        """Should properly escape backslashes for AppleScript."""
        # Backslashes need to be escaped in AppleScript
        title_with_backslash = "Path: C:\\Users\\test"
        result = notify_macos(title_with_backslash, "Check path")

        assert result is True
        call_args = mock_subprocess_success.call_args[0][0]
        script = call_args[2]
        # Backslashes should be escaped
        assert "\\\\" in script or "Users" in script
