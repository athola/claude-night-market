"""Room-schema enums and typed registry for project palaces (AR-05).

S8 (PR #470 review, issue #484): the room registries are typed via
enum keys (``RoomType`` for top-level rooms, ``ReviewSubroom`` for
review-chamber subrooms) and a frozen :class:`RoomMetadata`
dataclass. Replacing the prior ``dict[str, dict[str, Any]]`` shape
removes string-key drift (mistyped names, missing ``retention``
on a subroom) at construction time instead of at runtime.

Both enums inherit from ``str``, so ``REVIEW_CHAMBER_ROOMS["decisions"]``
and ``REVIEW_CHAMBER_ROOMS[ReviewSubroom.DECISIONS]`` resolve to the
same value. Existing call sites that index by string continue to work;
new sites should index by enum for static-checker coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RoomType(str, Enum):
    """Room types in a project palace."""

    ENTRANCE = "entrance"
    LIBRARY = "library"
    WORKSHOP = "workshop"
    REVIEW_CHAMBER = "review-chamber"
    GARDEN = "garden"


class ReviewSubroom(str, Enum):
    """Subroom types within the review-chamber."""

    DECISIONS = "decisions"
    PATTERNS = "patterns"
    STANDARDS = "standards"
    LESSONS = "lessons"


class SortBy(str, Enum):
    """Sort order for search results."""

    RECENCY = "recency"
    IMPORTANCE = "importance"


@dataclass(frozen=True, slots=True)
class RoomMetadata:
    """Static metadata for a palace room.

    Attributes:
        description: Human-readable summary shown in palace listings.
        icon: Single-glyph identifier rendered next to the room name.
        retention: Lifecycle policy (``"permanent"`` / ``"evergreen"``
            / ``"growing"``). Only meaningful for review-chamber
            subrooms; ``None`` on top-level rooms.
        subrooms: For ``RoomType.REVIEW_CHAMBER`` only, the registry
            of nested subrooms. ``None`` for every other room.

    """

    description: str
    icon: str
    retention: str | None = None
    subrooms: dict[ReviewSubroom, RoomMetadata] | None = None


# Review chamber room types (subrooms of the review-chamber).
REVIEW_CHAMBER_ROOMS: dict[ReviewSubroom, RoomMetadata] = {
    ReviewSubroom.DECISIONS: RoomMetadata(
        description="Architectural choices documented in PR discussions",
        icon="⚖️",
        retention="permanent",
    ),
    ReviewSubroom.PATTERNS: RoomMetadata(
        description="Recurring issues and their solutions",
        icon="🔄",
        retention="evergreen",
    ),
    ReviewSubroom.STANDARDS: RoomMetadata(
        description="Quality bar examples and coding standards",
        icon="📏",
        retention="evergreen",
    ),
    ReviewSubroom.LESSONS: RoomMetadata(
        description="Post-mortems and learnings from reviews",
        icon="💡",
        retention="growing",
    ),
}


# Project palace room structure (top-level rooms).
PROJECT_PALACE_ROOMS: dict[RoomType, RoomMetadata] = {
    RoomType.ENTRANCE: RoomMetadata(
        description="README, getting started, onboarding",
        icon="🚪",
    ),
    RoomType.LIBRARY: RoomMetadata(
        description="Documentation, ADRs, specifications",
        icon="📚",
    ),
    RoomType.WORKSHOP: RoomMetadata(
        description="Development patterns, tooling, workflows",
        icon="🔧",
    ),
    RoomType.REVIEW_CHAMBER: RoomMetadata(
        description="PR review knowledge",
        icon="🏛️",
        subrooms=REVIEW_CHAMBER_ROOMS,
    ),
    RoomType.GARDEN: RoomMetadata(
        description="Evolving knowledge, experiments",
        icon="🌱",
    ),
}

__all__ = [
    "PROJECT_PALACE_ROOMS",
    "REVIEW_CHAMBER_ROOMS",
    "ReviewSubroom",
    "RoomMetadata",
    "RoomType",
    "SortBy",
]
