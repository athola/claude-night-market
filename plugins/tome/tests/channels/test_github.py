"""
Feature: GitHub code search channel

As a research pipeline
I want to build GitHub search queries and parse responses into Findings
So that agents can retrieve relevant code repositories without coupling to HTTP
"""

from __future__ import annotations

from typing import Any

import pytest
from tome.channels.github import (
    build_github_api_search,
    build_github_search_queries,
    parse_github_api_response,
    parse_github_result,
    rank_github_findings,
)
from tome.models import Finding


class TestBuildGithubSearchQueries:
    """
    Feature: GitHub WebSearch query generation

    As a research agent
    I want URL-free query strings targeting GitHub
    So that I can pass them to a WebSearch tool without writing HTTP code
    """

    @pytest.mark.unit
    def test_returns_list_of_strings(self) -> None:
        """
        Scenario: Query builder produces string list
        Given a topic string
        When build_github_search_queries is called
        Then the result is a list of strings
        """
        result = build_github_search_queries("async patterns")

        assert isinstance(result, list)
        assert all(isinstance(q, str) for q in result)

    @pytest.mark.unit
    def test_each_query_contains_topic(self) -> None:
        """
        Scenario: Every query includes the topic
        Given the topic "bloom filter"
        When build_github_search_queries is called
        Then every returned query contains "bloom filter"
        """
        result = build_github_search_queries("bloom filter")

        for query in result:
            assert "bloom filter" in query

    @pytest.mark.unit
    def test_respects_max_queries_limit(self) -> None:
        """
        Scenario: max_queries caps the result length
        Given max_queries=2
        When build_github_search_queries is called
        Then at most 2 queries are returned
        """
        result = build_github_search_queries("lru cache", max_queries=2)

        assert len(result) <= 2

    @pytest.mark.unit
    def test_default_queries_target_github(self) -> None:
        """
        Scenario: Default queries reference GitHub
        Given no max_queries override
        When build_github_search_queries is called
        Then at least one query contains "github.com" or "github"
        """
        result = build_github_search_queries("raft consensus")

        assert any("github" in q.lower() for q in result)

    @pytest.mark.unit
    def test_max_queries_one_returns_single_query(self) -> None:
        """
        Scenario: max_queries=1 yields exactly one query
        Given max_queries=1
        When build_github_search_queries is called
        Then exactly one query string is returned
        """
        result = build_github_search_queries("merkle tree", max_queries=1)

        assert len(result) == 1


class TestBuildGithubApiSearch:
    """
    Feature: GitHub API search URL construction

    As a research agent
    I want a correct GitHub REST API URL
    So that WebFetch can retrieve structured repository data
    """

    @pytest.mark.unit
    def test_url_points_to_github_api(self) -> None:
        """
        Scenario: URL targets GitHub search/repositories endpoint
        Given the topic "skiplist"
        When build_github_api_search is called
        Then the URL starts with https://api.github.com/search/repositories
        """
        url = build_github_api_search("skiplist")

        assert url.startswith("https://api.github.com/search/repositories")

    @pytest.mark.unit
    def test_url_contains_encoded_topic(self) -> None:
        """
        Scenario: Multi-word topic is URL-encoded in the query string
        Given the topic "async python"
        When build_github_api_search is called
        Then the URL contains the encoded topic
        """
        url = build_github_api_search("async python")

        assert "async" in url
        assert "python" in url

    @pytest.mark.unit
    def test_url_sorts_by_stars(self) -> None:
        """
        Scenario: Results are sorted by stars for quality ranking
        Given any topic
        When build_github_api_search is called
        Then the URL includes sort=stars
        """
        url = build_github_api_search("parser combinator")

        assert "sort=stars" in url


