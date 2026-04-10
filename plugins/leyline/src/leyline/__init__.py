"""Leyline - Infrastructure and pipeline building blocks for Claude Code plugins.

Like ancient ley lines connecting sacred sites, leyline provides the foundational
patterns that connect and power plugin ecosystems.
"""

from leyline.fs import (
    FILE_OVERHEAD_TOKENS,
    SKIP_DIRS,
    SOURCE_EXTENSIONS,
    iter_source_files,
)
from leyline.mecw import (
    MECW_THRESHOLDS,
    MECWMonitor,
    MECWStatus,
    calculate_context_pressure,
    check_mecw_compliance,
)
from leyline.quota_tracker import QuotaConfig, QuotaStatus, QuotaTracker, UsageStats
from leyline.session_store import SessionStore, validate_session_id
from leyline.tokens import (
    FILE_TOKEN_RATIOS,
    estimate_file_tokens,
    estimate_tokens,
)

__version__ = "1.8.4"

__all__ = [
    "FILE_OVERHEAD_TOKENS",
    # File system utilities
    "SKIP_DIRS",
    "SOURCE_EXTENSIONS",
    "iter_source_files",
    # Token estimation
    "FILE_TOKEN_RATIOS",
    # MECW utilities
    "MECW_THRESHOLDS",
    "MECWMonitor",
    "MECWStatus",
    # Quota tracking
    "QuotaConfig",
    "QuotaStatus",
    "QuotaTracker",
    "UsageStats",
    "calculate_context_pressure",
    "check_mecw_compliance",
    "estimate_file_tokens",
    "estimate_tokens",
    # Session store
    "SessionStore",
    "validate_session_id",
]
