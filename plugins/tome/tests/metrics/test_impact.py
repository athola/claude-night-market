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
