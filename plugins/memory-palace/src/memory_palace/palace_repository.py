"""Palace CRUD operations, master index management, and backup handling."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Computational encoding helpers (Issue #394)
# ---------------------------------------------------------------------------

_DEFAULT_TEMPORAL_VALIDITY: dict[str, Any] = {"valid_from": None, "valid_to": None}


def _default_computational_entry() -> dict[str, Any]:
    """Return a default computational encoding entry for one entity."""
    return {
        "centrality": 0.0,
        "in_degree": 0,
        "out_degree": 0,
        "cluster_id": -1,
        "staleness": 0.0,
        "access_count": 0,
        "temporal_validity": dict(_DEFAULT_TEMPORAL_VALIDITY),
    }


def _build_computational_encoding(
    palace: dict[str, Any],
) -> dict[str, Any]:
    """Build computational_encoding keyed by entity ID.

    Populates defaults for every entity in ``associations``.
    Graph-derived metrics (centrality, cluster_id) remain at
    defaults unless a graph DB is available; callers that have
    access to PalaceGraphAnalyzer can enrich them separately.
    """
    associations: dict[str, Any] = palace.get("associations") or {}
    encoding: dict[str, Any] = {}
    for entity_id in associations:
        encoding[entity_id] = _default_computational_entry()
    return encoding


def _build_on_disk_palace(palace: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *palace* prepared for disk serialization.

    Replaces ``sensory_encoding`` with ``computational_encoding``.
    The caller's dict is not mutated.
    """
    on_disk = {k: v for k, v in palace.items() if k != "sensory_encoding"}
    on_disk["computational_encoding"] = _build_computational_encoding(palace)
    return on_disk