class TestParseGithubResult:
    """
    Feature: WebSearch result parsing

    As a research pipeline
    I want to convert a raw WebSearch result dict into a Finding
    So that downstream synthesis works with typed objects
    """

    @pytest.mark.unit
    def test_extracts_title_url_and_snippet(self) -> None:
        """
        Scenario: Standard result with all fields present
        Given a result dict with title, url, and snippet
        When parse_github_result is called
        Then the Finding has correct title and url
        """
        result: dict[str, Any] = {
            "title": "example/async-lib",
            "url": "https://github.com/example/async-lib",
            "snippet": "Async utilities for Python",
        }

        finding = parse_github_result(result)

        assert finding.title == "example/async-lib"
        assert finding.url == "https://github.com/example/async-lib"
        assert finding.source == "github"
        assert finding.channel == "code"

    @pytest.mark.unit
    def test_handles_missing_snippet_gracefully(self) -> None:
        """
        Scenario: Result with no snippet or description
        Given a result dict with only title and url
        When parse_github_result is called
        Then a Finding is returned without raising an exception
        """
        result: dict[str, Any] = {
            "title": "owner/repo",
            "url": "https://github.com/owner/repo",
        }

        finding = parse_github_result(result)

        assert isinstance(finding, Finding)
        assert finding.summary != ""

    @pytest.mark.unit
    def test_handles_empty_dict_gracefully(self) -> None:
        """
        Scenario: Completely empty result dict
        Given an empty dict
        When parse_github_result is called
        Then a Finding is returned without raising an exception
        """
        finding = parse_github_result({})

        assert isinstance(finding, Finding)

    @pytest.mark.unit
    def test_relevance_is_in_valid_range(self) -> None:
        """
        Scenario: Relevance score is always a valid float
        Given a standard result dict
        When parse_github_result is called
        Then relevance is in [0.0, 1.0]
        """
        result: dict[str, Any] = {
            "title": "owner/bloom-filter",
            "url": "https://github.com/owner/bloom-filter",
            "snippet": "Bloom filter implementation",
        }

        finding = parse_github_result(result)

        assert 0.0 <= finding.relevance <= 1.0


class TestParseGithubApiResponse:
    """
    Feature: GitHub API JSON response parsing

    As a research pipeline
    I want to convert a GitHub API payload into a list of Findings
    So that ranked code results are available for synthesis
    """

    @pytest.mark.unit
    def test_extracts_repo_name_stars_and_url(self) -> None:
        """
        Scenario: API response with one repository item
        Given a valid API payload with full_name, html_url, stargazers_count
        When parse_github_api_response is called
        Then the Finding has the correct metadata
        """
        data: dict[str, Any] = {
            "items": [
                {
                    "full_name": "redis/redis",
                    "html_url": "https://github.com/redis/redis",
                    "stargazers_count": 65000,
                    "description": "Redis data structure server",
                    "language": "C",
                    "updated_at": "2024-12-01T10:00:00Z",
                }
            ]
        }

        findings = parse_github_api_response(data, "redis")

        assert len(findings) == 1
        f = findings[0]
        assert f.metadata["repo_name"] == "redis/redis"
        assert f.metadata["stars"] == 65000
        assert f.url == "https://github.com/redis/redis"

    @pytest.mark.unit
    def test_skips_items_without_html_url(self) -> None:
        """
        Scenario: Item missing html_url is excluded
        Given an API payload where one item has no html_url
        When parse_github_api_response is called
        Then only the item with a url produces a Finding
        """
        data: dict[str, Any] = {
            "items": [
                {"full_name": "bad/item"},
                {
                    "full_name": "good/item",
                    "html_url": "https://github.com/good/item",
                    "stargazers_count": 100,
                    "description": "Good",
                },
            ]
        }

        findings = parse_github_api_response(data, "item")

        assert len(findings) == 1
        assert findings[0].metadata["repo_name"] == "good/item"

    @pytest.mark.unit
    def test_empty_items_list_returns_empty(self) -> None:
        """
        Scenario: API response with no items
        Given {"items": []}
        When parse_github_api_response is called
        Then an empty list is returned
        """
        findings = parse_github_api_response({"items": []}, "anything")

        assert findings == []

    @pytest.mark.unit
    def test_missing_items_key_returns_empty(self) -> None:
        """
        Scenario: API response missing the items key entirely
        Given {}
        When parse_github_api_response is called
        Then an empty list is returned without raising
        """
        findings = parse_github_api_response({}, "anything")

        assert findings == []

    @pytest.mark.unit
    def test_handles_null_description(self) -> None:
        """
        Scenario: Repository has a null description field
        Given an item with description=null
        When parse_github_api_response is called
        Then a Finding is returned without raising
        """
        data: dict[str, Any] = {
            "items": [
                {
                    "full_name": "user/nodesc",
                    "html_url": "https://github.com/user/nodesc",
                    "stargazers_count": 50,
                    "description": None,
                }
            ]
        }

        findings = parse_github_api_response(data, "nodesc")

        assert len(findings) == 1
        assert isinstance(findings[0].summary, str)

    @pytest.mark.unit
    def test_all_findings_have_github_source(self) -> None:
        """
        Scenario: All parsed findings carry the correct source tag
        Given a multi-item API response
        When parse_github_api_response is called
        Then every Finding has source="github" and channel="code"
        """
        data: dict[str, Any] = {
            "items": [
                {
                    "full_name": "a/b",
                    "html_url": "https://github.com/a/b",
                    "stargazers_count": 10,
                    "description": "B",
                },
                {
                    "full_name": "c/d",
                    "html_url": "https://github.com/c/d",
                    "stargazers_count": 20,
                    "description": "D",
                },
            ]
        }

        findings = parse_github_api_response(data, "test")

        for f in findings:
            assert f.source == "github"
            assert f.channel == "code"


