"""Knowledge store persistence for the gauntlet plugin."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from gauntlet.models import KnowledgeEntry


class KnowledgeStore:
    """Persists and queries KnowledgeEntry records."""

    def __init__(self, gauntlet_dir: Path) -> None:
        self._dir = gauntlet_dir
        self._knowledge_path = gauntlet_dir / "knowledge.json"
        self._annotations_dir = gauntlet_dir / "annotations"

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self, include_annotations: bool = False) -> list[KnowledgeEntry]:
        """Load entries from knowledge.json.

        If include_annotations is True, also load YAML files from the
        annotations/ subdirectory.
        """
        entries: list[KnowledgeEntry] = []

        if self._knowledge_path.exists():
            raw: Any = json.loads(self._knowledge_path.read_text())
            for item in raw:
                entries.append(KnowledgeEntry.from_dict(item))

        if include_annotations:
            entries.extend(self._load_annotations())

        return entries

    def save(self, entries: list[KnowledgeEntry]) -> None:
        """Write entries to knowledge.json."""
        self._dir.mkdir(parents=True, exist_ok=True)
        payload = [e.to_dict() for e in entries]
        self._knowledge_path.write_text(json.dumps(payload, indent=2))

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        files: list[str] | None = None,
        categories: list[str] | None = None,
        tags: list[str] | None = None,
        min_difficulty: int = 1,
        max_difficulty: int = 5,
    ) -> list[KnowledgeEntry]:
        """Return entries matching all supplied filters.

        Loads with annotations included.
        """
        entries = self.load(include_annotations=True)
        result: list[KnowledgeEntry] = []

        for entry in entries:
            if not (min_difficulty <= entry.difficulty <= max_difficulty):
                continue

            if files is not None:
                matched = any(
                    f == entry.module or f in entry.related_files for f in files
                )
                if not matched:
                    continue

            if categories is not None and entry.category not in categories:
                continue

            if tags is not None:
                if not set(tags).intersection(set(entry.tags)):
                    continue

            result.append(entry)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_annotations(self) -> list[KnowledgeEntry]:
        """Parse YAML annotation files into KnowledgeEntry objects."""
        if not _YAML_AVAILABLE:
            return []

        if not self._annotations_dir.exists():
            return []

        entries: list[KnowledgeEntry] = []
        for yaml_path in sorted(self._annotations_dir.glob("*.yaml")):
            data = yaml.safe_load(yaml_path.read_text())
            if not data:
                continue

            module = data.get("module", "")
            concept = data.get("concept", "")
            entry_id = (
                "curated-"
                + hashlib.sha256(f"{module}:{concept}".encode()).hexdigest()[:12]
            )

            entries.append(
                KnowledgeEntry(
                    id=entry_id,
                    category=data.get("category", "business_logic"),
                    module=module,
                    concept=concept,
                    detail=data.get("detail", ""),
                    difficulty=data.get("difficulty", 1),
                    extracted_at=data.get("extracted_at", ""),
                    source="curated",
                    related_files=data.get("related_files", []),
                    tags=data.get("tags", []),
                    consumers=data.get("consumers", []),
                )
            )

        return entries
