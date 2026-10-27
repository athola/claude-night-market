"""Tests for phantom.display - the OS-level action executor.

Feature: Display Toolkit
    As an automation developer
    I want to translate Claude's abstract actions into OS commands
    So that the agent loop can control a desktop environment
"""

from __future__ import annotations

import base64
import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from phantom import display as display_module
from phantom.display import (
    ActionResult,
    DisplayConfig,
    DisplayToolkit,
    check_display_environment,
)


class TestDisplayConfig:
    """Feature: Display configuration with sensible defaults."""

    def test_default_config_has_standard_resolution(self):
        """
        Scenario: Default display config
        Given no custom configuration
        When a DisplayConfig is created
        Then it uses 1920x1080 resolution
        """
        config = DisplayConfig()
        assert config.width == 1920
        assert config.height == 1080

    def test_custom_config_overrides_defaults(self):
        """
        Scenario: Custom display config
        Given specific resolution values
        When a DisplayConfig is created with those values
        Then it uses the custom resolution
        """
        config = DisplayConfig(width=1024, height=768)
        assert config.width == 1024
        assert config.height == 768


class TestActionResult:
    """Feature: Structured action results."""

    def test_success_result(self):
        result = ActionResult(success=True, screenshot_b64="abc123")
        assert result.success is True
        assert result.screenshot_b64 == "abc123"
        assert result.error is None

    def test_failure_result(self):
        result = ActionResult(success=False, error="boom")
        assert result.success is False
        assert result.error == "boom"


class TestDisplayToolkitActionRouting:
    """Feature: Action routing to correct handlers."""

    def test_unknown_action_returns_error(self, toolkit):
        """
        Scenario: Unknown action type
        Given a display toolkit
        When an unknown action type is executed
        Then it returns an error result
        """
        result = toolkit.execute({"action": "fly_to_moon"})
        assert result.success is False
        assert "Unknown action" in result.error

    def test_screenshot_action_dispatches(self, toolkit):
        """
        Scenario: Screenshot action
        Given a display toolkit
        When a screenshot action is executed
        Then it calls the screenshot handler
        """
        with patch("phantom.display._run") as mock_run:
            mock_run.side_effect = lambda cmd, **kw: Path(cmd[-1]).write_bytes(b"png")
            result = toolkit.execute({"action": "screenshot"})
        assert mock_run.call_args.args[0][0] == "scrot"
        assert result.success is True
        assert base64.b64decode(result.screenshot_b64) == b"png"

    def test_left_click_action_dispatches(self, toolkit):
        """
        Scenario: Left click action
        Given a display toolkit
        When a left_click action is executed
        Then it calls the click handler
        """
        with patch("phantom.display._run") as mock_run:
            result = toolkit.execute({"action": "left_click", "coordinate": [100, 200]})
        mock_run.assert_called_once_with(
            ["xdotool", "mousemove", "100", "200", "click", "--repeat", "1", "1"]
        )
        assert result.success is True


class TestClickActions:
    """Feature: Mouse click execution via xdotool."""

    @patch("phantom.display._run")
    def test_left_click_at_coordinates(self, mock_run, toolkit):
        """
        Scenario: Click at specific coordinates
        Given coordinates [500, 300]
        When a left_click action executes
        Then xdotool moves to (500,300) and clicks button 1
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_left_click(
            {"action": "left_click", "coordinate": [500, 300]}
        )
        assert result.success is True
        mock_run.assert_called_with(
            ["xdotool", "mousemove", "500", "300", "click", "--repeat", "1", "1"]
        )

    @patch("phantom.display._run")
    def test_click_without_coordinate_fails(self, mock_run, toolkit):
        """
        Scenario: Click without coordinates
        Given no coordinate
        When a left_click action executes
        Then it returns an error
        """
        result = toolkit._do_left_click({"action": "left_click"})
        assert result.success is False
        assert "coordinate" in result.error.lower()

    @patch("phantom.display._run")
    def test_right_click_uses_button_3(self, mock_run, toolkit):
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_right_click(
            {"action": "right_click", "coordinate": [10, 20]}
        )
        assert result.success is True
        mock_run.assert_called_with(
            ["xdotool", "mousemove", "10", "20", "click", "--repeat", "1", "3"]
        )

    @patch("phantom.display._run")
    def test_double_click_repeats_twice(self, mock_run, toolkit):
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_double_click(
            {"action": "double_click", "coordinate": [10, 20]}
        )
        assert result.success is True
        mock_run.assert_called_with(
            ["xdotool", "mousemove", "10", "20", "click", "--repeat", "2", "1"]
        )

    @patch("phantom.display._run")
    def test_click_with_modifier_holds_key(self, mock_run, toolkit):
        """
        Scenario: Shift+click
        Given a shift modifier
        When a left_click action executes
        Then xdotool holds shift, clicks, then releases shift
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_left_click(
            {"action": "left_click", "coordinate": [50, 50], "text": "shift"}
        )
        assert result.success is True
        calls = mock_run.call_args_list
        assert calls[0] == call(["xdotool", "keydown", "shift"])
        assert calls[-1] == call(["xdotool", "keyup", "shift"], check=False)


