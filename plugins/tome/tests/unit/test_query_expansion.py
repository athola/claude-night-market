"""
Feature: Query expansion for richer search coverage

As a research channel
I want to generate multiple query reformulations from a single topic
So that searches find results that a single query string would miss
"""

from __future__ import annotations

import pytest
from tome.channels.academic import expand_academic_queries
from tome.channels.discourse import expand_discourse_queries
from tome.channels.github import expand_github_queries


class TestExpandAcademicQueries:
    """
    Feature: Academic query expansion

    As the academic channel
    I want to produce synonym, specificity, and temporal variants
    So that arXiv and Semantic Scholar searches cover more ground
    """

    @pytest.mark.unit
    def test_returns_multiple_queries(self) -> None:
        """
        Scenario: Basic topic expansion
        Given a research topic "cache eviction policy"
        When expand_academic_queries is called
        Then at least 3 query strings are returned
        """
        queries = expand_academic_queries("cache eviction policy")
        assert len(queries) >= 3

    @pytest.mark.unit
    def test_original_topic_included(self) -> None:
        """
        Scenario: Original topic preserved
        Given a research topic
        When expand_academic_queries is called
        Then the original topic appears as one of the queries
        """
        topic = "distributed consensus"
        queries = expand_academic_queries(topic)
        assert topic in queries

    @pytest.mark.unit
    def test_queries_are_unique(self) -> None:
        """
        Scenario: No duplicate queries
        Given a topic
        When expand_academic_queries is called
        Then all returned queries are distinct
        """
        queries = expand_academic_queries("neural network pruning")
        assert len(queries) == len(set(queries))

    @pytest.mark.unit
    def test_includes_broad_variant(self) -> None:
        """
        Scenario: Broad variant included
        Given a specific topic "LRU cache eviction"
        When expand_academic_queries is called
        Then at least one query is broader (e.g., "cache eviction")
        """
        queries = expand_academic_queries("LRU cache eviction")
        # At least one query should be shorter than the original
        assert any(len(q) < len("LRU cache eviction") for q in queries)

    @pytest.mark.unit
    def test_includes_survey_variant(self) -> None:
        """
        Scenario: Survey/review variant included
        Given a topic
        When expand_academic_queries is called
        Then at least one query includes "survey" or "review"
        """
        queries = expand_academic_queries("graph neural networks")
        lowered = [q.lower() for q in queries]
        assert any("survey" in q or "review" in q for q in lowered)


class TestExpandGithubQueries:
    """
    Feature: GitHub query expansion

    As the code channel
    I want diverse search variants for GitHub
    So that implementation search finds repos beyond the obvious keywords
    """

    @pytest.mark.unit
    def test_returns_multiple_queries(self) -> None:
        """
        Scenario: Basic expansion
        Given a topic
        When expand_github_queries is called
        Then at least 3 queries are returned
        """
        queries = expand_github_queries("rate limiter")
        assert len(queries) >= 3

    @pytest.mark.unit
    def test_queries_are_unique(self) -> None:
        """
        Scenario: No duplicates
        Given a topic
        When expand_github_queries is called
        Then all queries are distinct
        """
        queries = expand_github_queries("websocket server")
        assert len(queries) == len(set(queries))

    @pytest.mark.unit
    def test_includes_implementation_variant(self) -> None:
        """
        Scenario: Implementation-focused variant
        Given a topic
        When expand_github_queries is called
        Then at least one query targets implementations
        """
        queries = expand_github_queries("bloom filter")
        lowered = [q.lower() for q in queries]
        assert any(
            "implementation" in q or "library" in q or "example" in q for q in lowered
        )


class TestExpandDiscourseQueries:
    """
    Feature: Discourse query expansion

    As the discourse channel
    I want diverse community search queries
    So that HN, Reddit, and blog searches capture varied discussions
    """

    @pytest.mark.unit
    def test_returns_multiple_queries(self) -> None:
        """
        Scenario: Basic expansion
        Given a topic
        When expand_discourse_queries is called
        Then at least 2 queries are returned
        """
        queries = expand_discourse_queries("microservice patterns")
        assert len(queries) >= 2

    @pytest.mark.unit
    def test_queries_are_unique(self) -> None:
        """
        Scenario: No duplicates
        Given a topic
        When expand_discourse_queries is called
        Then all queries are distinct
        """
        queries = expand_discourse_queries("async python")
        assert len(queries) == len(set(queries))
