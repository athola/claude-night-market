"""Tests for JSON palace to knowledge graph migration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from memory_palace.knowledge_graph import KnowledgeGraph
from memory_palace.migration import MigrationReport, PalaceMigrator


@pytest.fixture
def graph() -> KnowledgeGraph:
    g = KnowledgeGraph(":memory:")
    yield g
    g.close()


@pytest.fixture
def sample_palace() -> dict[str, Any]:
    return {
        "id": "abc12345",
        "name": "Test Palace",
        "domain": "testing",
        "metaphor": "library",
        "created": "2025-01-01T00:00:00",
        "last_modified": "2025-06-01T00:00:00",
        "layout": {
            "districts": [],
            "buildings": [],
            "rooms": [
                {"id": "room-arch", "name": "Architecture"},
                {"id": "room-data", "name": "Data Structures"},
            ],
            "connections": [
                {"from": "room-arch", "to": "room-data", "label": "related"},
            ],
        },
        "associations": {
            "concept1": {"label": "Dependency Injection", "location": "room-arch"},
            "concept2": {"label": "Observer Pattern", "location": "room-arch"},
            "concept3": {"label": "Binary Tree", "location": "room-data"},
        },
        "sensory_encoding": {
            "room-arch": {"visual": "blue walls", "auditory": "quiet hum"},
        },
        "metadata": {
            "concept_count": 3,
            "complexity_level": "intermediate",
            "access_patterns": [],
        },
    }


@pytest.fixture
def palace_dir(tmp_path: Path, sample_palace: dict[str, Any]) -> Path:
    palaces = tmp_path / "palaces"
    palaces.mkdir()
    (palaces / f"{sample_palace['id']}.json").write_text(json.dumps(sample_palace))
    return palaces


class TestMigrateSinglePalace:
    """Migrate a single JSON palace into the graph."""

    def test_creates_palace_entity(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        palace = graph.get_entity("abc12345")
        assert palace is not None
        assert palace["entity_type"] == "palace"
        assert palace["name"] == "Test Palace"

    def test_creates_room_entities(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        rooms = graph.get_entities_by_type("room")
        assert len(rooms) == 2
        names = {r["name"] for r in rooms}
        assert "Architecture" in names
        assert "Data Structures" in names

    def test_creates_concept_entities(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        concepts = graph.get_entities_by_type("concept")
        assert len(concepts) == 3

    def test_creates_residencies(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        # Concepts should reside in their rooms within the palace
        residencies = graph.get_residencies("concept1")
        assert len(residencies) == 1
        assert residencies[0]["palace_id"] == "abc12345"
        assert residencies[0]["room_id"] == "room-arch"

    def test_creates_synapses_from_connections(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        # Connections between rooms become synapses
        synapses = graph.get_synapses_from("room-arch")
        assert len(synapses) >= 1
        assert synapses[0]["target_id"] == "room-data"
        assert synapses[0]["strength"] == pytest.approx(0.5)

    def test_room_residencies_in_palace(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        # Rooms should have residencies as curators
        residencies = graph.get_residencies("room-arch")
        assert len(residencies) == 1
        assert residencies[0]["role"] == "curator"

    def test_returns_report(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_palace(sample_palace)
        assert isinstance(report, MigrationReport)
        assert report.palaces == 1
        assert report.rooms == 2
        assert report.concepts == 3
        assert report.synapses >= 1


class TestIdempotency:
    """Migration must be idempotent."""

    def test_running_twice_same_result(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        count1 = graph.entity_count()
        migrator.migrate_palace(sample_palace)
        count2 = graph.entity_count()
        assert count1 == count2

    def test_synapse_count_stable(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        syn1 = graph.synapse_count()
        migrator.migrate_palace(sample_palace)
        syn2 = graph.synapse_count()
        assert syn1 == syn2


class TestMigrateAll:
    """Migrate all palaces from a directory."""

    def test_migrate_directory(
        self,
        graph: KnowledgeGraph,
        palace_dir: Path,
    ) -> None:
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_all(str(palace_dir))
        assert report.palaces == 1
        assert graph.entity_count() >= 4  # 1 palace + 2 rooms + concepts

    def test_skips_non_palace_files(
        self,
        graph: KnowledgeGraph,
        palace_dir: Path,
    ) -> None:
        # Write a non-palace file
        (palace_dir / "master_index.json").write_text("{}")
        (palace_dir / "notes.txt").write_text("not a palace")
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_all(str(palace_dir))
        assert report.palaces == 1  # only the real palace


class TestEdgeCases:
    """Edge cases in migration."""

    def test_palace_without_rooms(self, graph: KnowledgeGraph) -> None:
        palace = {
            "id": "empty1",
            "name": "Empty",
            "domain": "test",
            "layout": {"rooms": [], "connections": []},
            "associations": {},
        }
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_palace(palace)
        assert report.rooms == 0
        assert report.concepts == 0

    def test_palace_without_associations(self, graph: KnowledgeGraph) -> None:
        palace = {
            "id": "noassoc",
            "name": "No Assoc",
            "domain": "test",
            "layout": {
                "rooms": [{"id": "r1", "name": "Room 1"}],
                "connections": [],
            },
        }
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_palace(palace)
        assert report.rooms == 1
        assert report.concepts == 0
