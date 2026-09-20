"""Tests for the SQLite-backed knowledge graph."""

from __future__ import annotations

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
        """Opening a fresh database lays down the full schema, not a lazy subset."""
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


class TestEntityCRUD:
    """Entity create, read, update, delete."""

    def test_upsert_and_get(self, graph: KnowledgeGraph) -> None:
        """An upserted entity reads back with the fields it was given."""
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

    def test_get_nonexistent_returns_none(self, graph: KnowledgeGraph) -> None:
        """A missing id yields None rather than raising."""
        assert graph.get_entity("nonexistent") is None


class TestResidencies:
    """Entity-palace residency management."""

    def test_get_residents_in_palace(self, graph: KnowledgeGraph) -> None:
        """The reverse lookup lists everything living in a palace."""
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.add_residency(entity_id="e1", palace_id="p1", role="curator")
        graph.add_residency(entity_id="e2", palace_id="p1", role="patron")
        graph.add_residency(entity_id="e2", palace_id="p2", role="patron")
        residents = graph.get_residents_in_palace("p1")
        assert len(residents) == 2


class TestTriples:
    """Temporal triples with validity windows."""

    def test_temporal_validity(self, graph: KnowledgeGraph) -> None:
        """A triple with no end date counts as still active."""
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


class TestSynapses:
    """Weighted synapse links with strength mechanics."""

    def test_get_synapses_from(self, graph: KnowledgeGraph) -> None:
        """Outgoing lookup returns every synapse leaving a node."""
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="A")
        graph.upsert_entity(entity_id="e2", entity_type="concept", name="B")
        graph.upsert_entity(entity_id="e3", entity_type="concept", name="C")
        graph.create_synapse(source_id="e1", target_id="e2")
        graph.create_synapse(source_id="e1", target_id="e3")
        synapses = graph.get_synapses_from("e1")
        assert len(synapses) == 2

    def test_get_synapses_to_returns_incoming_synapses(
        self, graph: KnowledgeGraph
    ) -> None:
        """get_synapses_to must return synapses whose target_id matches.

        Renders use incoming synapse direction so KnowledgeGraph must expose
        this query via public API rather than forcing callers to access
        the private _conn attribute directly (MP-004).
        """
        graph.upsert_entity(entity_id="src1", entity_type="concept", name="Src1")
        graph.upsert_entity(entity_id="src2", entity_type="concept", name="Src2")
        graph.upsert_entity(entity_id="tgt", entity_type="concept", name="Tgt")
        graph.create_synapse(source_id="src1", target_id="tgt")
        graph.create_synapse(source_id="src2", target_id="tgt")
        graph.create_synapse(source_id="src1", target_id="src2")  # unrelated

        synapses = graph.get_synapses_to("tgt")

        assert len(synapses) == 2
        target_ids = {s["target_id"] for s in synapses}
        assert target_ids == {"tgt"}

    def test_get_synapses_to_empty_when_no_incoming(
        self, graph: KnowledgeGraph
    ) -> None:
        """get_synapses_to must return empty list when entity has no incoming synapses."""
        graph.upsert_entity(entity_id="lone", entity_type="concept", name="Lone")
        assert graph.get_synapses_to("lone") == []


class TestJourneys:
    """Journey and waypoint tracking."""

    def test_add_waypoint(self, graph: KnowledgeGraph) -> None:
        """A waypoint records which palace the journey passed through."""
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


class TestFTS:
    """Full-text search via FTS5."""

    def test_search_entities(self, graph: KnowledgeGraph) -> None:
        """Full-text search finds an entity by a word from its body."""
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
        """An empty query returns nothing rather than everything."""
        results = graph.search("")
        assert results == []

    def test_search_no_results(self, graph: KnowledgeGraph) -> None:
        """A term matching nothing returns an empty list."""
        graph.upsert_entity(entity_id="e1", entity_type="concept", name="Foo")
        results = graph.search("nonexistent")
        assert results == []


class TestTierAssignments:
    """Tier assignment storage."""


class TestEdgeCases:
    """Edge cases and fallback paths."""

    def test_search_with_special_characters(self, graph: KnowledgeGraph) -> None:
        """FTS punctuation cannot break the query into a syntax error."""
        graph.upsert_entity("e1", "concept", "Test (special)")
        # FTS match may fail on special chars, should not raise
        results = graph.search("special")
        assert isinstance(results, list)

    def test_upsert_entity_with_none_metadata(self, graph: KnowledgeGraph) -> None:
        """Absent metadata is stored without raising."""
        graph.upsert_entity("e1", "concept", "Test", metadata=None)
        entity = graph.get_entity("e1")
        assert entity is not None


class TestBulkOperations:
    """Batch inserts and counts."""
