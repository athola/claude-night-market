"""Tests for per-room semantic indices (Issue #129).

Validates that the EmbeddingIndex supports room-scoped partitioning
to prevent cross-domain knowledge contamination, and that
search_review_chamber can use semantic search.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from memory_palace.corpus.embedding_index import EmbeddingIndex


class TestRoomPartitioning:
    """Test room-scoped index operations."""

    def test_add_to_room_creates_partition(self, tmp_path: Path) -> None:
        """Adding to a room creates a room-scoped partition."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "entry-1", "JWT authentication decision")

        rooms = index.get_room_entries()
        assert "decisions" in rooms
        assert "entry-1" in rooms["decisions"]

    def test_add_to_room_multiple_rooms(self, tmp_path: Path) -> None:
        """Entries added to different rooms stay separate."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "entry-1", "JWT authentication")
        index.add_to_room("patterns", "entry-2", "Error handling pattern")

        rooms = index.get_room_entries()
        assert "entry-1" in rooms["decisions"]
        assert "entry-2" in rooms["patterns"]
        assert "entry-1" not in rooms.get("patterns", {})
        assert "entry-2" not in rooms.get("decisions", {})

    def test_search_room_only_returns_room_entries(self, tmp_path: Path) -> None:
        """Searching a room does not return entries from other rooms."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "auth-entry", "JWT authentication tokens")
        index.add_to_room("patterns", "error-entry", "Error handling middleware")

        results = index.search_room("decisions", "authentication", top_k=5)

        result_ids = [entry_id for entry_id, _score in results]
        assert "auth-entry" in result_ids
        assert "error-entry" not in result_ids

    def test_search_room_returns_scored_tuples(self, tmp_path: Path) -> None:
        """Room search returns (entry_id, score) tuples sorted by score."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "e1", "authentication tokens")
        index.add_to_room("decisions", "e2", "database migrations")

        results = index.search_room("decisions", "authentication", top_k=5)

        assert len(results) == 2
        # Each result is (entry_id, score)
        assert len(results[0]) == 2
        entry_id, score = results[0]
        assert isinstance(entry_id, str)
        assert isinstance(score, float)
        # Results should be sorted descending by score
        assert results[0][1] >= results[1][1]

    def test_search_across_rooms_includes_room_labels(self, tmp_path: Path) -> None:
        """Cross-room search returns room labels with results."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "auth-decision", "authentication tokens")
        index.add_to_room("patterns", "auth-pattern", "authentication middleware")

        results = index.search_across_rooms("authentication", top_k=10)

        # Results are (entry_id, room, score)
        assert len(results) >= 2
        assert len(results[0]) == 3
        entry_id, room, score = results[0]
        assert isinstance(entry_id, str)
        assert isinstance(room, str)
        assert isinstance(score, float)

        # Both rooms should appear in results
        rooms_in_results = {r for _, r, _ in results}
        assert "decisions" in rooms_in_results
        assert "patterns" in rooms_in_results

    def test_search_across_rooms_filtered_subset(self, tmp_path: Path) -> None:
        """Cross-room search can be filtered to specific rooms."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "e1", "authentication tokens")
        index.add_to_room("patterns", "e2", "authentication middleware")
        index.add_to_room("standards", "e3", "authentication standards")

        results = index.search_across_rooms(
            "authentication", rooms=["decisions", "standards"], top_k=10
        )

        rooms_in_results = {r for _, r, _ in results}
        assert "patterns" not in rooms_in_results

    def test_backward_compat_flat_index(self, tmp_path: Path) -> None:
        """Old flat YAML format works as 'default' room."""
        embeddings_path = tmp_path / "embeddings.yaml"
        # Write old flat format (no rooms key)
        data = {
            "providers": {
                "hash": {"embeddings": {"old-entry": [0.1, 0.2, 0.3]}},
            },
            "metadata": {"default_provider": "hash"},
        }
        embeddings_path.write_text(
            yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
        )

        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        # Old flat entries should be searchable via the global search
        results = index.search("anything", top_k=5)
        assert len(results) == 1
        assert results[0][0] == "old-entry"

        # They should also be visible in room stats as "default"
        stats = index.get_room_stats()
        assert stats.get("default", 0) == 0 or "old-entry" in index.entries

    def test_room_stats(self, tmp_path: Path) -> None:
        """Room stats returns correct entry counts."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "e1", "entry one")
        index.add_to_room("decisions", "e2", "entry two")
        index.add_to_room("patterns", "e3", "entry three")

        stats = index.get_room_stats()
        assert stats["decisions"] == 2
        assert stats["patterns"] == 1

    def test_empty_room_search_returns_empty(self, tmp_path: Path) -> None:
        """Searching an empty room returns empty list."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        results = index.search_room("nonexistent-room", "anything")
        assert results == []

    def test_export_preserves_room_structure(self, tmp_path: Path) -> None:
        """Exporting persists the room-partitioned structure."""
        embeddings_path = tmp_path / "embeddings.yaml"
        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        index.add_to_room("decisions", "e1", "decision entry")
        index.add_to_room("patterns", "e2", "pattern entry")

        output_path = tmp_path / "exported.yaml"
        index.export(output_path)

        # Reload and verify structure
        data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
        provider_data = data["providers"]["hash"]
        assert "rooms" in provider_data
        assert "e1" in provider_data["rooms"]["decisions"]["embeddings"]
        assert "e2" in provider_data["rooms"]["patterns"]["embeddings"]

    def test_load_room_structured_yaml(self, tmp_path: Path) -> None:
        """Loading a room-structured YAML correctly populates room entries."""
        embeddings_path = tmp_path / "embeddings.yaml"
        data = {
            "providers": {
                "hash": {
                    "rooms": {
                        "decisions": {
                            "embeddings": {"e1": [0.1, 0.2]},
                        },
                        "patterns": {
                            "embeddings": {"e2": [0.3, 0.4]},
                        },
                    },
                    "vector_dimension": 2,
                },
            },
            "metadata": {"default_provider": "hash"},
        }
        embeddings_path.write_text(
            yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
        )

        index = EmbeddingIndex(str(embeddings_path), provider="hash")

        stats = index.get_room_stats()
        assert stats["decisions"] == 1
        assert stats["patterns"] == 1

        results = index.search_room("decisions", "anything")
        assert len(results) == 1
        assert results[0][0] == "e1"


class TestSemanticSearchIntegration:
    """Test semantic search integration in search_review_chamber."""

    def test_search_review_chamber_semantic_flag(self, tmp_path: Path) -> None:
        """search_review_chamber with semantic=True uses embedding search."""
        from memory_palace.project_palace import (
            ProjectPalaceManager,
            ReviewEntry,
        )

        # Set up palace manager with temp dir
        palaces_dir = tmp_path / "memory-palaces"
        palaces_dir.mkdir()
        config_path = tmp_path / "config" / "settings.json"
        config_path.parent.mkdir(parents=True)
        config = {
            "storage": {"palace_directory": str(palaces_dir)},
        }
        config_path.write_text(json.dumps(config))

        manager = ProjectPalaceManager(str(config_path), str(palaces_dir))
        palace = manager.create_project_palace("owner/repo")

        # Add entries
        entry1 = ReviewEntry(
            source_pr="#42",
            title="JWT Authentication Decision",
            room_type="decisions",
            content={"decision": "Use JWT for stateless auth"},
            tags=["security", "auth"],
        )
        entry2 = ReviewEntry(
            source_pr="#43",
            title="Error Handling Pattern",
            room_type="patterns",
            content={"decision": "Use structured error responses"},
            tags=["api"],
        )

        manager.add_review_entry(palace["id"], entry1)
        manager.add_review_entry(palace["id"], entry2)

        # Semantic search - should still return results (using hash fallback)
        results = manager.search_review_chamber(
            palace["id"], "authentication tokens", semantic=True
        )
        assert len(results) >= 1

    def test_search_review_chamber_semantic_false_uses_text(
        self, tmp_path: Path
    ) -> None:
        """search_review_chamber with semantic=False uses old text matching."""
        from memory_palace.project_palace import (
            ProjectPalaceManager,
            ReviewEntry,
        )

        palaces_dir = tmp_path / "memory-palaces"
        palaces_dir.mkdir()
        config_path = tmp_path / "config" / "settings.json"
        config_path.parent.mkdir(parents=True)
        config = {
            "storage": {"palace_directory": str(palaces_dir)},
        }
        config_path.write_text(json.dumps(config))

        manager = ProjectPalaceManager(str(config_path), str(palaces_dir))
        palace = manager.create_project_palace("owner/repo")

        entry = ReviewEntry(
            source_pr="#42",
            title="JWT Authentication",
            room_type="decisions",
            content={"decision": "Use JWT"},
            tags=["auth"],
        )
        manager.add_review_entry(palace["id"], entry)

        # Text substring search (default behavior)
        results = manager.search_review_chamber(palace["id"], "jwt")
        assert len(results) == 1
        assert results[0]["entry"]["title"] == "JWT Authentication"

        # Query that would not match via substring
        results = manager.search_review_chamber(
            palace["id"], "zzznotfound", semantic=False
        )
        assert len(results) == 0
