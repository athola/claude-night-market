"""Tests for research_storage_prompt PostToolUse hook.

Feature: Auto-prompt for research storage after web search (Issue #118)

As a researcher using Claude Code
I want to be reminded to store valuable web search findings
So that research doesn't get lost and feeds into the knowledge corpus
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add hooks dir to path so we can import the module
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import research_storage_prompt  # noqa: E402


class TestResearchStoragePromptOutput:
    """Feature: Emit storage reminder after WebSearch/WebFetch

    As a researcher
    I want a reminder after web searches complete
    So that I remember to store valuable findings via knowledge-intake
    """

    @pytest.mark.unit
    def test_emits_reminder_for_websearch(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: WebSearch completes with a query
        Given a PostToolUse payload for WebSearch with query "python asyncio patterns"
        When the hook processes the payload
        Then it outputs JSON with a reminder mentioning knowledge-intake
        """
        payload: dict[str, Any] = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "python asyncio patterns"},
        }

        with patch("sys.stdin", _json_stdin(payload)):
            with pytest.raises(SystemExit) as exc_info:
                research_storage_prompt.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "knowledge-intake" in ctx
        assert "WebSearch" in ctx

    @pytest.mark.unit
    def test_emits_reminder_for_webfetch(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scenario: WebFetch completes with a prompt
        Given a PostToolUse payload for WebFetch
        When the hook processes the payload
        Then it outputs JSON with a reminder mentioning knowledge-intake
        """
        payload: dict[str, Any] = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "summarize"},
        }

        with patch("sys.stdin", _json_stdin(payload)):
            with pytest.raises(SystemExit) as exc_info:
                research_storage_prompt.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "knowledge-intake" in ctx
        assert "WebFetch" in ctx

    @pytest.mark.unit
    def test_ignores_non_web_tools(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Scenario: A non-web tool completes
        Given a PostToolUse payload for tool "Read"
        When the hook processes the payload
        Then it exits silently with no output
        """
        payload: dict[str, Any] = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/foo.txt"},
        }

        with patch("sys.stdin", _json_stdin(payload)):
            with pytest.raises(SystemExit) as exc_info:
                research_storage_prompt.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""

    @pytest.mark.unit
    def test_ignores_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Scenario: Hook receives invalid JSON on stdin
        Given malformed input on stdin
        When the hook processes the payload
        Then it exits cleanly with code 0 and no output
        """
        import io

        with patch("sys.stdin", io.StringIO("not json {")):
            with pytest.raises(SystemExit) as exc_info:
                research_storage_prompt.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""


class TestRecentIntakePending:
    """Feature: Skip prompt when research_interceptor already flagged the query

    As a researcher
    I want to avoid redundant prompts
    So that the experience is clean and not noisy
    """

    @pytest.mark.unit
    def test_returns_true_when_query_in_queue(self, tmp_path: Path) -> None:
        """Scenario: Query was already queued by research_interceptor
        Given an intake_queue.jsonl containing a matching query
        When _recent_intake_pending is called
        Then it returns True
        """
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "python asyncio patterns", "query_id": "abc123"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch.object(research_storage_prompt, "PLUGIN_ROOT", tmp_path):
            assert research_storage_prompt._recent_intake_pending(
                "python asyncio patterns"
            )

    @pytest.mark.unit
    def test_case_insensitive_match(self, tmp_path: Path) -> None:
        """Scenario: Query matches case-insensitively
        Given an intake_queue.jsonl containing "python asyncio patterns" (lowercase)
        When _recent_intake_pending is called with "PYTHON ASYNCIO PATTERNS" (uppercase)
        Then it returns True because matching is case-insensitive
        """
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "python asyncio patterns", "query_id": "case1"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch.object(research_storage_prompt, "PLUGIN_ROOT", tmp_path):
            assert research_storage_prompt._recent_intake_pending(
                "PYTHON ASYNCIO PATTERNS"
            )

    @pytest.mark.unit
    def test_returns_false_when_no_match(self, tmp_path: Path) -> None:
        """Scenario: Query was NOT queued
        Given an intake_queue.jsonl with different queries
        When _recent_intake_pending is called
        Then it returns False
        """
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "rust ownership model", "query_id": "def456"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch.object(research_storage_prompt, "PLUGIN_ROOT", tmp_path):
            assert not research_storage_prompt._recent_intake_pending(
                "python asyncio patterns"
            )

    @pytest.mark.unit
    def test_returns_false_when_no_queue_file(self, tmp_path: Path) -> None:
        """Scenario: No intake queue file exists
        Given PLUGIN_ROOT/data/intake_queue.jsonl does not exist
        When _recent_intake_pending is called
        Then it returns False
        """
        with patch.object(research_storage_prompt, "PLUGIN_ROOT", tmp_path):
            assert not research_storage_prompt._recent_intake_pending("anything")

    @pytest.mark.unit
    def test_suppresses_prompt_when_already_flagged(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Scenario: WebSearch completes but query was already flagged for intake
        Given a matching entry in intake_queue.jsonl
        When the hook processes a WebSearch payload with that query
        Then it exits silently (no redundant prompt)
        """
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "python asyncio patterns"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        payload: dict[str, Any] = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "python asyncio patterns"},
        }

        with patch.object(research_storage_prompt, "PLUGIN_ROOT", tmp_path):
            with patch("sys.stdin", _json_stdin(payload)):
                with pytest.raises(SystemExit) as exc_info:
                    research_storage_prompt.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""


# -- Helpers ------------------------------------------------------------------

import io  # noqa: E402


def _json_stdin(data: dict[str, Any]) -> io.StringIO:
    """Create a StringIO that mimics stdin with JSON payload."""
    return io.StringIO(json.dumps(data))
