"""Improvement queue for tracking degrading skills.

Manages a JSON file that tracks which skills have been flagged for
degradation and need auto-improvement. Part of the homeostatic
monitoring system.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ImprovementQueue:
    """Manages the skill improvement queue."""

    def __init__(self, queue_file: Path) -> None:
        self.queue_file = queue_file
        self.skills: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load queue from disk, creating if absent."""
        if self.queue_file.exists():
            try:
                data = json.loads(self.queue_file.read_text())
                self.skills = data.get("skills", {})
            except (json.JSONDecodeError, OSError):
                self.skills = {}
        self._save()

    def _save(self) -> None:
        """Persist queue to disk."""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.queue_file.write_text(
            json.dumps(
                {"skills": self.skills},
                indent=2,
            )
        )
