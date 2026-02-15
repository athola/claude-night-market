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
from datetime import UTC, datetime
from pathlib import Path

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

        # Skill is degrading -- flag it in the queue
        queue_file = claude_home / "skills" / "improvement-queue.json"

        # Load or create queue
        queue_data: dict = {"skills": {}}
        if queue_file.exists():
            try:
                queue_data = json.loads(queue_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        skills = queue_data.setdefault("skills", {})
        if skill_ref not in skills:
            skills[skill_ref] = {
                "skill_name": skill_ref,
                "stability_gap": gap,
                "flagged_count": 0,
                "last_flagged": "",
                "execution_ids": [],
                "status": "monitoring",
            }

        entry = skills[skill_ref]

        # Don't flag if already evaluating or pending review
        if entry.get("status") in ("evaluating", "pending_rollback_review"):
            sys.exit(0)

        entry["flagged_count"] = entry.get("flagged_count", 0) + 1
        entry["stability_gap"] = gap
        entry["last_flagged"] = datetime.now(UTC).isoformat()
        invocation_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
        entry["execution_ids"].append(invocation_id)

        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text(json.dumps(queue_data, indent=2))

        status = "critical" if gap > CRITICAL_GAP_THRESHOLD else "degrading"
        trigger = entry["flagged_count"] >= 3

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
