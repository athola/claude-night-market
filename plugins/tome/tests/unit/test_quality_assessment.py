"""
Feature: Research quality self-assessment

As a report consumer
I want a quality score for the research session
So that I can gauge how thorough and diverse the results are
"""

from __future__ import annotations

import pytest
from tome.synthesis.quality import compute_quality_score

from tests.factories import make_finding


class TestComputeQualityScore:
    """
    Feature: Research quality scoring

    As the synthesis pipeline
    I want a composite score reflecting source diversity, coverage,
    and relevance distribution
    So that reports include an honest quality indicator
    """

    @pytest.mark.unit
    def test_diverse_high_quality_scores_high(self) -> None:
        """
        Scenario: Findings from multiple channels with high relevance
        Given findings across 3 channels with relevance > 0.7
        When compute_quality_score is called
        Then the score is above 0.7
        """
        findings = [
            make_finding(0.8, channel="code"),
            make_finding(0.9, source="arxiv", channel="academic"),
            make_finding(0.7, source="hn", channel="discourse"),
        ]

        score = compute_quality_score(findings, ["code", "academic", "discourse"])

        assert score > 0.7

    @pytest.mark.unit
    def test_single_channel_scores_lower(self) -> None:
        """
        Scenario: All findings from one channel
        Given 5 code findings and no other channels
        When compute_quality_score is called
        Then score is lower than a diverse set
        """
        single = [make_finding(0.8, channel="code") for _ in range(5)]
        diverse = [
            make_finding(0.8, channel="code"),
            make_finding(0.7, source="hn", channel="discourse"),
            make_finding(0.9, source="arxiv", channel="academic"),
        ]

        score_single = compute_quality_score(single, ["code", "discourse", "academic"])
        score_diverse = compute_quality_score(
            diverse, ["code", "discourse", "academic"]
        )

        assert score_diverse > score_single

    @pytest.mark.unit
    def test_empty_findings_scores_zero(self) -> None:
        """
        Scenario: No findings at all
        Given an empty findings list
        When compute_quality_score is called
        Then the score is 0.0
        """
        score = compute_quality_score([], ["code"])

        assert score == 0.0

    @pytest.mark.unit
    def test_score_capped_at_one(self) -> None:
        """
        Scenario: Maximum possible quality
        Given many diverse high-relevance findings
        When compute_quality_score is called
        Then the score does not exceed 1.0
        """
        findings = [
            make_finding(0.95, channel="code"),
            make_finding(0.95, source="arxiv", channel="academic"),
            make_finding(0.95, source="hn", channel="discourse"),
            make_finding(0.95, source="triz", channel="triz"),
        ]

        score = compute_quality_score(
            findings, ["code", "academic", "discourse", "triz"]
        )

        assert score <= 1.0

    @pytest.mark.unit
    def test_score_between_zero_and_one(self) -> None:
        """
        Scenario: Score bounds
        Given any non-empty findings
        When compute_quality_score is called
        Then the score is between 0.0 and 1.0
        """
        findings = [make_finding(0.5, channel="code")]

        score = compute_quality_score(findings, ["code", "discourse"])

        assert 0.0 <= score <= 1.0
