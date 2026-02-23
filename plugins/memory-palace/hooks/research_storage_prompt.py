#!/usr/bin/env python3
"""PostToolUse hook: prompt user to store research after WebSearch.

Issue #118: Auto-prompt for research storage after web search.

After a WebSearch completes, this hook emits a brief reminder suggesting
the user store valuable findings via the knowledge-intake skill.  It reads
the intake queue written by research_interceptor.py to check whether the
query was already flagged for intake (avoiding redundant prompts).

The hook is intentionally lightweight -- no heavy imports, no corpus
lookups, just a JSON message on stdout.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _recent_intake_pending(query: str) -> bool:
    """Check if research_interceptor already flagged this query for intake."""
    queue_path = PLUGIN_ROOT / "data" / "intake_queue.jsonl"
    if not queue_path.exists():
        return False

    try:
        # Read last 20 lines (most recent entries) to avoid scanning huge files
        lines = queue_path.read_text(encoding="utf-8").strip().splitlines()[-20:]
        normalized_query = query.lower().strip()
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("query", "").lower().strip() == normalized_query:
                    return True
            except (json.JSONDecodeError, KeyError):
                continue
    except (OSError, PermissionError):
        pass

    return False


def main() -> None:
    """Read PostToolUse payload and emit storage reminder."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("WebSearch", "WebFetch"):
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    query = tool_input.get("query", "") or tool_input.get("prompt", "")

    # If the pre-tool interceptor already flagged this for intake, the user
    # will get auto-intake processing -- no need to double-prompt.
    if query and _recent_intake_pending(query):
        sys.exit(0)

    # Build the reminder message
    skill_ref = "/memory-palace:knowledge-intake"
    message = f"Research detected via {tool_name}. Consider storing valuable findings with {skill_ref}"

    hook_output: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    }

    print(json.dumps(hook_output))
    sys.exit(0)


if __name__ == "__main__":
    main()
