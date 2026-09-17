"""
Feature: Web search channel

As a research pipeline
I want to build general-web search queries and parse results into
Findings from either the You.com MCP server or the WebSearch tool
So that sessions can retrieve vendor docs, comparisons, and news
without coupling to HTTP and without requiring any MCP setup
"""

from __future__ import annotations

import pytest

from tome.channels.web import (
    describe_you_mcp_setup,
    expand_web_queries,
    parse_websearch_result,
    parse_you_mcp_result,
    rank_web_findings,
)
from tome.models import Finding


class TestExpandWebQueries:
    """
    Feature: Web query expansion

    As the web channel
    I want doc, comparison, and recency variants of the topic
    So that a single framing does not decide what the web returns
    """

    @pytest.mark.unit
    def test_returns_list_of_strings(self) -> None:
        """
        Scenario: Query builder produces string list
        Given a topic string
        When expand_web_queries is called
        Then the result is a list of strings
        """
        result = expand_web_queries("vector databases")

        assert isinstance(result, list)
        assert all(isinstance(q, str) for q in result)

    @pytest.mark.unit
    def test_original_topic_included(self) -> None:
        """
        Scenario: Original topic preserved
        Given the topic "postgres row-level security"
        When expand_web_queries is called
        Then the bare topic is one of the queries
        """
        topic = "postgres row-level security"
        assert topic in expand_web_queries(topic)

    @pytest.mark.unit
    def test_queries_are_unique(self) -> None:
        """
        Scenario: No duplicate queries
        Given a topic
        When expand_web_queries is called
        Then all returned queries are distinct
        """
        queries = expand_web_queries("json schema validation")
        assert len(queries) == len(set(queries))

    @pytest.mark.unit
    def test_respects_max_variants(self) -> None:
        """
        Scenario: Variant cap honored
        Given max_variants=2
        When expand_web_queries is called
        Then at most 2 queries are returned
        """
        assert len(expand_web_queries("kafka", max_variants=2)) <= 2

    @pytest.mark.unit
    def test_each_query_contains_topic(self) -> None:
        """
        Scenario: Every query includes the topic
        Given the topic "bloom filter"
        When expand_web_queries is called
        Then every returned query contains "bloom filter"
        """
        for query in expand_web_queries("bloom filter"):
            assert "bloom filter" in query


class TestDescribeYouMcpSetup:
    """
    Feature: Optional MCP setup guidance

    As an operator
    I want the setup instructions to name the endpoint I should add
    So that opting in is a copy-paste step, not a research project
    """

    @pytest.mark.unit
    def test_free_profile_mentions_endpoint_and_no_key(self) -> None:
        """
        Scenario: Keyless guidance
        Given the free profile
        When describe_you_mcp_setup is called
        Then the you.com endpoint appears and no key is required
        """
        text = describe_you_mcp_setup()
        assert "api.you.com/mcp" in text
        assert "no API key" in text

    @pytest.mark.unit
    def test_authenticated_profile_mentions_key(self) -> None:
        """
        Scenario: Authenticated guidance
        Given the authenticated profile
        When describe_you_mcp_setup is called
        Then YDC_API_KEY is named
        """
        assert "YDC_API_KEY" in describe_you_mcp_setup(authenticated=True)


class TestParseYouMcpResult:
    """
    Feature: You.com MCP result parsing

    As the web channel
    I want MCP tool results parsed into Findings
    So that opting in changes the retrieval path, not the data model
    """

    @pytest.mark.unit
    def test_parses_full_result(self) -> None:
        """
        Scenario: Well-formed result list
        Given two result dicts with title, url, snippet
        When parse_you_mcp_result is called
        Then two Findings come back on the web channel
        """
        result = [
            {
                "title": "PostgreSQL Docs",
                "url": "https://postgresql.org/docs",
                "snippet": "The official documentation",
            },
            {
                "title": "Row Security Policies",
                "url": "https://example.com/rls",
                "snippet": "Policies and roles",
            },
        ]
        findings = parse_you_mcp_result(result, "postgres row security")

        assert len(findings) == 2
        assert all(f.channel == "web" for f in findings)
        assert all(f.source == "you-web" for f in findings)
        assert all(f.metadata["retrieved_via"] == "you-mcp" for f in findings)

    @pytest.mark.unit
    def test_skips_items_without_url(self) -> None:
        """
        Scenario: Result missing its URL
        Given a result dict with no url
        When parse_you_mcp_result is called
        Then that result is skipped, not fabricated
        """
        result = [{"title": "No URL", "snippet": "orphan"}]
        assert parse_you_mcp_result(result, "topic") == []

    @pytest.mark.unit
    def test_non_list_input_returns_empty(self) -> None:
        """
        Scenario: Malformed tool response
        Given a dict instead of a list
        When parse_you_mcp_result is called
        Then the result is empty rather than an error
        """
        assert parse_you_mcp_result({"error": "oops"}, "topic") == []

    @pytest.mark.unit
    def test_snippet_falls_back_to_description(self) -> None:
        """
        Scenario: Description key instead of snippet
        Given a result with description and no snippet
        When parse_you_mcp_result is called
        Then the description is used as the summary
        """
        result = [
            {
                "title": "T",
                "url": "https://example.com",
                "description": "from description",
            }
        ]
        findings = parse_you_mcp_result(result, "topic")
        assert findings[0].summary == "from description"


