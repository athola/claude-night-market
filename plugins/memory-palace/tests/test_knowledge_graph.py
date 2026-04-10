"""Tests for the SQLite-backed knowledge graph."""

from __future__ import annotations

from sqlite3 import ProgrammingError

import pytest

from memory_palace.knowledge_graph import KnowledgeGraph


@pytest.fixture
def graph() -> KnowledgeGraph:
    """Create an in-memory knowledge graph for testing."""
    g = KnowledgeGraph(":memory:")
    yield g
    g.close()


class TestSchemaAndLifecycle:
    """Schema creation and connection lifecycle."""

    def test_creates_tables_on_init(self, graph: KnowledgeGraph) -> None:
        tables = graph.table_names()
        for expected in [
            "entities",
            "residencies",
            "triples",
            "synapses",
            "journeys",
            "waypoints",
            "tier_assignments",
        ]:
            assert expected in tables, f"Missing table: {expected}"

    def test_context_manager(self) -> None:
        with KnowledgeGraph(":memory:") as g:
            assert g.entity_count() == 0
        # connection closed after exit -- calling again should fail
        with pytest.raises(ProgrammingError):
            g.entity_count()

    def test_node_count_empty(self, graph: KnowledgeGraph) -> None:
        assert graph.entity_count() == 0
        assert graph.synapse_count() == 0


