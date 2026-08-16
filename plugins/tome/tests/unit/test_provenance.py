"""
Feature: Research provenance tracking

As a research debugger
I want to know which queries were tried and what they returned
So that I can understand why results look the way they do
"""

from __future__ import annotations

import pytest

from tome.models import QueryLog


class TestQueryLog:
    """
    Feature: Query logging dataclass

    As the session manager
    I want to record every query attempted during research
    So that provenance is preserved for debugging and cross-session use
    """

    @pytest.mark.unit
    def test_create_query_log(self) -> None:
        """
        Scenario: Create a query log entry
        Given a channel, query string, and result count
        When QueryLog is constructed
        Then all fields are accessible
        """
        log = QueryLog(
            channel="academic",
            query="cache eviction survey",
            source="arxiv",
            result_count=5,
            succeeded=True,
        )

        assert log.channel == "academic"
        assert log.query == "cache eviction survey"
        assert log.source == "arxiv"
        assert log.result_count == 5
        assert log.succeeded is True

    @pytest.mark.unit
    def test_serialization_roundtrip(self) -> None:
        """
        Scenario: Serialize and deserialize
        Given a QueryLog
        When to_dict then from_dict is called
        Then the result equals the original
        """
        original = QueryLog(
            channel="code",
            query="site:github.com react patterns",
            source="websearch",
            result_count=3,
            succeeded=True,
        )

        restored = QueryLog.from_dict(original.to_dict())

        assert restored.channel == original.channel
        assert restored.query == original.query
        assert restored.source == original.source
        assert restored.result_count == original.result_count
        assert restored.succeeded == original.succeeded

    @pytest.mark.unit
    def test_empty_result_is_a_success_not_a_failure(self) -> None:
        """
        Scenario: Record a search that worked and found nothing
        Given a query on a topic nobody discusses
        When QueryLog is constructed with no error
        Then result_count is 0 and succeeded is True

        This test previously constructed the same query with
        succeeded=False, on the reading that "returned no results"
        meant "failed". It does not. A source that answers and has
        nothing to offer is the one case where absence says something
        about the topic rather than about the search, and recording it
        as a failure is where that distinction was first lost.
        """
        log = QueryLog(
            channel="discourse",
            query="obscure topic nobody discusses",
            source="hn",
            result_count=0,
        )

        assert log.result_count == 0
        assert log.succeeded is True
        assert log.error is None

    @pytest.mark.unit
    def test_failed_query_log(self) -> None:
        """
        Scenario: Record a query that actually failed
        Given a source that refused the request
        When QueryLog is constructed with an error kind
        Then succeeded is False and the cause is retained
        """
        log = QueryLog(
            channel="discourse",
            query="obscure topic nobody discusses",
            source="hn",
            result_count=0,
            error="rate_limit",
        )

        assert log.result_count == 0
        assert log.succeeded is False
        assert log.error == "rate_limit"

    @pytest.mark.unit
    def test_default_values(self) -> None:
        """
        Scenario: Minimal construction
        Given only required fields
        When QueryLog is constructed
        Then defaults are sensible
        """
        log = QueryLog(
            channel="academic",
            query="test query",
            source="arxiv",
        )

        assert log.result_count == 0
        assert log.succeeded is True
