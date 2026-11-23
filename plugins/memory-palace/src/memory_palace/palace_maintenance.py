"""Palace maintenance: queue ingestion, pruning, and import/export."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from memory_palace._vendored_leyline_atomic_file import file_lock, write_atomic
from memory_palace._vendored_leyline_session_store import validate_session_id
from memory_palace.palace_repository import PalaceRepository

MIN_KEYWORD_LENGTH = 2
LOW_QUALITY_THRESHOLD = 0.3


def _empty_sync_results(dry_run: bool) -> dict[str, Any]:
    return {
        "processed": 0,
        "skipped": 0,
        "palaces_updated": [],
        "palaces_created": [],
        "unmatched": [],
        "dry_run": dry_run,
    }


class PalaceMaintenance:
    """Handle queue ingestion, pruning, and import/export for palace data."""

    def __init__(self, repository: PalaceRepository) -> None:
        """Initialize maintenance with a palace repository.

        Args:
            repository: A PalaceRepository instance for persisting changes.

        """
        self._repo = repository

    # ------------------------------------------------------------------
    # Queue ingestion
    # ------------------------------------------------------------------

    def sync_from_queue(
        self,
        queue_path: str,
        auto_create: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Process intake queue entries into palaces.

        The intake hook appends under the queue's lock and gives up after a
        short wait, so the lock is held only to read the queue and to
        rewrite it, not while palaces are saved. The rewrite keeps whatever
        the hook appended in between.

        Args:
            queue_path: Path to the intake_queue.jsonl file.
            auto_create: If True, create new palaces for unmatched domains.
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dictionary with sync results.

        """
        if not os.path.exists(queue_path):
            return _empty_sync_results(dry_run)
        with file_lock(queue_path), open(queue_path, encoding="utf-8") as f:
            snapshot = f.read()
        results, entries_to_keep = self._process_queue_lines(
            snapshot.splitlines(), auto_create, dry_run
        )
        if dry_run:
            return results
        with file_lock(queue_path):
            with open(queue_path, encoding="utf-8") as f:
                current = f.read()
            if not current.startswith(snapshot):
                # Another sync rewrote the queue meanwhile. Its rewrite
                # stands; entries processed twice land under the same id.
                sys.stderr.write(
                    "palace_maintenance: queue rewritten during sync; left as is\n"
                )
                return results
            appended = [line for line in current[len(snapshot) :].splitlines() if line]
            kept = entries_to_keep + appended
            # Truncating in place lost the queue, hook appends included, to a
            # crash between the truncate and the write.
            write_atomic(queue_path, "".join(line + "\n" for line in kept), mode=None)
        return results

    def _process_queue_lines(  # noqa: PLR0912 - queue ingestion handles many content types and edge cases
        self,
        lines: list[str],
        auto_create: bool,
        dry_run: bool,
    ) -> tuple[dict[str, Any], list[str]]:
        """Route queue lines into palaces; return results and lines to keep."""
        results = _empty_sync_results(dry_run)

        if not lines:
            return results, []

        palace_by_domain: dict[str, dict[str, Any]] = {}
        for palace_summary in self._repo.list_palaces():
            palace = self._repo.load_palace(palace_summary["id"])
            if palace:
                domain = palace.get("domain", "").lower()
                palace_by_domain[domain] = palace

        entries_to_keep = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                sys.stderr.write(
                    f"palace_maintenance: dropping malformed queue entry: {line[:100]}\n"
                )
                continue

            query = entry.get("query", "")
            domain = self._extract_domain(query)

            if domain in palace_by_domain:
                palace = palace_by_domain[domain]
                if not dry_run:
                    self._add_entry_to_palace(palace, entry)
                    self._repo.save_palace(palace)
                if palace["id"] not in results["palaces_updated"]:
                    results["palaces_updated"].append(palace["id"])
                results["processed"] += 1
            elif auto_create and domain:
                if not dry_run:
                    new_palace = self._repo.create_palace(
                        name=domain.title(),
                        domain=domain,
                        metaphor="library",
                    )
                    self._add_entry_to_palace(new_palace, entry)
                    self._repo.save_palace(new_palace)
                    palace_by_domain[domain] = new_palace
                results["palaces_created"].append(domain)
                results["processed"] += 1
            else:
                results["unmatched"].append(query[:50])
                results["skipped"] += 1
                entries_to_keep.append(line)

        return results, entries_to_keep

    def _extract_domain(self, query: str) -> str:
        """Extract a domain keyword from a query string.

        Simple heuristic: return the first significant noun/keyword.
        """
        stopwords = {"test", "query", "the", "a", "an", "how", "what", "why"}
        words = query.lower().split()
        for word in words:
            if word not in stopwords and len(word) > MIN_KEYWORD_LENGTH:
                return word
        return ""

    def _add_entry_to_palace(
        self, palace: dict[str, Any], entry: dict[str, Any]
    ) -> None:
        """Add a queue entry as a knowledge item inside a palace."""
        entry_id = hashlib.sha256(
            f"{entry.get('query', '')}{entry.get('timestamp', '')}".encode()
        ).hexdigest()[:8]

        knowledge_entry = {
            "id": entry_id,
            "query": entry.get("query", ""),
            "source": "intake_queue",
            "timestamp": entry.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "novelty_score": entry.get("intake_payload", {}).get("novelty_score", 0),
        }

        if "associations" not in palace:
            palace["associations"] = {}
        palace["associations"][entry_id] = knowledge_entry
        palace["metadata"]["concept_count"] = len(palace["associations"])

    # ------------------------------------------------------------------
    # Pruning
    # ------------------------------------------------------------------

    def prune_check(self, stale_days: int = 90) -> dict[str, Any]:
        """Check palaces for entries needing cleanup or consolidation.

        Args:
            stale_days: Entries not accessed in this many days are stale.

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

        query_locations: dict[str, list[tuple[str, str]]] = defaultdict(list)
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)

        for palace_summary in self._repo.list_palaces():
            palace = self._repo.load_palace(palace_summary["id"])
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

                if query:
                    query_locations[query].append((palace["id"], entry_id))

                try:
                    entry_time = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                    entry_utc = (
                        entry_time
                        if entry_time.tzinfo
                        else entry_time.replace(tzinfo=timezone.utc)
                    )
                    if entry_utc < cutoff:
                        palace_recs["stale"].append(entry_id)
                        results["total_stale"] += 1
                except (ValueError, AttributeError) as e:
                    sys.stderr.write(
                        f"palace_maintenance: failed to parse timestamp for entry {entry_id}: {e}\n"
                    )

                if novelty < LOW_QUALITY_THRESHOLD:
                    palace_recs["low_quality"].append(entry_id)
                    results["total_low_quality"] += 1

            if palace_recs["stale"] or palace_recs["low_quality"]:
                results["recommendations"].append(palace_recs)

        duplicates = []
        for query, locations in query_locations.items():
            if len(locations) > 1:
                duplicates.append({"query": query[:50], "locations": locations})
                results["total_duplicates"] += len(locations) - 1

        if duplicates:
            results["duplicates"] = duplicates[:10]

        return results

    def apply_prune(
        self, recommendations: dict[str, Any], actions: list[str]
    ) -> dict[str, int]:
        """Apply prune actions based on recommendations.

        Args:
            recommendations: Output from prune_check().
            actions: List of actions to apply: "stale", "low_quality", "duplicates".

        Returns:
            Dictionary with counts of items removed.

        """
        removed = {"stale": 0, "low_quality": 0, "duplicates": 0}

        for rec in recommendations.get("recommendations", []):
            palace = self._repo.load_palace(rec["palace_id"])
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
            self._repo.save_palace(palace)

        return removed

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------

    def export_state(self, destination: str) -> str:
        """Export all palaces to a single JSON bundle file.

        Args:
            destination: The path to the destination JSON file.

        Returns:
            The path to the exported file.

        """
        palaces: list[dict[str, Any]] = []
        bundle: dict[str, Any] = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "palaces": palaces,
        }
        for _file_path, data in PalaceRepository._iter_palace_files(
            Path(self._repo.palaces_dir)
        ):
            palaces.append(data)

        dest_path = Path(destination)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
        return str(dest_path)

    def import_state(self, source: str, keep_existing: bool = True) -> dict[str, int]:
        """Import palaces from a JSON bundle file.

        Args:
            source: Path to the source JSON file.
            keep_existing: If True, preserve existing palaces with matching IDs.

        Returns:
            Dictionary with counts of imported and skipped palaces.

        """
        with open(source, encoding="utf-8") as f:
            bundle = json.load(f)

        imported = 0
        skipped = 0
        for palace in bundle.get("palaces", []):
            # A bundle is outside input; `../x` wrote outside palaces_dir.
            if not validate_session_id(palace["id"]):
                skipped += 1
                continue
            palace_file = Path(self._repo.palaces_dir) / f"{palace['id']}.json"
            if palace_file.exists() and keep_existing:
                skipped += 1
                continue

            if palace_file.exists():
                self._repo.create_backup(palace["id"])

            with open(palace_file, "w", encoding="utf-8") as f_out:
                json.dump(palace, f_out, indent=2)
            imported += 1

        self._repo.update_master_index()
        return {"imported": imported, "skipped": skipped}
