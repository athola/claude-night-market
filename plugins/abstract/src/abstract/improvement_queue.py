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
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, get_args

from ._vendored_leyline_atomic_file import write_atomic
from .stdlib_helpers import emit_warn


def _warn(message: str) -> None:
    """Forward to the shared stderr writer (D-12)."""
    emit_warn("improvement_queue", message)


QueueStatus = Literal["monitoring", "evaluating", "pending_rollback_review", "promoted"]

# A skill in either status is not re-flagged: one is being measured, the
# other is waiting for a person.
_HELD_STATUSES = ("evaluating", "pending_rollback_review")

_DEFAULT_EVAL_TARGET = 10


@dataclass
class QueueEntry:
    """One skill's queue record, as stored under ``skills`` in the JSON file.

    An entry that is evaluating always has ``eval_start``: the constructor
    refuses the combination, and ``begin_evaluation`` sets both together.
    The ``eval_*`` fields and ``baseline_gap`` are written to disk only
    once an evaluation has begun, which keeps files from before this
    class loadable and unchanged for skills that never reached one.
    """

    skill_name: str
    stability_gap: float = 0.0
    flagged_count: int = 0
    last_flagged: str = ""
    execution_ids: list[str] = field(default_factory=list)
    status: QueueStatus = "monitoring"
    eval_start: str | None = None
    eval_executions: int = 0
    eval_gaps: list[float] = field(default_factory=list)
    eval_target: int = _DEFAULT_EVAL_TARGET
    eval_history_start: int = 0
    eval_version: str = ""
    eval_change_summary: str = ""
    baseline_gap: float = 0.0
    regression_detected: str | None = None
    current_gap: float | None = None

    _EVAL_FIELDS = (
        "eval_start",
        "eval_executions",
        "eval_gaps",
        "eval_target",
        "eval_history_start",
        "eval_version",
        "eval_change_summary",
        "baseline_gap",
    )

    def __post_init__(self) -> None:
        """Refuse a status outside the Literal or an evaluating entry with no start."""
        if self.status not in get_args(QueueStatus):
            raise ValueError(f"unknown queue status {self.status!r}")
        if self.status == "evaluating" and self.eval_start is None:
            raise ValueError(f"{self.skill_name!r} is evaluating without eval_start")

    @classmethod
    def from_dict(cls, skill_ref: str, raw: object) -> QueueEntry:
        """Build an entry from its stored form; ValueError when it is invalid.

        Keys this class does not declare are ignored. ``skill_name`` falls
        back to the key the entry was stored under.
        """
        if not isinstance(raw, dict):
            raise ValueError(f"queue entry for {skill_ref!r} is not an object")
        known = {f.name for f in fields(cls)}
        kwargs = {key: value for key, value in raw.items() if key in known}
        kwargs.setdefault("skill_name", skill_ref)
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Return the stored form: unset optional fields are left out."""
        stored = asdict(self)
        if self.eval_start is None:
            for name in self._EVAL_FIELDS:
                del stored[name]
        for name in ("regression_detected", "current_gap"):
            if stored[name] is None:
                del stored[name]
        return stored

    def begin_evaluation(
        self,
        baseline_gap: float,
        eval_target: int,
        history_position: int,
        version: str,
        change_summary: str,
    ) -> None:
        """Open an evaluation window with a clean flag count."""
        self.status = "evaluating"
        self.eval_start = datetime.now(timezone.utc).isoformat()
        self.eval_executions = 0
        self.eval_gaps = []
        self.eval_target = eval_target
        self.eval_history_start = history_position
        self.eval_version = version
        self.eval_change_summary = change_summary
        self.baseline_gap = baseline_gap
        self.flagged_count = 0
        self.execution_ids = []


class ImprovementQueue:
    """Manages the skill improvement queue."""

    def __init__(self, queue_file: Path) -> None:
        self.queue_file = queue_file
        self.skills: dict[str, QueueEntry] = {}
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
        skills: dict[str, QueueEntry] | None = None
        if isinstance(data, dict) and isinstance(data.get("skills", {}), dict):
            try:
                skills = {
                    ref: QueueEntry.from_dict(ref, raw)
                    for ref, raw in data.get("skills", {}).items()
                }
            except (ValueError, TypeError) as e:
                # An entry that cannot be built is as unusable as bad JSON.
                _warn(f"invalid entry in {self.queue_file}: {e}")
        if skills is None:
            self._set_aside_corrupt()
            self.skills = {}
        else:
            self.skills = skills
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
            stored = {ref: entry.to_dict() for ref, entry in self.skills.items()}
            write_atomic(self.queue_file, json.dumps({"skills": stored}, indent=2))
        except OSError as e:
            _warn(f"failed to save queue to {self.queue_file}: {e}")
            raise

    TRIGGER_THRESHOLD = 3
    EVAL_TARGET = _DEFAULT_EVAL_TARGET

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
            entry = self.skills.get(skill_ref)
            if entry is not None and entry.status in _HELD_STATUSES:
                return False
            if entry is None:
                entry = QueueEntry(skill_name=skill_ref)
                self.skills[skill_ref] = entry
            entry.flagged_count += 1
            entry.stability_gap = stability_gap
            entry.last_flagged = datetime.now(timezone.utc).isoformat()
            entry.execution_ids.append(execution_id)
            del entry.execution_ids[: -self.MAX_EXECUTION_IDS]
            self._save()
            return True

    def needs_improvement(self, skill_ref: str) -> bool:
        """Check if a skill has enough flags to trigger improvement."""
        entry = self.skills.get(skill_ref)
        if entry is None or entry.status in _HELD_STATUSES:
            return False
        return entry.flagged_count >= self.TRIGGER_THRESHOLD

    def get_improvable_skills(self) -> list[str]:
        """Return skill refs that are ready for improvement."""
        return [
            ref
            for ref, entry in self.skills.items()
            if entry.status not in _HELD_STATUSES
            and entry.flagged_count >= self.TRIGGER_THRESHOLD
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
            if entry is None:
                _warn(f"start_evaluation called for unknown skill {skill_ref!r}")
                return False
            entry.begin_evaluation(
                baseline_gap,
                self.EVAL_TARGET,
                history_position,
                version,
                change_summary,
            )
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
            if entry is None:
                _warn(f"record_eval_execution called for unknown skill {skill_ref!r}")
                return False
            if entry.status != "evaluating":
                _warn(
                    f"record_eval_execution called for"
                    f" skill {skill_ref!r} with status"
                    f" {entry.status!r}, expected 'evaluating'"
                )
                return False
            entry.eval_executions += 1
            entry.stability_gap = stability_gap
            entry.eval_gaps.append(stability_gap)
            self._save()
            return True

    def is_eval_complete(self, skill_ref: str) -> bool:
        """Check if evaluation window is complete."""
        entry = self.skills.get(skill_ref)
        if entry is None or entry.status != "evaluating":
            return False
        return entry.eval_executions >= entry.eval_target

    def evaluate(self, skill_ref: str) -> str:
        """Make promotion/rollback decision after evaluation completes.

        Returns:
            "promote" if improved, "pending_rollback_review" otherwise.

        """
        with self._locked_reload():
            entry = self.skills.get(skill_ref)
            if entry is None:
                _warn(f"evaluate called for unknown skill {skill_ref!r}")
                return "unknown"

            # Each recorded gap already covers every run since the window
            # opened, so the last one is the window's. Averaging them would
            # count the early, short slices as if they were full windows.
            window_gap = entry.eval_gaps[-1] if entry.eval_gaps else entry.stability_gap

            if window_gap < entry.baseline_gap:
                entry.status = "promoted"
                decision = "promote"
            else:
                entry.status = "pending_rollback_review"
                entry.regression_detected = datetime.now(timezone.utc).isoformat()
                entry.current_gap = window_gap
                decision = "pending_rollback_review"

            self._save()
            return decision
