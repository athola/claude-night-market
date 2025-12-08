"""Shared utilities for memory-palace hooks."""

from .config import get_config, CONFIG_DEFAULTS, should_process_path
from .deduplication import is_known, get_content_hash, update_index, needs_update
from .safety_checks import is_safe_content, SafetyCheckResult, SafetyCheckTimeout

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
