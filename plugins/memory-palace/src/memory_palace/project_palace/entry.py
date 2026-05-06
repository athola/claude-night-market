"""ReviewEntry value object for project palaces (AR-05).

C7 (PR #470 review, issue #485): :class:`ReviewEntry` is a frozen
``@dataclass`` so identity / state cannot drift after construction.
``from_dict`` is a regular constructor call (no post-hoc attribute
mutation), and read-tracking goes through :meth:`with_access`, which
returns a new instance with the bumped counter and refreshed
timestamp instead of mutating in place.

The mid-PR fix (commit a7b8f460) already coerced ``room_type`` to a
:class:`ReviewSubroom` member at construction and validated
``importance_score`` against its 0..100 bound; this module preserves
that behaviour through ``__post_init__``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from .rooms import ReviewSubroom

_IMPORTANCE_MIN = 0
_IMPORTANCE_MAX = 100
# Sentinel so ``None`` (= "use default for this room type") and an
# explicit 0 score remain distinguishable. The dataclass cannot use
# ``None`` because the public field type stays ``int``.
_IMPORTANCE_UNSET = -1


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass(frozen=True)
class ReviewEntry:
    """A single PR review knowledge entry.

    All fields are constructor parameters so the class is a pure
    value object: ``ReviewEntry(...)`` and ``ReviewEntry.from_dict(d)``
    follow the same code path. Mutation is forbidden; tracked state
    (read counters, timestamps) flows through :meth:`with_access`,
    which returns a new instance.
    """

    source_pr: str
    title: str
    # Accepts ``str`` or ``ReviewSubroom`` from callers; ``__post_init__``
    # coerces the stored value to a ``ReviewSubroom`` member so downstream
    # reads see the canonical enum.
    room_type: str | ReviewSubroom
    content: dict[str, Any]
    participants: list[str] = field(default_factory=list)
    related_rooms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    importance_score: int = _IMPORTANCE_UNSET
    id: str = field(default_factory=_new_id)
    created: str = field(default_factory=_now_iso)
    last_accessed: str = ""
    access_count: int = 0

    def __post_init__(self) -> None:
        """Coerce ``room_type`` to enum and validate ``importance_score``.

        Runs at the end of dataclass-generated ``__init__``.
        """
        # frozen=True forbids ``self.x = y``; use object.__setattr__
        # to canonicalise fields exactly once at construction time.
        coerced_room = _coerce_room_type(self.room_type)
        object.__setattr__(self, "room_type", coerced_room)

        if self.importance_score == _IMPORTANCE_UNSET:
            default = 70 if coerced_room == ReviewSubroom.DECISIONS else 40
            object.__setattr__(self, "importance_score", default)
        elif not _IMPORTANCE_MIN <= self.importance_score <= _IMPORTANCE_MAX:
            msg = (
                f"importance_score must be in "
                f"[{_IMPORTANCE_MIN}, {_IMPORTANCE_MAX}], "
                f"got {self.importance_score}"
            )
            raise ValueError(msg)

        if not self.last_accessed:
            object.__setattr__(self, "last_accessed", self.created)

    def with_access(self) -> ReviewEntry:
        """Return a new entry with the read counter bumped.

        The original instance is unchanged. ``last_accessed`` is set
        to ``datetime.now()`` (UTC, ISO format), and ``access_count``
        is incremented by one. All other fields are preserved.
        """
        return replace(
            self,
            access_count=self.access_count + 1,
            last_accessed=_now_iso(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "source_pr": self.source_pr,
            "title": self.title,
            "room_type": self.room_type,
            "content": self.content,
            "participants": list(self.participants),
            "related_rooms": list(self.related_rooms),
            "tags": list(self.tags),
            "created": self.created,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "importance_score": self.importance_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewEntry:
        """Deserialize from dictionary via the constructor.

        All identity / tracking fields (``id``, ``created``,
        ``last_accessed``, ``access_count``) are passed as
        constructor arguments so the resulting instance can stay
        frozen.
        """
        return cls(
            source_pr=data["source_pr"],
            title=data["title"],
            room_type=data["room_type"],
            content=data["content"],
            participants=list(data.get("participants", [])),
            related_rooms=list(data.get("related_rooms", [])),
            tags=list(data.get("tags", [])),
            importance_score=data.get(
                "importance_score",
                _IMPORTANCE_UNSET,
            ),
            id=data["id"],
            created=data["created"],
            last_accessed=data.get("last_accessed", data["created"]),
            access_count=data.get("access_count", 0),
        )

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
