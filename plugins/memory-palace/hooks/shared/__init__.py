"""Shared utilities for memory-palace hooks."""

from .config import CONFIG_DEFAULTS, get_config, should_process_path
from .deduplication import get_content_hash, is_known, needs_update, update_index
from .formatting import format_cached_entry_context
from .query_classifier import extract_query_intent, is_evergreen, needs_freshness
from .safety_checks import SafetyCheckResult, SafetyCheckTimeoutError, is_safe_content

__all__ = [
    "CONFIG_DEFAULTS",
    "SafetyCheckResult",
    "SafetyCheckTimeoutError",
    "extract_query_intent",
    "format_cached_entry_context",
    "get_config",
    "get_content_hash",
    "is_evergreen",
    "is_known",
    "is_safe_content",
    "needs_freshness",
    "needs_update",
    "should_process_path",
    "update_index",
]