class TestTypeAction:
    """Feature: Keyboard text input."""

    @patch("phantom.display._run")
    def test_type_sends_text(self, mock_run, toolkit):
        """
        Scenario: Type a string
        Given text "Hello, world!"
        When a type action executes
        Then xdotool types the string
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_type({"action": "type", "text": "Hello, world!"})
        assert result.success is True
        mock_run.assert_called_with(
            ["xdotool", "type", "--clearmodifiers", "Hello, world!"]
        )

    @patch("phantom.display._run")
    def test_type_without_text_fails(self, mock_run, toolkit):
        result = toolkit._do_type({"action": "type"})
        assert result.success is False


class TestKeyAction:
    """Feature: Key press and keyboard shortcuts."""

    @patch("phantom.display._run")
    def test_key_press_single(self, mock_run, toolkit):
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_key({"action": "key", "text": "Return"})
        assert result.success is True
        mock_run.assert_called_with(["xdotool", "key", "Return"])

    @patch("phantom.display._run")
    def test_key_combo_normalized(self, mock_run, toolkit):
        """
        Scenario: Ctrl+S shortcut
        Given key text "ctrl+s"
        When a key action executes
        Then xdotool sends the normalized key combo
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_key({"action": "key", "text": "ctrl+s"})
        assert result.success is True
        mock_run.assert_called_with(["xdotool", "key", "ctrl+s"])


class TestScrollAction:
    """Feature: Scroll at position."""

    @patch("phantom.display._run")
    def test_scroll_down(self, mock_run, toolkit):
        """
        Scenario: Scroll down 3 clicks at position
        Given coordinate [500, 400] and direction "down"
        When a scroll action executes
        Then xdotool scrolls button 5 three times
        """
        mock_run.return_value = MagicMock(returncode=0)
        result = toolkit._do_scroll(
            {
                "action": "scroll",
                "coordinate": [500, 400],
                "scroll_direction": "down",
                "scroll_amount": 3,
            }
        )
        assert result.success is True

    @patch("phantom.display._run")
    def test_scroll_up_uses_button_4(self, mock_run, toolkit):
        mock_run.return_value = MagicMock(returncode=0)
        toolkit._do_scroll(
            {
                "action": "scroll",
                "coordinate": [0, 0],
                "scroll_direction": "up",
                "scroll_amount": 1,
            }
        )
        # The click call should use button 4 for scroll up
        click_call = [c for c in mock_run.call_args_list if "click" in c.args[0]]
        assert len(click_call) == 1
        assert "4" in click_call[0].args[0]


class TestKeyNormalization:
    """Feature: Key name normalization for cross-platform compat."""

    def test_common_key_mappings(self, toolkit):
        assert toolkit._normalize_key("enter") == "Return"
        assert toolkit._normalize_key("esc") == "Escape"
        assert toolkit._normalize_key("backspace") == "BackSpace"
        assert toolkit._normalize_key("tab") == "Tab"
        assert toolkit._normalize_key("cmd") == "super"

    def test_combo_normalization(self, toolkit):
        assert toolkit._normalize_key("ctrl+s") == "ctrl+s"
        assert toolkit._normalize_key("cmd+shift+p") == "super+shift+p"


class TestCheckDisplayEnvironment:
    """Feature: Environment diagnostics."""

    @patch("phantom.display._check_command")
    @patch.dict("os.environ", {"DISPLAY": ":1"}, clear=False)
    def test_detects_x11_display(self, mock_check):
        mock_check.return_value = True
        info = check_display_environment()
        assert info["display"] == ":1"
        assert info["has_display"] is True
        assert info["all_tools_available"] is True

    @patch("phantom.display._check_command")
    @patch.dict("os.environ", {"DISPLAY": "", "WAYLAND_DISPLAY": ""}, clear=False)
    def test_detects_missing_display(self, mock_check):
        mock_check.return_value = False
        info = check_display_environment()
        assert info["has_display"] is False
        assert info["all_tools_available"] is False


