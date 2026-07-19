"""
Feature: retrieval-metrics benchmark harness (make metrics)

As a maintainer
I want one command that scores a committed gold set offline
So that relevancy is measurable and trend-able with no network or model.
"""

from __future__ import annotations

import pytest

from tome.metrics.harness import (
    GoldItem,
    RetrievalReport,
    evaluate,
    load_gold_set,
    main,
)


class TestLoadGoldSet:
    @pytest.mark.unit
    def test_loads_committed_fixture(self) -> None:
        """The shipped fixture parses into GoldItems."""
        gold = load_gold_set()
        assert len(gold) >= 1
        assert all(isinstance(item, GoldItem) for item in gold)
        assert all(item.topic and item.ranked_ids for item in gold)


class TestEvaluate:
    @pytest.mark.unit
    def test_means_match_hand_computed(self) -> None:
        gold = [GoldItem("t", ["a", "b", "c"], frozenset({"a", "c"}))]
        report = evaluate(gold, k=3)
        # nDCG = 1.5 / 1.6309 = 0.9197; MRR = 1.0; recall = 1.0
        assert report.mean_ndcg == pytest.approx(0.9197, abs=1e-3)
        assert report.mean_mrr == pytest.approx(1.0)
        assert report.mean_recall == pytest.approx(1.0)
        assert report.n_topics == 1

    @pytest.mark.unit
    def test_averages_across_topics(self) -> None:
        gold = [
            GoldItem("t1", ["a"], frozenset({"a"})),  # perfect: ndcg 1
            GoldItem("t2", ["x", "y"], frozenset({"y"})),  # miss-then-hit
        ]
        report = evaluate(gold, k=2)
        assert 0.0 < report.mean_ndcg < 1.0
        assert report.n_topics == 2

    @pytest.mark.unit
    def test_empty_gold_is_zero(self) -> None:
        report = evaluate([], k=10)
        assert report.n_topics == 0
        assert report.mean_ndcg == 0.0


class TestReportRender:
    @pytest.mark.unit
    def test_render_shows_metric_names_and_values(self) -> None:
        report = RetrievalReport(
            k=10, n_topics=3, mean_ndcg=0.5, mean_mrr=0.6, mean_recall=0.7
        )
        text = report.render()
        assert "nDCG" in text
        assert "0.500" in text
        assert "MRR" in text


class TestMain:
    @pytest.mark.unit
    def test_main_prints_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        main()
        out = capsys.readouterr().out
        assert "nDCG" in out
