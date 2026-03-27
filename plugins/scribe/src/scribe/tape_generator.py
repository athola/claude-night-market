"""VHS tape generator for session replays.

Converts parsed session turns into VHS .tape files with
Type/Sleep/Enter commands and configurable timing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scribe.session_parser import Turn

from scribe.session_parser import AssistantTurn, ToolResult, ToolUse, UserTurn

# --- Constants ---

SUPPORTED_FORMATS: set[str] = {"gif", "mp4", "webm"}


# --- Configuration ---


@dataclass
class TapeConfig:
    """Configuration for tape generation."""

    output_path: str = "session-replay.gif"
    theme: str = "Dracula"
    width: int = 960
    height: int = 540
    font_size: int = 16
    speed: float = 1.0
    max_duration: float | None = None
    output_format: str | None = None


# --- String escaping ---


def escape_vhs(text: str) -> str:
    """Escape a string for VHS Type double-quoted syntax.

    Rules:
    - Backslash becomes double backslash
    - Double quote becomes backslash double quote
    - Unicode passes through unchanged
    - Newlines are handled externally (split into lines)
    """
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    return text


# --- Timing helpers ---


def _scale_ms(base_ms: float, speed: float) -> int:
    """Scale a duration in ms by the speed multiplier.

    Speed 2.0 halves durations. Speed 0.5 doubles them.
    """
    return max(1, round(base_ms / speed))


# --- Tape generation ---


def _resolve_output_path(config: TapeConfig) -> str:
    """Resolve the output path, applying format override and validation.

    If output_format is set, replaces the extension in output_path.
    Validates the resulting format is in SUPPORTED_FORMATS.

    Raises:
        ValueError: If the resolved format is not supported.
    """
    path = PurePosixPath(config.output_path)

    if config.output_format is not None:
        fmt = config.output_format.lower().lstrip(".")
        if fmt not in SUPPORTED_FORMATS:
            msg = (
                f"Unsupported output format: '{fmt}'. "
                f"Supported formats: {sorted(SUPPORTED_FORMATS)}"
            )
            raise ValueError(msg)
        return str(path.with_suffix(f".{fmt}"))

    # Derive format from extension
    ext = path.suffix.lower().lstrip(".")
    if ext not in SUPPORTED_FORMATS:
        msg = f"Unsupported output format: '{ext}'. Supported formats: {sorted(SUPPORTED_FORMATS)}"
        raise ValueError(msg)
    return config.output_path


def generate_tape(turns: list[Turn], config: TapeConfig) -> str:
    """Generate a VHS tape string from parsed turns.

    Args:
        turns: List of Turn objects from parse_session.
        config: Tape configuration.

    Returns:
        Complete VHS tape file content as a string.
    """
    lines: list[str] = []

    # Resolve output path and validate format
    output_path = _resolve_output_path(config)

    # Header
    lines.append(f"Output {output_path}")
    lines.append("")
    lines.append(f"Set Width {config.width}")
    lines.append(f"Set Height {config.height}")
    lines.append(f"Set FontSize {config.font_size}")
    lines.append(f'Set Theme "{config.theme}"')
    lines.append("")

    # Duration tracking
    elapsed_ms: float = 0.0
    max_ms = config.max_duration * 1000 if config.max_duration else None
    turns_rendered = 0
    total_turns = len(turns)

    for i, turn in enumerate(turns):
        # Check duration budget before rendering
        if max_ms is not None and turns_rendered > 0 and elapsed_ms >= max_ms:
            remaining = total_turns - i
            if remaining > 0:
                msg = f"... ({remaining} more turns)"
                _type_ms = _scale_ms(100, config.speed)
                lines.append(f'Type@{_type_ms}ms "{escape_vhs(msg)}"')
                lines.append("Enter")
            break

        # Pause between turns (not before the first one)
        if i > 0:
            pause_ms = _scale_ms(1500, config.speed)
            lines.append(f"Sleep {pause_ms}ms")
            elapsed_ms += pause_ms
            lines.append("")

        # Render the turn
        turn_ms = _render_turn(lines, turn, config)
        elapsed_ms += turn_ms
        turns_rendered += 1

    # Final hold
    lines.append("")
    final_ms = _scale_ms(3000, config.speed)
    lines.append(f"Sleep {final_ms}ms")

    return "\n".join(lines) + "\n"


def _render_turn(lines: list[str], turn: Turn, config: TapeConfig) -> float:
    """Render a single turn into tape lines. Returns duration in ms."""
    if isinstance(turn, UserTurn):
        return _render_user_turn(lines, turn, config)
    if isinstance(turn, AssistantTurn):
        return _render_assistant_turn(lines, turn, config)
    if isinstance(turn, ToolUse):
        return _render_tool_use(lines, turn, config)
    if isinstance(turn, ToolResult):
        return _render_tool_result(lines, turn, config)
    return 0.0


def _render_user_turn(lines: list[str], turn: UserTurn, config: TapeConfig) -> float:
    """Render a user turn. Returns duration in ms."""
    type_ms = _scale_ms(30, config.speed)
    elapsed = 0.0

    text_lines = turn.text.split("\n")
    for j, text_line in enumerate(text_lines):
        prefix = "$ " if j == 0 else ""
        escaped = escape_vhs(f"{prefix}{text_line}")
        lines.append(f'Type@{type_ms}ms "{escaped}"')
        lines.append("Enter")
        # Duration: chars * type_ms + 50ms for Enter
        char_count = len(f"{prefix}{text_line}")
        elapsed += char_count * type_ms + _scale_ms(50, config.speed)

    return elapsed


def _render_assistant_turn(
    lines: list[str], turn: AssistantTurn, config: TapeConfig
) -> float:
    """Render an assistant turn. Returns duration in ms."""
    type_ms = _scale_ms(15, config.speed)
    elapsed = 0.0

    text_lines = turn.text.split("\n")
    for text_line in text_lines:
        escaped = escape_vhs(text_line)
        lines.append(f'Type@{type_ms}ms "{escaped}"')
        lines.append("Enter")
        elapsed += len(text_line) * type_ms + _scale_ms(50, config.speed)

    return elapsed


def _render_tool_use(lines: list[str], turn: ToolUse, config: TapeConfig) -> float:
    """Render a tool use summary. Returns duration in ms."""
    type_ms = _scale_ms(100, config.speed)
    escaped = escape_vhs(f"  {turn.summary}")
    lines.append(f'Type@{type_ms}ms "{escaped}"')
    lines.append("Enter")
    return type_ms + _scale_ms(50, config.speed)


def _render_tool_result(
    lines: list[str], turn: ToolResult, config: TapeConfig
) -> float:
    """Render a tool result. Returns duration in ms."""
    type_ms = _scale_ms(100, config.speed)
    escaped = escape_vhs(f"  [result: {turn.tool_use_id}]")
    lines.append(f'Type@{type_ms}ms "{escaped}"')
    lines.append("Enter")
    return type_ms + _scale_ms(50, config.speed)