class TestDragReleasesButtonOnFailure:
    """Feature: a failed drag must not leave the mouse button pressed."""

    @patch("phantom.display._run")
    def test_drag_that_fails_mid_move_still_sends_mouseup(self, mock_run, toolkit):
        """
        Scenario: xdotool times out while moving with the button down
        Given mousedown succeeded
        When the move to the end point raises
        Then a mouseup is still sent, so later clicks are not drags
        """

        def fail_on_sync_move(cmd, **kwargs):
            if "--sync" in cmd:
                raise subprocess.TimeoutExpired(cmd, 10)
            return MagicMock(returncode=0)

        mock_run.side_effect = fail_on_sync_move

        result = toolkit.execute(
            {
                "action": "left_click_drag",
                "start_coordinate": [10, 10],
                "coordinate": [200, 200],
            }
        )

        assert result.success is False
        sent = [c.args[0] for c in mock_run.call_args_list]
        assert ["xdotool", "mouseup", "1"] in sent


class TestRealInputGuard:
    """Feature: the test suite never drives the real desktop."""

    def test_an_unpatched_click_is_refused_before_xdotool_runs(self, toolkit):
        """
        Scenario: A test forgets to patch _run
        Given the autouse guard in conftest
        When a click reaches the subprocess layer
        Then the action fails with the guard's error, not a real click
        """
        result = toolkit.execute({"action": "left_click", "coordinate": [1, 1]})
        assert result.success is False
        assert "real desktop command" in result.error
        assert "xdotool" in result.error


class TestRunSubprocess:
    """Feature: _run is the only path to xdotool and scrot."""

    def test_run_applies_timeout_and_check_to_subprocess(self, monkeypatch):
        """
        Scenario: A command is dispatched
        Given a recording stand-in for subprocess.run
        When _run is called with a timeout
        Then output is captured as text and the timeout and check flags pass through
        """
        seen = {}

        def record(cmd, **kwargs):
            seen["cmd"] = cmd
            seen.update(kwargs)
            return "done"

        monkeypatch.setattr(display_module.subprocess, "run", record)
        assert display_module._run(["xdotool", "key", "a"], timeout=3) == "done"
        assert seen == {
            "cmd": ["xdotool", "key", "a"],
            "capture_output": True,
            "text": True,
            "timeout": 3,
            "check": True,
        }


class TestExecuteErrorPaths:
    """Feature: subprocess failures become failed ActionResults."""

    @patch("phantom.display._run")
    def test_timeout_becomes_a_timed_out_result(self, mock_run, toolkit):
        mock_run.side_effect = subprocess.TimeoutExpired(["xdotool"], 10)
        result = toolkit.execute({"action": "key", "text": "Return"})
        assert result.success is False
        assert result.error == "Action 'key' timed out"

    @patch("phantom.display._run")
    def test_nonzero_exit_reports_stderr(self, mock_run, toolkit):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["xdotool"], stderr="Can't open display"
        )
        result = toolkit.execute({"action": "key", "text": "Return"})
        assert result.success is False
        assert result.error == "Action 'key' failed: Can't open display"

    @patch("phantom.display._run")
    def test_unexpected_exception_is_reported_not_raised(self, mock_run, toolkit):
        mock_run.side_effect = OSError("xdotool vanished")
        result = toolkit.execute({"action": "key", "text": "Return"})
        assert result.success is False
        assert result.error == "Action 'key' error: xdotool vanished"

    @patch("phantom.display._run")
    def test_non_screenshot_action_waits_the_configured_settle_delay(
        self, mock_run, toolkit, monkeypatch
    ):
        slept = []
        monkeypatch.setattr(display_module.time, "sleep", slept.append)
        toolkit.execute({"action": "key", "text": "Return"})
        assert slept == [toolkit.config.action_delay_ms / 1000]


