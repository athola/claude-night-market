"""
Feature: Discourse channel (HN, Lobsters, Reddit, tech blogs)

As a research pipeline
I want to build search queries and parse responses from community platforms
So that agents can retrieve discussion signals without coupling to HTTP
"""

from __future__ import annotations

from typing import Any

import pytest
from tome.channels.discourse import (
    build_blog_search_queries,
    build_hn_search_url,
    build_lobsters_search_url,
    build_lobsters_websearch_query,
    build_reddit_search_url,
    parse_blog_result,
    parse_hn_response,
    parse_lobsters_result,
    parse_reddit_response,
    suggest_subreddits,
)
from tome.models import Finding


class TestBuildHnSearchUrl:
    """
    Feature: Hacker News Algolia search URL construction

    As a research agent
    I want a correctly formed Algolia HN API URL
    So that WebFetch returns structured HN story results
    """

    @pytest.mark.unit
    def test_url_points_to_algolia_hn(self) -> None:
        """
        Scenario: URL targets the Algolia HN endpoint
        Given any topic
        When build_hn_search_url is called
        Then the URL starts with https://hn.algolia.com/api/v1/search
        """
        url = build_hn_search_url("async python")

        assert url.startswith("https://hn.algolia.com/api/v1/search")

    @pytest.mark.unit
    def test_url_contains_topic(self) -> None:
        """
        Scenario: Topic is embedded in the query string
        Given the topic "bloom filter"
        When build_hn_search_url is called
        Then the URL contains "bloom" and "filter"
        """
        url = build_hn_search_url("bloom filter")

        assert "bloom" in url
        assert "filter" in url

    @pytest.mark.unit
    def test_url_filters_to_stories(self) -> None:
        """
        Scenario: Only story-type posts are requested
        Given any topic
        When build_hn_search_url is called
        Then the URL contains tags=story
        """
        url = build_hn_search_url("consensus algorithms")

        assert "tags=story" in url

    @pytest.mark.unit
    def test_url_includes_hits_per_page(self) -> None:
        """
        Scenario: Custom page size is reflected in URL
        Given hits_per_page=5
        When build_hn_search_url is called
        Then the URL contains hitsPerPage=5
        """
        url = build_hn_search_url("raft", hits_per_page=5)

        assert "hitsPerPage=5" in url


class TestParseHnResponse:
    """
    Feature: HN Algolia response parsing

    As a research pipeline
    I want structured HN hits converted to Findings with score filtering
    So that low-quality discussions are excluded
    """

    @pytest.mark.unit
    def test_parses_hit_into_finding(self) -> None:
        """
        Scenario: Single high-score HN hit is converted to a Finding
        Given a payload with one hit above min_score
        When parse_hn_response is called
        Then one Finding is returned with correct fields
        """
        data: dict[str, Any] = {
            "hits": [
                {
                    "title": "Ask HN: Best async patterns?",
                    "url": "https://example.com/async",
                    "points": 250,
                    "num_comments": 80,
                    "objectID": "99001",
                }
            ]
        }

        findings = parse_hn_response(data, min_score=5)

        assert len(findings) == 1
        f = findings[0]
        assert f.source == "hn"
        assert f.channel == "discourse"
        assert f.title == "Ask HN: Best async patterns?"

    @pytest.mark.unit
    def test_filters_below_min_score(self) -> None:
        """
        Scenario: Low-score hit is excluded
        Given a payload with one hit scoring below min_score
        When parse_hn_response is called with min_score=50
        Then the finding is excluded and an empty list is returned
        """
        data: dict[str, Any] = {
            "hits": [
                {
                    "title": "Low quality post",
                    "url": "https://example.com/low",
                    "points": 3,
                    "num_comments": 0,
                    "objectID": "99002",
                }
            ]
        }

        findings = parse_hn_response(data, min_score=50)

        assert findings == []

    @pytest.mark.unit
    def test_keeps_hit_exactly_at_min_score(self) -> None:
        """
        Scenario: Hit at exactly min_score boundary is included
        Given a hit with points==min_score
        When parse_hn_response is called
        Then the finding is included
        """
        data: dict[str, Any] = {
            "hits": [
                {
                    "title": "Boundary post",
                    "url": "https://example.com/boundary",
                    "points": 10,
                    "num_comments": 2,
                    "objectID": "99003",
                }
            ]
        }

        findings = parse_hn_response(data, min_score=10)

        assert len(findings) == 1

    @pytest.mark.unit
    def test_empty_hits_returns_empty(self) -> None:
        """
        Scenario: Response with no hits
        Given {"hits": []}
        When parse_hn_response is called
        Then an empty list is returned
        """
        assert parse_hn_response({"hits": []}) == []

    @pytest.mark.unit
    def test_missing_hits_key_returns_empty(self) -> None:
        """
        Scenario: Malformed response missing hits key
        Given {}
        When parse_hn_response is called
        Then an empty list is returned without raising
        """
        assert parse_hn_response({}) == []

    @pytest.mark.unit
    def test_hit_without_url_uses_hn_item_fallback(self) -> None:
        """
        Scenario: HN Ask post has no url field
        Given a hit with no url but a valid objectID
        When parse_hn_response is called
        Then a Finding is returned with a fallback HN item URL
        """
        data: dict[str, Any] = {
            "hits": [
                {
                    "title": "Ask HN: No URL post",
                    "points": 100,
                    "num_comments": 30,
                    "objectID": "12345",
                }
            ]
        }

        findings = parse_hn_response(data, min_score=5)

        assert len(findings) == 1
        assert "12345" in findings[0].url


