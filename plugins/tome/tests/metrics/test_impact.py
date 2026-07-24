"""
Feature: impact metrics (impact dimension)

As the tome research engine
I want disruption and centrality measured over the citation graph
So that a paper's structural influence is quantified, with the
citation-inflation bias designed out of cross-cohort comparison.
"""

from __future__ import annotations

from typing import Any

import pytest

from tome.graph.palace_adapter import CitationGraphWriter
from tome.metrics.impact import (
    Cohort,
    DisruptionScore,
    assert_comparable,
    disruption_index,
    rank_by_centrality,
)
from tome.models import CitationEdge


class TestDisruptionIndex:
    @pytest.mark.unit
    def test_fully_disruptive(self) -> None:
        # Citing papers ignore the focal's references entirely.
        assert disruption_index({"A", "B"}, set()) == pytest.approx(1.0)

    @pytest.mark.unit
    def test_fully_consolidating(self) -> None:
        # Every citing paper also cites the focal's references.
        assert disruption_index({"A", "B"}, {"A", "B"}) == pytest.approx(-1.0)

    @pytest.mark.unit
    def test_mixed_case(self) -> None:
        # only_focal={A}=1, both={B,C}=2, only_refs={D}=1 -> (1-2)/4 = -0.25
        assert disruption_index({"A", "B", "C"}, {"B", "C", "D"}) == pytest.approx(
            -0.25
        )

    @pytest.mark.unit
    def test_no_citations_is_zero(self) -> None:
        assert disruption_index(set(), set()) == 0.0


class TestCohortGuardrail:
    @pytest.mark.unit
    def test_same_cohort_is_comparable(self) -> None:
        a = DisruptionScore("P1", 0.3, Cohort("cs.LG", 2024))
        b = DisruptionScore("P2", -0.1, Cohort("cs.LG", 2024))
        assert_comparable(a, b)  # must not raise

    @pytest.mark.unit
    def test_cross_field_raises(self) -> None:
        a = DisruptionScore("P1", 0.3, Cohort("cs.LG", 2024))
        b = DisruptionScore("P2", 0.3, Cohort("q-bio", 2024))
        with pytest.raises(ValueError, match="cohort"):
            assert_comparable(a, b)

    @pytest.mark.unit
    def test_cross_year_raises(self) -> None:
        a = DisruptionScore("P1", 0.3, Cohort("cs.LG", 2010))
        b = DisruptionScore("P2", 0.3, Cohort("cs.LG", 2024))
        with pytest.raises(ValueError, match="cohort"):
            assert_comparable(a, b)


class TestCentrality:
    @pytest.mark.unit
    def test_ranks_descending_by_pagerank(self) -> None:
        ranked = rank_by_centrality({"A": 0.1, "B": 0.5, "C": 0.3})
        assert [pid for pid, _ in ranked] == ["B", "C", "A"]

    @pytest.mark.unit
    def test_empty_is_empty(self) -> None:
        assert rank_by_centrality({}) == []


class TestCentralityContract:
    """Runs only where memory-palace is installed (combined CI)."""

    @pytest.mark.integration
    def test_pagerank_feeds_centrality(self, tmp_path: Any) -> None:
        mp = pytest.importorskip("memory_palace")
        graph = mp.KnowledgeGraph(str(tmp_path / "g.db"))
        CitationGraphWriter(graph).write_edges(
            [CitationEdge("P1", "P2"), CitationEdge("P3", "P2")]
        )
        analyzer = mp.PalaceGraphAnalyzer(graph)
        ranked = rank_by_centrality(analyzer.pagerank())

        assert isinstance(ranked, list)


class TestDisruptionScoreInvariants:
    """
    Feature: DisruptionScore refuses scores its producer cannot emit

    ``disruption_index`` provably returns the CD index in ``[-1.0, 1.0]``.
    A value outside that band is a defect in whatever built the score,
    so it is refused where it is constructed rather than carried into a
    ranking that silently misreads it.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize("score", [-1.0, -0.5, 0.0, 0.5, 1.0])
    def test_in_band_scores_construct(self, score: float) -> None:
        tagged = DisruptionScore(
            paper_id="p1", score=score, cohort=Cohort(field="cs", year=2026)
        )

        assert tagged.score == score

    @pytest.mark.unit
    @pytest.mark.parametrize("score", [-1.5, 1.5, 2.0, -100.0])
    def test_out_of_band_score_rejected(self, score: float) -> None:
        """
        Scenario: A score outside the CD index range
        Given a score below -1.0 or above 1.0
        When DisruptionScore is constructed
        Then it raises rather than entering a ranking
        """
        with pytest.raises(ValueError, match=r"disruption score .* \[-1.0, 1.0\]"):
            DisruptionScore(
                paper_id="p1", score=score, cohort=Cohort(field="cs", year=2026)
            )

    @pytest.mark.unit
    def test_empty_paper_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty paper ID"):
            DisruptionScore(
                paper_id="", score=0.0, cohort=Cohort(field="cs", year=2026)
            )

    @pytest.mark.unit
    def test_every_disruption_index_result_is_constructible(self) -> None:
        """The producer's full output range must satisfy the invariant."""
        cohort = Cohort(field="cs", year=2026)
        cases = [
            (set(), set()),
            ({"a", "b"}, set()),
            (set(), {"a", "b"}),
            ({"a"}, {"a"}),
            ({"a", "b"}, {"b", "c"}),
        ]

        for focal, refs in cases:
            score = disruption_index(focal, refs)
            assert (
                DisruptionScore(paper_id="p", score=score, cohort=cohort).score == score
            )
