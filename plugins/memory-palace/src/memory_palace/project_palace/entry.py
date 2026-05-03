"""ReviewEntry value object for project palaces (AR-05).

C7 (PR #470 review): the prior shape accepted ``room_type`` as both
``str`` and ``ReviewSubroom`` and never normalised the value, which
made the downstream ``room_type == ReviewSubroom.DECISIONS`` check in
``capture.py`` silently fail when a string ``"decisions"`` was passed.
``__init__`` now coerces every accepted shape into ``ReviewSubroom``
and validates ``importance_score`` against its documented 0..100
bound.

Frozen-dataclass conversion was considered and skipped: ``from_dict``
deserialisation needs to overwrite ``id`` / ``created`` post-hoc, and
the tracked mutation of ``access_count`` and ``last_accessed`` is part
of the public contract. Strict immutability is deferred to a
follow-up redesign that revisits the deserialiser shape.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .rooms import ReviewSubroom

_IMPORTANCE_MIN = 0
_IMPORTANCE_MAX = 100


def _coerce_room_type(value: str | ReviewSubroom) -> ReviewSubroom:
    """Map any accepted room_type shape onto a ``ReviewSubroom`` member."""
    if isinstance(value, ReviewSubroom):
        return value
    # Try the enum value (e.g. "decisions") first, then the upper-case name.
    try:
        return ReviewSubroom(value)
    except ValueError:
        pass
    try:
        return ReviewSubroom[value.upper()]
    except KeyError as exc:
        msg = f"unknown room_type {value!r}; expected a ReviewSubroom"
        raise ValueError(msg) from exc


class ReviewEntry:
    """Represents a single PR review knowledge entry."""

    def __init__(  # noqa: PLR0913 - review entries have many structured metadata fields
        self,
        source_pr: str,
        title: str,
        room_type: str | ReviewSubroom,
        content: dict[str, Any],
        participants: list[str] | None = None,
        related_rooms: list[str] | None = None,
        tags: list[str] | None = None,
        importance_score: int | None = None,
    ) -> None:
        """Initialize a review entry.

        Args:
            source_pr: Reference to source PR (e.g., "#42 - Add authentication")
            title: Short title for the entry
            room_type: One of decisions, patterns, standards, lessons.
                Accepts either the ``ReviewSubroom`` enum or the string
                value/name; both forms are normalised to the enum so
                identity comparisons work for downstream callers.
            content: Structured content of the entry
            participants: List of PR participants
            related_rooms: Links to related palace rooms
            tags: Searchable tags
            importance_score: Explicit importance (``_IMPORTANCE_MIN``..
                ``_IMPORTANCE_MAX``). Defaults to 70 for decisions,
                40 for other room types. ``ValueError`` on out-of-range.

        """
        now = datetime.now(timezone.utc).isoformat()
        self.id = uuid.uuid4().hex[:12]
        self.source_pr = source_pr
        self.title = title
        self.room_type = _coerce_room_type(room_type)
        self.content = content
        self.participants = participants or []
        self.related_rooms = related_rooms or []
        self.tags = tags or []
        self.created = now
        self.last_accessed = now
        self.access_count = 0

        if importance_score is None:
            default = 70 if self.room_type == ReviewSubroom.DECISIONS else 40
            self.importance_score = default
        else:
            if not _IMPORTANCE_MIN <= importance_score <= _IMPORTANCE_MAX:
                msg = (
                    f"importance_score must be in "
                    f"[{_IMPORTANCE_MIN}, {_IMPORTANCE_MAX}], "
                    f"got {importance_score}"
                )
                raise ValueError(msg)
            self.importance_score = importance_score

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "source_pr": self.source_pr,
            "title": self.title,
            "room_type": self.room_type,
            "content": self.content,
            "participants": self.participants,
            "related_rooms": self.related_rooms,
            "tags": self.tags,
            "created": self.created,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "importance_score": self.importance_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewEntry:
        """Deserialize from dictionary."""
        entry = cls(
            source_pr=data["source_pr"],
            title=data["title"],
            room_type=data["room_type"],
            content=data["content"],
            participants=data.get("participants", []),
            related_rooms=data.get("related_rooms", []),
            tags=data.get("tags", []),
            importance_score=data.get("importance_score"),
        )
        entry.id = data["id"]
        entry.created = data["created"]
        entry.last_accessed = data.get("last_accessed", entry.created)
        entry.access_count = data.get("access_count", 0)
        return entry

    def to_markdown(self) -> str:
        """Generate markdown representation for human readability."""
        lines = [
            "---",
            f'source_pr: "{self.source_pr}"',
            f"date: {self.created[:10]}",
            f"participants: {self.participants}",
            f"palace_location: review-chamber/{self.room_type}",
            f"related_rooms: {self.related_rooms}",
            f"tags: {self.tags}",
            f"importance_score: {self.importance_score}",
            "---",
            "",
            f"## {self.title}",
            "",
        ]

        # Add content sections
        if "decision" in self.content:
            lines.extend(["### Decision", self.content["decision"], ""])

        if "context" in self.content:
            lines.extend(["### Context (from PR discussion)"])
            for ctx in self.content["context"]:
                lines.append(f"- {ctx}")
            lines.append("")

        if "captured_knowledge" in self.content:
            lines.extend(["### Captured Knowledge"])
            for key, value in self.content["captured_knowledge"].items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        if "connected_concepts" in self.content:
            lines.extend(["### Connected Concepts"])
            for concept in self.content["connected_concepts"]:
                lines.append(f"- [[{concept}]]")
            lines.append("")

        return "\n".join(lines)


__all__ = ["ReviewEntry"]