class TestBuildLobstersQueries:
    """
    Feature: Lobste.rs search URL and WebSearch fallback

    As a research agent
    I want both a direct lobste.rs URL and a fallback site: query
    So that either WebFetch or WebSearch can retrieve lobsters discussions
    """

    @pytest.mark.unit
    def test_search_url_targets_lobsters(self) -> None:
        """
        Scenario: Direct search URL points to lobste.rs
        Given any topic
        When build_lobsters_search_url is called
        Then the URL starts with https://lobste.rs/search
        """
        url = build_lobsters_search_url("type inference")

        assert url.startswith("https://lobste.rs/search")

    @pytest.mark.unit
    def test_search_url_contains_topic(self) -> None:
        """
        Scenario: Topic appears in search URL
        Given the topic "garbage collection"
        When build_lobsters_search_url is called
        Then the URL contains "garbage" or the encoded equivalent
        """
        url = build_lobsters_search_url("garbage collection")

        assert "garbage" in url or "garbage+collection" in url.lower()

    @pytest.mark.unit
    def test_websearch_query_uses_site_prefix(self) -> None:
        """
        Scenario: Fallback query targets lobste.rs via site: operator
        Given the topic "compiler optimization"
        When build_lobsters_websearch_query is called
        Then the result starts with "site:lobste.rs"
        """
        query = build_lobsters_websearch_query("compiler optimization")

        assert query.startswith("site:lobste.rs")

    @pytest.mark.unit
    def test_websearch_query_contains_topic(self) -> None:
        """
        Scenario: Fallback query includes the topic
        Given the topic "memory allocator"
        When build_lobsters_websearch_query is called
        Then the result contains "memory allocator"
        """
        query = build_lobsters_websearch_query("memory allocator")

        assert "memory allocator" in query


class TestParseLobstersResult:
    """
    Feature: Lobste.rs WebSearch result parsing

    As a research pipeline
    I want a lobste.rs WebSearch hit converted to a Finding
    So that community discussion signals are uniformly typed
    """

    @pytest.mark.unit
    def test_parses_standard_result(self) -> None:
        """
        Scenario: Standard lobsters result with all fields
        Given a dict with title, url, snippet
        When parse_lobsters_result is called
        Then the Finding has source="lobsters" and channel="discourse"
        """
        result = {
            "title": "Understanding Borrow Checker | lobste.rs",
            "url": "https://lobste.rs/s/abc123/understanding_borrow_checker",
            "snippet": "A deep dive into Rust's borrow checker",
        }

        finding = parse_lobsters_result(result)

        assert finding.source == "lobsters"
        assert finding.channel == "discourse"
        assert "lobste.rs" in finding.url

    @pytest.mark.unit
    def test_handles_empty_dict(self) -> None:
        """
        Scenario: Empty result dict
        Given {}
        When parse_lobsters_result is called
        Then a Finding is returned without raising
        """
        finding = parse_lobsters_result({})

        assert isinstance(finding, Finding)


class TestBuildRedditSearchUrl:
    """
    Feature: Reddit JSON search URL construction

    As a research agent
    I want a Reddit search URL in JSON format
    So that WebFetch can retrieve structured Reddit data
    """

    @pytest.mark.unit
    def test_url_points_to_old_reddit_json(self) -> None:
        """
        Scenario: URL uses old.reddit.com JSON endpoint
        Given any topic and subreddit
        When build_reddit_search_url is called
        Then the URL starts with https://old.reddit.com
        """
        url = build_reddit_search_url("lru cache")

        assert url.startswith("https://old.reddit.com")

    @pytest.mark.unit
    def test_url_ends_with_json_suffix(self) -> None:
        """
        Scenario: URL ends with .json for API access
        Given any topic
        When build_reddit_search_url is called
        Then the URL contains .json
        """
        url = build_reddit_search_url("skip list")

        assert ".json" in url

    @pytest.mark.unit
    def test_default_subreddit_is_programming(self) -> None:
        """
        Scenario: Default subreddit is /r/programming
        Given no explicit subreddit argument
        When build_reddit_search_url is called
        Then the URL contains /r/programming
        """
        url = build_reddit_search_url("consistent hashing")

        assert "/r/programming" in url

    @pytest.mark.unit
    def test_custom_subreddit_is_used(self) -> None:
        """
        Scenario: Custom subreddit overrides default
        Given subreddit="MachineLearning"
        When build_reddit_search_url is called
        Then the URL contains /r/MachineLearning
        """
        url = build_reddit_search_url(
            "transformer attention", subreddit="MachineLearning"
        )

        assert "/r/MachineLearning" in url