class PalaceRepository:
    """Manage palace files on disk: create, load, save, delete, and index."""

    def __init__(self, palaces_dir: str) -> None:
        """Initialize repository with the palaces storage directory.

        Args:
            palaces_dir: Path to the directory that stores palace JSON files.

        """
        self.palaces_dir = palaces_dir
        self.index_file = os.path.join(palaces_dir, "master_index.json")

    # ------------------------------------------------------------------
    # Palace CRUD
    # ------------------------------------------------------------------

    def create_palace(
        self, name: str, domain: str, metaphor: str = "building"
    ) -> dict[str, Any]:
        """Create a new memory palace and persist it to disk.

        Args:
            name: The name of the palace.
            domain: The domain of the palace.
            metaphor: The architectural metaphor for the palace.

        Returns:
            A dictionary representing the new palace.

        """
        palace_id = hashlib.sha256(
            f"{name}{domain}{datetime.now(timezone.utc)}".encode()
        ).hexdigest()[:8]

        palace: dict[str, Any] = {
            "id": palace_id,
            "name": name,
            "domain": domain,
            "metaphor": metaphor,
            "created": datetime.now(timezone.utc).isoformat(),
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "layout": {
                "districts": [],
                "buildings": [],
                "rooms": [],
                "connections": [],
            },
            "associations": {},
            "sensory_encoding": {},
            "metadata": {
                "concept_count": 0,
                "complexity_level": "basic",
                "access_patterns": [],
            },
        }

        palace_file = os.path.join(self.palaces_dir, f"{palace_id}.json")
        with open(palace_file, "w", encoding="utf-8") as f:
            json.dump(palace, f, indent=2)

        self.update_master_index()
        return palace

    def load_palace(self, palace_id: str) -> dict[str, Any] | None:
        """Load a palace from disk by its ID.

        Args:
            palace_id: The ID of the palace to load.

        Returns:
            A dictionary representing the palace, or None if not found.

        """
        palace_file = os.path.join(self.palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            try:
                with open(palace_file, encoding="utf-8") as f:
                    palace_data: dict[str, Any] = json.load(f)
                    return palace_data
            except json.JSONDecodeError as e:
                sys.stderr.write(
                    f"palace_repository: corrupt palace file {palace_file}: {e}\n"
                )
                return None
            except OSError as e:
                sys.stderr.write(
                    f"palace_repository: failed to read {palace_file}: {e}\n"
                )
                return None
        return None

    def save_palace(self, palace: dict[str, Any]) -> None:
        """Persist a palace to disk, creating a backup first.

        Replaces ``sensory_encoding`` with ``computational_encoding``
        in the persisted data. The in-memory dict is not mutated —
        a shallow copy is written so callers preserve the original.

        Args:
            palace: The palace to save.

        """
        palace["last_modified"] = datetime.now(timezone.utc).isoformat()
        palace_file = os.path.join(self.palaces_dir, f"{palace['id']}.json")

        self.create_backup(palace["id"])

        # Build the on-disk representation with computational encoding
        on_disk = _build_on_disk_palace(palace)

        try:
            with open(palace_file, "w", encoding="utf-8") as f:
                json.dump(on_disk, f, indent=2)
        except OSError as exc:
            sys.stderr.write(
                f"palace_repository: failed to write {palace_file}: {exc}\n"
            )
            raise

        self.update_master_index()

    def delete_palace(self, palace_id: str) -> bool:
        """Delete a palace by its ID after creating a final backup.

        Args:
            palace_id: The ID of the palace to delete.

        Returns:
            True if deleted successfully, False if the file did not exist.

        """
        palace_file = os.path.join(self.palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            self.create_backup(palace_id)
            os.remove(palace_file)
            self.update_master_index()
            return True
        return False

    # ------------------------------------------------------------------
    # Backup management
    # ------------------------------------------------------------------

    def create_backup(self, palace_id: str, target_dir: str | None = None) -> None:
        """Create a timestamped backup of a palace file.

        Args:
            palace_id: The ID of the palace to back up.
            target_dir: Directory containing the palace file. Defaults to
                ``self.palaces_dir``.

        """
        base_dir = target_dir or self.palaces_dir
        palace_file = os.path.join(base_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            backup_dir = os.path.join(base_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{palace_id}_{timestamp}.json")

            with (
                open(palace_file, encoding="utf-8") as src,
                open(backup_file, "w", encoding="utf-8") as dst,
            ):
                dst.write(src.read())

    # ------------------------------------------------------------------
    # Master index
    # ------------------------------------------------------------------

    def update_master_index(self) -> None:
        """Scan the palaces directory and rebuild master_index.json."""
        domains: dict[str, int] = {}
        global_stats: dict[str, Any] = {
            "total_palaces": 0,
            "total_concepts": 0,
            "total_locations": 0,
            "domains": domains,
        }
        index: dict[str, Any] = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "palaces": [],
            "global_stats": global_stats,
        }

        for _file_path, palace in self._iter_palace_files(Path(self.palaces_dir)):
            try:
                palace_summary = {
                    "id": palace["id"],
                    "name": palace["name"],
                    "domain": palace["domain"],
                    "metaphor": palace["metaphor"],
                    "created": palace["created"],
                    "last_modified": palace["last_modified"],
                    "concept_count": palace["metadata"]["concept_count"],
                }

                palaces: list[dict[str, Any]] = index["palaces"]
                palaces.append(palace_summary)
                global_stats["total_palaces"] += 1
                global_stats["total_concepts"] += palace["metadata"]["concept_count"]
                global_stats["total_locations"] += len(
                    palace.get("layout", {}).get("rooms", [])
                )

                domain = palace["domain"]
                domains[domain] = domains.get(domain, 0) + 1

            except KeyError as e:
                print(f"[WARN] Skipped malformed palace file: {e}")

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def get_master_index(self) -> dict[str, Any]:
        """Load and return the master index, or a default empty index.

        Returns:
            Dictionary representing the master index of all palaces.

        """
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                return data
            except (json.JSONDecodeError, OSError) as exc:
                sys.stderr.write(f"palace_repository: corrupt master index: {exc}\n")
                # Fall through to return default
        return {
            "palaces": [],
            "global_stats": {
                "total_palaces": 0,
                "total_concepts": 0,
                "total_locations": 0,
                "domains": {},
            },
        }

    def list_palaces(self) -> list[dict[str, Any]]:
        """Return a list of all palace summaries from the master index."""
        palaces = self.get_master_index().get("palaces", [])
        return list(palaces)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_palace_files(
        directory: Path,
    ) -> list[tuple[Path, dict[str, Any]]]:
        """Load all non-index JSON files from *directory*.

        Skip ``master_index.json`` and ``project_index.json``.
        Files that fail to parse are silently skipped.
        """
        results: list[tuple[Path, dict[str, Any]]] = []
        skip = {"master_index.json", "project_index.json"}
        for file_path in directory.glob("*.json"):
            if file_path.name in skip:
                continue
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                results.append((file_path, data))
            except (json.JSONDecodeError, KeyError):
                pass
        return results
