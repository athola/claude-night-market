"""Tier assignment and token budget management.

Computes composite scores from PageRank, usage data, and keystone
detection to assign entities to tiers L0-L3. Each tier has a
token budget controlling how much context an entity consumes.
"""

from __future__ import annotations

from memory_palace.graph_analyzer import PalaceGraphAnalyzer
from memory_palace.knowledge_graph import KnowledgeGraph

# Tier thresholds (score >= threshold => tier)
_TIER_THRESHOLDS = [
    (0, 0.75),  # L0: score >= 0.75
    (1, 0.50),  # L1: score >= 0.50
    (2, 0.20),  # L2: score >= 0.20
    (3, 0.0),  # L3: everything else
]

# Token budgets per tier
_TOKEN_BUDGETS = {
    0: 50,
    1: 200,
    2: 500,
    3: 1000,
}

# Formula weights
_W_PAGERANK = 0.40
_W_USAGE = 0.35
_W_KEYSTONE = 0.25


class TierManager:
    """Assign entities to tiers and enforce token budgets."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        """Initialize tier manager with a knowledge graph."""
        self._kg = graph
        self._analyzer = PalaceGraphAnalyzer(graph)

    def compute_scores(
        self,
        usage_scores: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Compute composite tier scores for all entities.

        Formula: 0.40 * pagerank + 0.35 * usage + 0.25 * keystone

        Args:
            usage_scores: Optional dict mapping entity_id to a
                normalized usage score (0.0-1.0). If not provided,
                usage component defaults to 0.0.

        Returns:
            Dict mapping entity_id to composite score (0.0-1.0).

        """
        usage = usage_scores or {}

        # Compute PageRank
        ranks = self._analyzer.pagerank()
        if ranks:
            max_rank = max(ranks.values()) or 1.0
            normalized_ranks = {k: v / max_rank for k, v in ranks.items()}
        else:
            normalized_ranks = {}

        # Find keystones (articulation points)
        keystones = set(self._analyzer.find_keystones())

        # Compute composite scores
        all_entities = self._kg._conn.execute(
            "SELECT entity_id FROM entities"
        ).fetchall()

        scores: dict[str, float] = {}
        for row in all_entities:
            eid = row["entity_id"]
            pr = normalized_ranks.get(eid, 0.0)
            us = usage.get(eid, 0.0)
            ks = 1.0 if eid in keystones else 0.0
            score = _W_PAGERANK * pr + _W_USAGE * us + _W_KEYSTONE * ks
            scores[eid] = min(1.0, max(0.0, score))

        return scores

    def _score_to_tier(self, score: float) -> int:
        """Map a composite score to a tier number."""
        for tier, threshold in _TIER_THRESHOLDS:
            if score >= threshold:
                return tier
        return 3

    def assign_all_tiers(
        self,
        usage_scores: dict[str, float] | None = None,
    ) -> dict[str, int]:
        """Compute scores and assign tiers to all entities.

        Returns:
            Dict mapping entity_id to tier number.

        """
        scores = self.compute_scores(usage_scores=usage_scores)
        assignments: dict[str, int] = {}

        for eid, score in scores.items():
            tier = self._score_to_tier(score)
            self._kg.assign_tier(
                entity_id=eid,
                tier=tier,
                score=score,
                reason=f"pagerank={score:.3f}",
            )
            assignments[eid] = tier

        return assignments

    @staticmethod
    def token_budget(tier: int) -> int:
        """Return the token budget for a given tier."""
        return _TOKEN_BUDGETS.get(tier, 0)
