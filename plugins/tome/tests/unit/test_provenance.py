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
    def test_failed_query_log(self) -> None:
        """
        Scenario: Record a failed query
        Given a query that returned no results
        When QueryLog is constructed with succeeded=False
        Then result_count is 0 and succeeded is False
        """
        log = QueryLog(
            channel="discourse",
            query="obscure topic nobody discusses",
            source="hn",
            result_count=0,
            succeeded=False,
        )

        assert log.result_count == 0
        assert log.succeeded is False

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
