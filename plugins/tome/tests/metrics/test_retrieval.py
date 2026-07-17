"""
Feature: retrieval-quality metrics (build increment 5)

As the tome research engine
I want deterministic nDCG / MRR / recall against a gold set
So that relevancy is measured with the trustworthy IR yardstick,
not an LLM judge.
"""

from __future__ import annotations

import pytest
from tome.metrics.retrieval import mrr, ndcg_at_k, recall_at_k

RANKED = ["a", "b", "c", "d"]
RELEVANT = {"a", "c"}


class TestNdcg:
    @pytest.mark.unit
    def test_ndcg_matches_hand_computed_value(self) -> None:
        # DCG = 1/log2(2) + 1/log2(4) = 1.5; IDCG = 1 + 1/log2(3) = 1.6309
        assert ndcg_at_k(RANKED, RELEVANT, k=4) == pytest.approx(0.9197, abs=1e-3)

    @pytest.mark.unit
    def test_perfect_ranking_scores_one(self) -> None:
        assert ndcg_at_k(["a", "c", "b"], {"a", "c"}, k=3) == pytest.approx(1.0)

    @pytest.mark.unit
    def test_no_relevant_items_scores_zero(self) -> None:
        assert ndcg_at_k(RANKED, set(), k=4) == 0.0


class TestMrr:
    @pytest.mark.unit
    def test_first_relevant_at_rank_one(self) -> None:
        assert mrr(RANKED, RELEVANT) == pytest.approx(1.0)

    @pytest.mark.unit
    def test_first_relevant_at_rank_three(self) -> None:
        assert mrr(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)

    @pytest.mark.unit
    def test_no_relevant_scores_zero(self) -> None:
        assert mrr(RANKED, {"z"}) == 0.0


class TestRecall:
    @pytest.mark.unit
    def test_recall_at_2(self) -> None:
        assert recall_at_k(RANKED, RELEVANT, k=2) == pytest.approx(0.5)

    @pytest.mark.unit
    def test_recall_at_4_is_full(self) -> None:
        assert recall_at_k(RANKED, RELEVANT, k=4) == pytest.approx(1.0)

    @pytest.mark.unit
    def test_recall_empty_relevant_is_zero(self) -> None:
        assert recall_at_k(RANKED, set(), k=4) == 0.0
