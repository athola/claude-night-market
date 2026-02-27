# ruff: noqa: D101,D102,D103
"""BDD/TDD tests for web_research_handler.py PostToolUse hook.

Feature: Unified web research handling (PostToolUse)

As a researcher using Claude Code
I want web search/fetch results to be auto-captured and deduplicated
So that research findings are stored and not lost

This tests the consolidated hook that merged:
- web_content_processor.py (safety checks, dedup, auto-capture)
- research_storage_prompt.py (storage reminder prompts)
"""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

import web_research_handler
from web_research_handler import (
    _build_storage_reminder,
    _recent_intake_pending,
    extract_content_from_webfetch,
    extract_results_from_websearch,
    extract_title_from_content,
    slugify,
)


# -- Helpers ------------------------------------------------------------------


def _json_stdin(data: dict) -> StringIO:
    """Create a StringIO that mimics stdin with JSON payload."""
    return StringIO(json.dumps(data))


def _default_config(auto_capture: bool = True, enabled: bool = True) -> dict:
    """Return a config dict with feature flags."""
    return {
        "enabled": enabled,
        "feature_flags": {
            "lifecycle": True,
            "auto_capture": auto_capture,
        },
    }


# =============================================================================
# Pure Function Tests
# =============================================================================


class TestSlugify:
    """Feature: Convert text to URL-safe slugs for filenames."""

    @pytest.mark.unit
    def test_basic_text(self):
        """Given normal text, produce a lowercase hyphenated slug."""
        assert slugify("Hello World") == "hello-world"

    @pytest.mark.unit
    def test_special_characters_removed(self):
        """Given text with special chars, replace with hyphens."""
        assert slugify("Python 3.12: What's New?") == "python-3-12-what-s-new"

    @pytest.mark.unit
    def test_truncation_at_max_length(self):
        """Given text longer than max_length, truncate at word boundary."""
        result = slugify("a-very-long-title-that-exceeds-the-limit", max_length=20)
        assert len(result) <= 20
        # Should not end with a hyphen after truncation
        assert not result.endswith("-")

    @pytest.mark.unit
    def test_empty_input_returns_untitled(self):
        """Given empty or whitespace-only input, return 'untitled'."""
        assert slugify("") == "untitled"
        assert slugify("   ") == "untitled"

    @pytest.mark.unit
    def test_already_slug(self):
        """Given already-slugified text, return it unchanged."""
        assert slugify("hello-world") == "hello-world"


class TestExtractTitleFromContent:
    """Feature: Extract a human-readable title from web content."""

    @pytest.mark.unit
    def test_markdown_heading(self):
        """Given content with a markdown heading, extract it as title."""
        content = "# Python Async Patterns\n\nSome body text here."
        assert extract_title_from_content(content, "https://example.com") == (
            "Python Async Patterns"
        )

    @pytest.mark.unit
    def test_plain_text_title_line(self):
        """Given content with a plain title-like first line, use it."""
        content = "Getting Started with FastAPI\n\nFastAPI is a modern framework."
        title = extract_title_from_content(content, "https://example.com")
        assert title == "Getting Started with FastAPI"

    @pytest.mark.unit
    def test_fallback_to_url(self):
        """Given content with no extractable title, fall back to URL."""
        content = "\n\n\n"  # Empty-ish content
        title = extract_title_from_content(
            content, "https://docs.example.com/user-guide"
        )
        assert "User Guide" in title

    @pytest.mark.unit
    def test_fallback_to_netloc(self):
        """Given content with no title and root URL, use netloc."""
        content = "\n"
        title = extract_title_from_content(content, "https://example.com")
        assert title == "example.com"


