"""Improvement queue for tracking degrading skills.

Manages a JSON file that tracks which skills have been flagged for
degradation and need auto-improvement. Part of the homeostatic
monitoring system.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import safe_json_load


def _warn(message: str) -> None:
    """Write a warning message to stderr."""
    sys.stderr.write(f"improvement_queue: {message}\n")


class ImprovementQueue:
    """Manages the skill improvement queue."""

    def __init__(self, queue_file: Path) -> None:
        self.queue_file = queue_file
        self.skills: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load queue from disk, creating if absent."""
        if self.queue_file.exists():
            data = safe_json_load(self.queue_file)
            if data is None:
                _warn(f"corrupt queue file {self.queue_file}")
                self.skills = {}
            else:
                self.skills = data.get("skills", {})
        else:
            self._save()

    def _save(self) -> None:
        """Persist queue to disk using atomic write."""
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = self.queue_file.with_suffix(".tmp")
        try:
            tmp_file.write_text(
                json.dumps(
                    {"skills": self.skills},
                    indent=2,
                )
            )
            tmp_file.replace(self.queue_file)
        except OSError as e:
            _warn(f"failed to save queue to {self.queue_file}: {e}")

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
        entry["last_flagged"] = datetime.now(timezone.utc).isoformat()
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
        return [
            ref
            for ref, entry in self.skills.items()
            if entry.get("status") not in ("evaluating", "pending_rollback_review")
            and entry.get("flagged_count", 0) >= self.TRIGGER_THRESHOLD
        ]

    def start_evaluation(self, skill_ref: str, baseline_gap: float) -> bool:
        """Mark a skill as under evaluation after improvement.

        Side effects:
            Resets ``flagged_count`` to 0 and clears ``execution_ids``
            so the evaluation window starts from a clean slate.

        Returns:
            True if the skill was found and marked as evaluating,
            False if the skill_ref is unknown.

        """
        entry = self.skills.get(skill_ref)
        if not entry:
            _warn(f"start_evaluation called for unknown skill {skill_ref!r}")
            return False
        entry["status"] = "evaluating"
        entry["evaluating"] = True
        entry["eval_start"] = datetime.now(timezone.utc).isoformat()
        entry["eval_executions"] = 0
        entry["eval_target"] = 10
        entry["baseline_gap"] = baseline_gap
        entry["flagged_count"] = 0
        entry["execution_ids"] = []
        self._save()
        return True

    def record_eval_execution(self, skill_ref: str, stability_gap: float) -> bool:
        """Record one execution during evaluation window.

        Returns:
            True if the execution was recorded, False if the skill
            is unknown or not currently in evaluating status.

        """
        entry = self.skills.get(skill_ref)
        if not entry:
            _warn(f"record_eval_execution called for unknown skill {skill_ref!r}")
            return False
        if entry.get("status") != "evaluating":
            _warn(
                f"record_eval_execution called for"
                f" skill {skill_ref!r} with status"
                f" {entry.get('status')!r}, expected 'evaluating'"
            )
            return False
        entry["eval_executions"] = entry.get("eval_executions", 0) + 1
        entry["stability_gap"] = stability_gap
        eval_gaps: list[float] = entry.setdefault("eval_gaps", [])
        eval_gaps.append(stability_gap)
        self._save()
        return True

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
            _warn(f"evaluate called for unknown skill {skill_ref!r}")
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
            entry["regression_detected"] = datetime.now(timezone.utc).isoformat()
            entry["current_gap"] = avg_gap
            decision = "pending_rollback_review"

        entry["evaluating"] = False
        self._save()
        return decision
