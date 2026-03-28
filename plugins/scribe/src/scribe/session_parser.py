"""Session parser for Claude Code and Codex JSONL files.

Reads session JSONL from ~/.claude/projects/ (Claude Code)
or ~/.codex/sessions/ (Codex), extracts turns, filters by
type, layer, and range, and collapses tool calls into
readable summaries.

Supports auto-detection of session format from file content.
"""

from __future__ import annotations

import json
import logging
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# --- Data classes ---


@dataclass
class Turn:
    """Base class for all turn types."""


@dataclass
class UserTurn(Turn):
    """A human-typed message."""

    text: str = ""


@dataclass
class AssistantTurn(Turn):
    """A Claude text response."""

    text: str = ""


@dataclass
class ToolUse(Turn):
    """A tool call made by Claude."""

    tool_name: str = ""
    summary: str = ""
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult(Turn):
    """A tool result returned to Claude."""

    tool_use_id: str = ""
    content: str = ""


# --- Session discovery ---


_PREVIEW_MAX_LINES = 50
_MESSAGE_TRUNCATE_LEN = 120


@dataclass
class SessionInfo:
    """Metadata about a discovered session file."""

    path: Path
    modified: float  # mtime timestamp
    first_user_message: str
    turn_count: int
    project_name: str  # parent directory name


def _preview_session(path: Path) -> tuple[str, int]:
    """Read the first lines of a session file to extract preview metadata.

    Returns (first_user_message, turn_count) by scanning up to
    _PREVIEW_MAX_LINES for user records with string content.
    """
    first_message = ""
    turn_count = 0

    try:
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= _PREVIEW_MAX_LINES:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                if record.get("type") != "user":
                    continue

                content = record.get("message", {}).get("content")
                if not isinstance(content, str):
                    continue

                turn_count += 1
                if not first_message:
                    first_message = content
    except OSError:
        return "", 0

    # Truncate long messages for display
    if len(first_message) > _MESSAGE_TRUNCATE_LEN:
        first_message = first_message[:_MESSAGE_TRUNCATE_LEN] + "..."

    return first_message, turn_count


def list_sessions(
    base_dir: Path | None = None,
    limit: int = 20,
) -> list[SessionInfo]:
    """Discover session JSONL files sorted by modification time.

    Scans base_dir (default: ~/.claude/projects/) recursively
    for .jsonl files. Returns SessionInfo list sorted by mtime
    descending (most recent first), limited to ``limit`` entries.
    """
    if base_dir is None:
        base_dir = Path.home() / ".claude" / "projects"

    if not base_dir.is_dir():
        return []

    # Collect all .jsonl files with their mtime
    candidates: list[tuple[float, Path]] = []
    for path in base_dir.rglob("*.jsonl"):
        if not path.is_file():
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        candidates.append((mtime, path))

    # Sort by mtime descending (most recent first)
    candidates.sort(key=lambda item: item[0], reverse=True)

    # Cap at limit
    candidates = candidates[:limit]

    # Build SessionInfo for each file
    results: list[SessionInfo] = []
    for mtime, path in candidates:
        first_msg, count = _preview_session(path)
        results.append(
            SessionInfo(
                path=path,
                modified=mtime,
                first_user_message=first_msg,
                turn_count=count,
                project_name=path.parent.name,
            )
        )

    return results


# --- Tool collapse templates ---


def _collapse_tool(name: str, input_data: dict[str, Any]) -> str:
    """Generate a short summary string for a tool call."""
    if name == "Read":
        file_path = input_data.get("file_path", "unknown")
        return f"Read {file_path}"
    if name == "Write":
        file_path = input_data.get("file_path", "unknown")
        return f"Wrote {file_path}"
    if name == "Edit":
        file_path = input_data.get("file_path", "unknown")
        return f"Edited {file_path}"
    if name == "Bash":
        cmd = input_data.get("command", "")
        return f"Ran: {cmd[:60]}"
    if name == "Grep":
        pattern = input_data.get("pattern", "")
        path = input_data.get("path", ".")
        return f'Searched for "{pattern}" in {path}'
    if name == "Glob":
        pattern = input_data.get("pattern", "")
        return f"Found files matching {pattern}"
    if name == "Agent":
        subagent_type = input_data.get("subagent_type", "unknown")
        return f"Spawned {subagent_type} agent"
    if name == "Skill":
        skill = input_data.get("skill", "unknown")
        return f"Invoked {skill}"
    if name == "TodoWrite":
        subject = input_data.get("subject", "unknown")
        return f"Created task: {subject}"
    if name == "WebFetch":
        url = input_data.get("url", "")
        return f"Fetched {url[:50]}"
    return f"Used {name}"