class TestExtractContentFromWebfetch:
    """Feature: Extract content and URL from WebFetch responses."""

    @pytest.mark.unit
    def test_string_response(self):
        """Given a plain string response, return it as content."""
        content, url = extract_content_from_webfetch("Hello world")
        assert content == "Hello world"
        assert url is None

    @pytest.mark.unit
    def test_dict_with_content_key(self):
        """Given a dict response with 'content' key, extract it."""
        response = {"content": "Page content here", "url": "https://example.com"}
        content, url = extract_content_from_webfetch(response)
        assert content == "Page content here"
        assert url == "https://example.com"

    @pytest.mark.unit
    def test_nested_result(self):
        """Given a nested result dict, extract content from it."""
        response = {"result": {"content": "Nested content"}}
        content, url = extract_content_from_webfetch(response)
        assert content == "Nested content"

    @pytest.mark.unit
    def test_empty_dict(self):
        """Given an empty dict, return empty content."""
        content, url = extract_content_from_webfetch({})
        assert content == ""
        assert url is None


class TestExtractResultsFromWebsearch:
    """Feature: Extract structured search results from WebSearch responses."""

    @pytest.mark.unit
    def test_standard_results(self):
        """Given a response with results list, extract them."""
        response = {
            "results": [
                {
                    "url": "https://example.com/1",
                    "title": "Result 1",
                    "snippet": "Description 1",
                },
                {
                    "url": "https://example.com/2",
                    "title": "Result 2",
                    "description": "Description 2",
                },
            ],
        }
        results = extract_results_from_websearch(response)
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[1]["snippet"] == "Description 2"

    @pytest.mark.unit
    def test_limits_to_10_results(self):
        """Given more than 10 results, only extract first 10."""
        response = {
            "results": [
                {"url": f"https://example.com/{i}", "title": f"R{i}"}
                for i in range(15)
            ],
        }
        results = extract_results_from_websearch(response)
        assert len(results) == 10

    @pytest.mark.unit
    def test_empty_results(self):
        """Given an empty response, return empty list."""
        assert extract_results_from_websearch({}) == []
        assert extract_results_from_websearch({"results": []}) == []

    @pytest.mark.unit
    def test_non_dict_results_skipped(self):
        """Given non-dict items in results, skip them."""
        response = {"results": ["not a dict", {"url": "https://x.com", "title": "X"}]}
        results = extract_results_from_websearch(response)
        assert len(results) == 1


class TestRecentIntakePending:
    """Feature: Skip prompts when research_interceptor already flagged the query."""

    @pytest.mark.unit
    def test_returns_true_when_query_in_queue(self, tmp_path: Path):
        """Given a matching query in intake_queue.jsonl, return True."""
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "python asyncio patterns", "query_id": "abc123"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch.object(web_research_handler, "PLUGIN_ROOT", tmp_path):
            assert _recent_intake_pending("python asyncio patterns")

    @pytest.mark.unit
    def test_case_insensitive_match(self, tmp_path: Path):
        """Given matching query in different case, return True."""
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "python asyncio patterns"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch.object(web_research_handler, "PLUGIN_ROOT", tmp_path):
            assert _recent_intake_pending("PYTHON ASYNCIO PATTERNS")

    @pytest.mark.unit
    def test_returns_false_when_no_match(self, tmp_path: Path):
        """Given a non-matching query, return False."""
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        entry = {"query": "rust ownership model"}
        queue_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

        with patch.object(web_research_handler, "PLUGIN_ROOT", tmp_path):
            assert not _recent_intake_pending("python asyncio patterns")

    @pytest.mark.unit
    def test_returns_false_when_no_queue_file(self, tmp_path: Path):
        """Given no intake_queue.jsonl, return False."""
        with patch.object(web_research_handler, "PLUGIN_ROOT", tmp_path):
            assert not _recent_intake_pending("anything")

    @pytest.mark.unit
    def test_handles_malformed_jsonl(self, tmp_path: Path):
        """Given corrupted JSONL entries, skip them without crashing."""
        queue_file = tmp_path / "data" / "intake_queue.jsonl"
        queue_file.parent.mkdir(parents=True)
        queue_file.write_text(
            "not valid json\n"
            + json.dumps({"query": "target query"})
            + "\n",
            encoding="utf-8",
        )

        with patch.object(web_research_handler, "PLUGIN_ROOT", tmp_path):
            assert _recent_intake_pending("target query")


