"""Tests for tier assignment and token budget management."""

from __future__ import annotations

import pytest

from memory_palace.knowledge_graph import KnowledgeGraph
from memory_palace.tier_manager import TierManager


@pytest.fixture
def graph() -> KnowledgeGraph:
    """Graph with entities of varying importance."""
    g = KnowledgeGraph(":memory:")
    # Hub entity (high centrality)
    g.upsert_entity("hub", "concept", "Central Hub")
    # Spoke entities
    for i in range(5):
        eid = f"spoke{i}"
        g.upsert_entity(eid, "concept", f"Spoke {i}")
        g.create_synapse("hub", eid, strength=0.6)
        g.create_synapse(eid, "hub", strength=0.3)

    # Isolated entity (low importance)
    g.upsert_entity("isolated", "concept", "Isolated Node")

    yield g
    g.close()


@pytest.fixture
def manager(graph: KnowledgeGraph) -> TierManager:
    return TierManager(graph)


class TestCompositeScoring:
    """Composite tier score calculation."""

    def test_compute_scores_returns_all_entities(
        self, manager: TierManager, graph: KnowledgeGraph
    ) -> None:
        scores = manager.compute_scores()
        assert len(scores) == graph.entity_count()

    def test_scores_between_zero_and_one(self, manager: TierManager) -> None:
        scores = manager.compute_scores()
        for score in scores.values():
            assert 0.0 <= score <= 1.0

    def test_hub_scores_higher_than_isolated(self, manager: TierManager) -> None:
        scores = manager.compute_scores()
        assert scores["hub"] > scores["isolated"]


class TestTierAssignment:
    """Assigning entities to tiers L0-L3."""

    def test_assign_all_tiers(
        self, manager: TierManager, graph: KnowledgeGraph
    ) -> None:
        manager.assign_all_tiers()
        # All entities should have tier assignments
        for eid in ("hub", "spoke0", "spoke1", "isolated"):
            tier = graph.get_tier(eid)
            assert tier is not None
            assert 0 <= tier["tier"] <= 3

    def test_hub_gets_lower_tier_number(
        self, manager: TierManager, graph: KnowledgeGraph
    ) -> None:
        manager.assign_all_tiers()
        hub_tier = graph.get_tier("hub")
        iso_tier = graph.get_tier("isolated")
        # Lower tier number = more important
        assert hub_tier["tier"] <= iso_tier["tier"]

    def test_tier_thresholds(self, manager: TierManager) -> None:
        # Test the threshold mapping directly
        assert manager._score_to_tier(0.80) == 0
        assert manager._score_to_tier(0.60) == 1
        assert manager._score_to_tier(0.30) == 2
        assert manager._score_to_tier(0.10) == 3


class TestTokenBudgets:
    """Token budget enforcement per tier."""

    def test_token_budgets(self, manager: TierManager) -> None:
        assert manager.token_budget(0) == 50
        assert manager.token_budget(1) == 200
        assert manager.token_budget(2) == 500
        assert manager.token_budget(3) == 1000

    def test_invalid_tier_returns_zero(self, manager: TierManager) -> None:
        assert manager.token_budget(5) == 0


class TestUsageScoreIntegration:
    """Integration with usage scores (external input)."""

    def test_with_usage_scores(self, manager: TierManager) -> None:
        # Provide external usage scores
        usage = {"hub": 0.9, "spoke0": 0.5, "isolated": 0.1}
        scores = manager.compute_scores(usage_scores=usage)
        # Usage scores should influence the final score
        assert scores["hub"] > scores["isolated"]

    def test_without_usage_scores_defaults_to_zero(self, manager: TierManager) -> None:
        scores = manager.compute_scores()
        # Should still work, just with zero usage component
        assert all(isinstance(v, float) for v in scores.values())
