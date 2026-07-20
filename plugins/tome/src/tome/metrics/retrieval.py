"""Deterministic information-retrieval metrics.

nDCG, MRR, and recall against a gold-relevant set. These are the
trustworthy, label-based yardstick the research favored over
LLM-judged scores. Binary relevance: an item is relevant if its ID is
in the gold set. No dependencies, no network, no model.
"""

from __future__ import annotations

import math


def _dcg(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    """Discounted cumulative gain over the top ``k`` with binary gains."""
    total = 0.0
    for index, item_id in enumerate(ranked_ids[:k]):
        if item_id in relevant:
            total += 1.0 / math.log2(index + 2)
    return total


def ndcg_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    """Normalized DCG at ``k``; 0.0 when there are no relevant items."""
    if not relevant:
        return 0.0
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    if idcg == 0.0:
        return 0.0
    return _dcg(ranked_ids, relevant, k) / idcg


def mrr(ranked_ids: list[str], relevant: set[str]) -> float:
    """Reciprocal rank of the first relevant item; 0.0 when none appear."""
    for index, item_id in enumerate(ranked_ids):
        if item_id in relevant:
            return 1.0 / (index + 1)
    return 0.0


def recall_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant items appearing in the top ``k``."""
    if not relevant:
        return 0.0
    hits = sum(1 for item_id in ranked_ids[:k] if item_id in relevant)
    return hits / len(relevant)
