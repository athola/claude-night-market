"""
Feature: Finding scoring, ranking, and theme grouping

As a synthesis pipeline
I want findings ranked by composite authority + recency + base relevance
So that the top results in a report are the most credible sources
"""

from __future__ import annotations

# Use the same dynamic year as the production ranker.
from datetime import datetime, timezone

import pytest
from tome.synthesis.ranker import compute_relevance_score, group_by_theme, rank_findings

from tests.factories import make_finding

_THIS_YEAR: int = datetime.now(tz=timezone.utc).year  # noqa: UP017 - keep timezone.utc for 3.9 compat


class TestComputeRelevanceScore:
    """
    Feature: Composite relevance scoring

    As a ranker
    I want to compute a single score that blends base relevance with
    source authority and recency signals
    So that high-quality sources naturally rise to the top
    """

    @pytest.mark.unit
    def test_github_low_stars_no_bonus(self) -> None:
        """
        Scenario: GitHub repo with fewer than 1000 stars
        Given a GitHub finding with 500 stars
        When compute_relevance_score is called
        Then the score equals the base relevance
        """
        f = make_finding(0.5, source="github", metadata={"stars": 500})
        assert compute_relevance_score(f) == pytest.approx(0.5)

    @pytest.mark.unit
    def test_github_over_1000_stars_adds_01(self) -> None:
        """
        Scenario: GitHub repo with 1001 stars
        Given a GitHub finding with 1001 stars and base relevance 0.5
        When compute_relevance_score is called
        Then score is 0.6 (base + 0.1 bonus)
        """
        f = make_finding(0.5, source="github", metadata={"stars": 1001})
        assert compute_relevance_score(f) == pytest.approx(0.6)

    @pytest.mark.unit
    def test_github_over_5000_stars_adds_02(self) -> None:
        """
        Scenario: GitHub repo with 5001 stars
        Given a GitHub finding with 5001 stars and base relevance 0.5
        When compute_relevance_score is called
        Then score is 0.7 (base + 0.2 bonus)
        """
        f = make_finding(0.5, source="github", metadata={"stars": 5001})
        assert compute_relevance_score(f) == pytest.approx(0.7)

    @pytest.mark.unit
    def test_hn_over_100_score_adds_01(self) -> None:
        """
        Scenario: HN post with score > 100
        Given an HN finding with score 200 and base relevance 0.5
        When compute_relevance_score is called
        Then score is 0.6
        """
        f = make_finding(0.5, source="hn", channel="discourse", metadata={"score": 200})
        assert compute_relevance_score(f) == pytest.approx(0.6)

    @pytest.mark.unit
    def test_hn_over_500_score_adds_02(self) -> None:
        """
        Scenario: HN post with score > 500
        Given an HN finding with score 501 and base relevance 0.4
        When compute_relevance_score is called
        Then score is 0.6
        """
        f = make_finding(0.4, source="hn", channel="discourse", metadata={"score": 501})
        assert compute_relevance_score(f) == pytest.approx(0.6)

    @pytest.mark.unit
    def test_arxiv_over_50_citations_adds_01(self) -> None:
        """
        Scenario: arXiv paper with 51 citations
        Given an arxiv finding with 51 citations and base relevance 0.6
        When compute_relevance_score is called
        Then score is 0.7
        """
        f = make_finding(
            0.6, source="arxiv", channel="academic", metadata={"citations": 51}
        )
        assert compute_relevance_score(f) == pytest.approx(0.7)

    @pytest.mark.unit
    def test_arxiv_over_200_citations_adds_02(self) -> None:
        """
        Scenario: arXiv paper with 201 citations
        Given an arxiv finding with 201 citations and base relevance 0.6
        When compute_relevance_score is called
        Then score is 0.8
        """
        f = make_finding(
            0.6, source="arxiv", channel="academic", metadata={"citations": 201}
        )
        assert compute_relevance_score(f) == pytest.approx(0.8)

    @pytest.mark.unit
    def test_reddit_over_50_score_adds_005(self) -> None:
        """
        Scenario: Reddit post with score > 50
        Given a Reddit finding with score 100 and base relevance 0.5
        When compute_relevance_score is called
        Then score is 0.55
        """
        f = make_finding(
            0.5, source="reddit", channel="discourse", metadata={"score": 100}
        )
        assert compute_relevance_score(f) == pytest.approx(0.55)

    @pytest.mark.unit
    def test_reddit_over_200_score_adds_01(self) -> None:
        """
        Scenario: Reddit post with score > 200
        Given a Reddit finding with score 250 and base relevance 0.5
        When compute_relevance_score is called
        Then score is 0.6
        """
        f = make_finding(
            0.5, source="reddit", channel="discourse", metadata={"score": 250}
        )
        assert compute_relevance_score(f) == pytest.approx(0.6)

    @pytest.mark.unit
    def test_recency_bonus_for_recent_year(self) -> None:
        """
        Scenario: Finding published within the last 2 years
        Given a finding with year = current_year - 1 and base relevance 0.5
        When compute_relevance_score is called
        Then score includes +0.05 recency bonus
        """
        f = make_finding(0.5, metadata={"year": _THIS_YEAR - 1})
        assert compute_relevance_score(f) == pytest.approx(0.55)

    @pytest.mark.unit
    def test_no_recency_bonus_for_old_year(self) -> None:
        """
        Scenario: Finding published more than 2 years ago
        Given a finding with year = current_year - 3 and base relevance 0.5
        When compute_relevance_score is called
        Then score is just the base relevance
        """
        f = make_finding(0.5, metadata={"year": _THIS_YEAR - 3})
        assert compute_relevance_score(f) == pytest.approx(0.5)

    @pytest.mark.unit
    def test_score_capped_at_1_0(self) -> None:
        """
        Scenario: High base relevance plus multiple bonuses would exceed 1.0
        Given a finding with base relevance 0.95 and 5001 GitHub stars
        When compute_relevance_score is called
        Then score is exactly 1.0
        """
        f = make_finding(0.95, source="github", metadata={"stars": 5001})
        assert compute_relevance_score(f) == pytest.approx(1.0)

    @pytest.mark.unit
    def test_no_metadata_returns_base_relevance(self) -> None:
        """
        Scenario: Finding with no authority metadata
        Given a finding with base relevance 0.65 and empty metadata
        When compute_relevance_score is called
        Then score equals 0.65
        """
        f = make_finding(0.65)
        assert compute_relevance_score(f) == pytest.approx(0.65)


