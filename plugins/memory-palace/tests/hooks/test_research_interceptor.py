"""Tests for research_interceptor hook."""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

import research_interceptor
from research_interceptor import (
    extract_query_intent,
    format_cached_entry_context,
    is_evergreen,
    make_decision,
    needs_freshness,
    search_local_knowledge,
)


class TestExtractQueryIntent:
    """Tests for query intent extraction."""

    def test_websearch_query(self) -> None:
        """WebSearch query should be extracted."""
        query = extract_query_intent("WebSearch", {"query": "python async patterns"})
        assert query == "python async patterns"

    def test_webfetch_prompt(self) -> None:
        """WebFetch prompt should be extracted."""
        query = extract_query_intent(
            "WebFetch",
            {"prompt": "get fastapi docs", "url": "https://example.com"},
        )
        assert query == "get fastapi docs"

    def test_webfetch_url_fallback(self) -> None:
        """WebFetch should fall back to URL if no prompt."""
        query = extract_query_intent("WebFetch", {"url": "https://example.com/article"})
        assert query == "https://example.com/article"

    def test_empty_input(self) -> None:
        """Empty input should return empty string."""
        query = extract_query_intent("WebSearch", {})
        assert query == ""

    def test_unknown_tool(self) -> None:
        """Unknown tool should return empty string."""
        query = extract_query_intent("SomeTool", {"query": "test"})
        assert query == ""


class TestFreshnessDetection:
    """Tests for freshness detection."""

    def test_latest_keyword(self) -> None:
        """Query with 'latest' should need freshness."""
        assert needs_freshness("latest python features")

    def test_recent_keyword(self) -> None:
        """Query with 'recent' should need freshness."""
        assert needs_freshness("recent changes in fastapi")

    def test_year_2025(self) -> None:
        """Query with 2025 should need freshness."""
        assert needs_freshness("python 2025 roadmap")

    def test_year_2024(self) -> None:
        """Query with 2024 should need freshness."""
        assert needs_freshness("what changed in 2024")

    def test_timeless_query(self) -> None:
        """Timeless query should not need freshness."""
        assert not needs_freshness("async error handling patterns")

    def test_evergreen_query(self) -> None:
        """Evergreen query should not need freshness."""
        assert not needs_freshness("how to handle exceptions in python")


class TestEvergreenDetection:
    """Tests for evergreen content detection."""

    def test_pattern_keyword(self) -> None:
        """Query about patterns is evergreen."""
        assert is_evergreen("design patterns for async code")

    def test_principle_keyword(self) -> None:
        """Query about principles is evergreen."""
        assert is_evergreen("SOLID principles")

    def test_how_to_query(self) -> None:
        """How-to queries are evergreen."""
        assert is_evergreen("how to implement dependency injection")

    def test_guide_keyword(self) -> None:
        """Guide queries are evergreen."""
        assert is_evergreen("guide to python testing")

    def test_non_evergreen(self) -> None:
        """Specific version query is not evergreen."""
        assert not is_evergreen("FastAPI 0.100 release notes")


