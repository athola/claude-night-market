"""Room-schema enums and dicts for project palaces (AR-05)."""

from __future__ import annotations

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


# Review chamber room types
REVIEW_CHAMBER_ROOMS = {
    "decisions": {
        "description": "Architectural choices documented in PR discussions",
        "icon": "⚖️",
        "retention": "permanent",
    },
    "patterns": {
        "description": "Recurring issues and their solutions",
        "icon": "🔄",
        "retention": "evergreen",
    },
    "standards": {
        "description": "Quality bar examples and coding standards",
        "icon": "📏",
        "retention": "evergreen",
    },
    "lessons": {
        "description": "Post-mortems and learnings from reviews",
        "icon": "💡",
        "retention": "growing",
    },
}

# Project palace room structure
PROJECT_PALACE_ROOMS = {
    "entrance": {
        "description": "README, getting started, onboarding",
        "icon": "🚪",
    },
    "library": {
        "description": "Documentation, ADRs, specifications",
        "icon": "📚",
    },
    "workshop": {
        "description": "Development patterns, tooling, workflows",
        "icon": "🔧",
    },
    "review-chamber": {
        "description": "PR review knowledge",
        "icon": "🏛️",
        "subrooms": REVIEW_CHAMBER_ROOMS,
    },
    "garden": {
        "description": "Evolving knowledge, experiments",
        "icon": "🌱",
    },
}

__all__ = [
    "PROJECT_PALACE_ROOMS",
    "REVIEW_CHAMBER_ROOMS",
    "ReviewSubroom",
    "RoomType",
    "SortBy",
]
