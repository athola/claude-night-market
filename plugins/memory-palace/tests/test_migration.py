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
        """The palace itself becomes a typed node, not just a container for its rooms."""
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        palace = graph.get_entity("abc12345")
        assert palace is not None
        assert palace["entity_type"] == "palace"
        assert palace["name"] == "Test Palace"

    def test_creates_synapses_from_connections(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        """Declared connections become synapses pointing at the named target."""
        migrator = PalaceMigrator(graph)
        migrator.migrate_palace(sample_palace)
        # Connections between rooms become synapses
        synapses = graph.get_synapses_from("room-arch")
        assert len(synapses) >= 1
        assert synapses[0]["target_id"] == "room-data"
        assert synapses[0]["strength"] == pytest.approx(0.5)

    def test_returns_report(
        self, graph: KnowledgeGraph, sample_palace: dict[str, Any]
    ) -> None:
        """The migration reports what it moved rather than returning silently."""
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_palace(sample_palace)
        assert isinstance(report, MigrationReport)
        assert report.palaces == 1
        assert report.rooms == 2
        assert report.concepts == 3
        assert report.synapses >= 1


class TestIdempotency:
    """Migration must be idempotent."""


class TestMigrateAll:
    """Migrate all palaces from a directory."""

    def test_skips_non_palace_files(
        self,
        graph: KnowledgeGraph,
        palace_dir: Path,
    ) -> None:
        # Write a non-palace file
        """Files that are not palaces are passed over rather than half-parsed."""
        (palace_dir / "master_index.json").write_text("{}")
        (palace_dir / "notes.txt").write_text("not a palace")
        migrator = PalaceMigrator(graph)
        report = migrator.migrate_all(str(palace_dir))
        assert report.palaces == 1  # only the real palace


class TestEdgeCases:
    """Edge cases in migration."""

    def test_palace_without_rooms(self, graph: KnowledgeGraph) -> None:
        """A palace with no rooms migrates to zero rooms rather than failing."""
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
        """A room with no concepts migrates to zero concepts rather than failing."""
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
