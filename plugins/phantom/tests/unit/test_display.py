"""Tests for phantom.display - the OS-level action executor.

Feature: Display Toolkit
    As an automation developer
    I want to translate Claude's abstract actions into OS commands
    So that the agent loop can control a desktop environment
"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

from phantom.display import (
    ActionResult,
    DisplayConfig,
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
        with patch.object(
            toolkit, "_do_screenshot", return_value=ActionResult(success=True)
        ) as mock:
            result = toolkit.execute({"action": "screenshot"})
            mock.assert_called_once()
            assert result.success is True

    def test_left_click_action_dispatches(self, toolkit):
        """
        Scenario: Left click action
        Given a display toolkit
        When a left_click action is executed
        Then it calls the click handler
        """
        with patch.object(
            toolkit, "_do_left_click", return_value=ActionResult(success=True)
        ) as mock:
            result = toolkit.execute({"action": "left_click", "coordinate": [100, 200]})
            mock.assert_called_once()
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
