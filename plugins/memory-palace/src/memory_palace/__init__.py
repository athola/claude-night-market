"""Memory Palace plugin for Claude Code.

Provides spatial knowledge organization using memory palace techniques.
"""

from .palace_manager import MemoryPalaceManager
from .garden_metrics import compute_garden_metrics

__all__ = ["MemoryPalaceManager", "compute_garden_metrics"]
__version__ = "2.0.0"
