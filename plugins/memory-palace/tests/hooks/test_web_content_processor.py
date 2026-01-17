# ruff: noqa: D101,D102,D103
"""BDD/TDD tests for web_content_processor.py hook.

Tests follow the Given-When-Then pattern for:
1. Content extraction from WebFetch responses
2. Search result extraction from WebSearch responses
3. Title extraction and slugification
4. Auto-capture storage functionality
5. Safety check integration
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

from web_content_processor import (
    extract_content_from_webfetch,
    extract_results_from_websearch,
    extract_title_from_content,
    slugify,
)

HOOK_PATH = Path(__file__).resolve().parents[2] / "hooks" / "web_content_processor.py"
QUEUE_DIR = Path(__file__).resolve().parents[2] / "docs" / "knowledge-corpus" / "queue"


def run_hook(payload: dict) -> tuple[int, str, str]:
    """Run the web content processor hook and return results."""
    input_data = json.dumps(payload)
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=input_data,
        capture_output=True,
        text=True,
        check=False,
        cwd=HOOK_PATH.parent,  # Run from hooks directory for imports
    )
    return result.returncode, result.stdout, result.stderr


class TestSlugify:
    """Tests for the slugify helper function."""

    @pytest.mark.unit
    def test_converts_to_lowercase(self) -> None:
        """Given uppercase text, slugify should return lowercase."""
        assert slugify("Hello World") == "hello-world"

    @pytest.mark.unit
    def test_replaces_spaces_with_hyphens(self) -> None:
        """Given text with spaces, slugify should use hyphens."""
        assert slugify("hello world test") == "hello-world-test"

    @pytest.mark.unit
    def test_removes_special_characters(self) -> None:
        """Given text with special chars, slugify should remove them."""
        assert slugify("Hello! World? @#$%") == "hello-world"

    @pytest.mark.unit
    def test_truncates_long_slugs(self) -> None:
        """Given long text, slugify should truncate to max_length."""
        long_text = "a" * 100
        result = slugify(long_text, max_length=20)
        assert len(result) <= 20

    @pytest.mark.unit
    def test_returns_untitled_for_empty_input(self) -> None:
        """Given empty or special-only input, slugify should return 'untitled'."""
        assert slugify("") == "untitled"
        assert slugify("@#$%") == "untitled"

    @pytest.mark.unit
    def test_removes_leading_trailing_hyphens(self) -> None:
        """Given text that would create leading/trailing hyphens."""
        assert slugify("--hello world--") == "hello-world"


class TestExtractTitleFromContent:
    """Tests for title extraction from content."""

    @pytest.mark.unit
    def test_extracts_markdown_heading(self) -> None:
        """Given content with markdown heading, should extract it."""
        content = "# My Article Title\n\nSome content here."
        title = extract_title_from_content(content, "https://example.com")
        assert title == "My Article Title"

    @pytest.mark.unit
    def test_extracts_multi_level_heading(self) -> None:
        """Given content with ## heading, should extract it."""
        content = "## Section Title\n\nContent."
        title = extract_title_from_content(content, "https://example.com")
        assert title == "Section Title"

    @pytest.mark.unit
    def test_uses_first_substantial_line(self) -> None:
        """Given content without heading, should use first substantial line."""
        content = "This is the first line of content that is long enough."
        title = extract_title_from_content(content, "https://example.com")
        assert "first line" in title.lower()

    @pytest.mark.unit
    def test_fallback_to_url_path(self) -> None:
        """Given minimal content, should fall back to URL path."""
        content = "X"  # Too short to be a title
        title = extract_title_from_content(content, "https://example.com/my-article")
        assert "my" in title.lower() or "article" in title.lower()

    @pytest.mark.unit
    def test_fallback_to_domain(self) -> None:
        """Given minimal content and root URL, should use domain."""
        content = ""
        title = extract_title_from_content(content, "https://example.com")
        assert title == "example.com"

    @pytest.mark.unit
    def test_truncates_long_titles(self) -> None:
        """Given very long heading, should truncate to 100 chars."""
        long_heading = "# " + "A" * 200
        title = extract_title_from_content(long_heading, "https://example.com")
        assert len(title) <= 100


