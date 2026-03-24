"""Stuck detection via screenshot diffing.

Compares consecutive screenshot hashes to detect when the UI
hasn't changed between iterations, indicating a failed action
or unresponsive application.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass


class ScreenshotTracker:
    """Track screenshot similarity across agent loop iterations.

    Uses SHA-256 hashes of the base64 screenshot data to detect
    identical consecutive screenshots without storing full images.
    """

    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self.hash_history: deque[str] = deque(maxlen=max_history)
        self.stuck_count: int = 0
        self._last_hash: str | None = None

    def record(self, screenshot_b64: str) -> bool:
        """Record a screenshot and return True if stuck.

        Args:
            screenshot_b64: Base64-encoded screenshot data.

        Returns:
            True if this screenshot is identical to the previous one.
        """
        current_hash = hashlib.sha256(screenshot_b64.encode("ascii")).hexdigest()

        is_stuck = self._last_hash is not None and current_hash == self._last_hash

        if is_stuck:
            self.stuck_count += 1
        else:
            self.stuck_count = 0

        self._last_hash = current_hash
        self.hash_history.append(current_hash)
        return is_stuck


@dataclass
class StuckPolicy:
    """Policy for handling stuck state in the agent loop."""

    max_stuck: int = 3
    recovery_action: str = "screenshot"

    def should_abort(self, stuck_count: int) -> bool:
        """Return True if the loop should abort due to being stuck."""
        return stuck_count > self.max_stuck
