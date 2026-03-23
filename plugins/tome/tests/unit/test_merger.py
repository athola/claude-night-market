"""
Feature: Finding deduplication and channel merging

As a synthesis pipeline
I want to merge findings from multiple channels into a clean, deduplicated list
So that the ranker and report formatter receive unique, high-quality inputs
"""

from __future__ import annotations

import pytest
from tome.synthesis.merger import deduplicate, merge_findings

from tests.factories import make_finding


class TestDeduplicate:
    """
    Feature: Deduplication by URL

    As a synthesis pipeline
    I want duplicate findings (same URL) collapsed to the best one
    So that the report does not list the same source twice
    """

    @pytest.mark.unit
    def test_unique_findings_pass_through_unchanged(self) -> None:
        """
        Scenario: No duplicates in input
        Given a list of findings with distinct URLs
        When deduplicate is called
        Then all findings are returned, order preserved
        """
        findings = [
            make_finding(0.8, url="https://example.com/a"),
            make_finding(0.6, url="https://example.com/b"),
            make_finding(0.7, url="https://example.com/c"),
        ]

        result = deduplicate(findings)

        assert len(result) == 3
        assert [f.url for f in result] == [
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/c",
        ]

    @pytest.mark.unit
    def test_duplicate_url_keeps_higher_relevance(self) -> None:
        """
        Scenario: Two findings share the same URL
        Given one finding with relevance 0.5 and another at 0.9 for the same URL
        When deduplicate is called
        Then only the 0.9-relevance finding is kept
        """
        low = make_finding(0.5, url="https://example.com/shared")
        high = make_finding(0.9, url="https://example.com/shared")

        result = deduplicate([low, high])

        assert len(result) == 1
        assert result[0].relevance == 0.9

    @pytest.mark.unit
    def test_first_occurrence_wins_when_relevance_tied(self) -> None:
        """
        Scenario: Two findings share URL with equal relevance
        Given two findings at the same URL with relevance 0.7
        When deduplicate is called
        Then exactly one finding is returned
        """
        a = make_finding(0.7, url="https://example.com/tied")
        b = make_finding(0.7, url="https://example.com/tied")

        result = deduplicate([a, b])

        assert len(result) == 1

    @pytest.mark.unit
    def test_empty_list_returns_empty(self) -> None:
        """
        Scenario: Empty input
        Given an empty list
        When deduplicate is called
        Then an empty list is returned
        """
        assert deduplicate([]) == []

    @pytest.mark.unit
    def test_single_finding_returns_itself(self) -> None:
        """
        Scenario: Single finding input
        Given a list with exactly one finding
        When deduplicate is called
        Then that finding is returned unchanged
        """
        f = make_finding(0.75, url="https://example.com/only")
        result = deduplicate([f])
        assert result == [f]

    @pytest.mark.unit
    def test_multiple_duplicates_across_urls(self) -> None:
        """
        Scenario: Several URLs each appearing multiple times
        Given findings where URL A appears twice and URL B appears three times
        When deduplicate is called
        Then two findings are returned, each the highest-relevance version
        """
        findings = [
            make_finding(0.4, url="https://example.com/a"),
            make_finding(0.3, url="https://example.com/b"),
            make_finding(0.8, url="https://example.com/a"),
            make_finding(0.6, url="https://example.com/b"),
            make_finding(0.5, url="https://example.com/b"),
        ]

        result = deduplicate(findings)

        assert len(result) == 2
        by_url = {f.url: f for f in result}
        assert by_url["https://example.com/a"].relevance == 0.8
        assert by_url["https://example.com/b"].relevance == 0.6


class TestMergeFindings:
    """
    Feature: Channel result merging

    As a synthesis pipeline
    I want to combine per-channel finding lists into one list
    So that ranking and grouping can operate on the full result set
    """

    @pytest.mark.unit
    def test_merges_two_disjoint_channel_results(self) -> None:
        """
        Scenario: Two channels with unique URLs
        Given code-channel findings and discourse-channel findings with no overlap
        When merge_findings is called
        Then all findings appear in the result
        """
        code = [
            make_finding(0.8, url="https://github.com/a", channel="code"),
            make_finding(0.7, url="https://github.com/b", channel="code"),
        ]
        discourse = [
            make_finding(0.6, url="https://hn.com/1", source="hn", channel="discourse"),
        ]

        result = merge_findings([code, discourse])

        assert len(result) == 3

    @pytest.mark.unit
    def test_deduplicates_across_channels(self) -> None:
        """
        Scenario: Same URL appears in two channels
        Given a URL that appears in both code and discourse results
        When merge_findings is called
        Then only one finding for that URL is in the result
        """
        shared_url = "https://example.com/shared"
        code = [make_finding(0.5, url=shared_url, channel="code")]
        discourse = [make_finding(0.9, url=shared_url, channel="discourse")]

        result = merge_findings([code, discourse])

        assert len(result) == 1
        assert result[0].relevance == 0.9

    @pytest.mark.unit
    def test_empty_channel_list_returns_empty(self) -> None:
        """
        Scenario: No channels provided
        Given an empty list of channel results
        When merge_findings is called
        Then an empty list is returned
        """
        assert merge_findings([]) == []

    @pytest.mark.unit
    def test_single_empty_channel_returns_empty(self) -> None:
        """
        Scenario: One channel with no findings
        Given a list containing one empty channel result
        When merge_findings is called
        Then an empty list is returned
        """
        assert merge_findings([[]]) == []

    @pytest.mark.unit
    def test_merges_three_channels(self) -> None:
        """
        Scenario: Three channels each with one finding
        Given code, discourse, and academic channels each contributing one finding
        When merge_findings is called
        Then all three findings are present
        """
        code = [make_finding(0.8, url="https://github.com/x", channel="code")]
        discourse = [make_finding(0.7, url="https://hn.com/x", channel="discourse")]
        academic = [
            make_finding(
                0.9, url="https://arxiv.org/x", source="arxiv", channel="academic"
            )
        ]

        result = merge_findings([code, discourse, academic])

        assert len(result) == 3
