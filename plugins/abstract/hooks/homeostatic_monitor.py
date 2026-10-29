#!/usr/bin/env python3
"""Homeostatic monitor hook for PostToolUse.

Reads stability gap from execution history and flags degrading
skills in the improvement queue. When a skill accumulates 3+
flags, it becomes eligible for auto-improvement.

Part of the self-adapting system. See: docs/adr/0006-self-adapting-skill-health.md
"""

from __future__ import annotations

# pyright: reportPossiblyUnboundVariable=false
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, NamedTuple

# Allow importing from src/abstract/ and the co-located shared/ package
# when running as a hook.
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
_hooks_dir = Path(__file__).resolve().parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from shared.hook_io import read_hook_payload  # noqa: E402 - import after path setup
from shared.skill_utils import parse_skill_name  # noqa: E402 - import after path setup
from shared.stability import (  # noqa: E402 - import after path setup
    RECENT_RUNS,
    stability_gap_since,
)

try:
    from abstract.improvement_queue import ImprovementQueue
    from abstract.paths import get_improvement_queue_path

    _HAS_QUEUE = True
except ImportError:
    _HAS_QUEUE = False

try:
    from abstract.improvement_memory import ImprovementMemory, ImprovementOutcome

    _HAS_MEMORY = True
except ImportError:
    _HAS_MEMORY = False

try:
    from abstract.performance_tracker import PerformanceTracker

    _HAS_TRACKER = True
except ImportError:
    _HAS_TRACKER = False

STABILITY_GAP_THRESHOLD = 0.3
CRITICAL_GAP_THRESHOLD = 0.5


def _status(gap: float) -> str:
    """Health label for a stability gap."""
    if gap <= STABILITY_GAP_THRESHOLD:
        return "healthy"
    return "critical" if gap > CRITICAL_GAP_THRESHOLD else "degrading"


def _get_improvement_trend(claude_home: Path, skill_ref: str) -> float | None:
    """Fetch improvement trend from PerformanceTracker (best-effort)."""
    if not _HAS_TRACKER:
        return None
    tracker_file = claude_home / "skills" / "performance_history.json"
    tracker = PerformanceTracker(tracker_file)
    return tracker.get_improvement_trend(skill_ref)


def _build_output(
    skill_ref: str,
    gap: float,
    status: str,
    velocity: int,
    trend: float | None,
    **extra: Any,
) -> dict:
    """Build hookSpecificOutput dict."""
    payload: dict = {
        "hookEventName": "PostToolUse",
        "monitor": "homeostatic",
        "skill": skill_ref,
        "stability_gap": gap,
        "status": status,
        "stewardship_actions": velocity,
        "improvement_trend": trend,
    }
    payload.update(extra)
    return {"hookSpecificOutput": payload}


def _needs_metacognition(claude_home: Path) -> bool:  # noqa: PLR0911 - multi-criteria check with early returns for clarity
    """Check if metacognitive analysis is warranted.

    Triggers when:
    1. Effectiveness rate < 50% (with >= 5 outcomes)
    2. Every 10 improvement outcomes (periodic check)
    3. Most recent outcome was a regression

    Returns False if ImprovementMemory is unavailable.
    """
    min_outcomes = 5
    low_effectiveness = 0.5
    periodic_interval = 10
    try:
        if not _HAS_MEMORY:
            return False

        mem_file = claude_home / "skills" / "improvement_memory.json"
        if not mem_file.exists():
            return False
        mem = ImprovementMemory(mem_file)
        effective = mem.get_effective_strategies()
        failed = mem.get_failed_strategies()
        # Every recorded outcome is an attempt; small gains and neutral
        # results are neither effective nor failed but still count.
        total = sum(len(v) for v in mem.outcomes.values())
        if total == 0:
            return False
        # Trigger 1: low effectiveness
        if total >= min_outcomes and len(effective) / total < low_effectiveness:
            return True
        # Trigger 2: periodic
        if total % periodic_interval == 0:
            return True
        # Trigger 3: recent regression
        if failed:
            all_outcomes: list = []
            for skill_outcomes in mem.outcomes.values():
                all_outcomes.extend(skill_outcomes)
            if all_outcomes:
                all_outcomes.sort(key=lambda o: o.get("timestamp", ""))
                if all_outcomes[-1].get("outcome_type") == "failure":
                    return True
    except (OSError, KeyError) as e:
        sys.stderr.write(f"homeostatic_monitor: _needs_metacognition: {e}\n")
    return False


class SkillHealth(NamedTuple):
    """Computed health snapshot for one skill invocation."""

    gap: float
    velocity: int
    trend: float | None


