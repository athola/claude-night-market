"""Memory Palace plugin for Claude Code.

Provides spatial knowledge organization using memory palace techniques.
"""

from .garden_metrics import compute_garden_metrics
from .palace_manager import MemoryPalaceManager
from .project_palace import (
    ProjectPalaceManager,
    ReviewEntry,
    ReviewSubroom,
    RoomType,
    SortBy,
    capture_pr_review_knowledge,
)
from .session_history import SessionHistoryManager, SessionQuery, SessionRecord

__all__ = [
    "MemoryPalaceManager",
    "ProjectPalaceManager",
    "ReviewEntry",
    "ReviewSubroom",
    "RoomType",
    "SessionHistoryManager",
    "SessionQuery",
    "SessionRecord",
    "SortBy",
    "capture_pr_review_knowledge",
    "compute_garden_metrics",
]
__version__ = "1.6.1"
