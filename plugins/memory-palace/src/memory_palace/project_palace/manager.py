#!/usr/bin/env python3
# mypy: disable-error-code="index,operator,var-annotated,no-any-return"
"""ProjectPalaceManager extends MemoryPalaceManager with PR review rooms (AR-05)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..palace_manager import MemoryPalaceManager
from .entry import ReviewEntry
from .rooms import (
    PROJECT_PALACE_ROOMS,
    REVIEW_CHAMBER_ROOMS,
    ReviewSubroom,
    SortBy,
)


class ProjectPalaceManager(MemoryPalaceManager):
    """Manages project-scoped palaces with PR review room support.

    Extends MemoryPalaceManager to support project-as-palace metaphor
    where each repository becomes a palace with dedicated rooms for
    different knowledge types.
    """

    def __init__(
        self,
        config_path: str | None = None,
        palaces_dir_override: str | None = None,
    ) -> None:
        """Initialize ProjectPalaceManager.

        Args:
            config_path: Path to configuration file
            palaces_dir_override: Override directory for palace storage

        """
        super().__init__(config_path, palaces_dir_override)
        self.project_palaces_dir = os.path.join(self.palaces_dir, "projects")
        os.makedirs(self.project_palaces_dir, exist_ok=True)
        self._cached_embedding_index: Any = None

    def create_project_palace(
        self,
        repo_name: str,
        repo_url: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new project palace for a repository.

        Args:
            repo_name: Repository name (e.g., "owner/repo")
            repo_url: Optional GitHub URL
            description: Optional project description

        Returns:
            Dictionary representing the new project palace

        """
        palace_id = hashlib.sha256(
            f"{repo_name}{datetime.now(timezone.utc)}".encode()
        ).hexdigest()[:8]

        # Create room structure
        rooms = {}
        for room_name, room_config in PROJECT_PALACE_ROOMS.items():
            room_data: dict[str, Any] = {
                "description": room_config["description"],
                "icon": room_config["icon"],
                "entries": [],
                "created": datetime.now(timezone.utc).isoformat(),
            }

            # Add subrooms for review-chamber
            if "subrooms" in room_config:
                room_data["subrooms"] = {}
                for subroom_name, subroom_config in room_config["subrooms"].items():
                    room_data["subrooms"][subroom_name] = {
                        "description": subroom_config["description"],
                        "icon": subroom_config["icon"],
                        "retention": subroom_config["retention"],
                        "entries": [],
                    }

            rooms[room_name] = room_data

        project_palace = {
            "id": palace_id,
            "type": "project",
            "name": repo_name,
            "repo_url": repo_url,
            "description": description,
            "created": datetime.now(timezone.utc).isoformat(),
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "rooms": rooms,
            "metadata": {
                "total_entries": 0,
                "review_entries": 0,
                "pr_count": 0,
                "contributors": [],
            },
            "connections": [],  # Links to other project palaces
        }

        # Save to project palaces directory
        palace_file = os.path.join(self.project_palaces_dir, f"{palace_id}.json")
        with open(palace_file, "w", encoding="utf-8") as f:
            json.dump(project_palace, f, indent=2)

        self._update_project_index()
        return project_palace

    def load_project_palace(self, palace_id: str) -> dict[str, Any] | None:
        """Load a project palace by ID."""
        palace_file = os.path.join(self.project_palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            with open(palace_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def find_project_palace(self, repo_name: str) -> dict[str, Any] | None:
        """Find a project palace by repository name."""
        for _file_path, palace in self._iter_palace_files(
            Path(self.project_palaces_dir)
        ):
            if palace.get("name") == repo_name:
                return palace
        return None

    def get_or_create_project_palace(
        self,
        repo_name: str,
        repo_url: str | None = None,
    ) -> dict[str, Any]:
        """Get existing project palace or create new one."""
        palace = self.find_project_palace(repo_name)
        if palace:
            return palace
        return self.create_project_palace(repo_name, repo_url)

    def save_project_palace(self, palace: dict[str, Any]) -> None:
        """Persist ``palace`` to disk, refresh ``last_modified``, and back it up.

        Side effects: invalidates the embedding index cache and rewrites the
        project index.
        """
        palace["last_modified"] = datetime.now(timezone.utc).isoformat()
        palace_file = os.path.join(self.project_palaces_dir, f"{palace['id']}.json")

        # Invalidate cached embedding index since palace data changed
        self._cached_embedding_index = None

        # Create backup
        self.create_backup(palace["id"], self.project_palaces_dir)

        with open(palace_file, "w", encoding="utf-8") as f:
            json.dump(palace, f, indent=2)

        self._update_project_index()

    def add_review_entry(
        self,
        palace_id: str,
        entry: ReviewEntry,
    ) -> bool:
        """Add a review entry to a project palace's review chamber."""
        palace = self.load_project_palace(palace_id)
        if not palace:
            return False

        # Validate room type
        if entry.room_type not in REVIEW_CHAMBER_ROOMS:
            return False

        # Add to appropriate subroom
        review_chamber = palace["rooms"]["review-chamber"]
        subroom = review_chamber["subrooms"][entry.room_type]
        subroom["entries"].append(entry.to_dict())

        # Update metadata
        palace["metadata"]["total_entries"] += 1
        palace["metadata"]["review_entries"] += 1

        # Track contributors
        for participant in entry.participants:
            if participant not in palace["metadata"]["contributors"]:
                palace["metadata"]["contributors"].append(participant)

        self.save_project_palace(palace)
        return True

    def search_review_chamber(  # noqa: PLR0913 - search needs all filter and sort parameters
        self,
        palace_id: str,
        query: str,
        room_type: str | ReviewSubroom | None = None,
        tags: list[str] | None = None,
        semantic: bool = False,
        sort_by: str | SortBy = SortBy.RECENCY,
    ) -> list[dict[str, Any]]:
        """Search the review chamber of a project palace."""
        palace = self.load_project_palace(palace_id)
        if not palace:
            return []

        review_chamber = palace["rooms"]["review-chamber"]

        if semantic:
            results = self._search_review_chamber_semantic(
                palace, review_chamber, query, room_type, tags, sort_by
            )
        else:
            results = self._search_review_chamber_text(
                palace, review_chamber, query, room_type, tags, sort_by
            )

        if sort_by == SortBy.IMPORTANCE:
            results.sort(
                key=lambda r: r["entry"].get("importance_score", 0),
                reverse=True,
            )

        return results

    def _search_review_chamber_text(  # noqa: PLR0913 - mirrors search_review_chamber parameters
        self,
        palace: dict[str, Any],
        review_chamber: dict[str, Any],
        query: str,
        room_type: str | ReviewSubroom | None,
        tags: list[str] | None,
        sort_by: str | SortBy = SortBy.RECENCY,
    ) -> list[dict[str, Any]]:
        """Text substring search (original behavior)."""
        results = []
        query_lower = query.lower()

        for subroom_name, subroom in review_chamber.get("subrooms", {}).items():
            if room_type and subroom_name != room_type:
                continue

            for entry_data in subroom.get("entries", []):
                entry_text = json.dumps(entry_data).lower()
                if query_lower not in entry_text:
                    continue

                if tags:
                    entry_tags = entry_data.get("tags", [])
                    if not any(tag in entry_tags for tag in tags):
                        continue

                results.append(
                    {
                        "room": f"review-chamber/{subroom_name}",
                        "entry": entry_data,
                        "palace_id": palace["id"],
                        "palace_name": palace["name"],
                    }
                )

        return results

    def _search_review_chamber_semantic(  # noqa: PLR0913 - mirrors search_review_chamber parameters
        self,
        palace: dict[str, Any],
        review_chamber: dict[str, Any],
        query: str,
        room_type: str | ReviewSubroom | None,
        tags: list[str] | None,
        sort_by: str | SortBy = SortBy.RECENCY,
    ) -> list[dict[str, Any]]:
        """Embedding-based semantic search across review chamber rooms."""
        from ..corpus.embedding_index import (  # noqa: PLC0415 - lazy import to avoid faiss dependency at module load
            EmbeddingIndex,
        )

        # Cache the index to avoid rebuilding on every call
        if self._cached_embedding_index is None:
            embeddings_path = os.path.join(
                self.project_palaces_dir, f"{palace['id']}_embeddings.yaml"
            )
            self._cached_embedding_index = EmbeddingIndex(
                embeddings_path, provider="hash"
            )

        index = self._cached_embedding_index

        # Map entry IDs to their data and subroom for later retrieval
        entry_map: dict[str, tuple[str, dict[str, Any]]] = {}

        for subroom_name, subroom in review_chamber.get("subrooms", {}).items():
            if room_type and subroom_name != room_type:
                continue

            for entry_data in subroom.get("entries", []):
                entry_id = entry_data.get("id", "")
                if not entry_id:
                    continue

                # Pre-filter by tags if specified
                if tags:
                    entry_tags = entry_data.get("tags", [])
                    if not any(tag in entry_tags for tag in tags):
                        continue

                # Build searchable text from entry content
                text_parts = [
                    entry_data.get("title", ""),
                    json.dumps(entry_data.get("content", {})),
                ]
                text = " ".join(text_parts)

                index.add_to_room(subroom_name, entry_id, text)
                entry_map[entry_id] = (subroom_name, entry_data)

        # Search across the rooms we indexed
        target_rooms = [room_type] if room_type else None
        scored = index.search_across_rooms(query, rooms=target_rooms, top_k=50)

        results = []
        for entry_id, _room_name, score in scored:
            if entry_id not in entry_map:
                continue
            subroom_name, entry_data = entry_map[entry_id]
            results.append(
                {
                    "room": f"review-chamber/{subroom_name}",
                    "entry": entry_data,
                    "palace_id": palace["id"],
                    "palace_name": palace["name"],
                    "score": score,
                }
            )

        return results

    def get_review_chamber_stats(self, palace_id: str) -> dict[str, Any]:
        """Get statistics for a project palace's review chamber."""
        palace = self.load_project_palace(palace_id)
        if not palace:
            return {}

        tag_counts: Counter[str] = Counter()
        stats: dict[str, Any] = {
            "total_entries": 0,
            "by_room": {},
            "top_entries": [],
            "top_tags": tag_counts,
            "contributors": palace["metadata"].get("contributors", []),
        }

        review_chamber = palace["rooms"]["review-chamber"]
        all_entries = []

        for subroom_name, subroom in review_chamber.get("subrooms", {}).items():
            entries = subroom.get("entries", [])
            stats["by_room"][subroom_name] = len(entries)
            stats["total_entries"] += len(entries)

            for entry in entries:
                all_entries.append(entry)
                tag_counts.update(entry.get("tags", []))

        # Sort by importance (top entries) instead of recency
        all_entries.sort(
            key=lambda x: x.get("importance_score", 40),
            reverse=True,
        )
        stats["top_entries"] = all_entries[:5]
        stats["top_tags"] = dict(tag_counts.most_common(10))

        return stats

    def list_project_palaces(self) -> list[dict[str, Any]]:
        """List all project palaces."""
        palaces = []
        for _file_path, palace in self._iter_palace_files(
            Path(self.project_palaces_dir)
        ):
            with contextlib.suppress(KeyError):
                palaces.append(
                    {
                        "id": palace["id"],
                        "name": palace["name"],
                        "repo_url": palace.get("repo_url"),
                        "created": palace["created"],
                        "last_modified": palace["last_modified"],
                        "total_entries": palace["metadata"]["total_entries"],
                        "review_entries": palace["metadata"]["review_entries"],
                    }
                )
        return palaces

    def _update_project_index(self) -> None:
        """Update the project palaces index."""
        index: dict[str, Any] = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "projects": [],
            "stats": {
                "total_projects": 0,
                "total_review_entries": 0,
            },
        }

        for _file_path, palace in self._iter_palace_files(
            Path(self.project_palaces_dir)
        ):
            try:
                index["projects"].append(
                    {
                        "id": palace["id"],
                        "name": palace["name"],
                        "last_modified": palace["last_modified"],
                    }
                )
                index["stats"]["total_projects"] += 1
                index["stats"]["total_review_entries"] += palace["metadata"].get(
                    "review_entries", 0
                )
            except KeyError as e:
                sys.stderr.write(
                    f"project_palace: skipping malformed palace file: {e}\n"
                )

        index_file = os.path.join(self.project_palaces_dir, "project_index.json")
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)


__all__ = ["ProjectPalaceManager"]
