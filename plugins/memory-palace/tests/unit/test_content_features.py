"""Tests for content_features — extract_keywords and infer_queries.

Feature: Content Feature Extraction
  As a marginal value filter
  I want to extract keywords and infer queries from content
  So that I can compare new content against the existing corpus
"""

from __future__ import annotations

import pytest

from memory_palace.corpus.content_features import extract_keywords, infer_queries


class TestExtractKeywords:
    """Feature: Keyword extraction.

    As a filter
    I want to extract meaningful keywords from content
    So that I can detect overlap with existing entries
    """

    @pytest.mark.unit
    def test_extracts_tags(self) -> None:
        """Scenario: Tags provided are included in keywords
        Given tags ["python", "async"]
        When I extract keywords
        Then both tags are in the result.
        """
        keywords = extract_keywords("some content", "title", ["python", "async"])
        assert "python" in keywords
        assert "async" in keywords

    @pytest.mark.unit
    def test_extracts_words_from_title(self) -> None:
        """Scenario: Title words become keywords
        Given a title "Understanding Async Programming"
        When I extract keywords
        Then "understanding", "async", "programming" are in the result.
        """
        keywords = extract_keywords("content", "Understanding Async Programming", [])
        assert "understanding" in keywords
        assert "async" in keywords
        assert "programming" in keywords

    @pytest.mark.unit
    def test_extracts_hyphenated_technical_terms(self) -> None:
        """Scenario: Hyphenated terms from content body
        Given content with "event-driven" and "async-await"
        When I extract keywords
        Then those hyphenated terms are in the result.
        """
        keywords = extract_keywords(
            "Using event-driven architecture with async-await patterns", "test", []
        )
        assert "event-driven" in keywords
        assert "async-await" in keywords

    @pytest.mark.unit
    def test_extracts_emphasized_text(self) -> None:
        """Scenario: Bold and italic markdown text is extracted
        Given content with **important** and *critical*
        When I extract keywords
        Then "important" and "critical" are in the result.
        """
        keywords = extract_keywords(
            "This is **important** and *critical* for understanding", "test", []
        )
        assert "important" in keywords
        assert "critical" in keywords

    @pytest.mark.unit
    def test_extracts_heading_words(self) -> None:
        """Scenario: Markdown headings contribute keywords
        Given content with headings
        When I extract keywords
        Then heading words appear in the result.
        """
        content = "# Main Topic\n## Subtopic One\nBody text.\n"
        keywords = extract_keywords(content, "test", [])
        assert "main" in keywords
        assert "topic" in keywords
        assert "subtopic" in keywords

    @pytest.mark.unit
    def test_removes_stop_words(self) -> None:
        """Scenario: Common stop words are excluded
        Given tags containing "the" and "and"
        When I extract keywords
        Then those stop words are absent.
        """
        keywords = extract_keywords(
            "The quick brown fox", "The Big Test", ["the", "and"]
        )
        assert "the" not in keywords
        assert "and" not in keywords

    @pytest.mark.unit
    def test_returns_set(self) -> None:
        """Scenario: Return type is a set
        Given any content
        When I extract keywords
        Then the return value is a set.
        """
        result = extract_keywords("content", "title", [])
        assert isinstance(result, set)


class TestInferQueries:
    """Feature: Query inference.

    As a filter
    I want to infer potential search queries from content
    So that I can check whether existing entries already answer them
    """

    @pytest.mark.unit
    def test_infers_how_to_queries_from_headings(self) -> None:
        """Scenario: Heading with "how" generates a query
        Given a heading "How to implement caching"
        When I infer queries
        Then a query containing "how" is returned.
        """
        content = "# How to implement caching\n\nSome content.\n"
        queries = infer_queries(content, "Caching Guide")
        assert any("how" in q.lower() for q in queries)

    @pytest.mark.unit
    def test_infers_what_is_queries_for_patterns(self) -> None:
        """Scenario: Heading with "pattern" generates a "what is" query
        Given a heading "Repository Pattern"
        When I infer queries
        Then a query containing "pattern" is returned.
        """
        content = "# Repository Pattern\n\nDetails.\n"
        queries = infer_queries(content, "Design Patterns")
        assert any("pattern" in q.lower() for q in queries)

    @pytest.mark.unit
    def test_infers_best_practices_queries(self) -> None:
        """Scenario: Heading with "practice" generates a best-practices query
        Given a heading "Testing Best Practices"
        When I infer queries
        Then a query containing "best practices" is returned.
        """
        content = "# Testing Best Practices\n\nDetails.\n"
        queries = infer_queries(content, "Testing Guide")
        assert any("best practices" in q.lower() for q in queries)

    @pytest.mark.unit
    def test_returns_list(self) -> None:
        """Scenario: Return type is a list
        Given any content
        When I infer queries
        Then the return value is a list.
        """
        result = infer_queries("some content", "title")
        assert isinstance(result, list)
