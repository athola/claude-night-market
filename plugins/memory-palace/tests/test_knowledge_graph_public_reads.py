"""Public read methods that replace direct ``_conn`` access by callers."""

from __future__ import annotations

import pytest

from memory_palace.knowledge_graph import KnowledgeGraph


@pytest.fixture
def graph() -> KnowledgeGraph:
    """Create an in-memory knowledge graph for testing."""
    g = KnowledgeGraph(":memory:")
    yield g
    g.close()


def _entities(graph: KnowledgeGraph, *entity_ids: str) -> None:
    for entity_id in entity_ids:
        graph.upsert_entity(entity_id, "concept", f"Name {entity_id}")


class TestGetEntityIds:
    """get_entity_ids lists entity ids without callers reading _conn."""

    def test_returns_one_dict_per_entity(self, graph: KnowledgeGraph) -> None:
        """Each entity appears once, as a dict keyed by entity_id."""
        _entities(graph, "a", "b")

        rows = graph.get_entity_ids()

        assert sorted(rows, key=lambda r: r["entity_id"]) == [
            {"entity_id": "a"},
            {"entity_id": "b"},
        ]

    def test_empty_graph_returns_empty_list(self, graph: KnowledgeGraph) -> None:
        """A graph with no entities yields an empty list."""
        assert graph.get_entity_ids() == []


class TestGetEntitySummaries:
    """get_entity_summaries returns the fields a listing view needs."""

    def test_returns_id_type_and_name(self, graph: KnowledgeGraph) -> None:
        """Each summary carries the entity's id, type and display name."""
        graph.upsert_entity("a", "decision", "Alpha")

        assert graph.get_entity_summaries() == [
            {"entity_id": "a", "entity_type": "decision", "name": "Alpha"}
        ]


class TestGetSynapseEdges:
    """get_synapse_edges returns the graph's weighted edges."""

    def test_returns_source_target_and_strength(self, graph: KnowledgeGraph) -> None:
        """An edge reports both endpoints and its stored strength."""
        _entities(graph, "a", "b")
        graph.create_synapse("a", "b", strength=0.4)

        assert graph.get_synapse_edges() == [
            {"source_id": "a", "target_id": "b", "strength": pytest.approx(0.4)}
        ]


class TestGetJourneysByEntity:
    """get_journeys_by_entity filters journeys to a single entity."""

    def test_returns_only_that_entity_journeys_in_start_order(
        self, graph: KnowledgeGraph
    ) -> None:
        """Other entities' journeys drop out and the rest come back by start."""
        _entities(graph, "a", "b")
        first = graph.create_journey("a", trigger="one")
        second = graph.create_journey("a", trigger="two")
        graph.create_journey("b", trigger="other")

        rows = graph.get_journeys_by_entity("a")

        assert [r["id"] for r in rows] == [first, second]
        assert all(isinstance(r, dict) for r in rows)

    def test_unknown_entity_returns_empty_list(self, graph: KnowledgeGraph) -> None:
        """An entity id with no journeys yields an empty list."""
        assert graph.get_journeys_by_entity("missing") == []


class TestGetJourneyWaypointEvents:
    """get_journey_waypoint_events flattens journeys with their waypoints."""

    def test_joins_journeys_to_waypoints_ordered_by_sequence(
        self, graph: KnowledgeGraph
    ) -> None:
        """Waypoints come back by sequence with journey id, trigger and delta."""
        _entities(graph, "a")
        journey_id = graph.create_journey("a", trigger="visit")
        graph.add_waypoint(journey_id, 2, "p2", entity_delta='{"x": 2}')
        graph.add_waypoint(journey_id, 1, "p1", entity_delta='{"x": 1}')

        rows = graph.get_journey_waypoint_events("a")

        assert [(r["sequence"], r["palace_id"]) for r in rows] == [
            (1, "p1"),
            (2, "p2"),
        ]
        assert rows[0]["journey_id"] == journey_id
        assert rows[0]["trigger"] == "visit"
        assert rows[0]["entity_delta"] == '{"x": 1}'

    def test_entity_without_journeys_returns_empty_list(
        self, graph: KnowledgeGraph
    ) -> None:
        """An entity with no journeys yields no waypoint events."""
        assert graph.get_journey_waypoint_events("missing") == []


class TestGetActiveTriplesInvolving:
    """get_active_triples_involving filters on role and validity dates."""

    def test_matches_subject_or_object_inside_validity_window(
        self, graph: KnowledgeGraph
    ) -> None:
        """Subject or object matches count, and expired or future ones drop."""
        _entities(graph, "a", "b", "c", "d")
        graph.add_triple("a", "uses", "b")
        graph.add_triple("c", "uses", "a")
        graph.add_triple("c", "uses", "d")
        graph.add_triple("a", "old", "b", valid_to="2020-01-01")
        graph.add_triple("a", "future", "b", valid_from="2999-01-01")

        rows = graph.get_active_triples_involving(["a"], "2025-01-01")

        assert sorted(r["predicate"] for r in rows) == ["uses", "uses"]
        assert all(isinstance(r, dict) for r in rows)

    def test_no_ids_returns_empty_list(self, graph: KnowledgeGraph) -> None:
        """An empty id list yields an empty result."""
        assert graph.get_active_triples_involving([], "2025-01-01") == []


class TestSearchMalformedQuery:
    """search survives FTS syntax errors in user-typed queries."""

    def test_unbalanced_quote_still_returns_fts_ranked_results(
        self, graph: KnowledgeGraph
    ) -> None:
        """A stray quote still returns rows ranked by bm25 from the FTS index."""
        if not graph._has_fts:
            pytest.skip("FTS5 unavailable")
        graph.upsert_entity("e1", "concept", "foo bar")

        rows = graph.search('foo"')

        assert [r["entity_id"] for r in rows] == ["e1"]
        # The LIKE fallback reports a constant 0.0 rank; bm25 does not.
        assert rows[0]["rank"] != 0.0