class TestSuggestSubreddits:
    """
    Feature: Subreddit suggestion by domain

    As a research agent
    I want relevant subreddits for a given topic domain
    So that Reddit searches target high-signal communities
    """

    @pytest.mark.unit
    def test_algorithm_domain_includes_programming(self) -> None:
        """
        Scenario: Algorithm topics suggest programming subreddit
        Given domain="algorithm"
        When suggest_subreddits is called
        Then "programming" is in the suggestions
        """
        subs = suggest_subreddits("binary search tree", "algorithm")

        assert "programming" in subs

    @pytest.mark.unit
    def test_security_domain_includes_netsec(self) -> None:
        """
        Scenario: Security domain suggests netsec
        Given domain="security"
        When suggest_subreddits is called
        Then "netsec" is in the suggestions
        """
        subs = suggest_subreddits("buffer overflow", "security")

        assert "netsec" in subs

    @pytest.mark.unit
    def test_devops_domain_includes_devops(self) -> None:
        """
        Scenario: DevOps domain suggests devops subreddit
        Given domain="devops"
        When suggest_subreddits is called
        Then "devops" is in the suggestions
        """
        subs = suggest_subreddits("kubernetes networking", "devops")

        assert "devops" in subs

    @pytest.mark.unit
    def test_unknown_domain_falls_back_to_general(self) -> None:
        """
        Scenario: Unknown domain falls back to general subreddits
        Given domain="unknown-domain"
        When suggest_subreddits is called
        Then "programming" is in the suggestions
        """
        subs = suggest_subreddits("some topic", "unknown-domain")

        assert "programming" in subs

    @pytest.mark.unit
    def test_returns_list_of_strings(self) -> None:
        """
        Scenario: Return type is always a list of strings
        Given any valid domain
        When suggest_subreddits is called
        Then result is a non-empty list of strings
        """
        subs = suggest_subreddits("gradient descent", "scientific")

        assert isinstance(subs, list)
        assert len(subs) > 0
        assert all(isinstance(s, str) for s in subs)


class TestParseRedditResponse:
    """
    Feature: Reddit JSON response parsing

    As a research pipeline
    I want Reddit search results converted to Findings with score filtering
    So that low-quality posts are excluded
    """

    @pytest.mark.unit
    def test_parses_post_into_finding(self) -> None:
        """
        Scenario: Single high-score Reddit post is converted to a Finding
        Given a valid Reddit JSON response with one post
        When parse_reddit_response is called
        Then one Finding is returned with correct fields
        """
        data: dict[str, Any] = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Best resources for learning consistent hashing?",
                            "url": "https://example.com/hashing",
                            "score": 500,
                            "selftext": "Looking for books and papers",
                            "permalink": "/r/programming/comments/abc/best_resources/",
                        }
                    }
                ]
            }
        }

        findings = parse_reddit_response(data, min_score=10)

        assert len(findings) == 1
        f = findings[0]
        assert f.source == "reddit"
        assert f.channel == "discourse"

    @pytest.mark.unit
    def test_filters_below_min_score(self) -> None:
        """
        Scenario: Post below min_score is excluded
        Given a post with score=2 and min_score=10
        When parse_reddit_response is called
        Then an empty list is returned
        """
        data: dict[str, Any] = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Bad post",
                            "url": "https://example.com",
                            "score": 2,
                            "selftext": "",
                            "permalink": "/r/programming/comments/xyz/bad/",
                        }
                    }
                ]
            }
        }

        findings = parse_reddit_response(data, min_score=10)

        assert findings == []

    @pytest.mark.unit
    def test_empty_children_returns_empty(self) -> None:
        """
        Scenario: Response with no children
        Given {"data": {"children": []}}
        When parse_reddit_response is called
        Then an empty list is returned
        """
        assert parse_reddit_response({"data": {"children": []}}) == []

    @pytest.mark.unit
    def test_malformed_response_returns_empty(self) -> None:
        """
        Scenario: Completely malformed response
        Given {}
        When parse_reddit_response is called
        Then an empty list is returned without raising
        """
        assert parse_reddit_response({}) == []

    @pytest.mark.unit
    def test_post_without_url_uses_permalink(self) -> None:
        """
        Scenario: Self-post with no external URL uses permalink
        Given a post with a permalink but no url
        When parse_reddit_response is called
        Then a Finding is returned with a reddit.com URL
        """
        data: dict[str, Any] = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Self post no url",
                            "score": 50,
                            "selftext": "Discussion here",
                            "permalink": "/r/programming/comments/abc/self_post/",
                        }
                    }
                ]
            }
        }

        findings = parse_reddit_response(data, min_score=10)

        assert len(findings) == 1
        assert "reddit.com" in findings[0].url


