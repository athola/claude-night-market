"""Improvement queue for tracking degrading skills.

Manages a JSON file that tracks which skills have been flagged for
degradation and need auto-improvement. Part of the homeostatic
monitoring system.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ._vendored_leyline_atomic_file import write_atomic
from .stdlib_helpers import emit_warn


def _warn(message: str) -> None:
    """Forward to the shared stderr writer (D-12)."""
    emit_warn("improvement_queue", message)


class ImprovementQueue:
    """Manages the skill improvement queue."""

    def __init__(self, queue_file: Path) -> None:
        self.queue_file = queue_file
        self.skills: dict[str, dict[str, Any]] = {}
        if not self._load():
            # Create under the lock: another process may have written the
            # queue since the unlocked read missed it, and an empty save
            # here would replace its flags.
            with self._locked_reload() as found:
                if not found:
                    self._save()

    def _load(self) -> bool:
        """Load queue from disk; return False when the file is absent.

        Only a parse failure counts as corruption. Any other OSError
        propagates: moving a healthy file aside on a transient read error
        would empty the queue.
        """
        try:
            text = self.queue_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Absent, or moved aside by another process.
            self.skills = {}
            return False
        try:
            data = json.loads(text)
        except ValueError:
            data = None
        if not isinstance(data, dict):
            self._set_aside_corrupt()
            self.skills = {}
        else:
            self.skills = data.get("skills", {})
        return True

    def _set_aside_corrupt(self) -> None:
        """Move a corrupt queue file aside instead of letting _save replace it.

        The next _save would replace every other skill's history with one
        new entry. The timestamp keeps an earlier backup from being
        overwritten.
        """
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = self.queue_file.with_name(f"{self.queue_file.name}.corrupt-{stamp}")
        try:
            os.replace(self.queue_file, backup)
        except FileNotFoundError:
            return  # another process already moved it aside
        _warn(f"corrupt queue file {self.queue_file}; moved to {backup}")

    def _save(self) -> None:
        """Persist queue to disk using atomic write.

        The file keeps mkstemp's 0600 mode: it lives under the user's
        ~/.claude and nothing reads it as another user.
        """
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            write_atomic(self.queue_file, json.dumps({"skills": self.skills}, indent=2))
        except OSError as e:
            _warn(f"failed to save queue to {self.queue_file}: {e}")
            raise

    TRIGGER_THRESHOLD = 3
    EVAL_TARGET = 10

    # Every flag appends an id and the file is rewritten on each run, so
    # an unbounded list grows the queue file for the life of the skill.
    MAX_EXECUTION_IDS = 50

    @contextlib.contextmanager
    def _locked_reload(self) -> Iterator[bool]:
        """Hold the queue lock and re-read the file before a mutation.

        Parallel subagents each run the homeostatic hook, and every one
        loaded the queue at construction. Saving that stale copy dropped the
        skills another process flagged in between.
        """
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.queue_file.with_name(self.queue_file.name + ".lock")
        with open(lock_path, "a", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield self._load()

    def flag_skill(
        self, skill_ref: str, stability_gap: float, execution_id: str
    ) -> bool:
        """Flag a skill as degrading.

        Returns False, without flagging, while the skill is under
        evaluation or awaiting rollback review. The status is read under
        the lock so another process's start_evaluation is not missed.
        """
        with self._locked_reload():
            if self.skills.get(skill_ref, {}).get("status") in (
                "evaluating",
                "pending_rollback_review",
            ):
                return False
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
            del entry["execution_ids"][: -self.MAX_EXECUTION_IDS]
            self._save()
            return True

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

    def start_evaluation(
        self,
        skill_ref: str,
        baseline_gap: float,
        history_position: int = 0,
        version: str = "",
        change_summary: str = "",
    ) -> bool:
        """Mark a skill as under evaluation after improvement.

        ``history_position`` is how many outcomes the skill's history held
        when the window opened. The window is judged on the outcomes after
        it, so the failures that flagged the skill do not count against
        the change. ``version`` and ``change_summary`` describe the change
        for the improvement memory entry written when the window closes.

        Side effects:
            Resets ``flagged_count`` to 0 and clears ``execution_ids``
            so the evaluation window starts from a clean slate.

        Returns:
            True if the skill was found and marked as evaluating,
            False if the skill_ref is unknown.

        """
        with self._locked_reload():
            entry = self.skills.get(skill_ref)
            if not entry:
                _warn(f"start_evaluation called for unknown skill {skill_ref!r}")
                return False
            entry["status"] = "evaluating"
            entry["eval_start"] = datetime.now(timezone.utc).isoformat()
            entry["eval_executions"] = 0
            entry["eval_gaps"] = []
            entry["eval_target"] = self.EVAL_TARGET
            entry["eval_history_start"] = history_position
            entry["eval_version"] = version
            entry["eval_change_summary"] = change_summary
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
        with self._locked_reload():
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
        return bool(
            entry.get("eval_executions", 0)
            >= entry.get("eval_target", self.EVAL_TARGET)
        )

    def evaluate(self, skill_ref: str) -> str:
        """Make promotion/rollback decision after evaluation completes.

        Returns:
            "promote" if improved, "pending_rollback_review" otherwise.

        """
        with self._locked_reload():
            entry = self.skills.get(skill_ref)
            if not entry:
                _warn(f"evaluate called for unknown skill {skill_ref!r}")
                return "unknown"

            baseline = entry.get("baseline_gap", 0)
            eval_gaps: list[float] = entry.get("eval_gaps", [])
            # Each recorded gap already covers every run since the window
            # opened, so the last one is the window's. Averaging them would
            # count the early, short slices as if they were full windows.
            window_gap = eval_gaps[-1] if eval_gaps else entry.get("stability_gap", 0)

            if window_gap < baseline:
                entry["status"] = "promoted"
                decision = "promote"
            else:
                entry["status"] = "pending_rollback_review"
                entry["regression_detected"] = datetime.now(timezone.utc).isoformat()
                entry["current_gap"] = window_gap
                decision = "pending_rollback_review"

            self._save()
            return decision
