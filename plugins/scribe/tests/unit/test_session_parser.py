"""Tests for session parser.

Validates JSONL parsing, record filtering, tool collapse templates,
turn range filtering, layer filtering, and text truncation.
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
    _parse_turn_range,
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


def _user_record(content: str | list[Any]) -> dict[str, Any]:
    """Build a user-type JSONL record."""
    return {"type": "user", "message": {"content": content}}


def _assistant_record(content: list[dict[str, Any]]) -> dict[str, Any]:
    """Build an assistant-type JSONL record."""
    return {"type": "assistant", "message": {"content": content}}


def _sidechain_record(
    record_type: str, content: Any, sidechain: bool = True
) -> dict[str, Any]:
    """Build a record with isSidechain flag."""
    return {
        "type": record_type,
        "isSidechain": sidechain,
        "message": {"content": content},
    }


class TestRecordTypeFiltering:
    """Feature: only user/assistant records are processed.

    As a session parser
    I want to skip non-conversation records
    So that the replay shows only meaningful turns
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_user_and_assistant_records_processed(self, tmp_path: Path) -> None:
        """Scenario: user and assistant records produce turns.

        Given a JSONL file with user and assistant records
        When parsing the session
        Then turns are emitted for both record types
        """
        records = [
            _user_record("hello"),
            _assistant_record([{"type": "text", "text": "hi there"}]),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 2
        assert isinstance(turns[0], UserTurn)
        assert isinstance(turns[1], AssistantTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progress_records_skipped(self, tmp_path: Path) -> None:
        """Scenario: progress records are ignored.

        Given a JSONL file containing a progress record
        When parsing the session
        Then no turns are emitted for the progress record
        """
        records = [
            {"type": "progress", "data": "loading"},
            _user_record("hello"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1
        assert isinstance(turns[0], UserTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_system_records_skipped(self, tmp_path: Path) -> None:
        """Scenario: system records are ignored."""
        records = [
            {"type": "system", "message": {"content": "system context"}},
            _user_record("hello"),
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_non_conversation_types_skipped(self, tmp_path: Path) -> None:
        """Scenario: all non-conversation record types are skipped.

        Given JSONL with file-history-snapshot, queue-operation,
        last-prompt, custom-title, agent-name, and pr-link records
        When parsing the session
        Then zero turns are emitted
        """
        skip_types = [
            "file-history-snapshot",
            "queue-operation",
            "last-prompt",
            "custom-title",
            "agent-name",
            "pr-link",
        ]
        records = [{"type": t} for t in skip_types]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 0


class TestUserMessageParsing:
    """Feature: user messages parsed by content type.

    As a session parser
    I want to distinguish human input from tool results
    So that each user turn type maps to the correct data class
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_plain_string_becomes_user_turn(self, tmp_path: Path) -> None:
        """Scenario: plain string content becomes UserTurn.

        Given a user record with string content
        When parsing the session
        Then a UserTurn is emitted with the text
        """
        records = [_user_record("fix the auth bug")]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1
        assert isinstance(turns[0], UserTurn)
        assert turns[0].text == "fix the auth bug"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_result_list_becomes_tool_result(self, tmp_path: Path) -> None:
        """Scenario: tool_result blocks become ToolResult turns.

        Given a user record with a tool_result content list
        When parsing the session
        Then ToolResult turns are emitted
        """
        records = [
            _user_record(
                [
                    {
                        "type": "tool_result",
                        "tool_use_id": "abc123",
                        "content": "file contents here",
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1
        assert isinstance(turns[0], ToolResult)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_list_is_skipped(self, tmp_path: Path) -> None:
        """Scenario: text-type list content is skipped.

        Given a user record with a list of text blocks (skill injection)
        When parsing the session
        Then no turns are emitted
        """
        records = [_user_record([{"type": "text", "text": "system context injection"}])]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_multiple_tool_results_emit_multiple_turns(self, tmp_path: Path) -> None:
        """Scenario: multiple tool_result blocks in one record.

        Given a user record with two tool_result blocks
        When parsing the session
        Then two ToolResult turns are emitted
        """
        records = [
            _user_record(
                [
                    {
                        "type": "tool_result",
                        "tool_use_id": "a",
                        "content": "result 1",
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "b",
                        "content": "result 2",
                    },
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 2
        assert all(isinstance(t, ToolResult) for t in turns)


class TestAssistantMessageParsing:
    """Feature: assistant messages parsed by block type.

    As a session parser
    I want to extract text and tool_use blocks
    So that the replay shows Claude's responses and actions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_block_becomes_assistant_turn(self, tmp_path: Path) -> None:
        """Scenario: text block becomes AssistantTurn.

        Given an assistant record with a text block
        When parsing the session
        Then an AssistantTurn is emitted with the text
        """
        records = [_assistant_record([{"type": "text", "text": "I will fix the bug"}])]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1
        assert isinstance(turns[0], AssistantTurn)
        assert turns[0].text == "I will fix the bug"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tool_use_block_becomes_tool_use(self, tmp_path: Path) -> None:
        """Scenario: tool_use block becomes ToolUse turn.

        Given an assistant record with a tool_use block
        When parsing the session
        Then a ToolUse turn is emitted
        """
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "/src/auth.py"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1
        assert isinstance(turns[0], ToolUse)
        assert turns[0].tool_name == "Read"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_thinking_block_skipped(self, tmp_path: Path) -> None:
        """Scenario: thinking blocks are skipped.

        Given an assistant record with a thinking block
        When parsing the session
        Then no turns are emitted for the thinking block
        """
        records = [
            _assistant_record(
                [
                    {"type": "thinking", "thinking": ""},
                    {"type": "text", "text": "Here is my answer"},
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1
        assert isinstance(turns[0], AssistantTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_mixed_blocks_produce_multiple_turns(self, tmp_path: Path) -> None:
        """Scenario: mixed assistant blocks produce ordered turns.

        Given an assistant record with text and tool_use blocks
        When parsing the session
        Then turns are emitted in block order
        """
        records = [
            _assistant_record(
                [
                    {"type": "text", "text": "Let me read the file"},
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "/src/main.py"},
                    },
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 2
        assert isinstance(turns[0], AssistantTurn)
        assert isinstance(turns[1], ToolUse)


class TestSidechainFiltering:
    """Feature: sidechain records are excluded.

    As a session parser
    I want to skip subagent work
    So that the replay shows the main conversation only
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_sidechain_true_excluded(self, tmp_path: Path) -> None:
        """Scenario: records with isSidechain true are skipped.

        Given a user record with isSidechain true
        When parsing the session
        Then no turns are emitted
        """
        records = [_sidechain_record("user", "subagent work", sidechain=True)]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_sidechain_false_included(self, tmp_path: Path) -> None:
        """Scenario: records with isSidechain false are included.

        Given a user record with isSidechain false
        When parsing the session
        Then the turn is emitted normally
        """
        records = [_sidechain_record("user", "main work", sidechain=False)]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_sidechain_assistant_excluded(self, tmp_path: Path) -> None:
        """Scenario: sidechain assistant records are also excluded.

        Given an assistant record with isSidechain true
        When parsing the session
        Then no turns are emitted
        """
        records = [
            {
                "type": "assistant",
                "isSidechain": True,
                "message": {"content": [{"type": "text", "text": "subagent response"}]},
            }
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert len(turns) == 0


class TestToolCollapseTemplates:
    """Feature: tool calls collapse to readable summaries.

    As a session parser
    I want each tool call to produce a short summary
    So that the replay is readable without raw JSON
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_read_template(self, tmp_path: Path) -> None:
        """Scenario: Read tool produces file path and line count."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "/src/auth.py"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert isinstance(turns[0], ToolUse)
        assert "/src/auth.py" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_write_template(self, tmp_path: Path) -> None:
        """Scenario: Write tool produces file path."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Write",
                        "input": {
                            "file_path": "/src/new.py",
                            "content": "x = 1",
                        },
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Wrote /src/new.py" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_edit_template(self, tmp_path: Path) -> None:
        """Scenario: Edit tool produces file path."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Edit",
                        "input": {
                            "file_path": "/src/fix.py",
                            "old_string": "a",
                            "new_string": "b",
                        },
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Edited /src/fix.py" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_bash_template(self, tmp_path: Path) -> None:
        """Scenario: Bash tool shows first 60 chars of command."""
        cmd = "python -m pytest tests/ -v --tb=short 2>&1 | tail -30 && echo done"
        records = [
            _assistant_record(
                [{"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        summary = turns[0].summary
        assert summary.startswith("Ran: ")
        # command should be truncated to 60 chars
        assert len(summary) <= len("Ran: ") + 60

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_grep_template(self, tmp_path: Path) -> None:
        """Scenario: Grep tool shows pattern and path."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Grep",
                        "input": {"pattern": "def auth", "path": "/src"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert 'Searched for "def auth" in /src' in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_glob_template(self, tmp_path: Path) -> None:
        """Scenario: Glob tool shows pattern."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Glob",
                        "input": {"pattern": "**/*.py"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Found files matching **/*.py" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_template(self, tmp_path: Path) -> None:
        """Scenario: Agent tool shows subagent type."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Agent",
                        "input": {"subagent_type": "research"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Spawned research agent" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_template(self, tmp_path: Path) -> None:
        """Scenario: Skill tool shows skill name."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "Skill",
                        "input": {"skill": "scribe:slop-detector"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Invoked scribe:slop-detector" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_todo_write_template(self, tmp_path: Path) -> None:
        """Scenario: TodoWrite tool shows subject."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "TodoWrite",
                        "input": {"subject": "Fix auth timeout"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Created task: Fix auth timeout" in turns[0].summary

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_web_fetch_template(self, tmp_path: Path) -> None:
        """Scenario: WebFetch tool shows first 50 chars of URL."""
        url = "https://docs.example.com/api/v2/reference/authentication/oauth2"
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "WebFetch",
                        "input": {"url": url},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        summary = turns[0].summary
        assert summary.startswith("Fetched ")
        # URL portion should be at most 50 chars
        url_part = summary[len("Fetched ") :]
        assert len(url_part) <= 50

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_unknown_tool_template(self, tmp_path: Path) -> None:
        """Scenario: unknown tools use fallback template."""
        records = [
            _assistant_record(
                [
                    {
                        "type": "tool_use",
                        "name": "CustomTool",
                        "input": {"foo": "bar"},
                    }
                ]
            )
        ]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert "Used CustomTool" in turns[0].summary


class TestTurnRangeFilter:
    """Feature: --turns filters by UserTurn boundaries.

    As a replay user
    I want to select specific turn ranges
    So that I can focus on a portion of the session
    """

    @pytest.fixture
    def session_path(self, tmp_path: Path) -> Path:
        """Build a session with 3 user turns and interleaved responses."""
        records = [
            _user_record("turn one"),
            _assistant_record([{"type": "text", "text": "response one"}]),
            _user_record("turn two"),
            _assistant_record([{"type": "text", "text": "response two"}]),
            _user_record("turn three"),
            _assistant_record([{"type": "text", "text": "response three"}]),
        ]
        return _write_jsonl(tmp_path, records)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_single_turn(self, session_path: Path) -> None:
        """Scenario: selecting a single turn.

        Given a session with 3 user turns
        When filtering with turns="2"
        Then only turn 2 and its responses are included
        """
        turns = parse_session(session_path, turns="2")
        user_turns = [t for t in turns if isinstance(t, UserTurn)]
        assert len(user_turns) == 1
        assert user_turns[0].text == "turn two"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_turn_range(self, session_path: Path) -> None:
        """Scenario: selecting a range of turns.

        Given a session with 3 user turns
        When filtering with turns="1-2"
        Then turns 1 and 2 with their responses are included
        """
        turns = parse_session(session_path, turns="1-2")
        user_turns = [t for t in turns if isinstance(t, UserTurn)]
        assert len(user_turns) == 2
        assert user_turns[0].text == "turn one"
        assert user_turns[1].text == "turn two"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_filter_returns_all(self, session_path: Path) -> None:
        """Scenario: no turns filter returns everything.

        Given a session with 3 user turns
        When parsing without turns filter
        Then all turns are included
        """
        turns = parse_session(session_path)
        user_turns = [t for t in turns if isinstance(t, UserTurn)]
        assert len(user_turns) == 3


class TestLayerFilter:
    """Feature: --show controls which layers appear.

    As a replay user
    I want to include/exclude user, assistant, and tool turns
    So that I can customize what the replay shows
    """

    @pytest.fixture
    def session_path(self, tmp_path: Path) -> Path:
        """Build a session with all turn types."""
        records = [
            _user_record("hello"),
            _assistant_record(
                [
                    {"type": "text", "text": "let me check"},
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "/src/main.py"},
                    },
                ]
            ),
        ]
        return _write_jsonl(tmp_path, records)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_show_user_only(self, session_path: Path) -> None:
        """Scenario: show=user includes only user turns."""
        turns = parse_session(session_path, show="user")
        assert all(isinstance(t, UserTurn) for t in turns)
        assert len(turns) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_show_assistant_only(self, session_path: Path) -> None:
        """Scenario: show=assistant includes only assistant turns."""
        turns = parse_session(session_path, show="assistant")
        assert all(isinstance(t, AssistantTurn) for t in turns)
        assert len(turns) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_show_tools_only(self, session_path: Path) -> None:
        """Scenario: show=tools includes only tool turns."""
        turns = parse_session(session_path, show="tools")
        assert all(isinstance(t, (ToolUse, ToolResult)) for t in turns)
        assert len(turns) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_show_user_assistant(self, session_path: Path) -> None:
        """Scenario: show=user,assistant excludes tools."""
        turns = parse_session(session_path, show="user,assistant")
        assert len(turns) == 2
        assert not any(isinstance(t, (ToolUse, ToolResult)) for t in turns)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_show_all_default(self, session_path: Path) -> None:
        """Scenario: default show includes all layers."""
        turns = parse_session(session_path)
        assert len(turns) == 3


class TestTextTruncation:
    """Feature: text wrapping and truncation.

    As a tape generator consumer
    I want text wrapped at cols and truncated at rows
    So that the replay fits the terminal dimensions
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_long_text_wrapped_at_cols(self, tmp_path: Path) -> None:
        """Scenario: long assistant text is wrapped at cols.

        Given an assistant response longer than 40 characters
        When parsing with cols=40
        Then the text is wrapped to multiple lines
        """
        long_text = "This is a long response that should wrap at column 40."
        records = [_assistant_record([{"type": "text", "text": long_text}])]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, cols=40)
        lines = turns[0].text.split("\n")
        assert all(len(line) <= 40 for line in lines)
        assert len(lines) > 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_truncated_at_rows(self, tmp_path: Path) -> None:
        """Scenario: text exceeding rows is truncated with ellipsis.

        Given an assistant response that wraps to 30+ lines
        When parsing with rows=5
        Then the text is truncated to 5 lines with "..." appended
        """
        long_text = " ".join(["word"] * 200)
        records = [_assistant_record([{"type": "text", "text": long_text}])]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, cols=40, rows=5)
        lines = turns[0].text.split("\n")
        assert len(lines) == 5
        assert lines[-1] == "..."

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_short_text_not_truncated(self, tmp_path: Path) -> None:
        """Scenario: short text is unchanged.

        Given an assistant response of one word
        When parsing with default cols and rows
        Then the text is unchanged
        """
        records = [_assistant_record([{"type": "text", "text": "hello"}])]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path)
        assert turns[0].text == "hello"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_user_text_also_wrapped(self, tmp_path: Path) -> None:
        """Scenario: user text is also wrapped at cols.

        Given a long user message
        When parsing with cols=30
        Then the user text is wrapped
        """
        long_text = "Please fix this really long authentication bug in the system"
        records = [_user_record(long_text)]
        path = _write_jsonl(tmp_path, records)
        turns = parse_session(path, cols=30)
        lines = turns[0].text.split("\n")
        assert all(len(line) <= 30 for line in lines)


class TestCorruptJSONLBody:
    """Feature: graceful handling of corrupt JSONL body lines.

    As a session parser
    I want to skip malformed lines in the body
    So that a single corrupt line does not crash the entire parse
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_corrupt_body_lines_skipped_claude(self, tmp_path: Path) -> None:
        """Scenario: valid header with corrupt body lines (Claude format).

        Given a JSONL file with a valid first record (Claude format)
        And corrupt (non-JSON) lines interspersed in the body
        When parsing the session
        Then the corrupt lines are skipped
        And valid records are still parsed into turns
        """
        valid_record_1 = json.dumps(_user_record("hello"))
        corrupt_line = "this is not valid json {{{{"
        valid_record_2 = json.dumps(
            _assistant_record([{"type": "text", "text": "response"}])
        )
        valid_record_3 = json.dumps(_user_record("goodbye"))

        content = "\n".join(
            [
                valid_record_1,
                corrupt_line,
                valid_record_2,
                "another bad line !!!",
                valid_record_3,
            ]
        )
        path = tmp_path / "corrupt_body.jsonl"
        path.write_text(content)

        turns = parse_session(path, format="claude")
        assert len(turns) == 3
        assert isinstance(turns[0], UserTurn)
        assert turns[0].text == "hello"
        assert isinstance(turns[1], AssistantTurn)
        assert isinstance(turns[2], UserTurn)
        assert turns[2].text == "goodbye"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_corrupt_body_lines_skipped_codex(self, tmp_path: Path) -> None:
        """Scenario: valid header with corrupt body lines (Codex format).

        Given a JSONL file with a valid first record (Codex format)
        And corrupt (non-JSON) lines interspersed in the body
        When parsing the session
        Then the corrupt lines are skipped
        And valid records are still parsed into turns
        """
        codex_user = {"type": "message", "role": "user", "content": "hello"}
        codex_asst = {
            "type": "message",
            "role": "assistant",
            "content": "response",
        }

        content = "\n".join(
            [
                json.dumps(codex_user),
                "{malformed json",
                json.dumps(codex_asst),
                "not json at all",
            ]
        )
        path = tmp_path / "corrupt_codex.jsonl"
        path.write_text(content)

        turns = parse_session(path, format="codex")
        assert len(turns) == 2
        assert isinstance(turns[0], UserTurn)
        assert isinstance(turns[1], AssistantTurn)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_corrupt_body_returns_empty(self, tmp_path: Path) -> None:
        """Scenario: valid header but all body lines corrupt.

        Given a JSONL file with a valid first record
        And all subsequent lines are corrupt
        When parsing the session
        Then partial results are returned (just from the valid header)
        """
        valid_record = json.dumps(_user_record("only valid line"))
        content = "\n".join(
            [
                valid_record,
                "corrupt line 1",
                "corrupt line 2",
                "corrupt line 3",
            ]
        )
        path = tmp_path / "mostly_corrupt.jsonl"
        path.write_text(content)

        turns = parse_session(path, format="claude")
        assert len(turns) == 1
        assert isinstance(turns[0], UserTurn)
        assert turns[0].text == "only valid line"


class TestTurnRangeValidation:
    """Feature: turn range input validation.

    As a session parser
    I want clear error messages for invalid turn ranges
    So that users can correct their input quickly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_integer_raises_descriptive_error(self) -> None:
        """Scenario: non-integer turn spec raises ValueError with message."""
        with pytest.raises(ValueError, match="Invalid turn range"):
            _parse_turn_range("abc")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_non_integer_range_raises_descriptive_error(self) -> None:
        """Scenario: non-integer range spec raises ValueError with message."""
        with pytest.raises(ValueError, match="Invalid turn range"):
            _parse_turn_range("a-b")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_start_greater_than_end_raises(self) -> None:
        """Scenario: start > end in range raises ValueError."""
        with pytest.raises(ValueError, match="must not exceed end"):
            _parse_turn_range("5-2")
