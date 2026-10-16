"""Stuck detection via screenshot diffing.

Compares consecutive screenshot hashes to detect when the UI
hasn't changed between iterations, indicating a failed action
or unresponsive application.
"""

from __future__ import annotations

import hashlib
import warnings
from collections import deque
from dataclasses import InitVar, dataclass
from typing import Any

_DEFAULT_RECOVERY_ACTION = "screenshot"


def _warn_deprecated(name: str) -> None:
    warnings.warn(
        f"{name} has no reader in phantom and will be removed in the next "
        "minor release",
        DeprecationWarning,
        stacklevel=3,
    )


class ScreenshotTracker:
    """Track screenshot similarity across agent loop iterations.

    Uses SHA-256 hashes of the base64 screenshot data to detect
    identical consecutive screenshots without storing full images.
    """

    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self._hash_history: deque[str] = deque(maxlen=max_history)
        self.stuck_count: int = 0
        self._last_hash: str | None = None

    @property
    def hash_history(self) -> deque[str]:
        """Deprecated: recent hashes, kept for callers that read it."""
        _warn_deprecated("ScreenshotTracker.hash_history")
        return self._hash_history

    @property
    def identical_run(self) -> int:
        """Identical screenshots in the current run, the first one included.

        ``stuck_count`` counts repeats, so a run of N frames has N - 1.
        """
        if self._last_hash is None:
            return 0
        return self.stuck_count + 1

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
        self._hash_history.append(current_hash)
        return is_stuck


@dataclass
class StuckPolicy:
    """Policy for handling stuck state in the agent loop."""

    max_stuck: int = 3
    recovery_action: InitVar[str | None] = None

    def __post_init__(self, recovery_action: str | None) -> None:
        if recovery_action is not None:
            _warn_deprecated("StuckPolicy.recovery_action")
        if self.max_stuck < 1:
            msg = f"max_stuck must be at least 1, got {self.max_stuck}"
            raise ValueError(msg)

    def __getattr__(self, name: str) -> Any:
        # Reached only for names the instance lacks. The InitVar default is
        # deleted from the class below, so a read of recovery_action lands
        # here instead of returning that default silently.
        if name == "recovery_action":
            _warn_deprecated("StuckPolicy.recovery_action")
            return _DEFAULT_RECOVERY_ACTION
        msg = f"{type(self).__name__!r} object has no attribute {name!r}"
        raise AttributeError(msg)

    def should_abort(self, stuck_count: int) -> bool:
        """Return True once ``max_stuck`` identical screenshots have been seen.

        ``stuck_count`` counts repeats, so N identical screenshots give N - 1.
        """
        return stuck_count + 1 >= self.max_stuck


delattr(StuckPolicy, "recovery_action")
