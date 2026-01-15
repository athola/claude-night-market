#!/usr/bin/env python3
"""Manage memory palace data structures.

Handle creation, storage, indexing, and retrieval of memory palaces.
Support operations including palace creation, loading, saving, master index
management, and data export/import.
"""

import argparse
import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Constants for quality thresholds
MIN_KEYWORD_LENGTH = 2
LOW_QUALITY_THRESHOLD = 0.3


class MemoryPalaceManager:
    """Manage lifecycle and operations for Memory Palace data."""

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
        # Determine plugin directory (where this file lives)
        self._plugin_dir = Path(__file__).resolve().parents[2]

        if config_path is None:
            # Default to plugin's config directory
            config_path = str(self._plugin_dir / "config" / "settings.json")

        self.config_path = config_path
        self.config = self.load_config()

        # Priority for palaces directory:
        # 1. Explicit override
        # 2. Environment variable
        # 3. Config file setting
        # 4. Plugin's data/palaces directory (NEW default)
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

    def load_config(self) -> dict[str, Any]:
        """Load configuration from the specified file.

        Open and parse the JSON configuration file at `self.config_path`.
        Return an empty config if the file is not found to allow defaults to work.

        Returns:
            Dictionary containing the loaded configuration, or empty dict if not found.

        """
        try:
            with open(self.config_path) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except FileNotFoundError:
            # Return empty config; defaults will be used
            return {}

    def ensure_directories(self) -> None:
        """Validate necessary palace directories exist."""
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
        """Scan the palaces directory and rebuild the master index.

        Iterate through JSON files in the configured palaces directory, extract
        metadata, and aggregate it into `master_index.json`. Include palace
        summaries and global statistics.
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

                except (json.JSONDecodeError, KeyError) as e:
                    # Log skipped files so operators know some files were not indexed
                    print(f"[WARN] Skipped malformed palace file {file_path}: {e}")

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
        """Retrieve the master index or create a default empty one.

        Load the `master_index.json` file and return its content if found.
        Return a new default index structure if the file does not exist to
        ensure a valid structure for dependent operations.

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

    def sync_from_queue(  # noqa: PLR0912
        self,
        queue_path: str,
        auto_create: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Process intake queue entries into palaces.

        Read queued research items and add them to appropriate palaces based on
        domain matching. Optionally create new palaces for unmatched domains.

        Args:
            queue_path: Path to the intake_queue.jsonl file.
            auto_create: If True, create new palaces for unmatched domains.
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dictionary with sync results including items processed, palaces
            updated, and any items that couldn't be matched.

        """
        results: dict[str, Any] = {
            "processed": 0,
            "skipped": 0,
            "palaces_updated": [],
            "palaces_created": [],
            "unmatched": [],
            "dry_run": dry_run,
        }

        if not os.path.exists(queue_path):
            return results

        # Load existing palaces for domain matching
        palace_by_domain: dict[str, dict[str, Any]] = {}
        for palace_summary in self.list_palaces():
            palace = self.load_palace(palace_summary["id"])
            if palace:
                domain = palace.get("domain", "").lower()
                palace_by_domain[domain] = palace

        # Process queue entries
        entries_to_keep = []
        with open(queue_path) as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    entries_to_keep.append(line)
                    continue

                # Extract domain from entry (from query or tags)
                query = entry.get("query", "")
                domain = self._extract_domain(query)

                if domain in palace_by_domain:
                    # Add to existing palace
                    palace = palace_by_domain[domain]
                    if not dry_run:
                        self._add_entry_to_palace(palace, entry)
                        self.save_palace(palace)
                    if palace["id"] not in results["palaces_updated"]:
                        results["palaces_updated"].append(palace["id"])
                    results["processed"] += 1
                elif auto_create and domain:
                    # Create new palace for this domain
                    if not dry_run:
                        new_palace = self.create_palace(
                            name=domain.title(),
                            domain=domain,
                            metaphor="library",
                        )
                        self._add_entry_to_palace(new_palace, entry)
                        self.save_palace(new_palace)
                        palace_by_domain[domain] = new_palace
                    results["palaces_created"].append(domain)
                    results["processed"] += 1
                else:
                    # No matching palace and auto_create is False
                    results["unmatched"].append(query[:50])
                    results["skipped"] += 1
                    entries_to_keep.append(line)

        # Write back unprocessed entries (unless dry run)
        if not dry_run and entries_to_keep:
            with open(queue_path, "w") as f:
                f.write("\n".join(entries_to_keep))
                if entries_to_keep:
                    f.write("\n")
        elif not dry_run and not entries_to_keep:
            # Clear the queue file
            with open(queue_path, "w") as f:
                pass

        return results

    def _extract_domain(self, query: str) -> str:
        """Extract a domain keyword from a query string.

        Simple heuristic: use the most significant noun/keyword.
        """
        # Remove common words and extract domain
        stopwords = {"test", "query", "the", "a", "an", "how", "what", "why"}
        words = query.lower().split()
        for word in words:
            if word not in stopwords and len(word) > MIN_KEYWORD_LENGTH:
                return word
        return ""

    def _add_entry_to_palace(
        self, palace: dict[str, Any], entry: dict[str, Any]
    ) -> None:
        """Add a queue entry as a knowledge item in a palace."""
        entry_id = hashlib.sha256(
            f"{entry.get('query', '')}{entry.get('timestamp', '')}".encode()
        ).hexdigest()[:8]

        knowledge_entry = {
            "id": entry_id,
            "query": entry.get("query", ""),
            "source": "intake_queue",
            "timestamp": entry.get("timestamp", datetime.now().isoformat()),
            "novelty_score": entry.get("intake_payload", {}).get("novelty_score", 0),
        }

        # Add to associations (simple storage for now)
        if "associations" not in palace:
            palace["associations"] = {}
        palace["associations"][entry_id] = knowledge_entry

        # Update metadata
        palace["metadata"]["concept_count"] = len(palace["associations"])

    def prune_check(self, stale_days: int = 90) -> dict[str, Any]:
        """Check palaces for entries needing cleanup or consolidation.

        Identifies:
        - Stale entries (no access in stale_days)
        - Duplicate entries (same query across palaces)
        - Low-quality entries (novelty_score < LOW_QUALITY_THRESHOLD)

        Returns:
            Dictionary with prune recommendations per palace.

        """
        results: dict[str, Any] = {
            "palaces_checked": 0,
            "recommendations": [],
            "total_stale": 0,
            "total_duplicates": 0,
            "total_low_quality": 0,
        }

        # Track queries across palaces for duplicate detection
        query_locations: dict[str, list[tuple[str, str]]] = defaultdict(list)
        cutoff = datetime.now() - __import__("datetime").timedelta(days=stale_days)

        for palace_summary in self.list_palaces():
            palace = self.load_palace(palace_summary["id"])
            if not palace:
                continue

            results["palaces_checked"] += 1
            palace_recs: dict[str, Any] = {
                "palace_id": palace["id"],
                "palace_name": palace["name"],
                "stale": [],
                "low_quality": [],
            }

            for entry_id, entry in palace.get("associations", {}).items():
                query = entry.get("query", "")
                timestamp_str = entry.get("timestamp", "")
                novelty = entry.get("novelty_score", 1.0)

                # Track for duplicates
                if query:
                    query_locations[query].append((palace["id"], entry_id))

                # Check staleness
                try:
                    entry_time = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                    if entry_time < cutoff:
                        palace_recs["stale"].append(entry_id)
                        results["total_stale"] += 1
                except (ValueError, AttributeError):
                    pass

                # Check quality
                if novelty < LOW_QUALITY_THRESHOLD:
                    palace_recs["low_quality"].append(entry_id)
                    results["total_low_quality"] += 1

            if palace_recs["stale"] or palace_recs["low_quality"]:
                results["recommendations"].append(palace_recs)

        # Find duplicates (same query in multiple places)
        duplicates = []
        for query, locations in query_locations.items():
            if len(locations) > 1:
                duplicates.append({"query": query[:50], "locations": locations})
                results["total_duplicates"] += len(locations) - 1

        if duplicates:
            results["duplicates"] = duplicates[:10]  # Limit output

        return results

    def apply_prune(
        self, recommendations: dict[str, Any], actions: list[str]
    ) -> dict[str, int]:
        """Apply prune actions based on recommendations.

        Args:
            recommendations: Output from prune_check()
            actions: List of actions to apply: "stale", "low_quality", "duplicates"

        Returns:
            Dictionary with counts of items removed.

        """
        removed = {"stale": 0, "low_quality": 0, "duplicates": 0}

        for rec in recommendations.get("recommendations", []):
            palace = self.load_palace(rec["palace_id"])
            if not palace:
                continue

            if "stale" in actions:
                for entry_id in rec.get("stale", []):
                    if entry_id in palace.get("associations", {}):
                        del palace["associations"][entry_id]
                        removed["stale"] += 1

            if "low_quality" in actions:
                for entry_id in rec.get("low_quality", []):
                    if entry_id in palace.get("associations", {}):
                        del palace["associations"][entry_id]
                        removed["low_quality"] += 1

            palace["metadata"]["concept_count"] = len(palace.get("associations", {}))
            self.save_palace(palace)

        return removed

    def delete_palace(self, palace_id: str) -> bool:
        """Delete a palace by its ID after creating a final backup.

        Remove the specified palace file from the storage directory. Create a
        backup of the palace before deletion and update the master index after
        successful deletion.

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
