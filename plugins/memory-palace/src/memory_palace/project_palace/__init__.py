"""Project Palace package (AR-05).

Public API preserved verbatim from the prior 823-line
``project_palace.py`` module so existing imports keep working:

    from memory_palace.project_palace import (
        PROJECT_PALACE_ROOMS,
        REVIEW_CHAMBER_ROOMS,
        ProjectPalaceManager,
        ReviewEntry,
        ReviewSubroom,
        RoomType,
        SortBy,
        capture_pr_review_knowledge,
    )
"""

from __future__ import annotations

from .capture import _classify_finding, capture_pr_review_knowledge
from .entry import ReviewEntry
from .manager import ProjectPalaceManager
from .rooms import (
    PROJECT_PALACE_ROOMS,
    REVIEW_CHAMBER_ROOMS,
    ReviewSubroom,
    RoomType,
    SortBy,
)

__all__ = [
    "PROJECT_PALACE_ROOMS",
    "REVIEW_CHAMBER_ROOMS",
    "ProjectPalaceManager",
    "ReviewEntry",
    "ReviewSubroom",
    "RoomType",
    "SortBy",
    "_classify_finding",
    "capture_pr_review_knowledge",
]
