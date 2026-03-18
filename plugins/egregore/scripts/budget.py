"""Egregore token budget tracking.

Tracks token usage within budget windows and manages cooldown
periods after rate limits.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass
class Budget:
    """Token budget state for an egregore session window."""

    window_type: str = "5h"
    window_started_at: str | None = None
    estimated_tokens_used: int = 0
    session_count: int = 0
    last_rate_limit_at: str | None = None
    cooldown_until: str | None = None

    def record_rate_limit(self, cooldown_minutes: int) -> None:
        """Record a rate limit event and set cooldown.

        Args:
            cooldown_minutes: Number of minutes to stay in cooldown.

        """
        now = datetime.now(timezone.utc)
        self.last_rate_limit_at = now.isoformat()
        self.cooldown_until = (now + timedelta(minutes=cooldown_minutes)).isoformat()

    def increment_session(self) -> None:
        """Increment the session counter by one."""
        self.session_count += 1


def is_in_cooldown(budget: Budget) -> bool:
    """Check whether the budget is currently in a cooldown period.

    Args:
        budget: The budget to check.

    Returns:
        True if cooldown_until is set and in the future.

    """
    if budget.cooldown_until is None:
        return False
    cooldown = datetime.fromisoformat(budget.cooldown_until)
    now = datetime.now(timezone.utc)
    return cooldown > now


def save_budget(budget: Budget, path: Path) -> None:
    """Serialize a Budget to a JSON file.

    Args:
        budget: The budget state to save.
        path: File path to write JSON to.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(budget)
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_budget(path: Path) -> Budget:
    """Load a Budget from a JSON file.

    If the file does not exist, returns a default Budget.

    Args:
        path: File path to read JSON from.

    Returns:
        A Budget instance.

    """
    if not path.exists():
        return Budget()

    data = json.loads(path.read_text())
    known_fields = {f.name for f in fields(Budget)}
    filtered = {k: v for k, v in data.items() if k in known_fields}
    return Budget(**filtered)