class TestRankGithubFindings:
    """
    Feature: GitHub finding ranking

    As a synthesis stage
    I want findings ordered by quality signal
    So that the most useful repositories appear first
    """

    @pytest.mark.unit
    def test_higher_stars_ranks_first(self) -> None:
        """
        Scenario: Repository with more stars outranks one with fewer
        Given two findings with different star counts and equal relevance
        When rank_github_findings is called
        Then the finding with more stars comes first
        """
        low = Finding(
            source="github",
            channel="code",
            title="owner/low-stars",
            url="https://github.com/owner/low-stars",
            relevance=0.7,
            summary="Low",
            metadata={"stars": 50, "updated_at": "2024-01-01T00:00:00Z"},
        )
        high = Finding(
            source="github",
            channel="code",
            title="owner/high-stars",
            url="https://github.com/owner/high-stars",
            relevance=0.7,
            summary="High",
            metadata={"stars": 10000, "updated_at": "2024-01-01T00:00:00Z"},
        )

        ranked = rank_github_findings([low, high])

        assert ranked[0].metadata["stars"] == 10000

    @pytest.mark.unit
    def test_preserves_all_findings(self) -> None:
        """
        Scenario: Ranking does not drop any findings
        Given three findings
        When rank_github_findings is called
        Then exactly three findings are returned
        """
        findings = [
            Finding(
                "github",
                "code",
                f"r/{i}",
                f"https://github.com/r/{i}",
                0.5,
                "s",
                metadata={"stars": i * 100},
            )
            for i in range(3)
        ]

        ranked = rank_github_findings(findings)

        assert len(ranked) == 3

    @pytest.mark.unit
    def test_empty_list_returns_empty(self) -> None:
        """
        Scenario: Empty input produces empty output
        Given an empty findings list
        When rank_github_findings is called
        Then an empty list is returned
        """
        assert rank_github_findings([]) == []

    @pytest.mark.unit
    def test_does_not_mutate_input(self) -> None:
        """
        Scenario: Ranking is non-destructive
        Given a list of findings in a known order
        When rank_github_findings is called
        Then the original list order is unchanged
        """
        findings = [
            Finding(
                "github",
                "code",
                "a/a",
                "https://github.com/a/a",
                0.9,
                "A",
                metadata={"stars": 1},
            ),
            Finding(
                "github",
                "code",
                "b/b",
                "https://github.com/b/b",
                0.1,
                "B",
                metadata={"stars": 9000},
            ),
        ]
        original_first = findings[0].title

        rank_github_findings(findings)

        assert findings[0].title == original_first