class TestBuildBlogSearchQueries:
    """
    Feature: Tech blog WebSearch query generation

    As a research agent
    I want queries that target high-quality tech blogs
    So that authoritative articles are retrieved alongside community discussion
    """

    @pytest.mark.unit
    def test_returns_list_of_strings(self) -> None:
        """
        Scenario: Query builder produces string list
        Given a topic
        When build_blog_search_queries is called
        Then result is a list of strings
        """
        result = build_blog_search_queries("tail call optimization")

        assert isinstance(result, list)
        assert all(isinstance(q, str) for q in result)

    @pytest.mark.unit
    def test_each_query_targets_known_domain(self) -> None:
        """
        Scenario: Queries use site: operator for known blog domains
        Given a topic
        When build_blog_search_queries is called
        Then every returned query contains "site:" targeting a known domain
        """
        known_domains = {
            "martinfowler.com",
            "blog.pragmaticengineer.com",
            "danluu.com",
            "jvns.ca",
            "rachelbythebay.com",
            "eli.thegreenplace.net",
            "brandur.org",
        }

        result = build_blog_search_queries("state machine")

        assert all(any(domain in q for domain in known_domains) for q in result)

    @pytest.mark.unit
    def test_each_query_contains_topic(self) -> None:
        """
        Scenario: Every query includes the topic
        Given the topic "event sourcing"
        When build_blog_search_queries is called
        Then every returned query contains "event sourcing"
        """
        result = build_blog_search_queries("event sourcing")

        for q in result:
            assert "event sourcing" in q

    @pytest.mark.unit
    def test_respects_max_queries_limit(self) -> None:
        """
        Scenario: max_queries caps the result length
        Given max_queries=2
        When build_blog_search_queries is called
        Then at most 2 queries are returned
        """
        result = build_blog_search_queries("CRDT", max_queries=2)

        assert len(result) <= 2

    @pytest.mark.unit
    def test_non_empty_for_any_topic(self) -> None:
        """
        Scenario: At least one query is always returned
        Given any topic
        When build_blog_search_queries is called
        Then the result is non-empty
        """
        result = build_blog_search_queries("zero-copy networking")

        assert len(result) >= 1


class TestParseBlogResult:
    """
    Feature: Tech blog WebSearch result parsing

    As a research pipeline
    I want blog search results converted to Findings
    So that authoritative articles are uniformly typed
    """

    @pytest.mark.unit
    def test_parses_standard_result(self) -> None:
        """
        Scenario: Blog result with all fields present
        Given a dict with title, url, snippet
        When parse_blog_result is called
        Then the Finding has channel="discourse" and correct fields
        """
        result = {
            "title": "How I Think About Distributed Systems",
            "url": "https://martinfowler.com/articles/distributed-systems.html",
            "snippet": "Martin Fowler on CAP theorem and consistency models",
        }

        finding = parse_blog_result(result)

        assert finding.channel == "discourse"
        assert finding.title == "How I Think About Distributed Systems"
        assert "martinfowler.com" in finding.url

    @pytest.mark.unit
    def test_source_reflects_blog_domain(self) -> None:
        """
        Scenario: Source is extracted from URL domain
        Given a danluu.com URL
        When parse_blog_result is called
        Then finding.source contains recognisable blog identifier
        """
        result = {
            "title": "Distributed systems reading list",
            "url": "https://danluu.com/dsys-reading-list/",
            "snippet": "A reading list for distributed systems",
        }

        finding = parse_blog_result(result)

        assert finding.source in ("blog", "danluu.com", "danluu")

    @pytest.mark.unit
    def test_handles_empty_dict(self) -> None:
        """
        Scenario: Empty result dict
        Given {}
        When parse_blog_result is called
        Then a Finding is returned without raising
        """
        finding = parse_blog_result({})

        assert isinstance(finding, Finding)

    @pytest.mark.unit
    def test_relevance_in_valid_range(self) -> None:
        """
        Scenario: Relevance is always a valid float
        Given a blog result
        When parse_blog_result is called
        Then relevance is in [0.0, 1.0]
        """
        result = {
            "title": "Understanding LSM Trees",
            "url": "https://jvns.ca/blog/lsm-trees/",
            "snippet": "Julia Evans explains log-structured merge trees",
        }

        finding = parse_blog_result(result)

        assert 0.0 <= finding.relevance <= 1.0