# --- Text processing ---


def _wrap_and_truncate(text: str, cols: int, rows: int) -> str:
    """Wrap text at cols and truncate at rows lines.

    If the wrapped text exceeds rows, the last line is
    replaced with "...".
    """
    wrapped_lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            wrapped_lines.append("")
            continue
        lines = textwrap.wrap(paragraph, width=cols, break_long_words=True)
        wrapped_lines.extend(lines if lines else [""])

    if len(wrapped_lines) > rows:
        wrapped_lines = wrapped_lines[: rows - 1]
        wrapped_lines.append("...")

    return "\n".join(wrapped_lines)


# --- Turn range parsing ---


def _parse_turn_range(turns_str: str) -> tuple[int, int]:
    """Parse a turns spec like '3' or '1-5' into (start, end) inclusive."""
    if "-" in turns_str:
        parts = turns_str.split("-", 1)
        start_str, end_str = parts[0], parts[1]
        try:
            start, end = int(start_str), int(end_str)
        except ValueError:
            msg = (
                f"Invalid turn range: expected integers, "
                f"got '{start_str}' and/or '{end_str}'"
            )
            raise ValueError(msg) from None
        if start > end:
            msg = f"Invalid turn range: start ({start}) must not exceed end ({end})"
            raise ValueError(msg)
        return start, end
    try:
        n = int(turns_str)
    except ValueError:
        msg = f"Invalid turn range: expected integer, got '{turns_str}'"
        raise ValueError(msg) from None
    return n, n


# --- Format detection ---


def _read_lines(path: Path) -> list[str]:
    """Read a JSONL file and return stripped non-empty lines."""
    lines: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
    return lines


def _detect_format_from_lines(lines: list[str]) -> str:
    """Detect session format from pre-loaded lines.

    Codex records carry a "role" field at the top level;
    Claude Code records do not.
    """
    for line in lines:
        try:
            record = json.loads(line)
            if "role" in record:
                return "codex"
            return "claude"
        except (json.JSONDecodeError, ValueError):
            continue
    return "claude"


def detect_format(path: Path) -> str:
    """Detect session format from file content.

    Reads the first non-empty JSON line and checks for
    format-specific fields.  Codex records carry a "role"
    field at the top level; Claude Code records do not.

    Returns:
        "codex" or "claude".
    """
    try:
        return _detect_format_from_lines(_read_lines(path))
    except OSError:
        return "claude"


# --- Main parser ---


def parse_session(
    path: Path,
    turns: str | None = None,
    show: str = "user,assistant,tools",
    cols: int = 80,
    rows: int = 24,
    format: str | None = None,
) -> list[Turn]:
    """Parse a session JSONL file into turns.

    Supports both Claude Code and Codex session formats.
    When format is None, the format is auto-detected from
    the file content.

    Args:
        path: Path to the JSONL file.
        turns: Optional turn range filter (e.g. "1-5" or "3").
               Counts only UserTurn entries as turn boundaries.
        show: Comma-separated layers to include.
              Options: user, assistant, tools.
        cols: Text wrapping width in characters.
        rows: Text truncation height in lines.
        format: Session format: "claude", "codex", or None
                for auto-detection.

    Returns:
        List of Turn objects in session order.
    """
    lines = _read_lines(path)

    if format is None:
        format = _detect_format_from_lines(lines)

    show_layers = {s.strip() for s in show.split(",")}

    # Phase 1: parse all turns from pre-loaded lines
    if format == "codex":
        all_turns = _parse_codex_lines(lines, cols, rows)
    else:
        all_turns = _parse_claude_lines(lines, cols, rows)

    # Phase 2: apply turn range filter
    if turns is not None:
        all_turns = _apply_turn_range(all_turns, turns)

    # Phase 3: apply layer filter
    all_turns = _apply_layer_filter(all_turns, show_layers)

    return all_turns


def _parse_claude_lines(lines: list[str], cols: int, rows: int) -> list[Turn]:
    """Parse Claude Code session lines into raw turns."""
    all_turns: list[Turn] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping malformed JSONL line: %s", line[:80])
            continue
        record_type = record.get("type")

        if record_type not in ("user", "assistant"):
            continue

        if record.get("isSidechain", False):
            continue

        message = record.get("message", {})
        content = message.get("content")

        if record_type == "user":
            all_turns.extend(_parse_user_content(content, cols, rows))
        elif record_type == "assistant":
            all_turns.extend(_parse_assistant_content(content, cols, rows))

    return all_turns


# --- Codex parser ---


