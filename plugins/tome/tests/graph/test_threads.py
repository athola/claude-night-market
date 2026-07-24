"""
Feature: research threads and paths (build increment 3)

As the tome research engine
I want communities and predicted links over the citation graph
So that I can surface "common threads" and "further research paths",
reusing memory-palace's PalaceGraphAnalyzer.
"""

from __future__ import annotations

from typing import Any

import pytest

from tome.graph.palace_adapter import CitationGraphWriter, GraphBackendUnavailable
from tome.graph.threads import (
    GraphAnalyzer,
    ResearchPath,
    ResearchThread,
    ThreadFinder,
    analyzer_available,
    open_analyzer,
)
from tome.models import CitationEdge


class FakeAnalyzer:
    """Stand-in satisfying the GraphAnalyzer protocol."""

    def __init__(
        self,
        communities: dict[int, set[str]],
        links: list[tuple[str, str, float]],
    ) -> None:
        self._communities = communities
        self._links = links

    def detect_communities(self) -> dict[int, set[str]]:
        return self._communities

    def predict_links(self, top_n: int = 10) -> list[tuple[str, str, float]]:
        return self._links[:top_n]


class TestThreadFinder:
    @pytest.mark.unit
    def test_common_threads_map_communities(self) -> None:
        analyzer = FakeAnalyzer({0: {"A", "B"}, 1: {"C"}}, [])
        finder = ThreadFinder(analyzer)

        threads = finder.common_threads()

        assert ResearchThread(0, frozenset({"A", "B"})) in threads
        assert ResearchThread(1, frozenset({"C"})) in threads
        assert len(threads) == 2

    @pytest.mark.unit
    def test_research_paths_map_predicted_links(self) -> None:
        analyzer = FakeAnalyzer({}, [("A", "B", 0.9), ("A", "C", 0.4)])
        finder = ThreadFinder(analyzer)

        paths = finder.research_paths()

        assert paths[0] == ResearchPath(from_id="A", to_id="B", score=0.9)
        assert paths[1] == ResearchPath(from_id="A", to_id="C", score=0.4)

    @pytest.mark.unit
    def test_research_paths_respects_top_n(self) -> None:
        analyzer = FakeAnalyzer({}, [("A", "B", 0.9), ("A", "C", 0.4)])
        finder = ThreadFinder(analyzer)

        assert len(finder.research_paths(top_n=1)) == 1

    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        assert isinstance(FakeAnalyzer({}, []), GraphAnalyzer)


class TestOpenAnalyzer:
    @pytest.mark.unit
    def test_raises_explicitly_when_backend_absent(self) -> None:
        if analyzer_available():
            pytest.skip("memory-palace installed; cannot test absent path")
        with pytest.raises(GraphBackendUnavailable, match="memory-palace"):
            open_analyzer(object())


class TestRealAnalyzerContract:
    """Runs only where memory-palace is installed (combined CI)."""

    @pytest.mark.integration
    def test_threads_over_real_graph(self, tmp_path: Any) -> None:
        mp = pytest.importorskip("memory_palace")

        graph = mp.KnowledgeGraph(str(tmp_path / "g.db"))
        CitationGraphWriter(graph).write_edges(
            [
                CitationEdge(citing_id="P1", cited_id="P2"),
                CitationEdge(citing_id="P2", cited_id="P3"),
            ]
        )

        finder = ThreadFinder(open_analyzer(graph))
        # Communities/paths may be empty on a tiny graph, but the calls
        # must succeed and return the right shapes.
        assert isinstance(finder.common_threads(), list)
        assert isinstance(finder.research_paths(top_n=5), list)


class TestResearchPathInvariants:
    """
    Feature: ResearchPath refuses paths that predict nothing

    ``PalaceGraphAnalyzer.predict_links`` emits Adamic-Adar scores and
    already filters to ``score > 0`` over non-existing edges, so a
    zero/negative score or a self-referential path is a producer defect.
    Adamic-Adar is unbounded above, so no upper bound is imposed.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize("score", [0.01, 1.0, 42.7])
    def test_positive_scores_construct(self, score: float) -> None:
        path = ResearchPath(from_id="a", to_id="b", score=score)

        assert path.score == score

    @pytest.mark.unit
    @pytest.mark.parametrize("score", [0.0, -0.5])
    def test_non_positive_score_rejected(self, score: float) -> None:
        """
        Scenario: A predicted link with no predictive weight
        Given a score of zero or below
        When ResearchPath is constructed
        Then it raises, matching the producer's own > 0 filter
        """
        with pytest.raises(ValueError, match="score must be positive"):
            ResearchPath(from_id="a", to_id="b", score=score)

    @pytest.mark.unit
    def test_self_path_rejected(self) -> None:
        with pytest.raises(ValueError, match="cannot point at itself"):
            ResearchPath(from_id="a", to_id="a", score=1.0)

    @pytest.mark.unit
    @pytest.mark.parametrize(("src", "dst"), [("", "b"), ("a", ""), ("  ", "b")])
    def test_empty_endpoint_rejected(self, src: str, dst: str) -> None:
        with pytest.raises(ValueError, match="non-empty node IDs"):
            ResearchPath(from_id=src, to_id=dst, score=1.0)