class TestExtractContentFromWebfetch:
    """Tests for WebFetch response content extraction."""

    @pytest.mark.unit
    def test_extracts_from_string_response(self) -> None:
        """Given string response, should return it as content."""
        content, url = extract_content_from_webfetch("Hello content")
        assert content == "Hello content"
        assert url is None

    @pytest.mark.unit
    def test_extracts_from_dict_with_content(self) -> None:
        """Given dict with content key, should extract content."""
        response = {"content": "Page content", "url": "https://example.com"}
        content, url = extract_content_from_webfetch(response)
        assert content == "Page content"
        assert url == "https://example.com"

    @pytest.mark.unit
    def test_extracts_from_nested_result(self) -> None:
        """Given dict with nested result, should extract content."""
        response = {"result": {"content": "Nested content"}}
        content, url = extract_content_from_webfetch(response)
        assert content == "Nested content"

    @pytest.mark.unit
    def test_handles_result_as_string(self) -> None:
        """Given result as string, should extract it."""
        response = {"result": "String result"}
        content, url = extract_content_from_webfetch(response)
        assert content == "String result"

    @pytest.mark.unit
    def test_handles_empty_response(self) -> None:
        """Given empty response, should return empty content."""
        content, url = extract_content_from_webfetch({})
        assert content == ""
        assert url is None


class TestExtractResultsFromWebsearch:
    """Tests for WebSearch response extraction."""

    @pytest.mark.unit
    def test_extracts_search_results(self) -> None:
        """Given valid search response, should extract results."""
        response = {
            "results": [
                {
                    "url": "https://example.com/1",
                    "title": "Result 1",
                    "snippet": "Text",
                },
                {
                    "url": "https://example.com/2",
                    "title": "Result 2",
                    "description": "Desc",
                },
            ]
        }
        results = extract_results_from_websearch(response)
        assert len(results) == 2
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["title"] == "Result 1"
        assert results[1]["snippet"] == "Desc"  # Uses description as fallback

    @pytest.mark.unit
    def test_limits_to_10_results(self) -> None:
        """Given many results, should limit to 10."""
        response = {
            "results": [
                {"url": f"https://example.com/{i}", "title": f"Result {i}"}
                for i in range(20)
            ]
        }
        results = extract_results_from_websearch(response)
        assert len(results) == 10

    @pytest.mark.unit
    def test_handles_empty_results(self) -> None:
        """Given empty results, should return empty list."""
        results = extract_results_from_websearch({"results": []})
        assert results == []

    @pytest.mark.unit
    def test_handles_missing_results_key(self) -> None:
        """Given response without results key, should return empty list."""
        results = extract_results_from_websearch({})
        assert results == []

    @pytest.mark.unit
    def test_handles_non_dict_results(self) -> None:
        """Given non-dict items in results, should skip them."""
        response = {"results": ["string", {"url": "https://example.com"}, 123]}
        results = extract_results_from_websearch(response)
        assert len(results) == 1
        assert results[0]["url"] == "https://example.com"


