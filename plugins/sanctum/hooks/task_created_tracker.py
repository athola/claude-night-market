#!/usr/bin/env python3
"""Track task creation for workflow completeness monitoring.

Records TaskCreate tool invocations to a session-scoped JSONL ledger
so the Stop hook (verify_workflow_complete.py) can check whether
all created tasks reached completion before session end.

Two payload shapes are accepted:

* **PostToolUse for TaskCreate** (current Claude Code shape, fires
  reliably). The payload contains ``hook_event_name``, ``tool_name``,
  ``tool_input`` (with ``subject``/``description``/``activeForm``)
  and a ``tool_response`` of the form
  ``"Task #N created successfully: <subject>"``.

* **Legacy TaskCreated** (kept for forward/backward compatibility if
  the dedicated event is reintroduced). The payload contains
  ``task_id`` and ``description`` at the top level.

The hook is non-critical: any failure path exits 0 silently so it
never blocks tool execution. Empty/unparseable payloads are skipped
without writing -- this prevents the ledger pollution regression
that produced 394 empty entries in ``tasks_unknown.jsonl``.
"""

from __future__ import annotations

import json
import os
import re
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

# Matches the integer id embedded in TaskCreate tool responses, e.g.
# "Task #1 created successfully: Mission scaffold + state files".
_TASK_ID_RE = re.compile(r"Task\s*#(\d+)\b")


def _extract_from_post_tool_use(payload: dict) -> tuple[str, str]:
    """Return (task_id, description) for a PostToolUse TaskCreate event.

    Returns empty strings for either field that cannot be recovered.
    """
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or ""

    description = tool_input.get("description") or tool_input.get("subject") or ""

    task_id = ""
    if isinstance(tool_response, str):
        match = _TASK_ID_RE.search(tool_response)
        if match:
            task_id = match.group(1)

    return task_id, description


def _extract_from_legacy(payload: dict) -> tuple[str, str]:
    """Return (task_id, description) for the legacy TaskCreated event."""
    return (
        str(payload.get("task_id", "")),
        payload.get("description", "") or "",
    )


def main() -> None:
    """Read a hook payload from stdin and append a ledger entry."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if not isinstance(input_data, dict):
        sys.exit(0)

    # Branch on payload shape. PostToolUse delivers ``tool_name``;
    # legacy TaskCreated delivers ``task_id`` at top level.
    is_post_tool_use = (
        input_data.get("hook_event_name") == "PostToolUse" or "tool_name" in input_data
    )

    if is_post_tool_use:
        if input_data.get("tool_name") != "TaskCreate":
            sys.exit(0)
        task_id, task_description = _extract_from_post_tool_use(input_data)
    else:
        task_id, task_description = _extract_from_legacy(input_data)

    # Skip writes when we cannot recover anything useful. This avoids
    # the empty-row pollution that hid real signal in the ledger.
    if not task_id and not task_description:
        sys.exit(0)

    if not task_id:
        # Without an id we cannot correlate against TaskUpdate/Complete
        # later, so the entry would not aid completeness checks.
        sys.exit(0)

    session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

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
        pass  # Non-critical -- never block the tool call.

    print(
        f"[TaskCreated] Tracking task {task_id}: {task_description[:80]}",
        file=sys.stderr,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
