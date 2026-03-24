"""
Feature: Cross-channel triangulation scoring

As a synthesis pipeline
I want findings corroborated across multiple channels to rank higher
So that insights confirmed by code, discourse, and literature are prioritized
"""

from __future__ import annotations

import pytest
from tome.synthesis.ranker import (
    compute_triangulation_bonus,
)

from tests.factories import make_finding


class TestComputeTriangulationBonus:
    """
    Feature: Triangulation bonus calculation

    As the ranker
    I want to detect when a topic appears across channels
    So that corroborated findings get a scoring boost
    """

    @pytest.mark.unit
    def test_no_corroboration_no_bonus(self) -> None:
        """
        Scenario: Finding appears in only one channel
        Given a single finding with no similar findings in other channels
        When compute_triangulation_bonus is called
        Then the bonus is 0.0
        """
        finding = make_finding(0.7, channel="code", title="react patterns")
        all_findings = [finding]

        bonus = compute_triangulation_bonus(finding, all_findings)

        assert bonus == 0.0

    @pytest.mark.unit
    def test_two_channel_corroboration(self) -> None:
        """
        Scenario: Same topic in code and discourse
        Given a code finding about "react patterns"
        And a discourse finding with similar title "react patterns"
        When compute_triangulation_bonus is called for either
        Then a positive bonus is returned
        """
        code = make_finding(
            0.7,
            channel="code",
            title="react patterns",
            url="https://github.com/react-patterns",
        )
        discourse = make_finding(
            0.6,
            source="hn",
            channel="discourse",
            title="react patterns",
            url="https://hn.com/react-patterns",
        )

        bonus = compute_triangulation_bonus(code, [code, discourse])

        assert bonus > 0.0

    @pytest.mark.unit
    def test_three_channel_corroboration_higher(self) -> None:
        """
        Scenario: Topic confirmed across code, discourse, and academic
        Given findings about the same topic in 3 channels
        When compute_triangulation_bonus is called
        Then the bonus is higher than 2-channel corroboration
        """
        code = make_finding(
            0.7,
            channel="code",
            title="attention mechanism",
            url="https://github.com/attention",
        )
        discourse = make_finding(
            0.6,
            source="hn",
            channel="discourse",
            title="attention mechanism",
            url="https://hn.com/attention",
        )
        academic = make_finding(
            0.8,
            source="arxiv",
            channel="academic",
            title="attention mechanism",
            url="https://arxiv.org/attention",
        )

        all_findings = [code, discourse, academic]
        bonus_3 = compute_triangulation_bonus(code, all_findings)
        bonus_2 = compute_triangulation_bonus(code, [code, discourse])

        assert bonus_3 > bonus_2

    @pytest.mark.unit
    def test_bonus_capped(self) -> None:
        """
        Scenario: Triangulation bonus does not exceed cap
        Given findings in all 4 channels with matching titles
        When compute_triangulation_bonus is called
        Then the bonus does not exceed 0.15
        """
        findings = [
            make_finding(0.7, channel="code", title="caching", url="https://a"),
            make_finding(
                0.6,
                source="hn",
                channel="discourse",
                title="caching",
                url="https://b",
            ),
            make_finding(
                0.8,
                source="arxiv",
                channel="academic",
                title="caching",
                url="https://c",
            ),
            make_finding(
                0.5,
                source="triz",
                channel="triz",
                title="caching",
                url="https://d",
            ),
        ]

        bonus = compute_triangulation_bonus(findings[0], findings)

        assert bonus <= 0.15

    @pytest.mark.unit
    def test_same_channel_not_counted(self) -> None:
        """
        Scenario: Multiple findings in same channel
        Given two code findings with similar titles
        When compute_triangulation_bonus is called
        Then no bonus is awarded (same-channel matches don't count)
        """
        a = make_finding(0.7, channel="code", title="react hooks", url="https://a")
        b = make_finding(0.6, channel="code", title="react hooks", url="https://b")

        bonus = compute_triangulation_bonus(a, [a, b])

        assert bonus == 0.0