class TestScreenshot:
    """Feature: screenshots are read back as base64 PNG."""

    @patch("phantom.display._run")
    def test_scrot_output_is_base64_encoded_and_the_temp_file_removed(
        self, mock_run, toolkit
    ):
        written = {}

        def fake_scrot(cmd, **kwargs):
            path = Path(cmd[-1])
            path.write_bytes(b"\x89PNG-bytes")
            written["path"] = path

        mock_run.side_effect = fake_scrot
        result = toolkit.take_screenshot()
        assert result.success is True
        assert base64.b64decode(result.screenshot_b64) == b"\x89PNG-bytes"
        assert mock_run.call_args.args[0][:2] == ["scrot", "-o"]
        assert not written["path"].exists()

    @patch("phantom.display._run")
    def test_imagemagick_import_is_used_when_scrot_is_missing(
        self, mock_run, toolkit, monkeypatch
    ):
        monkeypatch.setattr(display_module, "_check_command", lambda n: n == "import")
        mock_run.side_effect = lambda cmd, **kw: Path(cmd[-1]).write_bytes(b"x")
        result = toolkit.take_screenshot()
        assert result.success is True
        assert mock_run.call_args.args[0][:3] == ["import", "-window", "root"]

    @patch("phantom.display._run")
    def test_no_screenshot_tool_fails_without_running_anything(
        self, mock_run, toolkit, monkeypatch
    ):
        monkeypatch.setattr(display_module, "_check_command", lambda n: False)
        result = toolkit.take_screenshot()
        assert result.success is False
        assert result.error == "No screenshot tool available"
        mock_run.assert_not_called()


class TestMissingDependencies:
    """Feature: missing system tools are reported at construction."""

    def test_missing_tools_are_logged_with_an_install_hint(self, monkeypatch, caplog):
        monkeypatch.setattr(display_module, "_check_command", lambda n: False)
        with caplog.at_level(logging.WARNING, logger="phantom.display"):
            DisplayToolkit()
        assert "xdotool, xclip, scrot (or imagemagick)" in caplog.text
        assert "sudo apt install xdotool xclip scrot" in caplog.text

    def test_no_warning_when_every_tool_is_present(self, monkeypatch, caplog):
        monkeypatch.setattr(display_module, "_check_command", lambda n: True)
        with caplog.at_level(logging.WARNING, logger="phantom.display"):
            DisplayToolkit()
        assert caplog.text == ""


class TestActionArgumentErrors:
    """Feature: malformed actions fail before any input is sent."""

    @patch("phantom.display._run")
    def test_mouse_move_without_coordinate_fails(self, mock_run, toolkit):
        result = toolkit.execute({"action": "mouse_move"})
        assert result.success is False
        assert "coordinate" in result.error
        mock_run.assert_not_called()

    @patch("phantom.display._run")
    def test_drag_without_start_coordinate_fails(self, mock_run, toolkit):
        result = toolkit.execute({"action": "left_click_drag", "coordinate": [1, 1]})
        assert result.success is False
        assert "requires coordinates" in result.error
        mock_run.assert_not_called()

    @patch("phantom.display._run")
    def test_key_without_text_fails(self, mock_run, toolkit):
        result = toolkit.execute({"action": "key"})
        assert result.success is False
        mock_run.assert_not_called()

    @patch("phantom.display._run")
    def test_type_truncates_text_to_4096_characters(self, mock_run, toolkit):
        toolkit.execute({"action": "type", "text": "a" * 5000})
        assert mock_run.call_args.args[0][-1] == "a" * 4096


class TestHeldInputIsReleased:
    """Feature: a key or button pressed down is always released."""

    @patch("phantom.display._run")
    def test_hold_key_releases_the_key_when_the_wait_is_interrupted(
        self, mock_run, toolkit, monkeypatch
    ):
        def interrupted(_seconds):
            raise KeyboardInterrupt

        monkeypatch.setattr(display_module.time, "sleep", interrupted)
        with pytest.raises(KeyboardInterrupt):
            toolkit._do_hold_key({"action": "hold_key", "text": "shift"})
        assert mock_run.call_args_list[-1] == call(
            ["xdotool", "keyup", "shift"], check=False
        )

    @patch("phantom.display._run")
    def test_scroll_modifier_is_released_when_the_scroll_fails(self, mock_run, toolkit):
        def fail_on_click(cmd, **kwargs):
            if "click" in cmd:
                raise subprocess.CalledProcessError(1, cmd, stderr="boom")

        mock_run.side_effect = fail_on_click
        result = toolkit.execute(
            {"action": "scroll", "coordinate": [5, 5], "text": "ctrl"}
        )
        assert result.success is False
        assert mock_run.call_args_list[-1] == call(
            ["xdotool", "keyup", "ctrl"], check=False
        )

    def test_wait_is_capped_at_ten_seconds(self, toolkit, monkeypatch):
        slept = []
        monkeypatch.setattr(display_module.time, "sleep", slept.append)
        assert toolkit._do_wait({"action": "wait", "duration": 60}).success is True
        assert slept == [10]
