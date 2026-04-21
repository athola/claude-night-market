"""Migrate existing JSON palace data into the knowledge graph.

Reads palace JSON files and creates entities, residencies, and
synapses in the graph. Migration is idempotent: running it twice
produces the same result via upsert semantics.

Also provides ``migrate_sensory_to_computational`` for bulk
conversion of palace JSON files from sensory_encoding to
computational_encoding (Issue #394).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from memory_palace.knowledge_graph import KnowledgeGraph


@dataclass
class MigrationReport:
    """Summary of a migration run."""

    palaces: int = 0
    rooms: int = 0
    concepts: int = 0
    synapses: int = 0
    errors: list[str] = field(default_factory=list)


class PalaceMigrator:
    """Migrate JSON palace files into the knowledge graph."""

    def __init__(self, graph: KnowledgeGraph) -> None:
        """Initialize migrator with target knowledge graph."""
        self._graph = graph

    def migrate_palace(self, palace: dict[str, Any]) -> MigrationReport:
        """Migrate a single palace dict into the graph.

        Creates:
        - A palace entity
        - Room entities with curator residencies
        - Concept entities with patron residencies
        - Synapses from layout connections (strength 0.5)
        """
        report = MigrationReport()
        palace_id = palace.get("id", "")
        palace_name = palace.get("name", "Unknown Palace")

        # Create palace entity
        self._graph.upsert_entity(
            entity_id=palace_id,
            entity_type="palace",
            name=palace_name,
            metadata={
                "domain": palace.get("domain", ""),
                "metaphor": palace.get("metaphor", ""),
            },
        )
        report.palaces = 1

        # Create room entities
        layout = palace.get("layout", {})
        rooms = layout.get("rooms", [])
        for room in rooms:
            room_id = room.get("id", "")
            room_name = room.get("name", room_id)
            if not room_id:
                continue
            self._graph.upsert_entity(
                entity_id=room_id,
                entity_type="room",
                name=room_name,
            )
            self._graph.add_residency(
                entity_id=room_id,
                palace_id=palace_id,
                role="curator",
            )
            report.rooms += 1

        # Create concept entities from associations
        associations = palace.get("associations", {})
        for concept_id, assoc in associations.items():
            label = (
                assoc.get("label", concept_id)
                if isinstance(assoc, dict)
                else str(assoc)
            )
            location = assoc.get("location", "") if isinstance(assoc, dict) else ""
            self._graph.upsert_entity(
                entity_id=concept_id,
                entity_type="concept",
                name=label,
            )
            self._graph.add_residency(
                entity_id=concept_id,
                palace_id=palace_id,
                room_id=location,
                role="patron",
            )
            report.concepts += 1

        # Create synapses from connections
        connections = layout.get("connections", [])
        for conn in connections:
            from_id = conn.get("from", "")
            to_id = conn.get("to", "")
            if not from_id or not to_id:
                continue
            # Check if synapse already exists to maintain idempotency
            existing = self._graph.get_synapses_from(from_id)
            if not any(s["target_id"] == to_id for s in existing):
                self._graph.create_synapse(
                    source_id=from_id,
                    target_id=to_id,
                    strength=0.5,
                )
                report.synapses += 1

        return report

    def migrate_all(self, palaces_dir: str) -> MigrationReport:
        """Migrate all palace JSON files from a directory."""
        total = MigrationReport()
        dir_path = Path(palaces_dir)

        for f in sorted(dir_path.iterdir()):
            if f.suffix != ".json":
                continue
            if f.name in ("master_index.json", "session_index.json"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                total.errors.append(f"{f.name}: {exc}")
                continue
            if "id" not in data or "layout" not in data:
                continue
            report = self.migrate_palace(data)
            total.palaces += report.palaces
            total.rooms += report.rooms
            total.concepts += report.concepts
            total.synapses += report.synapses

        return total


# ---------------------------------------------------------------------------
# Sensory to computational encoding migration (Issue #394)
# ---------------------------------------------------------------------------

_SKIP_FILES = {"master_index.json", "session_index.json"}


def _default_comp_entry() -> dict[str, Any]:
    """Return a default computational encoding entry for one entity."""
    return {
        "centrality": 0.0,
        "in_degree": 0,
        "out_degree": 0,
        "cluster_id": -1,
        "staleness": 0.0,
        "access_count": 0,
        "temporal_validity": {"valid_from": None, "valid_to": None},
    }


def migrate_sensory_to_computational(palaces_dir: Path) -> None:
    """Bulk-convert palace JSON files from sensory to computational encoding.

    For each palace JSON in *palaces_dir*:
    - Remove ``sensory_encoding`` key.
    - Add ``computational_encoding`` keyed by entity ID (from associations).
    - Write the updated file back.
    - Idempotent: already-converted files are re-converted safely.

    Args:
        palaces_dir: Path to the directory containing palace JSON files.

    """
    for palace_file in sorted(palaces_dir.iterdir()):
        if palace_file.suffix != ".json":
            continue
        if palace_file.name in _SKIP_FILES:
            continue

        try:
            data: dict[str, Any] = json.loads(palace_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if "id" not in data:
            continue

        # Remove sensory encoding (if present)
        data.pop("sensory_encoding", None)
        # Remove stale computational encoding (will rebuild fresh)
        data.pop("computational_encoding", None)

        # Build fresh computational encoding from associations
        associations: dict[str, Any] = data.get("associations") or {}
        comp_enc: dict[str, Any] = {}
        for entity_id in associations:
            comp_enc[entity_id] = _default_comp_entry()

        data["computational_encoding"] = comp_enc

        try:
            palace_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            continue