def _flag_and_build_output(
    claude_home: Path,
    skill_ref: str,
    health: SkillHealth,
    session_id: str,
) -> dict | None:
    """Flag degrading skill in queue and return output dict.

    Reads ``health`` fields directly rather than destructuring; the bundle is
    constructed once at the call site and never re-exploded here.
    """
    queue_file = get_improvement_queue_path(claude_home)
    queue = ImprovementQueue(queue_file)

    if not queue.flag_skill(skill_ref, health.gap, session_id):
        return None  # under evaluation or review; caller handles None

    entry = queue.skills[skill_ref]
    status = _status(health.gap)
    trigger = queue.needs_improvement(skill_ref)

    # Check if metacognitive analysis is warranted
    metacognitive_needed = False
    if trigger:
        metacognitive_needed = _needs_metacognition(claude_home)
        sys.stderr.write(
            f"HOMEOSTATIC: {skill_ref} flagged {entry['flagged_count']}x "
            f"(gap={health.gap:.2f}), improvement eligible"
            f"{' [metacognitive recommended]' if metacognitive_needed else ''}\n"
        )

    return _build_output(
        skill_ref,
        health.gap,
        status,
        health.velocity,
        health.trend,
        flagged_count=entry["flagged_count"],
        improvement_triggered=trigger,
        metacognitive_needed=metacognitive_needed,
    )


def _mean(outcomes: list[float]) -> float:
    return sum(outcomes) / len(outcomes)


def _record_window_outcome(
    claude_home: Path, skill_ref: str, entry: dict[str, Any], accuracies: list[float]
) -> None:
    """Write the closed window's measured scores to the learning stores.

    ``before_score`` is the success rate over the runs that preceded the
    window and ``after_score`` the rate inside it, so ImprovementMemory
    classifies the change as success, failure or neutral from data. A
    window opened without a history position has no measured "before".
    """
    start = entry.get("eval_history_start", 0)
    before_runs = accuracies[max(0, start - RECENT_RUNS) : start]
    window_runs = accuracies[start:]
    if not before_runs or not window_runs:
        return
    after_score = _mean(window_runs)
    version = str(entry.get("eval_version", ""))
    if _HAS_MEMORY:
        ImprovementMemory(
            claude_home / "skills" / "improvement_memory.json"
        ).record_improvement_outcome(
            skill_ref,
            ImprovementOutcome(
                version=version,
                change_summary=str(entry.get("eval_change_summary", "")),
                before_score=_mean(before_runs),
                after_score=after_score,
            ),
        )
    if _HAS_TRACKER:
        PerformanceTracker(
            claude_home / "skills" / "performance_history.json"
        ).record_generation(skill_ref, version, after_score)


def _advance_evaluation(
    claude_home: Path, skill_ref: str, accuracies: list[float]
) -> dict[str, Any] | None:
    """Count this execution toward an open evaluation window.

    ``flag_skill`` refuses an evaluating skill, so this is the only path
    that moves one out of ``evaluating``: each execution is recorded and
    the window is decided once it holds ``eval_target`` of them. The gap
    recorded is over the outcomes since the window opened only.

    Returns:
        Output fields for the hook report, plus ``window_gap``, or None
        when the skill is not under evaluation. A missing queue file is
        not created.

    """
    queue_file = get_improvement_queue_path(claude_home)
    if not queue_file.exists():
        return None
    queue = ImprovementQueue(queue_file)
    entry = queue.skills.get(skill_ref, {})
    if entry.get("status") != "evaluating":
        return None
    window_gap = stability_gap_since(accuracies, entry.get("eval_history_start", 0))
    if not queue.record_eval_execution(skill_ref, window_gap):
        return None
    if not queue.is_eval_complete(skill_ref):
        entry = queue.skills[skill_ref]
        return {
            "window_gap": window_gap,
            "evaluation": {
                "executions": entry["eval_executions"],
                "target": entry.get("eval_target", queue.EVAL_TARGET),
            },
        }
    decision = queue.evaluate(skill_ref)
    sys.stderr.write(f"HOMEOSTATIC: {skill_ref} evaluation finished: {decision}\n")
    _record_window_outcome(claude_home, skill_ref, queue.skills[skill_ref], accuracies)
    return {"window_gap": window_gap, "evaluation_decision": decision}


def _evaluation_report(
    claude_home: Path, skill_ref: str, health: SkillHealth, accuracies: list[float]
) -> dict | None:
    """Return the hook output for an evaluating skill, else None."""
    if not _HAS_QUEUE:
        return None
    try:
        evaluation = _advance_evaluation(claude_home, skill_ref, accuracies)
    except OSError as e:
        sys.stderr.write(
            f"homeostatic_monitor: evaluation not recorded for {skill_ref}: {e}\n"
        )
        return None
    if evaluation is None:
        return None
    window_gap = evaluation.pop("window_gap")
    return _build_output(
        skill_ref,
        window_gap,
        _status(window_gap),
        health.velocity,
        health.trend,
        **evaluation,
    )