class TestHookExecution:
    """Tests for the main hook execution."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exits_cleanly_for_non_web_tools(self) -> None:
        """Given non-WebFetch/WebSearch tool, hook should exit cleanly."""
        payload = {"tool_name": "Read", "tool_input": {}, "tool_response": {}}
        returncode, stdout, stderr = run_hook(payload)
        assert returncode == 0
        assert stdout == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exits_cleanly_for_empty_content(self) -> None:
        """Given WebFetch with empty content, hook should exit cleanly."""
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com"},
            "tool_response": {"content": ""},
        }
        returncode, stdout, stderr = run_hook(payload)
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exits_cleanly_for_short_content(self) -> None:
        """Given WebFetch with content < 100 chars, hook should skip."""
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com"},
            "tool_response": {"content": "Short content"},
        }
        returncode, stdout, stderr = run_hook(payload)
        assert returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_invalid_json_gracefully(self) -> None:
        """Given invalid JSON input, hook should exit cleanly."""
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            check=False,
            cwd=HOOK_PATH.parent,
        )
        assert result.returncode == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_processes_webfetch_with_substantial_content(self) -> None:
        """Given WebFetch with substantial content, hook should process it."""
        # Generate content > 100 chars
        content = "# Test Article\n\n" + "This is test content. " * 20
        payload = {
            "tool_name": "WebFetch",
            "tool_input": {"url": "https://example.com/test", "prompt": "Summarize"},
            "tool_response": {"content": content, "url": "https://example.com/test"},
        }
        returncode, stdout, stderr = run_hook(payload)
        assert returncode == 0
        # Should have output if auto_capture is enabled (default)
        if stdout:
            output = json.loads(stdout)
            assert "hookSpecificOutput" in output
            context = output["hookSpecificOutput"].get("additionalContext", "")
            # Should mention Memory Palace
            assert "Memory Palace" in context or "memory" in context.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_processes_websearch_results(self) -> None:
        """Given WebSearch with results, hook should process them."""
        payload = {
            "tool_name": "WebSearch",
            "tool_input": {"query": "python testing"},
            "tool_response": {
                "results": [
                    {
                        "url": "https://example.com/test1",
                        "title": "Testing in Python",
                        "snippet": "Learn testing",
                    },
                    {
                        "url": "https://example.com/test2",
                        "title": "Pytest Guide",
                        "snippet": "Using pytest",
                    },
                ]
            },
        }
        returncode, stdout, stderr = run_hook(payload)
        assert returncode == 0


class TestWebFetchContentStorage:
    """Tests for WebFetch content storage to queue."""

    @pytest.fixture
    def clean_queue(self, tmp_path: Path) -> Path:
        """Create a temporary queue directory for testing."""
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir(parents=True)
        return queue_dir

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_stored_content_has_frontmatter(self, tmp_path: Path) -> None:
        """Given stored content, it should have proper YAML frontmatter."""
        # This test verifies the format of stored content
        from web_content_processor import store_webfetch_content

        # Use a temporary directory to avoid polluting real queue
        with patch("web_content_processor.QUEUE_DIR", tmp_path / "queue"):
            with patch("web_content_processor.update_index"):  # Skip index updates
                content = "# Test Article\n\n" + "Content " * 100
                tmp_queue = tmp_path / "queue"
                tmp_queue.mkdir(parents=True, exist_ok=True)

                result = store_webfetch_content(
                    content=content,
                    url="https://example.com/article",
                    prompt="Summarize this",
                )

                if result:
                    stored_file = Path(result)
                    assert stored_file.exists()
                    stored_content = stored_file.read_text()

                    # Check frontmatter structure
                    assert stored_content.startswith("---")
                    assert "queue_entry_id:" in stored_content
                    assert "source_type: webfetch" in stored_content
                    assert "status: pending_review" in stored_content
                    assert 'url: "https://example.com/article"' in stored_content


class TestWebSearchResultsStorage:
    """Tests for WebSearch results storage to queue."""

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_stored_search_has_frontmatter(self, tmp_path: Path) -> None:
        """Given stored search results, they should have proper frontmatter."""
        from web_content_processor import store_websearch_results

        with patch("web_content_processor.QUEUE_DIR", tmp_path / "queue"):
            tmp_queue = tmp_path / "queue"
            tmp_queue.mkdir(parents=True, exist_ok=True)

            results = [
                {
                    "url": "https://example.com/1",
                    "title": "Result 1",
                    "snippet": "Text 1",
                },
                {
                    "url": "https://example.com/2",
                    "title": "Result 2",
                    "snippet": "Text 2",
                },
            ]

            result = store_websearch_results(query="test query", results=results)

            if result:
                stored_file = Path(result)
                assert stored_file.exists()
                stored_content = stored_file.read_text()

                # Check frontmatter structure
                assert stored_content.startswith("---")
                assert "source_type: websearch" in stored_content
                assert "result_count: 2" in stored_content
                assert 'query: "test query"' in stored_content

    @pytest.mark.unit
    def test_empty_results_returns_none(self) -> None:
        """Given empty results list, should return None."""
        from web_content_processor import store_websearch_results

        result = store_websearch_results(query="test", results=[])
        assert result is None
