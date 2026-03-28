"""Tests for Codex session format parsing.

Validates Codex JSONL parsing, tool collapse summaries,
and auto-detection of session format (Claude vs Codex).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from scribe.session_parser import (
    AssistantTurn,
    ToolResult,
    ToolUse,
    UserTurn,
    detect_format,
    parse_session,
)


def _make_jsonl(records: list[dict[str, Any]]) -> str:
    """Convert a list of dicts to a JSONL string."""
    return "\n".join(json.dumps(r) for r in records)


def _write_jsonl(tmp_path: Path, records: list[dict[str, Any]]) -> Path:
    """Write records as JSONL to a temp file and return the path."""
    p = tmp_path / "session.jsonl"
    p.write_text(_make_jsonl(records))
    return p


def _codex_user(content: str) -> dict[str, Any]:
    """Build a Codex user message record."""
    return {"type": "message", "role": "user", "content": content}


def _codex_assistant(content: str) -> dict[str, Any]:
    """Build a Codex assistant text message record."""
    return {"type": "message", "role": "assistant", "content": content}


def _codex_assistant_with_tools(
    tool_calls: list[dict[str, Any]],
    content: str | None = None,
) -> dict[str, Any]:
    """Build a Codex assistant record with tool_calls."""
    record: dict[str, Any] = {
        "type": "message",
        "role": "assistant",
        "tool_calls": tool_calls,
    }
    if content is not None:
        record["content"] = content
    return record


def _codex_tool_result(tool_call_id: str, content: str) -> dict[str, Any]:
    """Build a Codex tool result record."""
    return {
        "type": "message",
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def _codex_tool_call(call_id: str, name: str, arguments: str) -> dict[str, Any]:
    """Build a single tool_call entry for a Codex assistant record."""
    return {
        "id": call_id,
        "function": {"name": name, "arguments": arguments},
    }


# -- Claude format fixtures for auto-detection tests --


def _claude_user(content: str) -> dict[str, Any]:
    """Build a Claude Code user record."""
    return {"type": "user", "message": {"content": content}}


def _claude_assistant(text: str) -> dict[str, Any]:
    """Build a Claude Code assistant record."""
    return {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": text}]},
    }


class TestCodexRecordParsing:
    """Feature: Codex JSONL records are parsed into Turn objects.

    As a session parser
    I want to parse Codex session format
    So that replays work for both Claude Code and Codex sessions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_user_message_becomes_user_turn(self, tmp_path: Path) -> None:
        """Scenario: Codex user message produces UserTurn."""
        records = [_codex_user("fix the bug")]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        assert len(turns) == 1
        assert isinstance(turns[0], UserTurn)
        assert turns[0].text == "fix the bug"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_assistant_string_becomes_assistant_turn(self, tmp_path: Path) -> None:
        """Scenario: Codex assistant text produces AssistantTurn."""
        records = [
            _codex_user("hello"),
            _codex_assistant("I will help you"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        assert len(turns) == 2
        assert isinstance(turns[1], AssistantTurn)
        assert turns[1].text == "I will help you"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_assistant_list_content(self, tmp_path: Path) -> None:
        """Scenario: Codex assistant with list content extracts text."""
        records = [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "first part"},
                    {"type": "text", "text": "second part"},
                ],
            }
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        texts = [t.text for t in turns if isinstance(t, AssistantTurn)]
        assert "first part" in texts
        assert "second part" in texts

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_call_becomes_tool_use(self, tmp_path: Path) -> None:
        """Scenario: Codex assistant tool_calls produce ToolUse turns."""
        records = [
            _codex_assistant_with_tools(
                tool_calls=[
                    _codex_tool_call(
                        "call_1",
                        "Read",
                        json.dumps({"file_path": "/src/main.py"}),
                    )
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        tool_uses = [t for t in turns if isinstance(t, ToolUse)]
        assert len(tool_uses) == 1
        assert tool_uses[0].tool_name == "Read"
        assert tool_uses[0].input == {"file_path": "/src/main.py"}

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_result_becomes_tool_result(self, tmp_path: Path) -> None:
        """Scenario: Codex tool role produces ToolResult turns."""
        records = [_codex_tool_result("call_1", "file contents")]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        results = [t for t in turns if isinstance(t, ToolResult)]
        assert len(results) == 1
        assert results[0].tool_use_id == "call_1"
        assert results[0].content == "file contents"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mixed_text_and_tool_calls(self, tmp_path: Path) -> None:
        """Scenario: assistant with both text and tool_calls."""
        records = [
            _codex_assistant_with_tools(
                content="Let me check the file",
                tool_calls=[
                    _codex_tool_call(
                        "call_1",
                        "Bash",
                        json.dumps({"command": "ls -la"}),
                    )
                ],
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        assert any(isinstance(t, AssistantTurn) for t in turns)
        assert any(isinstance(t, ToolUse) for t in turns)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_message_types_skipped(self, tmp_path: Path) -> None:
        """Scenario: non-message type records are skipped."""
        records = [
            {"type": "status", "status": "running"},
            _codex_user("hello"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        assert len(turns) == 1
        assert isinstance(turns[0], UserTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_multiple_tool_calls_in_one_record(self, tmp_path: Path) -> None:
        """Scenario: multiple tool_calls in one assistant record."""
        records = [
            _codex_assistant_with_tools(
                tool_calls=[
                    _codex_tool_call(
                        "call_1",
                        "Read",
                        json.dumps({"file_path": "/a.py"}),
                    ),
                    _codex_tool_call(
                        "call_2",
                        "Grep",
                        json.dumps({"pattern": "TODO", "path": "/src"}),
                    ),
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        tool_uses = [t for t in turns if isinstance(t, ToolUse)]
        assert len(tool_uses) == 2
        assert tool_uses[0].tool_name == "Read"
        assert tool_uses[1].tool_name == "Grep"


class TestCodexToolCollapse:
    """Feature: Codex tool calls use the same collapse templates.

    As a session parser
    I want Codex tool summaries to match Claude Code format
    So that the tape generator works identically for both
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_read_collapse(self, tmp_path: Path) -> None:
        """Scenario: Read tool call collapses to file path."""
        records = [
            _codex_assistant_with_tools(
                tool_calls=[
                    _codex_tool_call(
                        "c1",
                        "Read",
                        json.dumps({"file_path": "/src/auth.py"}),
                    )
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        tool = [t for t in turns if isinstance(t, ToolUse)][0]
        assert "Read /src/auth.py" in tool.summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_bash_collapse(self, tmp_path: Path) -> None:
        """Scenario: Bash tool call collapses to command prefix."""
        records = [
            _codex_assistant_with_tools(
                tool_calls=[
                    _codex_tool_call(
                        "c1",
                        "Bash",
                        json.dumps({"command": "python test.py"}),
                    )
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        tool = [t for t in turns if isinstance(t, ToolUse)][0]
        assert tool.summary.startswith("Ran: ")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_unknown_tool_collapse(self, tmp_path: Path) -> None:
        """Scenario: unknown Codex tool uses fallback template."""
        records = [
            _codex_assistant_with_tools(
                tool_calls=[
                    _codex_tool_call(
                        "c1",
                        "codex_file_write",
                        json.dumps({"path": "/tmp/out.txt"}),
                    )
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        tool = [t for t in turns if isinstance(t, ToolUse)][0]
        assert "Used codex_file_write" in tool.summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_malformed_arguments_handled(self, tmp_path: Path) -> None:
        """Scenario: invalid JSON in arguments does not crash."""
        records = [
            _codex_assistant_with_tools(
                tool_calls=[_codex_tool_call("c1", "Read", "not valid json")]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        tool = [t for t in turns if isinstance(t, ToolUse)][0]
        assert tool.tool_name == "Read"
        assert tool.input == {}


class TestFormatAutoDetection:
    """Feature: auto-detect Codex vs Claude format from file content.

    As a session parser
    I want to detect the format automatically
    So that users do not have to specify --format manually
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detect_claude_format(self, tmp_path: Path) -> None:
        """Scenario: Claude Code JSONL detected by type field."""
        records = [
            _claude_user("hello"),
            _claude_assistant("hi there"),
        ]
        path = _write_jsonl(tmp_path, records)
        assert detect_format(path) == "claude"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detect_codex_format(self, tmp_path: Path) -> None:
        """Scenario: Codex JSONL detected by role field."""
        records = [
            _codex_user("hello"),
            _codex_assistant("hi there"),
        ]
        path = _write_jsonl(tmp_path, records)
        assert detect_format(path) == "codex"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_auto_detect_parses_claude(self, tmp_path: Path) -> None:
        """Scenario: parse_session auto-detects Claude format."""
        records = [
            _claude_user("hello"),
            _claude_assistant("hi"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 2
        assert isinstance(turns[0], UserTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_auto_detect_parses_codex(self, tmp_path: Path) -> None:
        """Scenario: parse_session auto-detects Codex format."""
        records = [
            _codex_user("fix the bug"),
            _codex_assistant("on it"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 2
        assert isinstance(turns[0], UserTurn)
        assert turns[0].text == "fix the bug"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_explicit_format_overrides_detection(self, tmp_path: Path) -> None:
        """Scenario: explicit format param skips detection."""
        records = [_codex_user("hello")]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex")
        assert len(turns) == 1
        assert isinstance(turns[0], UserTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_file_defaults_to_claude(self, tmp_path: Path) -> None:
        """Scenario: empty file defaults to claude format."""
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        assert detect_format(path) == "claude"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_codex_turn_range_filter(self, tmp_path: Path) -> None:
        """Scenario: turn range filtering works with Codex format."""
        records = [
            _codex_user("turn one"),
            _codex_assistant("response one"),
            _codex_user("turn two"),
            _codex_assistant("response two"),
            _codex_user("turn three"),
            _codex_assistant("response three"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex", turns="2")
        user_turns = [t for t in turns if isinstance(t, UserTurn)]
        assert len(user_turns) == 1
        assert user_turns[0].text == "turn two"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_codex_layer_filter(self, tmp_path: Path) -> None:
        """Scenario: layer filtering works with Codex format."""
        records = [
            _codex_user("hello"),
            _codex_assistant_with_tools(
                content="checking",
                tool_calls=[
                    _codex_tool_call(
                        "c1",
                        "Read",
                        json.dumps({"file_path": "/a.py"}),
                    )
                ],
            ),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, format="codex", show="user,assistant")
        assert all(isinstance(t, (UserTurn, AssistantTurn)) for t in turns)
        assert not any(isinstance(t, ToolUse) for t in turns)
