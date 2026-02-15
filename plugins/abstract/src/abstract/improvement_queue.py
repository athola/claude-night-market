"""Improvement queue for tracking degrading skills.

Manages a JSON file that tracks which skills have been flagged for
degradation and need auto-improvement. Part of the homeostatic
monitoring system.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
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

    TRIGGER_THRESHOLD = 3

    def flag_skill(
        self, skill_ref: str, stability_gap: float, execution_id: str
    ) -> None:
        """Flag a skill as degrading."""
        if skill_ref not in self.skills:
            self.skills[skill_ref] = {
                "skill_name": skill_ref,
                "stability_gap": stability_gap,
                "flagged_count": 0,
                "last_flagged": "",
                "execution_ids": [],
                "status": "monitoring",
            }
        entry = self.skills[skill_ref]
        entry["flagged_count"] += 1
        entry["stability_gap"] = stability_gap
        entry["last_flagged"] = datetime.now(UTC).isoformat()
        entry["execution_ids"].append(execution_id)
        self._save()

    def needs_improvement(self, skill_ref: str) -> bool:
        """Check if a skill has enough flags to trigger improvement."""
        entry = self.skills.get(skill_ref)
        if not entry:
            return False
        if entry.get("status") in ("evaluating", "pending_rollback_review"):
            return False
        return bool(entry["flagged_count"] >= self.TRIGGER_THRESHOLD)

    def get_improvable_skills(self) -> list[str]:
        """Return skill refs that are ready for improvement."""
        return [ref for ref in self.skills if self.needs_improvement(ref)]

    def start_evaluation(self, skill_ref: str, baseline_gap: float) -> None:
        """Mark a skill as under evaluation after improvement."""
        entry = self.skills.get(skill_ref)
        if not entry:
            return
        entry["status"] = "evaluating"
        entry["evaluating"] = True
        entry["eval_start"] = datetime.now(UTC).isoformat()
        entry["eval_executions"] = 0
        entry["eval_target"] = 10
        entry["baseline_gap"] = baseline_gap
        entry["flagged_count"] = 0
        entry["execution_ids"] = []
        self._save()
