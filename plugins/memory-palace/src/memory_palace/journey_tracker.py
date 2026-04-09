"""Journey and waypoint lifecycle tracking with synapse mechanics.

Records entity traversals across palaces, tracks state deltas
at each waypoint, and updates synapse strength based on journey
outcomes.
"""

from __future__ import annotations

import json
from typing import Any

from memory_palace.knowledge_graph import KnowledgeGraph

# Outcome -> synapse strength delta
_OUTCOME_DELTAS = {
    "enriched": 0.1,
    "unchanged": 0.02,
    "contradicted": 0.0,
}


class JourneyTracker:
    """Track entity journeys across palaces."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        """Initialize journey tracker with a knowledge graph."""
        self._kg = graph

    def start_journey(
        self,
        entity_id: str,
        trigger: str = "",
    ) -> int:
        """Start a new journey for an entity. Returns journey ID."""
        return self._kg.create_journey(entity_id=entity_id, trigger=trigger)

    def record_waypoint(  # noqa: PLR0913 - waypoint requires all context fields
        self,
        journey_id: int,
        palace_id: str,
        room_id: str = "",
        entity_delta: dict[str, Any] | None = None,
        palace_delta: dict[str, Any] | None = None,
        synapse_id: int | None = None,
    ) -> int:
        """Record a waypoint on a journey.

        Automatically assigns the next sequence number.
        """
        # Get current waypoint count to determine sequence
        existing = self._kg.get_waypoints(journey_id)
        sequence = len(existing) + 1

        return self._kg.add_waypoint(
            journey_id=journey_id,
            sequence=sequence,
            palace_id=palace_id,
            room_id=room_id,
            entity_delta=json.dumps(entity_delta or {}),
            palace_delta=json.dumps(palace_delta or {}),
            synapse_id=synapse_id,
        )

    def complete_journey(
        self,
        journey_id: int,
        outcome: str,
    ) -> None:
        """Complete a journey and update synapse strengths.

        Outcome determines how much traversed synapses strengthen:
        - enriched: +0.1
        - unchanged: +0.02
        - contradicted: +0.0 (no change)
        """
        self._kg.complete_journey(journey_id, outcome=outcome)

        # Strengthen traversed synapses based on outcome
        delta = _OUTCOME_DELTAS.get(outcome, 0.0)
        if delta > 0:
            waypoints = self._kg.get_waypoints(journey_id)
            for wp in waypoints:
                syn_id = wp.get("synapse_id")
                if syn_id:
                    self._kg.strengthen_synapse(syn_id, delta=delta)

    def get_entity_journeys(self, entity_id: str) -> list[dict[str, Any]]:
        """Get all journeys for an entity."""
        rows = self._kg._conn.execute(
            "SELECT * FROM journeys WHERE entity_id = ? ORDER BY started_at",
            (entity_id,),
        ).fetchall()
        return [dict(r) for r in rows]