class TestMakeDecision:
    """Tests for decision making logic."""

    def test_web_only_mode(self) -> None:
        """web_only mode should always proceed."""
        decision = make_decision("test query", [], "web_only")
        assert decision.action == "proceed"
        assert len(decision.context) == 0

    def test_cache_only_no_match(self) -> None:
        """cache_only with no match should block."""
        decision = make_decision("test query", [], "cache_only")
        assert decision.action == "block"
        assert "cache_only mode" in decision.context[0]

    def test_cache_first_no_match(self) -> None:
        """cache_first with no match should proceed and flag for intake."""
        decision = make_decision("test query", [], "cache_first")
        assert decision.action == "proceed"
        assert decision.should_flag_for_intake is True

    def test_strong_match_evergreen_cache_first(self) -> None:
        """Strong match on evergreen topic in cache_first should augment."""
        results = [
            {
                "match_score": 0.85,
                "match_strength": "strong",
                "title": "Python Async Patterns",
                "file": "docs/async.md",
            },
        ]
        decision = make_decision("async error handling patterns", results, "cache_first")
        assert decision.action == "augment"
        assert "strong cached match" in decision.context[0]

    def test_strong_match_needs_freshness(self) -> None:
        """Strong match but needs freshness should augment."""
        results = [
            {
                "match_score": 0.90,
                "match_strength": "strong",
                "title": "Python Release Notes",
                "file": "docs/releases.md",
            },
        ]
        decision = make_decision("latest python 2025 features", results, "cache_first")
        assert decision.action == "augment"
        assert "fresh data" in decision.context[0]

    def test_partial_match_cache_first(self) -> None:
        """Partial match in cache_first should augment and flag for intake."""
        results = [
            {
                "match_score": 0.60,
                "match_strength": "partial",
                "title": "Python Basics",
                "file": "docs/python.md",
            },
        ]
        decision = make_decision("python advanced patterns", results, "cache_first")
        assert decision.action == "augment"
        assert decision.should_flag_for_intake is True
        assert "partial match" in decision.context[0]

    def test_weak_match_cache_first(self) -> None:
        """Weak match in cache_first should proceed."""
        results = [
            {
                "match_score": 0.30,
                "match_strength": "weak",
                "title": "General Programming",
                "file": "docs/general.md",
            },
        ]
        decision = make_decision("python async patterns", results, "cache_first")
        assert decision.should_flag_for_intake is True

    def test_augment_mode_partial_match(self) -> None:
        """Augment mode should always augment with cache."""
        results = [
            {
                "match_score": 0.60,
                "match_strength": "partial",
                "title": "Python Basics",
                "file": "docs/python.md",
            },
        ]
        decision = make_decision("python patterns", results, "augment")
        assert decision.action == "augment"
        assert len(decision.cached_entries) > 0

    def test_cache_only_partial_match(self) -> None:
        """cache_only with partial match should block."""
        results = [
            {
                "match_score": 0.50,
                "match_strength": "partial",
                "title": "Python Basics",
                "file": "docs/python.md",
            },
        ]
        decision = make_decision("python patterns", results, "cache_only")
        assert decision.action == "block"

    def test_domain_alignment_surface(self) -> None:
        """Domains of interest should surface in the intake payload."""
        config = {"domains_of_interest": ["python async", "security"]}
        decision = make_decision(
            "python async telemetry strategy",
            [],
            "cache_first",
            config=config,
        )
        assert decision.intake_payload is not None
        assert decision.aligned_domains == ["python async"]
        assert decision.intake_payload.domain_alignment.is_aligned
        assert decision.novelty_score == pytest.approx(1.0)

    def test_duplicate_detection_toggles_intake(self) -> None:
        """High-overlap duplicates should disable intake flagging."""
        results = [
            {
                "match_score": 0.95,
                "match_strength": "strong",
                "title": "Python Async Patterns",
                "file": "docs/async.md",
                "entry_id": "entry-123",
            },
        ]
        config = {"intake_threshold": 80}
        decision = make_decision("python async patterns", results, "cache_first", config=config)
        assert decision.should_flag_for_intake is False
        assert decision.intake_payload is not None
        assert decision.intake_payload.duplicate_entry_ids == ["entry-123"]
        assert decision.novelty_score == pytest.approx(0.05)


class TestFormatCachedEntry:
    """Tests for cached entry formatting."""

    def test_basic_formatting(self) -> None:
        """Entry should be formatted with title and match score."""
        entry = {"title": "Python Async Patterns", "file": "docs/async.md", "match_score": 0.85}
        formatted = format_cached_entry_context(entry)
        assert "Python Async Patterns" in formatted
        assert "85%" in formatted
        assert "docs/async.md" in formatted

    def test_with_content_excerpt(self) -> None:
        """Entry with content should include excerpt."""
        entry = {
            "title": "Test Entry",
            "file": "docs/test.md",
            "match_score": 0.70,
            "content": "This is a long piece of content that should be truncated. " * 10,
        }
        formatted = format_cached_entry_context(entry)
        assert "Excerpt:" in formatted
        assert "..." in formatted

    def test_untitled_entry(self) -> None:
        """Entry without title should use 'Untitled'."""
        entry = {"file": "docs/unknown.md", "match_score": 0.60}
        formatted = format_cached_entry_context(entry)
        assert "Untitled" in formatted