class TestBuildStorageReminder:
    """Feature: Build storage reminder messages."""

    @pytest.mark.unit
    def test_includes_tool_name(self):
        """Given a tool name, include it in the reminder."""
        msg = _build_storage_reminder("WebSearch")
        assert "WebSearch" in msg
        assert "knowledge-intake" in msg

    @pytest.mark.unit
    def test_webfetch_tool(self):
        """Given WebFetch, produce a valid reminder."""
        msg = _build_storage_reminder("WebFetch")
        assert "WebFetch" in msg


# =============================================================================
# Main Entry Point Tests
# =============================================================================


class TestMainIgnoresNonWebTools:
    """Feature: Hook exits silently for non-web tools."""

    @pytest.mark.unit
    def test_ignores_read_tool(self, capsys: pytest.CaptureFixture[str]):
        """Given a Read tool payload, exit silently."""
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/foo"}}

        with patch("sys.stdin", _json_stdin(payload)):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""

    @pytest.mark.unit
    def test_ignores_invalid_json(self, capsys: pytest.CaptureFixture[str]):
        """Given malformed JSON on stdin, exit cleanly."""
        with patch("sys.stdin", StringIO("not json {")):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""


class TestMainWebFetchHandling:
    """Feature: Process WebFetch results with safety checks and dedup."""

    @pytest.mark.unit
    def test_short_content_ignored(self, capsys: pytest.CaptureFixture[str]):
        """Given WebFetch content under 100 chars, exit silently."""
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "summarize"},
            "tool_response": {"content": "Short", "url": "https://example.com"},
        }

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(),
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""

    @pytest.mark.unit
    def test_unsafe_content_skipped(self, capsys: pytest.CaptureFixture[str]):
        """Given content that fails safety checks, emit skip message."""
        long_content = "x" * 200
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "get"},
            "tool_response": {"content": long_content, "url": "https://example.com"},
        }

        safety_result = MagicMock()
        safety_result.is_safe = False
        safety_result.reason = "contains secrets"

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(),
            ),
            patch(
                "web_research_handler.is_safe_content",
                return_value=safety_result,
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "skipped" in ctx
        assert "contains secrets" in ctx

    @pytest.mark.unit
    def test_known_url_no_changes(self, capsys: pytest.CaptureFixture[str]):
        """Given a known URL with unchanged content, emit storage reminder.

        Note: When URL is known and unchanged, context_parts is empty (no
        specific message). The fallback storage reminder at the end of main()
        fires because stored_path is None and context_parts is empty.
        """
        long_content = "x" * 200
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "get"},
            "tool_response": {"content": long_content, "url": "https://example.com"},
        }

        safety_result = MagicMock()
        safety_result.is_safe = True
        safety_result.should_sanitize = False

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(),
            ),
            patch(
                "web_research_handler.is_safe_content",
                return_value=safety_result,
            ),
            patch("web_research_handler.is_known", return_value=True),
            patch("web_research_handler.needs_update", return_value=False),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        # Fallback reminder emitted when no specific context was generated
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "knowledge-intake" in ctx

    @pytest.mark.unit
    def test_known_url_with_changes(self, capsys: pytest.CaptureFixture[str]):
        """Given a known URL with changed content, suggest update."""
        long_content = "x" * 200
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "get"},
            "tool_response": {"content": long_content, "url": "https://example.com"},
        }

        safety_result = MagicMock()
        safety_result.is_safe = True
        safety_result.should_sanitize = False

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(),
            ),
            patch(
                "web_research_handler.is_safe_content",
                return_value=safety_result,
            ),
            patch("web_research_handler.is_known", return_value=True),
            patch("web_research_handler.needs_update", return_value=True),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "has changed" in ctx

    @pytest.mark.unit
    def test_new_content_auto_captured(self, capsys: pytest.CaptureFixture[str]):
        """Given new content with auto_capture enabled, store it."""
        long_content = "x" * 200
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "get"},
            "tool_response": {"content": long_content, "url": "https://example.com"},
        }

        safety_result = MagicMock()
        safety_result.is_safe = True
        safety_result.should_sanitize = False

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(auto_capture=True),
            ),
            patch(
                "web_research_handler.is_safe_content",
                return_value=safety_result,
            ),
            patch("web_research_handler.is_known", return_value=False),
            patch("web_research_handler.get_content_hash", return_value="abc123"),
            patch(
                "web_research_handler.store_webfetch_content",
                return_value="/tmp/stored.md",
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "Auto-captured" in ctx
        assert "pending_review" in ctx

    @pytest.mark.unit
    def test_auto_capture_disabled_shows_reminder(
        self, capsys: pytest.CaptureFixture[str]
    ):
        """Given auto_capture disabled and new content, show manual reminder."""
        long_content = "x" * 200
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com", "prompt": "get"},
            "tool_response": {"content": long_content, "url": "https://example.com"},
        }

        safety_result = MagicMock()
        safety_result.is_safe = True
        safety_result.should_sanitize = False

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(auto_capture=False),
            ),
            patch(
                "web_research_handler.is_safe_content",
                return_value=safety_result,
            ),
            patch("web_research_handler.is_known", return_value=False),
            patch("web_research_handler.get_content_hash", return_value="abc123"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "knowledge-intake" in ctx


class TestMainWebSearchHandling:
    """Feature: Process WebSearch results with dedup and auto-capture."""

    @pytest.mark.unit
    def test_new_results_auto_captured(self, capsys: pytest.CaptureFixture[str]):
        """Given new search results with auto_capture, store them."""
        payload = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "python async patterns"},
            "tool_response": {
                "results": [
                    {
                        "url": "https://example.com/1",
                        "title": "Async 101",
                        "snippet": "Learn async",
                    },
                ],
            },
        }

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(auto_capture=True),
            ),
            patch("web_research_handler.is_known", return_value=False),
            patch("web_research_handler._recent_intake_pending", return_value=False),
            patch(
                "web_research_handler.store_websearch_results",
                return_value="/tmp/search.md",
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "Auto-captured" in ctx
        assert "python async patterns" in ctx

    @pytest.mark.unit
    def test_known_results_noted(self, capsys: pytest.CaptureFixture[str]):
        """Given all results already known, note they exist."""
        payload = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "python docs"},
            "tool_response": {
                "results": [
                    {
                        "url": "https://example.com/known",
                        "title": "Known",
                        "snippet": "Already stored",
                    },
                ],
            },
        }

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(),
            ),
            patch("web_research_handler.is_known", return_value=True),
            patch("web_research_handler._recent_intake_pending", return_value=False),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        output = capsys.readouterr().out.strip()
        result = json.loads(output)
        ctx = result["hookSpecificOutput"]["additionalContext"]
        assert "already stored" in ctx

    @pytest.mark.unit
    def test_intake_already_pending_no_duplicate_prompt(
        self, capsys: pytest.CaptureFixture[str]
    ):
        """Given intake already pending for this query, skip redundant prompt."""
        payload = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "python async"},
            "tool_response": {"results": []},
        }

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value=_default_config(),
            ),
            patch("web_research_handler._recent_intake_pending", return_value=True),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        # Should be silent when intake is already pending
        assert capsys.readouterr().out.strip() == ""


class TestMainDisabledConfig:
    """Feature: Hook respects config to disable itself."""

    @pytest.mark.unit
    def test_disabled_via_config(self, capsys: pytest.CaptureFixture[str]):
        """Given enabled=False in config, exit silently."""
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com"},
            "tool_response": {"content": "x" * 200},
        }

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value={"enabled": False},
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""

    @pytest.mark.unit
    def test_lifecycle_flag_disabled(self, capsys: pytest.CaptureFixture[str]):
        """Given lifecycle feature flag off, exit silently."""
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com"},
            "tool_response": {"content": "x" * 200},
        }

        with (
            patch("sys.stdin", _json_stdin(payload)),
            patch(
                "web_research_handler.get_config",
                return_value={
                    "enabled": True,
                    "feature_flags": {"lifecycle": False},
                },
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                web_research_handler.main()

        assert exc_info.value.code == 0
        assert capsys.readouterr().out.strip() == ""
