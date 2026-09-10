#!/usr/bin/env python3
"""Log auto-mode permission denials for observability.

Fires on PermissionDenied events (new in v2.1.89). When auto mode's
classifier denies a tool call, this hook logs the denial and optionally
signals retry for known-safe patterns.

Return {retry: true} to tell the model it can retry the denied tool.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Tools that are safe to retry after denial (read-only operations)
RETRY_SAFE_TOOLS = frozenset({"Read", "Glob", "Grep", "WebFetch", "WebSearch"})


def log_dir() -> Path:
    """Where the log lives, resolved per call rather than at import.

    A module-level constant freezes the project root at import time,
    which makes the destination untestable and silently wrong for any
    caller that sets ``CLAUDE_PROJECT_DIR`` afterwards. The sibling
    ``background_agent_notice.py`` documents the same reason; this hook
    kept the constant.
    """
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PWD") or "."
    return Path(root) / ".claude" / "logs"


def main() -> None:
    """Record a denied tool call to the permission log, then exit quietly.

    Runs as a hook, so any failure to parse or write must still exit 0:
    a logging hook may never block the tool path it observes.
    """
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "unknown")
    reason = input_data.get("reason", "")
    timestamp = datetime.now(timezone.utc).isoformat()

    # Log the denial
    print(
        f"[PermissionDenied] {timestamp} tool={tool_name} reason={reason}",
        file=sys.stderr,
    )

    # Append to denial log file for post-session analysis
    try:
        destination = log_dir()
        destination.mkdir(parents=True, exist_ok=True)
        log_file = destination / "permission_denials.jsonl"
        entry = {
            "timestamp": timestamp,
            "tool": tool_name,
            "reason": reason,
            "session": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # Non-critical logging failure

    # Auto-retry read-only tools (safe to re-attempt)
    if tool_name in RETRY_SAFE_TOOLS:
        output = {"retry": True}
        print(json.dumps(output))
        print(
            f"[PermissionDenied] Auto-retry for read-only tool: {tool_name}",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
