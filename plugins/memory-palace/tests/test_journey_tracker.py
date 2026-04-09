"""Tests for journey and waypoint tracking with synapse mechanics."""

from __future__ import annotations

import pytest

from memory_palace.journey_tracker import JourneyTracker
from memory_palace.knowledge_graph import KnowledgeGraph


@pytest.fixture
def graph() -> KnowledgeGraph:
    """Graph with cross-palace entities and synapses."""
    g = KnowledgeGraph(":memory:")
    # Two palaces
    g.upsert_entity("p1", "palace", "Palace A")
    g.upsert_entity("p2", "palace", "Palace B")

    # Entity that exists in both palaces (messenger)
    g.upsert_entity("traveler", "concept", "Shared Concept")
    g.add_residency("traveler", palace_id="p1", role="patron")
    g.add_residency("traveler", palace_id="p2", role="messenger")

    # Synapse between palaces
    g.upsert_entity("anchor_a", "concept", "Anchor A")
    g.upsert_entity("anchor_b", "concept", "Anchor B")
    g.add_residency("anchor_a", palace_id="p1", role="patron")
    g.add_residency("anchor_b", palace_id="p2", role="patron")

    yield g
    g.close()


@pytest.fixture
def tracker(graph: KnowledgeGraph) -> JourneyTracker:
    return JourneyTracker(graph)


class TestJourneyLifecycle:
    """Creating, tracking, and completing journeys."""

    def test_start_journey(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        journey_id = tracker.start_journey("traveler", trigger="search")
        journey = graph.get_journey(journey_id)
        assert journey is not None
        assert journey["entity_id"] == "traveler"
        assert journey["outcome"] == ""

    def test_record_waypoint(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        journey_id = tracker.start_journey("traveler", trigger="search")
        tracker.record_waypoint(
            journey_id=journey_id,
            palace_id="p1",
            room_id="room-a",
            entity_delta={"learned": ["new fact"]},
            palace_delta={"deposited": ["knowledge"]},
        )
        waypoints = graph.get_waypoints(journey_id)
        assert len(waypoints) == 1
        assert waypoints[0]["sequence"] == 1

    def test_multiple_waypoints_auto_sequence(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        journey_id = tracker.start_journey("traveler", trigger="search")
        tracker.record_waypoint(journey_id, palace_id="p1")
        tracker.record_waypoint(journey_id, palace_id="p2")
        waypoints = graph.get_waypoints(journey_id)
        assert waypoints[0]["sequence"] == 1
        assert waypoints[1]["sequence"] == 2

    def test_complete_journey_enriched(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        journey_id = tracker.start_journey("traveler", trigger="search")
        tracker.record_waypoint(journey_id, palace_id="p1")
        tracker.complete_journey(journey_id, outcome="enriched")
        journey = graph.get_journey(journey_id)
        assert journey["outcome"] == "enriched"
        assert journey["completed_at"] != ""


class TestSynapseStrengthening:
    """Outcome-weighted synapse strength updates."""

    def test_enriched_strengthens_synapse(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        syn_id = graph.create_synapse("anchor_a", "anchor_b", strength=0.3)
        journey_id = tracker.start_journey("traveler", trigger="search")
        tracker.record_waypoint(journey_id, palace_id="p1", synapse_id=syn_id)
        tracker.complete_journey(journey_id, outcome="enriched")
        synapse = graph.get_synapse(syn_id)
        assert synapse["strength"] == pytest.approx(0.4)  # +0.1

    def test_unchanged_weakly_strengthens(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        syn_id = graph.create_synapse("anchor_a", "anchor_b", strength=0.3)
        journey_id = tracker.start_journey("traveler", trigger="search")
        tracker.record_waypoint(journey_id, palace_id="p1", synapse_id=syn_id)
        tracker.complete_journey(journey_id, outcome="unchanged")
        synapse = graph.get_synapse(syn_id)
        assert synapse["strength"] == pytest.approx(0.32)  # +0.02

    def test_contradicted_no_strengthening(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        syn_id = graph.create_synapse("anchor_a", "anchor_b", strength=0.3)
        journey_id = tracker.start_journey("traveler", trigger="search")
        tracker.record_waypoint(journey_id, palace_id="p1", synapse_id=syn_id)
        tracker.complete_journey(journey_id, outcome="contradicted")
        synapse = graph.get_synapse(syn_id)
        assert synapse["strength"] == pytest.approx(0.3)  # unchanged


class TestJourneyQueries:
    """Querying journey history."""

    def test_get_entity_journeys(
        self, tracker: JourneyTracker, graph: KnowledgeGraph
    ) -> None:
        tracker.start_journey("traveler", trigger="search1")
        tracker.start_journey("traveler", trigger="search2")
        journeys = tracker.get_entity_journeys("traveler")
        assert len(journeys) == 2

    def test_empty_journeys(self, tracker: JourneyTracker) -> None:
        journeys = tracker.get_entity_journeys("nonexistent")
        assert journeys == []