class TestEntityCRUD:
    """Entity create, read, update, delete."""

    def test_upsert_and_get(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(
            entity_id="e001",
            entity_type="concept",
            name="Dependency Injection",
            metadata={"domain": "architecture"},
        )
        entity = graph.get_entity("e001")
        assert entity is not None
        assert entity["name"] == "Dependency Injection"
        assert entity["entity_type"] == "concept"

    def test_upsert_updates_existing(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e001", entity_type="concept", name="Old Name")
        graph.upsert_entity(entity_id="e001", entity_type="concept", name="New Name")
        entity = graph.get_entity("e001")
        assert entity["name"] == "New Name"
        assert graph.entity_count() == 1

    def test_get_nonexistent_returns_none(self, graph: KnowledgeGraph) -> None:
        assert graph.get_entity("nonexistent") is None

    def test_get_entities_by_type(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="decision", name="B")
        graph.upsert_entity(entity_id="e3", entity_type="concept", name="C")
        concepts = graph.get_entities_by_type("concept")
        assert len(concepts) == 2
        assert {e["entity_id"] for e in concepts} == {"e1", "e3"}

    def test_delete_entity(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        assert graph.entity_count() == 1
        graph.delete_entity("e1")
        assert graph.entity_count() == 0
        assert graph.get_entity("e1") is None


class TestResidencies:
    """Entity-palace residency management."""

    def test_add_and_get_residency(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="DI")
        graph.add_residency(
            entity_id="e1",
            palace_id="p1",
            room_id="room-arch",
            role="curator",
        )
        residencies = graph.get_residencies(entity_id="e1")
        assert len(residencies) == 1
        assert residencies[0]["palace_id"] == "p1"
        assert residencies[0]["role"] == "curator"

    def test_multiple_residencies(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="DI")
        graph.add_residency(entity_id="e1", palace_id="p1", role="curator")
        graph.add_residency(entity_id="e1", palace_id="p2", role="messenger")
        residencies = graph.get_residencies(entity_id="e1")
        assert len(residencies) == 2

    def test_get_residents_in_palace(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.add_residency(entity_id="e1", palace_id="p1", role="curator")
        graph.add_residency(entity_id="e2", palace_id="p1", role="patron")
        graph.add_residency(entity_id="e2", palace_id="p2", role="patron")
        residents = graph.get_residents_in_palace("p1")
        assert len(residents) == 2

    def test_duplicate_residency_ignored(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.add_residency(entity_id="e1", palace_id="p1", role="curator")
        graph.add_residency(entity_id="e1", palace_id="p1", role="curator")
        assert len(graph.get_residencies(entity_id="e1")) == 1

    def test_messenger_bridges_palaces(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Bridge")
        graph.add_residency(entity_id="e1", palace_id="p1", role="messenger")
        graph.add_residency(entity_id="e1", palace_id="p2", role="messenger")
        messengers = graph.get_messengers()
        assert len(messengers) >= 1
        assert messengers[0]["entity_id"] == "e1"


class TestTriples:
    """Temporal triples with validity windows."""

    def test_add_and_query_triple(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.add_triple(
            subject_id="e1",
            predicate="depends-on",
            object_id="e2",
            confidence=0.9,
        )
        triples = graph.get_triples_from("e1")
        assert len(triples) == 1
        assert triples[0]["predicate"] == "depends-on"
        assert triples[0]["confidence"] == 0.9

    def test_temporal_validity(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.add_triple(
            subject_id="e1",
            predicate="uses",
            object_id="e2",
            valid_from="2025-01-01T00:00:00",
            valid_to="2025-06-01T00:00:00",
        )
        graph.add_triple(
            subject_id="e1",
            predicate="uses",
            object_id="e2",
            valid_from="2025-06-01T00:00:00",
        )
        # Only the second triple should be active (no valid_to)
        active = graph.get_active_triples_from("e1")
        assert len(active) == 1
        assert active[0]["valid_to"] is None or active[0]["valid_to"] == ""

    def test_invalidate_triple(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.add_triple(subject_id="e1", predicate="uses", object_id="e2")
        triples = graph.get_active_triples_from("e1")
        assert len(triples) == 1
        graph.invalidate_triple(
            triples[0]["id"],
            valid_to="2025-12-01T00:00:00",
        )
        assert len(graph.get_active_triples_from("e1")) == 0


class TestSynapses:
    """Weighted synapse links with strength mechanics."""

    def test_create_synapse(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        syn_id = graph.create_synapse(source_id="e1", target_id="e2")
        assert syn_id > 0
        synapse = graph.get_synapse(syn_id)
        assert synapse["strength"] == pytest.approx(0.1)
        assert synapse["traversal_count"] == 0

    def test_strengthen_synapse(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        syn_id = graph.create_synapse(source_id="e1", target_id="e2")
        graph.strengthen_synapse(syn_id, delta=0.1)
        synapse = graph.get_synapse(syn_id)
        assert synapse["strength"] == pytest.approx(0.2)
        assert synapse["traversal_count"] == 1

    def test_strength_capped_at_one(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        syn_id = graph.create_synapse(source_id="e1", target_id="e2")
        for _ in range(20):
            graph.strengthen_synapse(syn_id, delta=0.1)
        synapse = graph.get_synapse(syn_id)
        assert synapse["strength"] <= 1.0

    def test_get_synapses_from(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.upsert_entity(entity_id="e3", entity_type="concept", name="C")
        graph.create_synapse(source_id="e1", target_id="e2")
        graph.create_synapse(source_id="e1", target_id="e3")
        synapses = graph.get_synapses_from("e1")
        assert len(synapses) == 2


class TestJourneys:
    """Journey and waypoint tracking."""

    def test_create_journey(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Traveler")
        journey_id = graph.create_journey(
            entity_id="e1",
            trigger="cross-palace search",
        )
        assert journey_id > 0
        journey = graph.get_journey(journey_id)
        assert journey["entity_id"] == "e1"
        assert journey["outcome"] is None or journey["outcome"] == ""

    def test_add_waypoint(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Traveler")
        journey_id = graph.create_journey(entity_id="e1", trigger="search")
        graph.add_waypoint(
            journey_id=journey_id,
            sequence=1,
            palace_id="p1",
            room_id="room-a",
            entity_delta='{"learned": ["new fact"]}',
            palace_delta='{"deposited": ["knowledge"]}',
        )
        waypoints = graph.get_waypoints(journey_id)
        assert len(waypoints) == 1
        assert waypoints[0]["palace_id"] == "p1"
        assert waypoints[0]["sequence"] == 1

    def test_complete_journey(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Traveler")
        journey_id = graph.create_journey(entity_id="e1", trigger="search")
        graph.complete_journey(journey_id, outcome="enriched")
        journey = graph.get_journey(journey_id)
        assert journey["outcome"] == "enriched"
        assert journey["completed_at"] != ""


class TestFTS:
    """Full-text search via FTS5."""

    def test_search_entities(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(
            entity_id="e1",
            entity_type="concept",
            name="Dependency Injection Pattern",
        )
        graph.upsert_entity(
            entity_id="e2",
            entity_type="decision",
            name="Use PostgreSQL for storage",
        )
        results = graph.search("injection")
        assert len(results) >= 1
        assert results[0]["entity_id"] == "e1"

    def test_search_empty_query(self, graph: KnowledgeGraph) -> None:
        results = graph.search("")
        assert results == []

    def test_search_no_results(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Foo")
        results = graph.search("nonexistent")
        assert results == []


class TestTierAssignments:
    """Tier assignment storage."""

    def test_assign_and_get_tier(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Core")
        graph.assign_tier(
            entity_id="e1",
            tier=0,
            score=0.85,
            reason="High PageRank + keystone",
        )
        tier = graph.get_tier("e1")
        assert tier is not None
        assert tier["tier"] == 0
        assert tier["score"] == pytest.approx(0.85)

    def test_get_entities_by_tier(self, graph: KnowledgeGraph) -> None:
        for i, t in enumerate([0, 1, 1, 2, 3]):
            graph.upsert_entity(
                entity_id=f"e{i}",
                entity_type="concept",
                name=f"Entity {i}",
            )
            graph.assign_tier(entity_id=f"e{i}", tier=t, score=0.5)
        l1 = graph.get_entities_by_tier(1)
        assert len(l1) == 2


class TestEdgeCases:
    """Edge cases and fallback paths."""

    def test_search_with_special_characters(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity("e1", "concept", "Test (special)")
        # FTS match may fail on special chars, should not raise
        results = graph.search("special")
        assert isinstance(results, list)

    def test_upsert_entity_with_none_metadata(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity("e1", "concept", "Test", metadata=None)
        entity = graph.get_entity("e1")
        assert entity is not None

    def test_get_synapse_nonexistent(self, graph: KnowledgeGraph) -> None:
        assert graph.get_synapse(9999) is None

    def test_get_journey_nonexistent(self, graph: KnowledgeGraph) -> None:
        assert graph.get_journey(9999) is None

    def test_get_tier_nonexistent(self, graph: KnowledgeGraph) -> None:
        assert graph.get_tier("nonexistent") is None


class TestBulkOperations:
    """Batch inserts and counts."""

    def test_bulk_upsert_entities(self, graph: KnowledgeGraph) -> None:
        entities = [
            {"entity_id": f"e{i}", "entity_type": "concept", "name": f"E{i}"}
            for i in range(100)
        ]
        graph.bulk_upsert_entities(entities)
        assert graph.entity_count() == 100

    def test_counts(self, graph: KnowledgeGraph) -> None:
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.create_synapse(source_id="e1", target_id="e2")
        assert graph.entity_count() == 2
        assert graph.synapse_count() == 1