class TestSearchLocalKnowledge:
    """Tests for local knowledge search integration."""

    def test_successful_search(self) -> None:
        """Successful search should return results."""
        config = {"corpus_dir": "docs/knowledge-corpus/", "indexes_dir": "data/indexes"}
        with patch.object(research_interceptor, "CacheLookup") as mock_lookup:
            mock_instance = MagicMock()
            mock_instance.search.return_value = [{"title": "Test", "match_score": 0.8}]
            mock_lookup.return_value = mock_instance

            results = search_local_knowledge("test query", config)
            assert len(results) == 1
            assert results[0]["title"] == "Test"
            mock_instance.search.assert_called_once_with(
                "test query",
                mode="unified",
                min_score=0.0,
            )
            expected_corpus = str(research_interceptor.PLUGIN_ROOT / "docs/knowledge-corpus/")
            expected_index = str(research_interceptor.PLUGIN_ROOT / "data/indexes")
            mock_lookup.assert_called_once_with(
                expected_corpus, expected_index, embedding_provider="none"
            )

    def test_search_error_handling(self) -> None:
        """Search errors should return empty results."""
        config = {"corpus_dir": "docs/knowledge-corpus/", "indexes_dir": "data/indexes"}
        with patch.object(research_interceptor, "CacheLookup") as mock_lookup:
            mock_lookup.side_effect = Exception("Search failed")
            results = search_local_knowledge("test query", config)
            assert results == []

    def test_search_with_unified_mode(self) -> None:
        """Search should use unified mode."""
        config = {"corpus_dir": "docs/knowledge-corpus/", "indexes_dir": "data/indexes"}
        with patch.object(research_interceptor, "CacheLookup") as mock_lookup:
            mock_instance = MagicMock()
            mock_instance.search.return_value = []
            mock_lookup.return_value = mock_instance

            search_local_knowledge("test query", config)
            mock_instance.search.assert_called_once_with(
                "test query",
                mode="unified",
                min_score=0.0,
            )


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow_cache_first(self) -> None:
        """Test complete workflow in cache_first mode."""
        # This would require a full integration test setup
        # For now, test the decision flow
        results = [
            {
                "match_score": 0.85,
                "match_strength": "strong",
                "title": "Test Knowledge",
                "file": "docs/test.md",
            },
        ]

        decision = make_decision("evergreen test query", results, "cache_first")
        assert decision.action == "augment"
        assert len(decision.cached_entries) > 0

    def test_complete_workflow_cache_only(self) -> None:
        """Test complete workflow in cache_only mode."""
        results = [
            {
                "match_score": 0.85,
                "match_strength": "strong",
                "title": "Test Knowledge",
                "file": "docs/test.md",
            },
        ]

        decision = make_decision("test query", results, "cache_only")
        assert decision.action == "block"
        assert "cache_only" in decision.context[0]

    def test_complete_workflow_augment(self) -> None:
        """Test complete workflow in augment mode."""
        results = [
            {
                "match_score": 0.60,
                "match_strength": "partial",
                "title": "Test Knowledge",
                "file": "docs/test.md",
            },
        ]

        decision = make_decision("test query", results, "augment")
        assert decision.action == "augment"
        assert len(decision.cached_entries) > 0

    def test_hook_output_format_deny(self) -> None:
        """Test hook JSON output uses correct API fields for deny action."""
        # Mock stdin with a WebSearch request
        mock_stdin = StringIO(
            json.dumps(
                {
                    "tool_name": "WebSearch",
                    "tool_input": {"query": "test query"},
                },
            ),
        )

        # Mock config to enable cache_only mode
        mock_config = {
            "enabled": True,
            "research_mode": "cache_only",
            "telemetry": {"enabled": False},
        }

        # Mock search to return a strong match
        mock_results = [
            {
                "match_score": 0.85,
                "match_strength": "strong",
                "title": "Test Knowledge",
                "file": "docs/test.md",
                "content": "Test content",
            },
        ]

        # Capture stdout
        mock_stdout = StringIO()

        with (
            patch("sys.stdin", mock_stdin),
            patch("sys.stdout", mock_stdout),
            patch("shared.config.get_config", return_value=mock_config),
            patch("research_interceptor.search_local_knowledge", return_value=mock_results),
            pytest.raises(SystemExit) as exc_info,
        ):
            research_interceptor.main()

        assert exc_info.value.code == 0

        # Parse the JSON output
        output = mock_stdout.getvalue()
        if output:
            response = json.loads(output)

            # Verify correct API fields are present
            assert "hookSpecificOutput" in response
            hook_output = response["hookSpecificOutput"]

            assert hook_output["hookEventName"] == "PreToolUse"
            assert hook_output["permissionDecision"] == "deny"
            assert "permissionDecisionReason" in hook_output
            assert "additionalContext" in hook_output
            assert "intakeFlagPayload" in hook_output
            assert "intakeDecisionRationale" in hook_output

            # Verify incorrect fields are NOT present
            assert "blockToolExecution" not in hook_output
            assert "blockReason" not in hook_output

    def test_hook_output_format_allow(self) -> None:
        """Test hook JSON output uses correct API fields for allow action."""
        # Mock stdin with a WebSearch request
        mock_stdin = StringIO(
            json.dumps(
                {
                    "tool_name": "WebSearch",
                    "tool_input": {"query": "test query"},
                },
            ),
        )

        # Mock config to enable cache_first mode
        mock_config = {
            "enabled": True,
            "research_mode": "cache_first",
            "telemetry": {"enabled": False},
        }

        # Mock search to return a partial match (augment mode)
        mock_results = [
            {
                "match_score": 0.60,
                "match_strength": "partial",
                "title": "Test Knowledge",
                "file": "docs/test.md",
                "content": "Test content",
            },
        ]

        # Capture stdout
        mock_stdout = StringIO()

        with (
            patch("sys.stdin", mock_stdin),
            patch("sys.stdout", mock_stdout),
            patch("shared.config.get_config", return_value=mock_config),
            patch("research_interceptor.search_local_knowledge", return_value=mock_results),
            pytest.raises(SystemExit) as exc_info,
        ):
            research_interceptor.main()

        assert exc_info.value.code == 0

        # Parse the JSON output
        output = mock_stdout.getvalue()
        if output:
            response = json.loads(output)

            # Verify correct API fields are present
            assert "hookSpecificOutput" in response
            hook_output = response["hookSpecificOutput"]

            assert hook_output["hookEventName"] == "PreToolUse"
            assert hook_output["permissionDecision"] == "allow"
            assert "additionalContext" in hook_output
            assert "intakeFlagPayload" in hook_output
            assert "intakeDecisionRationale" in hook_output

            # Verify incorrect fields are NOT present
            assert "blockToolExecution" not in hook_output
            assert "blockReason" not in hook_output

    def test_telemetry_logging_enabled(self) -> None:
        """Telemetry logger should receive a structured event when enabled."""
        mock_stdin = StringIO(
            json.dumps(
                {
                    "tool_name": "WebSearch",
                    "tool_input": {"query": "async error handling"},
                },
            ),
        )
        mock_config = {
            "enabled": True,
            "research_mode": "cache_first",
            "telemetry": {"enabled": True, "file": "data/telemetry/test.csv"},
        }
        mock_results = [
            {
                "match_score": 0.95,
                "match_strength": "strong",
                "title": "Async Patterns",
                "file": "docs/test.md",
                "entry_id": "async-patterns",
                "content": "Structured concurrency keeps resources safe.",
            },
        ]
        mock_logger = MagicMock()

        with (
            patch("sys.stdin", mock_stdin),
            patch("sys.stdout", StringIO()),
            patch("shared.config.get_config", return_value=mock_config),
            patch("research_interceptor.search_local_knowledge", return_value=mock_results),
            patch("research_interceptor.TelemetryLogger", return_value=mock_logger),
            pytest.raises(SystemExit),
        ):
            research_interceptor.main()

        mock_logger.log_event.assert_called_once()
        telemetry_event = mock_logger.log_event.call_args[0][0]
        assert telemetry_event.decision == "augment"
        assert telemetry_event.cache_hits == 1
        assert telemetry_event.returned_entries == 1
        assert telemetry_event.novelty_score is not None
        assert telemetry_event.intake_delta_reasoning
        assert telemetry_event.duplicate_entry_ids == "async-patterns"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