class TestRankFindings:
    """
    Feature: Descending relevance sort

    As a report formatter
    I want findings ordered from most to least relevant
    So that the top of the report shows the strongest sources
    """

    @pytest.mark.unit
    def test_rank_findings_descending_order(self) -> None:
        """
        Scenario: Three findings with distinct relevance scores
        Given findings with relevance 0.4, 0.9, and 0.6
        When rank_findings is called
        Then they are returned in order 0.9, 0.6, 0.4
        """
        findings = [
            make_finding(0.4, url="https://example.com/a"),
            make_finding(0.9, url="https://example.com/b"),
            make_finding(0.6, url="https://example.com/c"),
        ]

        result = rank_findings(findings)

        scores = [compute_relevance_score(f) for f in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.unit
    def test_rank_empty_list(self) -> None:
        """
        Scenario: Empty input
        Given an empty list of findings
        When rank_findings is called
        Then an empty list is returned
        """
        assert rank_findings([]) == []

    @pytest.mark.unit
    def test_rank_single_finding(self) -> None:
        """
        Scenario: Single finding input
        Given a list with one finding
        When rank_findings is called
        Then that finding is returned unchanged
        """
        f = make_finding(0.7)
        assert rank_findings([f]) == [f]

    @pytest.mark.unit
    def test_authority_bonus_affects_ordering(self) -> None:
        """
        Scenario: Authority bonus lifts a lower-relevance finding above a higher one
        Given a GitHub finding with 0.5 base relevance and 5001 stars
        And a plain finding with 0.65 base relevance and no metadata
        When rank_findings is called
        Then the GitHub finding ranks first (0.5 + 0.2 = 0.7 > 0.65)
        """
        high_authority = make_finding(
            0.5,
            source="github",
            metadata={"stars": 5001},
            url="https://github.com/popular",
        )
        plain = make_finding(0.65, url="https://example.com/plain")

        result = rank_findings([plain, high_authority])

        assert result[0].url == "https://github.com/popular"


class TestGroupByTheme:
    """
    Feature: Channel-based grouping

    As a report formatter
    I want findings grouped by channel
    So that each section of the report lists findings from the right channel
    """

    @pytest.mark.unit
    def test_groups_by_channel(self) -> None:
        """
        Scenario: Findings from three channels
        Given one code, one discourse, and one academic finding
        When group_by_theme is called
        Then each channel key maps to its finding
        """
        code = make_finding(0.8, channel="code", url="https://github.com/x")
        discourse = make_finding(
            0.7,
            source="hn",
            channel="discourse",
            url="https://hn.com/x",
        )
        academic = make_finding(
            0.9,
            source="arxiv",
            channel="academic",
            url="https://arxiv.org/x",
        )

        groups = group_by_theme([code, discourse, academic])

        assert set(groups.keys()) == {"code", "discourse", "academic"}
        assert groups["code"] == [code]
        assert groups["discourse"] == [discourse]
        assert groups["academic"] == [academic]

    @pytest.mark.unit
    def test_multiple_findings_per_channel(self) -> None:
        """
        Scenario: Two findings share the same channel
        Given two code findings
        When group_by_theme is called
        Then the code group contains both
        """
        f1 = make_finding(0.8, channel="code", url="https://github.com/a")
        f2 = make_finding(0.6, channel="code", url="https://github.com/b")

        groups = group_by_theme([f1, f2])

        assert len(groups["code"]) == 2

    @pytest.mark.unit
    def test_empty_input_returns_empty_dict(self) -> None:
        """
        Scenario: No findings
        Given an empty list
        When group_by_theme is called
        Then an empty dict is returned
        """
        assert group_by_theme([]) == {}

    @pytest.mark.unit
    def test_semantic_scholar_gets_academic_bonus(self) -> None:
        """
        Scenario: Semantic Scholar findings get citation authority bonus
        Given a semantic_scholar finding with 201 citations
        When compute_relevance_score is called
        Then score includes the +0.2 academic bonus
        """
        f = make_finding(
            0.6,
            source="semantic_scholar",
            channel="academic",
            metadata={"citations": 201},
        )
        assert compute_relevance_score(f) == pytest.approx(0.8)
