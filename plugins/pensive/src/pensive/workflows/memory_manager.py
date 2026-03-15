"""Memory-aware processing strategy for pensive workflows."""

from __future__ import annotations

from typing import Any

import psutil

# Memory thresholds in MB
LOW_MEMORY_THRESHOLD_MB = 200
DEFAULT_BATCH_SIZE = 100
MIN_BATCH_SIZE = 10


def get_optimal_strategy(file_count: int) -> dict[str, Any]:
    """Get optimal processing strategy based on available memory.

    Args:
        file_count: Number of files to process

    Returns:
        Strategy dict with concurrent flag and batch_size
    """
    try:
        available_mb = psutil.virtual_memory().available / (1024 * 1024)
    except Exception:
        # Default to conservative settings if psutil fails
        available_mb = LOW_MEMORY_THRESHOLD_MB

    # Low memory: disable concurrent processing, reduce batch size
    if available_mb < LOW_MEMORY_THRESHOLD_MB:
        batch_size = min(MIN_BATCH_SIZE, file_count)
        return {
            "concurrent": False,
            "batch_size": batch_size,
            "reason": "low_memory",
        }

    # Normal memory: enable concurrent, use reasonable batch size
    batch_size = min(DEFAULT_BATCH_SIZE, file_count)
    return {
        "concurrent": True,
        "batch_size": batch_size,
        "reason": "normal",
    }
