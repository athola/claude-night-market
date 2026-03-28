"""Display toolkit: translate Claude actions into OS-level commands.

Supports Linux (xdotool + scrot) and headless Docker (Xvfb)
environments. Each action maps to a subprocess call.
"""

from __future__ import annotations

import base64
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DisplayConfig:
    """Configuration for a display environment."""

    width: int = 1920
    height: int = 1080
    display_number: int = 1
    screenshot_format: str = "png"
    action_delay_ms: int = 100


@dataclass
class ActionResult:
    """Result of executing a display action."""

    success: bool
    screenshot_b64: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _check_command(name: str) -> bool:
    """Check if a system command is available."""
    return shutil.which(name) is not None


def _run(
    cmd: list[str],
    timeout: int = 10,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a subprocess with timeout and error handling."""
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


class DisplayToolkit:
    """Execute computer use actions on a display.

    Translates Claude's tool_use actions into real mouse/keyboard
    commands using xdotool and captures screenshots with scrot.
    """

    def __init__(self, config: DisplayConfig | None = None) -> None:
        self.config = config or DisplayConfig()
        self._validate_deps()

    def _validate_deps(self) -> None:
        """Check that required system tools are installed."""
        missing = []
        for cmd in ("xdotool", "xclip"):
            if not _check_command(cmd):
                missing.append(cmd)

        # Accept either scrot or ImageMagick import for screenshots
        if not _check_command("scrot") and not _check_command("import"):
            missing.append("scrot (or imagemagick)")

        if missing:
            logger.warning(
                "Missing system tools: %s. Install with: sudo apt install %s",
                ", ".join(missing),
                " ".join(m.split(" ")[0] for m in missing),
            )

    def execute(self, action: dict[str, Any]) -> ActionResult:
        """Execute a single computer use action.

        Args:
            action: The action dict from Claude's tool_use response.
                Expected keys: action (str), coordinate, text, etc.

        Returns:
            ActionResult with optional screenshot.
        """
        action_type = action.get("action", "")
        handler = getattr(self, f"_do_{action_type}", None)

        if handler is None:
            return ActionResult(
                success=False,
                error=f"Unknown action: {action_type}",
            )

        try:
            result: ActionResult = handler(action)
            # Brief pause to let UI settle after actions
            if action_type != "screenshot":
                time.sleep(self.config.action_delay_ms / 1000)
            return result
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                error=f"Action '{action_type}' timed out",
            )
        except subprocess.CalledProcessError as e:
            return ActionResult(
                success=False,
                error=f"Action '{action_type}' failed: {e.stderr}",
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=f"Action '{action_type}' error: {e}",
            )

    def take_screenshot(self) -> ActionResult:
        """Capture the current display as a base64-encoded PNG."""
        return self._do_screenshot({})

    # --- Action handlers ---

    def _do_screenshot(self, action: dict[str, Any]) -> ActionResult:
        """Capture the display."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            if _check_command("scrot"):
                _run(["scrot", "-o", tmp_path])
            elif _check_command("import"):
                _run(
                    [
                        "import",
                        "-window",
                        "root",
                        tmp_path,
                    ]
                )
            else:
                return ActionResult(
                    success=False,
                    error="No screenshot tool available",
                )

            img_bytes = Path(tmp_path).read_bytes()
            b64 = base64.standard_b64encode(img_bytes).decode("ascii")
            return ActionResult(success=True, screenshot_b64=b64)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _do_left_click(self, action: dict[str, Any]) -> ActionResult:
        """Click at coordinates."""
        return self._click(action, button=1)

    def _do_right_click(self, action: dict[str, Any]) -> ActionResult:
        return self._click(action, button=3)

    def _do_middle_click(self, action: dict[str, Any]) -> ActionResult:
        return self._click(action, button=2)

    def _do_double_click(self, action: dict[str, Any]) -> ActionResult:
        return self._click(action, button=1, repeat=2)

    def _do_triple_click(self, action: dict[str, Any]) -> ActionResult:
        return self._click(action, button=1, repeat=3)

    def _click(
        self,
        action: dict[str, Any],
        button: int = 1,
        repeat: int = 1,
    ) -> ActionResult:
        """Execute a click at the given coordinate."""
        coord = action.get("coordinate")
        if not coord or len(coord) != 2:
            return ActionResult(
                success=False,
                error="Click requires coordinate [x, y]",
            )
        x, y = int(coord[0]), int(coord[1])

        # Handle modifier keys
        modifier = action.get("text")
        held_keys: list[str] = []
        if modifier:
            held_keys = self._parse_modifier(modifier)
            for key in held_keys:
                _run(["xdotool", "keydown", key])

        try:
            cmd = [
                "xdotool",
                "mousemove",
                str(x),
                str(y),
                "click",
                "--repeat",
                str(repeat),
                str(button),
            ]
            _run(cmd)
            return ActionResult(success=True)
        finally:
            for key in reversed(held_keys):
                _run(["xdotool", "keyup", key], check=False)

    def _do_mouse_move(self, action: dict[str, Any]) -> ActionResult:
        """Move mouse to coordinates."""
        coord = action.get("coordinate")
        if not coord or len(coord) != 2:
            return ActionResult(
                success=False,
                error="mouse_move requires coordinate [x, y]",
            )
        x, y = int(coord[0]), int(coord[1])
        _run(["xdotool", "mousemove", str(x), str(y)])
        return ActionResult(success=True)

    def _do_left_click_drag(self, action: dict[str, Any]) -> ActionResult:
        """Click and drag from start to end coordinate."""
        start = action.get("start_coordinate")
        end = action.get("coordinate")
        if not start or not end:
            return ActionResult(
                success=False,
                error="left_click_drag requires coordinates",
            )
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])

        _run(["xdotool", "mousemove", str(sx), str(sy)])
        _run(["xdotool", "mousedown", "1"])
        _run(["xdotool", "mousemove", "--sync", str(ex), str(ey)])
        _run(["xdotool", "mouseup", "1"])
        return ActionResult(success=True)

    def _do_type(self, action: dict[str, Any]) -> ActionResult:
        """Type text string."""
        text = action.get("text", "")
        if not text:
            return ActionResult(
                success=False,
                error="type requires text",
            )
        # Cap length to prevent blocking the event loop
        _MAX_TYPE_LEN = 4096
        if len(text) > _MAX_TYPE_LEN:
            text = text[:_MAX_TYPE_LEN]
        # xdotool type handles special characters
        _run(["xdotool", "type", "--clearmodifiers", text])
        return ActionResult(success=True)

    def _do_key(self, action: dict[str, Any]) -> ActionResult:
        """Press a key or key combination (e.g., 'ctrl+s')."""
        text = action.get("text", "")
        if not text:
            return ActionResult(
                success=False,
                error="key requires text (key name)",
            )
        # Map common key names to xdotool format
        key = self._normalize_key(text)
        _run(["xdotool", "key", key])
        return ActionResult(success=True)

    def _do_scroll(self, action: dict[str, Any]) -> ActionResult:
        """Scroll at position."""
        coord = action.get("coordinate", [0, 0])
        direction = action.get("scroll_direction", "down")
        amount = int(action.get("scroll_amount", 3))

        x, y = int(coord[0]), int(coord[1])
        _run(["xdotool", "mousemove", str(x), str(y)])

        # xdotool: button 4 = scroll up, 5 = scroll down
        # 6 = scroll left, 7 = scroll right
        button_map = {
            "up": "4",
            "down": "5",
            "left": "6",
            "right": "7",
        }
        btn = button_map.get(direction, "5")

        modifier = action.get("text")
        held_keys: list[str] = []
        if modifier:
            held_keys = self._parse_modifier(modifier)
            for key in held_keys:
                _run(["xdotool", "keydown", key])

        try:
            _run(
                [
                    "xdotool",
                    "click",
                    "--repeat",
                    str(amount),
                    btn,
                ]
            )
            return ActionResult(success=True)
        finally:
            for key in reversed(held_keys):
                _run(["xdotool", "keyup", key], check=False)

    def _do_hold_key(self, action: dict[str, Any]) -> ActionResult:
        """Hold a key for a duration."""
        text = action.get("text", "")
        duration = float(action.get("duration", 1))
        key = self._normalize_key(text)

        _run(["xdotool", "keydown", key])
        try:
            time.sleep(duration)
        finally:
            _run(["xdotool", "keyup", key], check=False)
        return ActionResult(success=True)

    def _do_wait(self, action: dict[str, Any]) -> ActionResult:
        """Pause between actions."""
        duration = float(action.get("duration", 1))
        time.sleep(min(duration, 10))  # Cap at 10s
        return ActionResult(success=True)

    def _do_left_mouse_down(self, action: dict[str, Any]) -> ActionResult:
        coord = action.get("coordinate")
        if coord:
            _run(["xdotool", "mousemove", str(int(coord[0])), str(int(coord[1]))])
        _run(["xdotool", "mousedown", "1"])
        return ActionResult(success=True)

    def _do_left_mouse_up(self, action: dict[str, Any]) -> ActionResult:
        coord = action.get("coordinate")
        if coord:
            _run(["xdotool", "mousemove", str(int(coord[0])), str(int(coord[1]))])
        _run(["xdotool", "mouseup", "1"])
        return ActionResult(success=True)

    # --- Helpers ---

    @staticmethod
    def _normalize_key(key_str: str) -> str:
        """Normalize key names to xdotool format."""
        replacements = {
            "ctrl": "ctrl",
            "cmd": "super",
            "command": "super",
            "option": "alt",
            "enter": "Return",
            "return": "Return",
            "esc": "Escape",
            "escape": "Escape",
            "tab": "Tab",
            "space": "space",
            "backspace": "BackSpace",
            "delete": "Delete",
            "up": "Up",
            "down": "Down",
            "left": "Left",
            "right": "Right",
        }
        parts = key_str.split("+")
        normalized = []
        for part in parts:
            p = part.strip().lower()
            normalized.append(replacements.get(p, p))
        return "+".join(normalized)

    @staticmethod
    def _parse_modifier(modifier: str) -> list[str]:
        """Parse modifier key for held-key operations."""
        mod_map = {
            "shift": "shift",
            "ctrl": "ctrl",
            "alt": "alt",
            "super": "super",
            "command": "super",
            "cmd": "super",
        }
        return [mod_map.get(modifier.lower(), modifier.lower())]


def check_display_environment() -> dict[str, Any]:
    """Check the current display environment and available tools.

    Returns a dict with availability info for use in diagnostics.
    """
    display = os.environ.get("DISPLAY", "")
    wayland = os.environ.get("WAYLAND_DISPLAY", "")

    tools = {}
    for cmd in ("xdotool", "scrot", "import", "xclip", "xdg-open"):
        tools[cmd] = _check_command(cmd)

    return {
        "display": display,
        "wayland_display": wayland,
        "has_display": bool(display or wayland),
        "tools": tools,
        "all_tools_available": all(tools.get(t, False) for t in ("xdotool", "xclip"))
        and (tools.get("scrot", False) or tools.get("import", False)),
    }
