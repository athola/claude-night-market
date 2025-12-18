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

__version__ = "1.0.1"

__all__ = [
    "FILE_OVERHEAD_TOKENS",
    # Token estimation
    "FILE_TOKEN_RATIOS",
    # MECW utilities
    "MECW_THRESHOLDS",
    "MECWMonitor",
    "MECWStatus",
    # Quota tracking
    "QuotaConfig",
    "QuotaTracker",
    "calculate_context_pressure",
    "check_mecw_compliance",
    "estimate_file_tokens",
    "estimate_tokens",
]
