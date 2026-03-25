#!/usr/bin/env python3
"""Homeostatic monitor hook for PostToolUse.

Reads stability gap from execution history and flags degrading
skills in the improvement queue. When a skill accumulates 3+
flags, it becomes eligible for auto-improvement.

Part of the self-adapting system. See: docs/adr/0006-self-adapting-skill-health.md
"""

from __future__ import annotations

# pyright: reportPossiblyUnboundVariable=false
import json
import os
import sys
from pathlib import Path

# Allow importing from src/abstract/ when running as a hook
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

try:
    from abstract.improvement_queue import ImprovementQueue  # noqa: E402

    _HAS_QUEUE = True
except ImportError:
    _HAS_QUEUE = False

try:
    from abstract.performance_tracker import PerformanceTracker  # noqa: E402

    _HAS_TRACKER = True
except ImportError:
    _HAS_TRACKER = False

STABILITY_GAP_THRESHOLD = 0.3
CRITICAL_GAP_THRESHOLD = 0.5


def _get_improvement_trend(claude_home: Path, skill_ref: str) -> float | None:  # noqa: UP007
    """Fetch improvement trend from PerformanceTracker (best-effort)."""
    if not _HAS_TRACKER:
        return None
    tracker_file = claude_home / "skills" / "performance_history.json"
    tracker = PerformanceTracker(tracker_file)
    return tracker.get_improvement_trend(skill_ref)


def _build_output(
    skill_ref: str, gap: float, status: str, velocity: int, trend: float | None, **extra
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


def _needs_metacognition(claude_home: Path) -> bool:
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
        from abstract.improvement_memory import ImprovementMemory  # noqa: E402

        mem_file = claude_home / "skills" / "improvement_memory.json"
        if not mem_file.exists():
            return False
        mem = ImprovementMemory(mem_file)
        effective = mem.get_effective_strategies()
        failed = mem.get_failed_strategies()
        total = len(effective) + len(failed)
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
    except ImportError:
        pass  # ImprovementMemory not available
    except (OSError, KeyError) as e:
        sys.stderr.write(f"homeostatic_monitor: _needs_metacognition: {e}\n")
    return False


def _flag_and_build_output(
    claude_home: Path,
    skill_ref: str,
    gap: float,
    velocity: int,
    trend: float | None,
) -> dict:
    """Flag degrading skill in queue and return output dict."""
    queue_file = claude_home / "skills" / "improvement-queue.json"
    queue = ImprovementQueue(queue_file)

    entry = queue.skills.get(skill_ref, {})
    if entry.get("status") in ("evaluating", "pending_rollback_review"):
        return None  # type: ignore[return-value]  # caller handles None

    invocation_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
    queue.flag_skill(skill_ref, gap, invocation_id)

    entry = queue.skills[skill_ref]
    status = "critical" if gap > CRITICAL_GAP_THRESHOLD else "degrading"
    trigger = queue.needs_improvement(skill_ref)

    # Check if metacognitive analysis is warranted
    metacognitive_needed = False
    if trigger:
        metacognitive_needed = _needs_metacognition(claude_home)
        sys.stderr.write(
            f"HOMEOSTATIC: {skill_ref} flagged {entry['flagged_count']}x "
            f"(gap={gap:.2f}), improvement eligible"
            f"{' [metacognitive recommended]' if metacognitive_needed else ''}\n"
        )

    return _build_output(
        skill_ref,
        gap,
        status,
        velocity,
        trend,
        flagged_count=entry["flagged_count"],
        improvement_triggered=trigger,
        metacognitive_needed=metacognitive_needed,
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
        return json.loads(history_file.read_text())
    except json.JSONDecodeError:
        sys.stderr.write(f"homeostatic_monitor: corrupt history file {history_file}\n")
        return {}
    except OSError as e:
        sys.stderr.write(
            f"homeostatic_monitor: failed to read history file {history_file}: {e}\n"
        )
        return {}


def calculate_stability_gap(history_entry: dict) -> float:
    """Calculate stability gap from accuracy history."""
    accuracies = history_entry.get("accuracies", [])
    if not accuracies:
        return 0.0
    worst_case = min(accuracies)
    avg_accuracy = sum(accuracies) / len(accuracies)
    return avg_accuracy - worst_case


def main() -> None:
    """PostToolUse hook entry point."""
    try:
        tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
        if tool_name != "Skill":
            sys.exit(0)

        tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
        try:
            tool_input = json.loads(tool_input_str)
        except json.JSONDecodeError:
            sys.exit(0)

        skill_ref = tool_input.get("skill", "")
        if not skill_ref:
            sys.exit(0)

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
        output = _flag_and_build_output(claude_home, skill_ref, gap, velocity, trend)
        if output is None:
            sys.exit(0)
        print(json.dumps(output))
        sys.exit(0)

    except (json.JSONDecodeError, OSError, KeyError) as e:
        sys.stderr.write(f"homeostatic_monitor error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
