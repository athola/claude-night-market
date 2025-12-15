"""Memory manager for pensive workflows."""

from __future__ import annotations


class MemoryManager:
    """Manages memory usage during analysis."""

    def __init__(self, limit_mb: int = 100) -> None:
        """Initialize memory manager."""
        self.limit_mb = limit_mb
        self._current_usage = 0

    def check_usage(self) -> int:
        """Check current memory usage in MB."""
        return self._current_usage

    def is_within_limits(self) -> bool:
        """Check if memory usage is within limits."""
        return self._current_usage < self.limit_mb

    def cleanup(self) -> None:
        """Cleanup to reduce memory usage."""
        self._current_usage = 0
