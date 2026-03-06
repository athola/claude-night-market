"""Memory Palace plugin for Claude Code.

Provides spatial knowledge organization using memory palace techniques.
"""

from .garden_metrics import compute_garden_metrics
from .palace_manager import MemoryPalaceManager
from .session_history import SessionHistoryManager, SessionRecord

__all__ = [
    "MemoryPalaceManager",
    "SessionHistoryManager",
    "SessionRecord",
    "compute_garden_metrics",
]
__version__ = "1.5.7"
