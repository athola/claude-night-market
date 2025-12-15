#!/usr/bin/env python3
"""Core utilities for managing memory palace data structures.

Implements the `MemoryPalaceManager` class, handling creation, storage, indexing,
and retrieval of memory palaces. Supports operations including palace creation,
loading, saving, master index management for quick lookups, and data export/import.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoryPalaceManager:
    """Manages the lifecycle and operations for Memory Palace data.

    Includes creating, loading, saving, and deleting individual palaces,
    alongside maintaining a master index for efficient searching and overview.
    Abstracts underlying storage mechanisms and provides a consistent interface
    for interacting with memory palace data.
    """

    def __init__(
        self,
        config_path: str | None = None,
        palaces_dir_override: str | None = None,
    ) -> None:
        """Initialize `MemoryPalaceManager`.

        Args:
            config_path: Path to the configuration file.
            palaces_dir_override: Optional path to override the palaces directory.

        """
        if config_path is None:
            config_path = os.path.expanduser("~/memory-palace/config/settings.json")

        self.config_path = config_path
        self.config = self.load_config()

        # Use default palace directory if config doesn't exist or doesn't have storage section
        default_palaces_dir = "~/memory-palaces"
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
                self.palaces_dir = os.path.expanduser(default_palaces_dir)

        self.index_file = os.path.join(self.palaces_dir, "master_index.json")

        self.ensure_directories()

    def load_config(self) -> dict[str, Any]:
        """Load configuration from the specified file.

        Attempt to open and parse the JSON configuration file at `self.config_path`.
        If the file is not found, print an error message to stderr and exit the program.

        Returns:
            Dictionary containing the loaded configuration.

        Raises:
            SystemExit: If the configuration file is not found.

        """
        try:
            with open(self.config_path) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except FileNotFoundError:
            sys.exit(1)

    def ensure_directories(self) -> None:
        """Ensure necessary palace directories exist."""
        os.makedirs(self.palaces_dir, exist_ok=True)
        os.makedirs(os.path.join(self.palaces_dir, "backups"), exist_ok=True)

    def create_palace(
        self, name: str, domain: str, metaphor: str = "building"
    ) -> dict[str, Any]:
        """Create a new memory palace.

        Args:
            name: The name of the palace.
            domain: The domain of the palace.
            metaphor: The architectural metaphor for the palace.

        Returns:
            A dictionary representing the new palace.

        """
        palace_id = hashlib.sha256(
            f"{name}{domain}{datetime.now()}".encode()
        ).hexdigest()[:8]

        palace = {
            "id": palace_id,
            "name": name,
            "domain": domain,
            "metaphor": metaphor,
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
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
        with open(palace_file, "w") as f:
            json.dump(palace, f, indent=2)

        self.update_master_index()
        return palace

    def load_palace(self, palace_id: str) -> dict[str, Any] | None:
        """Load a palace from a file by its ID.

        Args:
            palace_id: The ID of the palace to load.

        Returns:
            A dictionary representing the palace, or None if not found.

        """
        palace_file = os.path.join(self.palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            with open(palace_file) as f:
                palace_data: dict[str, Any] = json.load(f)
                return palace_data
        return None

    def save_palace(self, palace: dict[str, Any]) -> None:
        """Save a palace to a file on disk.

        Args:
            palace: The palace to save.

        """
        palace["last_modified"] = datetime.now().isoformat()
        palace_file = os.path.join(self.palaces_dir, f"{palace['id']}.json")

        # Create backup before saving
        self.create_backup(palace["id"])

        with open(palace_file, "w") as f:
            json.dump(palace, f, indent=2)

        self.update_master_index()

    def create_backup(self, palace_id: str) -> None:
        """Create a backup of a palace file.

        Args:
            palace_id: The ID of the palace to back up.

        """
        palace_file = os.path.join(self.palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            backup_dir = os.path.join(self.palaces_dir, "backups")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{palace_id}_{timestamp}.json")

            with open(palace_file) as src, open(backup_file, "w") as dst:
                dst.write(src.read())

    def update_master_index(self) -> None:
        """Scan the palaces directory; rebuild the master index.

        Iterate through JSON files in the configured palaces directory (excluding
        the master index), extract key metadata from each palace file, and
        aggregate it into a central `master_index.json` file. The index includes
        palace summaries and global statistics: total palaces, total concepts,
        and concepts per domain. This index facilitates quick lookups and system
        status reporting without loading individual palace files. Report errors
        encountered during indexing of individual palace files as warnings.
        """
        domains: dict[str, int] = {}
        global_stats: dict[str, Any] = {
            "total_palaces": 0,
            "total_concepts": 0,
            "domains": domains,
        }
        index: dict[str, Any] = {
            "last_updated": datetime.now().isoformat(),
            "palaces": [],
            "global_stats": global_stats,
        }

        for file_path in Path(self.palaces_dir).glob("*.json"):
            if file_path.name != "master_index.json":
                try:
                    with open(file_path) as f:
                        palace = json.load(f)

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
                    global_stats["total_concepts"] += palace["metadata"][
                        "concept_count"
                    ]

                    domain = palace["domain"]
                    domains[domain] = domains.get(domain, 0) + 1

                except (json.JSONDecodeError, KeyError):
                    pass

        with open(self.index_file, "w") as f:
            json.dump(index, f, indent=2)

    def search_palaces(
        self, query: str, search_type: str = "semantic"
    ) -> list[dict[str, Any]]:
        """Search across all memory palaces.

        Args:
            query: The search query.
            search_type: The type of search to perform.

        Returns:
            A list of search results.

        """
        results = []

        for palace_summary in self.get_master_index()["palaces"]:
            palace = self.load_palace(palace_summary["id"])
            if palace:
                matches = self._search_in_palace(palace, query, search_type)
                if matches:
                    results.append(
                        {
                            "palace_id": palace["id"],
                            "palace_name": palace["name"],
                            "matches": matches,
                        },
                    )

        return results

    def _search_in_palace(
        self,
        palace: dict[str, Any],
        query: str,
        search_type: str,
    ) -> list[dict[str, Any]]:
        """Search for a query within a single palace.

        Args:
            palace: The palace to search in.
            query: The search query.
            search_type: The type of search to perform.

        Returns:
            A list of matches found in the palace.

        """
        matches = []
        query_lower = query.lower()

        # Search in associations
        for concept_id, association in palace.get("associations", {}).items():
            if self._matches_query(association, query_lower, search_type):
                matches.append(
                    {
                        "type": "association",
                        "concept_id": concept_id,
                        "data": association,
                    },
                )

        # Search in sensory encoding
        for location_id, sensory_data in palace.get("sensory_encoding", {}).items():
            if self._matches_query(sensory_data, query_lower, search_type):
                matches.append(
                    {
                        "type": "sensory",
                        "location_id": location_id,
                        "data": sensory_data,
                    },
                )

        return matches

    def export_state(self, destination: str) -> str:
        """Export all palaces to a single JSON file.

        Args:
            destination: The path to the destination JSON file.

        Returns:
            The path to the exported file.

        """
        palaces: list[dict[str, Any]] = []
        bundle: dict[str, Any] = {
            "exported_at": datetime.now().isoformat(),
            "palaces": palaces,
        }
        for file_path in Path(self.palaces_dir).glob("*.json"):
            if file_path.name == "master_index.json":
                continue
            with open(file_path) as f:
                palaces.append(json.load(f))

        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w") as f:
            json.dump(bundle, f, indent=2)
        return str(dest_path)

    def import_state(self, source: str, keep_existing: bool = True) -> dict[str, int]:
        """Import palaces from a JSON file.

        Args:
            source: Path to the source JSON file.
            keep_existing: If `True`, preserve existing palaces. If `False`,
                overwrite palaces with matching IDs.

        Returns:
            Dictionary with the count of imported and skipped palaces.

        """
        with open(source) as f:
            bundle = json.load(f)

        imported = 0
        skipped = 0
        for palace in bundle.get("palaces", []):
            palace_file = Path(self.palaces_dir) / f"{palace['id']}.json"
            if palace_file.exists() and keep_existing:
                skipped += 1
                continue

            # backup existing before overwrite
            if palace_file.exists():
                self.create_backup(palace["id"])

            with open(palace_file, "w") as f_out:
                json.dump(palace, f_out, indent=2)
            imported += 1

        self.update_master_index()
        return {"imported": imported, "skipped": skipped}

    def _matches_query(
        self, data: dict[str, Any], query: str, search_type: str
    ) -> bool:
        """Check if the given data matches the query.

        Args:
            data: The data to check.
            query: The search query.
            search_type: The type of search to perform.

        Returns:
            True if the data matches the query, False otherwise.

        """
        if search_type == "semantic":
            # Simple text matching - in a real implementation, use embeddings
            text_content = json.dumps(data).lower()
            return query in text_content
        if search_type == "exact":
            return query == json.dumps(data).lower()
        if search_type == "fuzzy":
            # Simple fuzzy matching - implement Levenshtein or similar for real use
            text_content = json.dumps(data).lower()
            return any(word in text_content for word in query.split())

        return False

    def get_master_index(self) -> dict[str, Any]:
        """Retrieve the master index; create a default empty one if it does not exist.

        Attempt to load the `master_index.json` file. If found, return its content.
        If the file does not exist, return a new default index structure. This
        ensures operations relying on the master index always have a valid structure.

        Returns:
            Dictionary representing the master index of all palaces, or a
            default empty index if the file is not found.

        """
        if os.path.exists(self.index_file):
            with open(self.index_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        # Return a default empty index if the file doesn't exist
        return {
            "palaces": [],
            "global_stats": {"total_palaces": 0, "total_concepts": 0, "domains": {}},
        }

    def list_palaces(self) -> list[dict[str, Any]]:
        """Return a list of all palaces."""
        palaces = self.get_master_index().get("palaces", [])
        return list(palaces)

    def delete_palace(self, palace_id: str) -> bool:
        """Delete a palace by its ID after creating a final backup.

        Remove the specified palace file from the storage directory. Create a
        backup of the palace before deletion to prevent accidental data loss.
        After successful deletion, update the master index to reflect the change.

        Args:
            palace_id: The ID of the palace to delete.

        Returns:
            `True` if the palace was successfully deleted, `False` otherwise (e.g., if
            the palace file did not exist).

        """
        palace_file = os.path.join(self.palaces_dir, f"{palace_id}.json")
        if os.path.exists(palace_file):
            # Create final backup before deletion
            self.create_backup(palace_id)
            os.remove(palace_file)
            self.update_master_index()
            return True
        return False


def main() -> None:  # noqa: PLR0912,PLR0915
    """Parse command-line arguments and run the corresponding command."""
    parser = argparse.ArgumentParser(description="Memory Palace Manager")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--palaces-dir", help="Override palaces directory")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create palace
    create_parser = subparsers.add_parser("create", help="Create a new palace")
    create_parser.add_argument("name", help="Palace name")
    create_parser.add_argument("domain", help="Palace domain")
    create_parser.add_argument(
        "--metaphor", default="building", help="Architectural metaphor"
    )

    # List palaces
    subparsers.add_parser("list", help="List all palaces")

    # Search
    search_parser = subparsers.add_parser("search", help="Search palaces")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--type", default="semantic", choices=["semantic", "exact", "fuzzy"]
    )

    # Delete palace
    delete_parser = subparsers.add_parser("delete", help="Delete a palace")
    delete_parser.add_argument("palace_id", help="Palace ID to delete")

    # Status
    subparsers.add_parser("status", help="Show system status")

    # Export/Import
    export_parser = subparsers.add_parser(
        "export", help="Export all palaces to a bundle"
    )
    export_parser.add_argument(
        "--destination", required=True, help="Destination JSON path"
    )

    import_parser = subparsers.add_parser("import", help="Import palaces from a bundle")
    import_parser.add_argument("--source", required=True, help="Source bundle JSON")
    import_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing palaces with same IDs",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = MemoryPalaceManager(args.config, args.palaces_dir)

    if args.command == "create":
        manager.create_palace(args.name, args.domain, args.metaphor)

    elif args.command == "list":
        palaces = manager.list_palaces()
        if palaces:
            for _palace in palaces:
                pass
        else:
            pass

    elif args.command == "search":
        results = manager.search_palaces(args.query, args.type)
        if results:
            for result in results:
                for match in result["matches"]:
                    match.get("concept_id", match.get("location_id", "unknown"))
        else:
            pass

    elif args.command == "delete":
        if manager.delete_palace(args.palace_id):
            pass
        else:
            pass

    elif args.command == "status":
        index = manager.get_master_index()
        stats = index["global_stats"]
        for _domain, _count in stats["domains"].items():
            pass

    elif args.command == "export":
        manager.export_state(args.destination)

    elif args.command == "import":
        stats = manager.import_state(args.source, keep_existing=not args.overwrite)


if __name__ == "__main__":
    main()
