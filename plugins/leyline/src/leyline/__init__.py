"""Leyline - Infrastructure and pipeline building blocks for Claude Code plugins.

Like ancient ley lines connecting sacred sites, leyline provides the foundational
patterns that connect and power plugin ecosystems.
"""

from leyline.mecw import (
    MECW_THRESHOLDS,
    MECWMonitor,
    MECWStatus,
    calculate_context_pressure,
    check_mecw_compliance,
)
from leyline.quota_tracker import QuotaConfig, QuotaTracker
from leyline.tokens import (
    FILE_OVERHEAD_TOKENS,
    FILE_TOKEN_RATIOS,
    estimate_file_tokens,
    estimate_tokens,
)

__version__ = "1.0.0"

__all__ = [
    # Token estimation
    "FILE_TOKEN_RATIOS",
    "FILE_OVERHEAD_TOKENS",
    "estimate_tokens",
    "estimate_file_tokens",
    # Quota tracking
    "QuotaConfig",
    "QuotaTracker",
    # MECW utilities
    "MECW_THRESHOLDS",
    "MECWMonitor",
    "MECWStatus",
    "calculate_context_pressure",
    "check_mecw_compliance",
]