def _parse_codex_lines(lines: list[str], cols: int, rows: int) -> list[Turn]:
    """Parse Codex session lines into raw turns."""
    all_turns: list[Turn] = []
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping malformed JSONL line: %s", line[:80])
            continue

        if record.get("type") != "message":
            continue

        role = record.get("role")

        if role == "user":
            text = record.get("content", "")
            if isinstance(text, str) and text:
                wrapped = _wrap_and_truncate(text, cols, rows)
                all_turns.append(UserTurn(text=wrapped))

        elif role == "assistant":
            all_turns.extend(_parse_codex_assistant(record, cols, rows))

        elif role == "tool":
            all_turns.append(
                ToolResult(
                    tool_use_id=record.get("tool_call_id", ""),
                    content=str(record.get("content", "")),
                )
            )

    return all_turns


def _parse_codex_assistant(record: dict[str, Any], cols: int, rows: int) -> list[Turn]:
    """Parse a Codex assistant record into turns.

    Handles text content (string or list of blocks) and
    tool_calls arrays.
    """
    result: list[Turn] = []
    content = record.get("content")

    if isinstance(content, str) and content:
        text = _wrap_and_truncate(content, cols, rows)
        result.append(AssistantTurn(text=text))
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = _wrap_and_truncate(block.get("text", ""), cols, rows)
                result.append(AssistantTurn(text=text))

    for call in record.get("tool_calls", []):
        func = call.get("function", {})
        name = func.get("name", "unknown")
        raw_args = func.get("arguments", "{}")
        try:
            input_data = json.loads(raw_args)
        except (json.JSONDecodeError, TypeError):
            input_data = {}
        summary = _collapse_tool(name, input_data)
        result.append(ToolUse(tool_name=name, summary=summary, input=input_data))

    return result


def _parse_user_content(content: Any, cols: int, rows: int) -> list[Turn]:
    """Parse user record content into turns."""
    # Plain string = human input
    if isinstance(content, str):
        text = _wrap_and_truncate(content, cols, rows)
        return [UserTurn(text=text)]

    # List of blocks
    if isinstance(content, list) and content:
        first_type = content[0].get("type", "")

        # tool_result blocks
        if first_type == "tool_result":
            results: list[Turn] = []
            for block in content:
                if block.get("type") == "tool_result":
                    results.append(
                        ToolResult(
                            tool_use_id=block.get("tool_use_id", ""),
                            content=str(block.get("content", "")),
                        )
                    )
            return results

        # text blocks = system injection, skip
        if first_type == "text":
            return []

    return []


def _parse_assistant_content(content: Any, cols: int, rows: int) -> list[Turn]:
    """Parse assistant record content blocks into turns."""
    if not isinstance(content, list):
        return []

    result: list[Turn] = []
    for block in content:
        block_type = block.get("type", "")

        if block_type == "text":
            text = _wrap_and_truncate(block.get("text", ""), cols, rows)
            result.append(AssistantTurn(text=text))

        elif block_type == "tool_use":
            name = block.get("name", "unknown")
            input_data = block.get("input", {})
            summary = _collapse_tool(name, input_data)
            result.append(ToolUse(tool_name=name, summary=summary, input=input_data))

        # Skip thinking blocks and any other types

    return result


def _apply_turn_range(all_turns: list[Turn], turns_spec: str) -> list[Turn]:
    """Filter turns by UserTurn-based range boundaries.

    UserTurn entries are numbered sequentially starting at 1.
    A turn "group" includes the UserTurn and all following
    non-UserTurn entries until the next UserTurn.
    """
    start, end = _parse_turn_range(turns_spec)

    # Group turns by UserTurn boundaries
    groups: list[list[Turn]] = []
    current_group: list[Turn] = []

    for turn in all_turns:
        if isinstance(turn, UserTurn):
            if current_group:
                groups.append(current_group)
            current_group = [turn]
        else:
            current_group.append(turn)

    if current_group:
        groups.append(current_group)

    # Select the requested range (1-indexed)
    selected: list[Turn] = []
    for i, group in enumerate(groups, start=1):
        if start <= i <= end:
            selected.extend(group)

    return selected


def _apply_layer_filter(all_turns: list[Turn], show_layers: set[str]) -> list[Turn]:
    """Filter turns by layer visibility."""
    result: list[Turn] = []
    for turn in all_turns:
        if isinstance(turn, UserTurn) and "user" in show_layers:
            result.append(turn)
        elif isinstance(turn, AssistantTurn) and "assistant" in show_layers:
            result.append(turn)
        elif isinstance(turn, (ToolUse, ToolResult)) and "tools" in show_layers:
            result.append(turn)
    return result