class TestParseWebsearchResult:
    """
    Feature: WebSearch fallback parsing

    As the web channel
    I want WebSearch results parsed into Findings
    So that the channel works with zero MCP configuration
    """

    @pytest.mark.unit
    def test_parses_full_result(self) -> None:
        """
        Scenario: Well-formed WebSearch result
        Given title, url, snippet
        When parse_websearch_result is called
        Then a web-channel Finding is returned
        """
        finding = parse_websearch_result(
            {
                "title": "Kafka Documentation",
                "url": "https://kafka.apache.org/docs",
                "snippet": "Apache Kafka docs",
            },
            "kafka documentation",
        )

        assert finding.channel == "web"
        assert finding.source == "web"
        assert finding.title == "Kafka Documentation"
        assert finding.url == "https://kafka.apache.org/docs"
        assert finding.metadata["retrieved_via"] == "websearch"

    @pytest.mark.unit
    def test_missing_keys_handled_gracefully(self) -> None:
        """
        Scenario: Sparse result
        Given only a url
        When parse_websearch_result is called
        Then the Finding still parses, with the url as title
        """
        finding = parse_websearch_result({"url": "https://example.com"}, "topic")

        assert finding.title == "https://example.com"
        assert finding.summary == "https://example.com"

    @pytest.mark.unit
    def test_relevance_bounded(self) -> None:
        """
        Scenario: Relevance stays in range
        Given any result
        When parse_websearch_result is called
        Then relevance lies within [0, 1]
        """
        finding = parse_websearch_result(
            {"title": "x", "url": "https://example.com", "snippet": ""},
            "completely unrelated topic words",
        )
        assert 0.0 <= finding.relevance <= 1.0


class TestRankWebFindings:
    """
    Feature: Web finding ranking

    As a research session
    I want web Findings ordered by the shared relevance scorer
    So that the report shows the strongest pages first
    """

    @pytest.mark.unit
    def test_sorts_by_relevance_descending(self) -> None:
        """
        Scenario: Ordering
        Given findings with different relevance
        When rank_web_findings is called
        Then they are sorted descending
        """
        low = Finding(
            source="web",
            channel="web",
            title="low",
            url="https://example.com/low",
            relevance=0.2,
            summary="s",
        )
        high = Finding(
            source="web",
            channel="web",
            title="high",
            url="https://example.com/high",
            relevance=0.9,
            summary="s",
        )
        ranked = rank_web_findings([low, high])

        assert ranked[0] is high
        assert ranked[1] is low

    @pytest.mark.unit
    def test_does_not_mutate_input(self) -> None:
        """
        Scenario: Input preserved
        Given an ordered list
        When rank_web_findings is called
        Then the input order is unchanged
        """
        low = Finding(
            source="web",
            channel="web",
            title="low",
            url="https://example.com/low",
            relevance=0.1,
            summary="s",
        )
        high = Finding(
            source="web",
            channel="web",
            title="high",
            url="https://example.com/high",
            relevance=0.8,
            summary="s",
        )
        original = [low, high]
        rank_web_findings(original)

        assert original == [low, high]

    @pytest.mark.unit
    def test_empty_input_returns_empty(self) -> None:
        """
        Scenario: Nothing to rank
        Given no findings
        When rank_web_findings is called
        Then an empty list is returned
        """
        assert rank_web_findings([]) == []
