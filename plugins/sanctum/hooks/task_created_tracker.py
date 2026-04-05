#!/usr/bin/env python3
"""Track task creation for workflow completeness monitoring.

Fires on TaskCreated events (documented in v2.1.89). Records tasks
so the Stop hook (verify_workflow_complete.py) can check whether
all created tasks reached completion before session end.

Note: TaskCreated is a blocking hook. Keep processing minimal.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATE_DIR = (
    Path(
        os.environ.get(
            "CLAUDE_PROJECT_DIR",
            os.environ.get("PWD", "."),
        )
    )
    / ".claude"
    / "state"
)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    task_id = input_data.get("task_id", "")
    task_description = input_data.get("description", "")
    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

    if not task_id:
        sys.exit(0)

    # Append to session task ledger
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        ledger_file = STATE_DIR / f"tasks_{session_id}.jsonl"
        entry = {
            "event": "created",
            "task_id": task_id,
            "description": task_description[:200],
        }
        with open(ledger_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Non-critical

    print(
        f"[TaskCreated] Tracking task {task_id}: {task_description[:80]}",
        file=sys.stderr,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
