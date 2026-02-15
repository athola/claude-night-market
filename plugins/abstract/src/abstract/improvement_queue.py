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

    def record_eval_execution(self, skill_ref: str, stability_gap: float) -> None:
        """Record one execution during evaluation window."""
        entry = self.skills.get(skill_ref)
        if not entry or entry.get("status") != "evaluating":
            return
        entry["eval_executions"] = entry.get("eval_executions", 0) + 1
        entry["stability_gap"] = stability_gap
        eval_gaps: list[float] = entry.setdefault("eval_gaps", [])
        eval_gaps.append(stability_gap)
        self._save()

    def is_eval_complete(self, skill_ref: str) -> bool:
        """Check if evaluation window is complete."""
        entry = self.skills.get(skill_ref)
        if not entry or entry.get("status") != "evaluating":
            return False
        return bool(entry.get("eval_executions", 0) >= entry.get("eval_target", 10))

    def evaluate(self, skill_ref: str) -> str:
        """Make promotion/rollback decision after evaluation completes.

        Returns:
            "promote" if improved, "pending_rollback_review" otherwise.

        """
        entry = self.skills.get(skill_ref)
        if not entry:
            return "unknown"

        baseline = entry.get("baseline_gap", 0)
        eval_gaps: list[float] = entry.get("eval_gaps", [])
        avg_gap = (
            sum(eval_gaps) / len(eval_gaps)
            if eval_gaps
            else entry.get("stability_gap", 0)
        )

        if avg_gap < baseline:
            entry["status"] = "promoted"
            decision = "promote"
        else:
            entry["status"] = "pending_rollback_review"
            entry["regression_detected"] = datetime.now(UTC).isoformat()
            entry["current_gap"] = avg_gap
            decision = "pending_rollback_review"

        entry["evaluating"] = False
        self._save()
        return decision
