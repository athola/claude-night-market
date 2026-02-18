"""Hybrid source lineage tracking.

Implements full and simple lineage tracking based on source importance.
Full lineage is used for important sources (research papers, documentation)
while simple lineage is used for standard sources to save storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SourceType(Enum):
    """Types of knowledge sources."""

    WEB_ARTICLE = "web_article"
    DOCUMENTATION = "documentation"
    RESEARCH_PAPER = "research_paper"
    CODE_EXAMPLE = "code_example"
    USER_INPUT = "user_input"
    DERIVED = "derived"  # Derived from other entries


@dataclass
class SourceReference:
    """Reference to a knowledge source."""

    source_id: str
    source_type: SourceType
    url: str | None = None
    title: str | None = None
    author: str | None = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 1.0  # Confidence in source accuracy


@dataclass
class FullLineage:
    """Full lineage tracking for important sources.

    Includes complete derivation chain, transformations applied,
    and validation history.
    """

    entry_id: str
    primary_source: SourceReference
    derived_from: list[str] = field(default_factory=list)
    transformations: list[str] = field(default_factory=list)
    validation_chain: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SimpleLineage:
    """Simple lineage for standard sources.

    Minimal tracking to save storage while maintaining
    basic provenance information.
    """

    entry_id: str
    source_type: SourceType
    source_url: str | None
    retrieved_at: datetime


class SourceLineageManager:
    """Manages hybrid source lineage with full and simple tracking.

    Uses full lineage for important sources (research papers, documentation,
    high-importance entries) and simple lineage for standard sources.
    """

    FULL_LINEAGE_CRITERIA: dict[str, Any] = {
        "importance_threshold": 0.7,
        "source_types": [SourceType.RESEARCH_PAPER, SourceType.DOCUMENTATION],
    }

    def __init__(self) -> None:
        """Initialize the source lineage manager."""
        self._lineages: dict[str, FullLineage | SimpleLineage] = {}

    def should_use_full_lineage(
        self,
        source_type: SourceType,
        importance_score: float,
    ) -> bool:
        """Determine if full lineage should be used.

        Args:
            source_type: Type of the source
            importance_score: Importance score of the entry

        Returns:
            True if full lineage should be used

        """
        # Always use full lineage for important source types
        if source_type in self.FULL_LINEAGE_CRITERIA["source_types"]:
            return True

        # Use full lineage for high-importance entries
        if importance_score >= self.FULL_LINEAGE_CRITERIA["importance_threshold"]:
            return True

        return False

    def create_lineage(
        self,
        entry_id: str,
        source: SourceReference,
        importance_score: float,
    ) -> FullLineage | SimpleLineage:
        """Create appropriate lineage based on criteria.

        Args:
            entry_id: ID of the knowledge entry
            source: Source reference
            importance_score: Importance score of the entry

        Returns:
            FullLineage or SimpleLineage instance

        """
        if self.should_use_full_lineage(source.source_type, importance_score):
            return FullLineage(
                entry_id=entry_id,
                primary_source=source,
            )
        else:
            return SimpleLineage(
                entry_id=entry_id,
                source_type=source.source_type,
                source_url=source.url,
                retrieved_at=source.retrieved_at,
            )

    def register_lineage(self, lineage: FullLineage | SimpleLineage) -> None:
        """Register lineage for an entry.

        Args:
            lineage: The lineage to register

        """
        self._lineages[lineage.entry_id] = lineage

    def get_lineage(self, entry_id: str) -> FullLineage | SimpleLineage | None:
        """Get lineage for an entry.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            Lineage or None if not found

        """
        return self._lineages.get(entry_id)

    def get_lineage_type(self, entry_id: str) -> str | None:
        """Get the type of lineage for an entry.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            "full", "simple", or None

        """
        lineage = self._lineages.get(entry_id)
        if lineage is None:
            return None
        if isinstance(lineage, FullLineage):
            return "full"
        return "simple"

    def add_derivation(
        self,
        entry_id: str,
        derived_from: str,
        transformation: str | None = None,
    ) -> None:
        """Add derivation information to full lineage.

        Args:
            entry_id: ID of the knowledge entry
            derived_from: ID of source entry
            transformation: Description of transformation applied

        """
        lineage = self._lineages.get(entry_id)
        if not isinstance(lineage, FullLineage):
            return

        if derived_from not in lineage.derived_from:
            lineage.derived_from.append(derived_from)

        if transformation and transformation not in lineage.transformations:
            lineage.transformations.append(transformation)

    def add_validation(
        self,
        entry_id: str,
        validator: str,
        status: str,
        notes: str | None = None,
    ) -> None:
        """Add validation record to full lineage.

        Args:
            entry_id: ID of the knowledge entry
            validator: ID of validator (user or system)
            status: Validation status
            notes: Optional validation notes

        """
        lineage = self._lineages.get(entry_id)
        if not isinstance(lineage, FullLineage):
            return

        validation_record = {
            "validator": validator,
            "date": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }
        if notes:
            validation_record["notes"] = notes

        lineage.validation_chain.append(validation_record)

    def upgrade_to_full_lineage(
        self,
        entry_id: str,
        new_importance: float | None = None,
    ) -> bool:
        """Upgrade simple lineage to full lineage.

        Args:
            entry_id: ID of the knowledge entry
            new_importance: New importance score triggering upgrade

        Returns:
            True if upgraded, False if already full or not found

        """
        lineage = self._lineages.get(entry_id)
        if lineage is None:
            return False
        if isinstance(lineage, FullLineage):
            return False

        # Create full lineage from simple
        source = SourceReference(
            source_id=f"upgraded-{entry_id}",
            source_type=lineage.source_type,
            url=lineage.source_url,
            retrieved_at=lineage.retrieved_at,
        )
        full_lineage = FullLineage(
            entry_id=entry_id,
            primary_source=source,
        )
        self._lineages[entry_id] = full_lineage
        return True

    def get_entries_by_source_url(self, url: str) -> list[str]:
        """Find entries from the same source URL.

        Args:
            url: The source URL to search for

        Returns:
            List of entry IDs from that source

        """
        entry_ids = []
        for entry_id, lineage in self._lineages.items():
            if isinstance(lineage, FullLineage):
                if lineage.primary_source.url == url:
                    entry_ids.append(entry_id)
            elif isinstance(lineage, SimpleLineage):
                if lineage.source_url == url:
                    entry_ids.append(entry_id)
        return entry_ids

    def get_derivation_tree(self, entry_id: str) -> list[str]:
        """Build complete derivation tree for an entry.

        Recursively finds all source entries.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            List of all source entry IDs in derivation chain

        """
        tree: list[str] = []
        visited: set[str] = set()

        def traverse(eid: str) -> None:
            if eid in visited:
                return
            visited.add(eid)

            lineage = self._lineages.get(eid)
            if not isinstance(lineage, FullLineage):
                return

            for derived_id in lineage.derived_from:
                if derived_id not in tree:
                    tree.append(derived_id)
                traverse(derived_id)

        traverse(entry_id)
        return tree

    def get_propagated_confidence(self, entry_id: str) -> float:
        """Calculate propagated confidence through derivation chain.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            Propagated confidence (product of confidence chain)

        """
        lineage = self._lineages.get(entry_id)
        if lineage is None:
            return 1.0

        if isinstance(lineage, SimpleLineage):
            return 1.0

        # Start with primary source confidence
        confidence = lineage.primary_source.confidence

        # Multiply through derivation chain
        for derived_id in lineage.derived_from:
            derived_confidence = self.get_propagated_confidence(derived_id)
            confidence *= derived_confidence

        return confidence

    def export_lineage(self) -> dict[str, dict[str, Any]]:
        """Export all lineage as serializable data.

        Returns:
            Dict of entry_id -> lineage data

        """
        exported: dict[str, dict[str, Any]] = {}

        for entry_id, lineage in self._lineages.items():
            if isinstance(lineage, FullLineage):
                exported[entry_id] = {
                    "type": "full",
                    "entry_id": lineage.entry_id,
                    "primary_source": {
                        "source_id": lineage.primary_source.source_id,
                        "source_type": lineage.primary_source.source_type.value,
                        "url": lineage.primary_source.url,
                        "title": lineage.primary_source.title,
                        "author": lineage.primary_source.author,
                        "retrieved_at": lineage.primary_source.retrieved_at.isoformat(),
                        "confidence": lineage.primary_source.confidence,
                    },
                    "derived_from": lineage.derived_from,
                    "transformations": lineage.transformations,
                    "validation_chain": lineage.validation_chain,
                }
            else:
                exported[entry_id] = {
                    "type": "simple",
                    "entry_id": lineage.entry_id,
                    "source_type": lineage.source_type.value,
                    "source_url": lineage.source_url,
                    "retrieved_at": lineage.retrieved_at.isoformat(),
                }

        return exported

    def import_lineage(self, lineage_data: dict[str, dict[str, Any]]) -> None:
        """Import lineage from serializable data.

        Args:
            lineage_data: Dict of entry_id -> lineage data

        """
        for entry_id, data in lineage_data.items():
            if data["type"] == "full":
                source_data = data["primary_source"]
                source = SourceReference(
                    source_id=source_data["source_id"],
                    source_type=SourceType(source_data["source_type"]),
                    url=source_data.get("url"),
                    title=source_data.get("title"),
                    author=source_data.get("author"),
                    retrieved_at=datetime.fromisoformat(source_data["retrieved_at"]),
                    confidence=source_data.get("confidence", 1.0),
                )
                full_lineage = FullLineage(
                    entry_id=entry_id,
                    primary_source=source,
                    derived_from=data.get("derived_from", []),
                    transformations=data.get("transformations", []),
                    validation_chain=data.get("validation_chain", []),
                )
                self._lineages[entry_id] = full_lineage
            else:
                simple_lineage = SimpleLineage(
                    entry_id=entry_id,
                    source_type=SourceType(data["source_type"]),
                    source_url=data.get("source_url"),
                    retrieved_at=datetime.fromisoformat(data["retrieved_at"]),
                )
                self._lineages[entry_id] = simple_lineage
