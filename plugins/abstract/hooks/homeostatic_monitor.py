#!/usr/bin/env python3
"""Homeostatic monitor hook for PostToolUse.

Reads stability gap from execution history and flags degrading
skills in the improvement queue. When a skill accumulates 3+
flags, it becomes eligible for auto-improvement.

Part of the self-adapting system. See:
docs/plans/2026-02-15-self-adapting-systems-design.md
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Allow importing from src/abstract/ when running as a hook
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from abstract.improvement_queue import ImprovementQueue  # noqa: E402

STABILITY_GAP_THRESHOLD = 0.3
CRITICAL_GAP_THRESHOLD = 0.5


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
    except (json.JSONDecodeError, OSError):
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

        if gap <= STABILITY_GAP_THRESHOLD:
            # Skill is healthy, no action needed
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "monitor": "homeostatic",
                    "skill": skill_ref,
                    "stability_gap": gap,
                    "status": "healthy",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        # Skill is degrading -- flag it in the queue via ImprovementQueue
        queue_file = claude_home / "skills" / "improvement-queue.json"
        queue = ImprovementQueue(queue_file)

        # Don't flag if already evaluating or pending review
        entry = queue.skills.get(skill_ref, {})
        if entry.get("status") in ("evaluating", "pending_rollback_review"):
            sys.exit(0)

        invocation_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
        queue.flag_skill(skill_ref, gap, invocation_id)

        entry = queue.skills[skill_ref]
        status = "critical" if gap > CRITICAL_GAP_THRESHOLD else "degrading"
        trigger = queue.needs_improvement(skill_ref)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "monitor": "homeostatic",
                "skill": skill_ref,
                "stability_gap": gap,
                "status": status,
                "flagged_count": entry["flagged_count"],
                "improvement_triggered": trigger,
            }
        }
        print(json.dumps(output))

        if trigger:
            sys.stderr.write(
                f"HOMEOSTATIC: {skill_ref} flagged {entry['flagged_count']}x "
                f"(gap={gap:.2f}), improvement eligible\n"
            )

        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"homeostatic_monitor error: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
