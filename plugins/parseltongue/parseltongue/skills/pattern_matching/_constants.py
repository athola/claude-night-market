"""Shared constants for pattern matching."""

from __future__ import annotations

__all__ = [
    "MIN_OBSERVER_METHODS",
    "MIN_FACTORY_RETURN_CLASSES",
    "MIN_REPO_METHODS",
    "_OBSERVER_METHODS",
]

# Constants for pattern detection thresholds
MIN_OBSERVER_METHODS = 2
MIN_FACTORY_RETURN_CLASSES = 2
MIN_REPO_METHODS = 2

_OBSERVER_METHODS = frozenset(
    {
        "subscribe",
        "notify",
        "attach",
        "detach",
        "add_observer",
        "remove_observer",
        "notify_observers",
    }
)
