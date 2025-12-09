"""Shared utilities for memory-palace hooks."""

from .config import CONFIG_DEFAULTS, get_config, should_process_path
from .deduplication import get_content_hash, is_known, needs_update, update_index
from .safety_checks import SafetyCheckResult, SafetyCheckTimeout, is_safe_content

__all__ = [
    'get_config',
    'CONFIG_DEFAULTS',
    'should_process_path',
    'is_known',
    'get_content_hash',
    'update_index',
    'needs_update',
    'is_safe_content',
    'SafetyCheckResult',
    'SafetyCheckTimeout',
]
