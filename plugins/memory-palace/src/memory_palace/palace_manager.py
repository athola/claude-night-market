"""Manage memory palace data structures.

Thin facade that composes PalaceRepository, PalaceSearchEngine, and
PalaceMaintenance. Preserves the original public API so all existing
callers work unchanged.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from memory_palace.palace_maintenance import PalaceMaintenance
from memory_palace.palace_repository import PalaceRepository
from memory_palace.palace_search import PalaceSearchEngine


class MemoryPalaceManager:
    """Manage lifecycle and operations for Memory Palace data."""

    def __init__(
        self,
        config_path: str | None = None,
        palaces_dir_override: str | None = None,
    ) -> None:
        """Initialize ``MemoryPalaceManager``.

        Args:
            config_path: Path to the configuration file.
            palaces_dir_override: Optional path to override the palaces directory.

        """
        self._plugin_dir = Path(__file__).resolve().parents[2]

        if config_path is None:
            config_path = str(self._plugin_dir / "config" / "settings.json")

        self.config_path = config_path
        self.config = self.load_config()

        default_palaces_dir = str(self._plugin_dir / "data" / "palaces")
        override_env = os.environ.get("PALACES_DIR")
        chosen_dir = palaces_dir_override or override_env
        if chosen_dir:
            self.palaces_dir = os.path.expanduser(chosen_dir)
        else:
            try:
                self.palaces_dir = os.path.expanduser(
                    self.config.get("storage", {}).get(
                        "palace_directory", default_palaces_dir
                    ),
                )
            except (AttributeError, KeyError):
                self.palaces_dir = default_palaces_dir

        self.index_file = os.path.join(self.palaces_dir, "master_index.json")

        self.ensure_directories()

        self._repo = PalaceRepository(self.palaces_dir)
        self._search = PalaceSearchEngine(self._repo)
        self._maintenance = PalaceMaintenance(self._repo)

    # ------------------------------------------------------------------
    # Config / directory helpers (kept on manager, not in sub-objects)
    # ------------------------------------------------------------------

    def load_config(self) -> dict[str, Any]:
        """Load configuration from the specified file.

        Returns:
            Dictionary containing the loaded configuration, or empty dict.

        """
        try:
            with open(self.config_path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except FileNotFoundError:
            return {}
        except (json.JSONDecodeError, PermissionError, OSError) as e:
            sys.stderr.write(
                f"palace_manager: failed to load config {self.config_path}: {e}\n"
            )
            return {}

    def ensure_directories(self) -> None:
        """Validate necessary palace directories exist."""
        os.makedirs(self.palaces_dir, exist_ok=True)
        os.makedirs(os.path.join(self.palaces_dir, "backups"), exist_ok=True)

    # ------------------------------------------------------------------
    # Palace CRUD — delegate to PalaceRepository
    # ------------------------------------------------------------------

    def create_palace(
        self, name: str, domain: str, metaphor: str = "building"
    ) -> dict[str, Any]:
        """Create a new memory palace."""
        return self._repo.create_palace(name, domain, metaphor)

    def load_palace(self, palace_id: str) -> dict[str, Any] | None:
        """Load a palace from a file by its ID."""
        return self._repo.load_palace(palace_id)

    def save_palace(self, palace: dict[str, Any]) -> None:
        """Save a palace to a file on disk."""
        self._repo.save_palace(palace)

    def create_backup(self, palace_id: str, target_dir: str | None = None) -> None:
        """Create a backup of a palace file."""
        self._repo.create_backup(palace_id, target_dir)

    def delete_palace(self, palace_id: str) -> bool:
        """Delete a palace by its ID after creating a final backup."""
        return self._repo.delete_palace(palace_id)

    # ------------------------------------------------------------------
    # Master index — delegate to PalaceRepository
    # ------------------------------------------------------------------

    def update_master_index(self) -> None:
        """Scan the palaces directory and rebuild the master index."""
        self._repo.update_master_index()

    def get_master_index(self) -> dict[str, Any]:
        """Retrieve the master index or create a default empty one."""
        return self._repo.get_master_index()

    def list_palaces(self) -> list[dict[str, Any]]:
        """Return a list of all palaces."""
        return self._repo.list_palaces()

    # ------------------------------------------------------------------
    # Legacy static helper — kept for subclass compatibility
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_palace_files(
        directory: Path,
    ) -> list[tuple[Path, Any]]:
        """Delegate to PalaceRepository._iter_palace_files.

        Retained so subclasses (e.g. ProjectPalaceManager) that call
        ``self._iter_palace_files(...)`` continue to work without change.
        """
        return PalaceRepository._iter_palace_files(directory)

    # ------------------------------------------------------------------
    # Search — delegate to PalaceSearchEngine
    # ------------------------------------------------------------------

    def search_palaces(
        self, query: str, search_type: str = "semantic"
    ) -> list[dict[str, Any]]:
        """Search across all memory palaces."""
        return self._search.search_palaces(query, search_type)

    # ------------------------------------------------------------------
    # Maintenance — delegate to PalaceMaintenance
    # ------------------------------------------------------------------

    def sync_from_queue(
        self,
        queue_path: str,
        auto_create: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Process intake queue entries into palaces."""
        return self._maintenance.sync_from_queue(queue_path, auto_create, dry_run)

    def prune_check(self, stale_days: int = 90) -> dict[str, Any]:
        """Check palaces for entries needing cleanup or consolidation."""
        return self._maintenance.prune_check(stale_days)

    def apply_prune(
        self, recommendations: dict[str, Any], actions: list[str]
    ) -> dict[str, int]:
        """Apply prune actions based on recommendations."""
        return self._maintenance.apply_prune(recommendations, actions)

    def export_state(self, destination: str) -> str:
        """Export all palaces to a single JSON file."""
        return self._maintenance.export_state(destination)

    def import_state(self, source: str, keep_existing: bool = True) -> dict[str, int]:
        """Import palaces from a JSON file."""
        return self._maintenance.import_state(source, keep_existing)