# Stewardship integration: lightweight velocity read


def _stewardship_velocity(claude_home: Path) -> int:
    """Count stewardship actions (0 if tracker absent)."""
    actions_file = claude_home / "stewardship" / "actions.jsonl"
    if not actions_file.exists():
        return 0
    try:
        return sum(
            1
            for line in actions_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    except FileNotFoundError:
        return 0
    except OSError as e:
        sys.stderr.write(f"homeostatic_monitor: failed to read {actions_file}: {e}\n")
        return 0


def get_claude_home() -> Path:
    """Get Claude home directory."""
    return Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))


def read_history(claude_home: Path) -> dict:
    """Read execution history from .history.json."""
    history_file = claude_home / "skills" / "logs" / ".history.json"
    if not history_file.exists():
        return {}
    try:
        data = json.loads(history_file.read_text())
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        sys.stderr.write(f"homeostatic_monitor: corrupt history file {history_file}\n")
        return {}
    except OSError as e:
        sys.stderr.write(
            f"homeostatic_monitor: failed to read history file {history_file}: {e}\n"
        )
        return {}


def calculate_stability_gap(history_entry: dict) -> float:
    """Windowed stability gap of a skill's pass/fail history (shared.stability)."""
    stability = importlib.import_module("shared.stability")
    return float(stability.stability_gap(history_entry.get("accuracies", [])))


def main() -> None:
    """PostToolUse hook entry point."""
    try:
        payload = read_hook_payload()
        tool_name = payload["tool_name"]
        if tool_name != "Skill":
            sys.exit(0)

        tool_input = payload["tool_input"]
        if not tool_input.get("skill", ""):
            sys.exit(0)
        # The logger keys .history.json this way; a raw name such as
        # "proof-of-work" is stored as "unknown:proof-of-work".
        plugin, skill = parse_skill_name(tool_input)
        skill_ref = f"{plugin}:{skill}"

        claude_home = get_claude_home()
        history = read_history(claude_home)
        skill_history = history.get(skill_ref)

        if not skill_history:
            sys.exit(0)

        gap = calculate_stability_gap(skill_history)

        try:
            trend = _get_improvement_trend(claude_home, skill_ref)
        except Exception as e:
            sys.stderr.write(f"homeostatic_monitor: tracker error: {e}\n")
            trend = None

        velocity = _stewardship_velocity(claude_home)

        # Before the healthy exit: a window exists to watch the executions
        # that follow an improvement, and those are meant to be healthy.
        report = _evaluation_report(
            claude_home,
            skill_ref,
            SkillHealth(gap, velocity, trend),
            skill_history.get("accuracies", []),
        )
        if report is not None:
            print(json.dumps(report))
            sys.exit(0)

        if gap <= STABILITY_GAP_THRESHOLD:
            print(json.dumps(_build_output(skill_ref, gap, "healthy", velocity, trend)))
            sys.exit(0)

        if not _HAS_QUEUE:
            sys.stderr.write(
                f"homeostatic_monitor: ImprovementQueue unavailable, "
                f"skipping queue ops for {skill_ref} (gap={gap:.2f})\n"
            )
            print(
                json.dumps(_build_output(skill_ref, gap, "degrading", velocity, trend))
            )
            sys.exit(0)

        # Skill is degrading -- flag it in the queue via ImprovementQueue
        health = SkillHealth(gap, velocity, trend)
        try:
            output = _flag_and_build_output(
                claude_home, skill_ref, health, payload["session_id"]
            )
        except OSError as e:
            # A read-only or full ~/.claude: the queue cannot be locked or
            # written, but the health report still holds.
            sys.stderr.write(
                f"homeostatic_monitor: queue not updated for {skill_ref}: {e}\n"
            )
            output = _build_output(skill_ref, gap, "degrading", velocity, trend)
        if output is None:
            sys.exit(0)
        print(json.dumps(output))
        sys.exit(0)

    except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as e:
        # TypeError and ValueError were missing while sibling hooks catch
        # them: a payload whose fields have the wrong type reaches this
        # code as a TypeError, and an unparseable field as a ValueError.
        # Either one escaped as a traceback on stderr with a nonzero exit,
        # which for a hook is the same outcome, minus the label that says
        # which hook it was.
        sys.stderr.write(f"homeostatic_monitor error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
