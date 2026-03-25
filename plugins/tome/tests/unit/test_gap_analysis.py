"""
Feature: Research gap analysis

As a report consumer
I want to know what the research did NOT find
So that I understand the boundaries of the investigation
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from tome.synthesis.quality import identify_gaps

from tests.factories import make_finding

_CURRENT_YEAR: int = datetime.now(tz=timezone.utc).year  # noqa: UP017


class TestIdentifyGaps:
    """
    Feature: Gap detection in research results

    As the synthesis pipeline
    I want to flag channels with no results and missing time coverage
    So that the report honestly represents research completeness
    """

    @pytest.mark.unit
    def test_empty_channel_flagged(self) -> None:
        """
        Scenario: A planned channel returned nothing
        Given planned channels ["code", "discourse", "academic"]
        And only code and academic have findings
        When identify_gaps is called
        Then "discourse" appears in empty_channels
        """
        findings = [
            make_finding(0.7, channel="code"),
            make_finding(0.8, source="arxiv", channel="academic"),
        ]
        planned_channels = ["code", "discourse", "academic"]

        gaps = identify_gaps(findings, planned_channels)

        assert "discourse" in gaps["empty_channels"]

    @pytest.mark.unit
    def test_no_gaps_when_all_channels_produce(self) -> None:
        """
        Scenario: All channels have results
        Given findings from every planned channel
        When identify_gaps is called
        Then empty_channels is empty
        """
        findings = [
            make_finding(0.7, channel="code"),
            make_finding(0.6, source="hn", channel="discourse"),
            make_finding(0.8, source="arxiv", channel="academic"),
        ]

        gaps = identify_gaps(findings, ["code", "discourse", "academic"])

        assert gaps["empty_channels"] == []

    @pytest.mark.unit
    def test_low_diversity_flagged(self) -> None:
        """
        Scenario: Results heavily skewed to one channel
        Given 10 code findings and 1 academic finding
        When identify_gaps is called
        Then source_diversity_warning is True
        """
        findings = [make_finding(0.7, channel="code") for _ in range(10)]
        findings.append(make_finding(0.8, source="arxiv", channel="academic"))

        gaps = identify_gaps(findings, ["code", "academic"])

        assert gaps["source_diversity_warning"] is True

    @pytest.mark.unit
    def test_empty_findings_all_channels_flagged(self) -> None:
        """
        Scenario: No findings at all
        Given an empty findings list
        When identify_gaps is called
        Then all planned channels are empty
        """
        gaps = identify_gaps([], ["code", "discourse"])

        assert set(gaps["empty_channels"]) == {"code", "discourse"}

    @pytest.mark.unit
    def test_recency_gap_flagged(self) -> None:
        """
        Scenario: All findings are old
        Given findings where all years are > 5 years ago
        When identify_gaps is called
        Then recency_gap is True
        """
        findings = [
            make_finding(0.7, channel="code", metadata={"year": _CURRENT_YEAR - 5}),
            make_finding(0.6, channel="code", metadata={"year": _CURRENT_YEAR - 6}),
        ]

        gaps = identify_gaps(findings, ["code"])

        assert gaps["recency_gap"] is True

    @pytest.mark.unit
    def test_recency_gap_not_flagged_for_recent_findings(self) -> None:
        """
        Scenario: Findings are recent
        Given findings where all years are within recency window
        When identify_gaps is called
        Then recency_gap is False
        """
        findings = [
            make_finding(0.7, channel="code", metadata={"year": _CURRENT_YEAR - 1}),
            make_finding(0.6, channel="code", metadata={"year": _CURRENT_YEAR - 2}),
        ]

        gaps = identify_gaps(findings, ["code"])

        assert gaps["recency_gap"] is False
