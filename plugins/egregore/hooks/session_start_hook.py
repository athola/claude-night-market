#!/usr/bin/env python3
"""Egregore SessionStart hook: resumes orchestration on boot.

When a session starts or resumes after crash/relaunch,
checks for an active egregore manifest and injects context
to resume the pipeline.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def find_manifest() -> Path:
    """Find manifest.json walking up from CWD."""
    cwd = Path(os.getcwd())
    for directory in [cwd] + list(cwd.parents):
        candidate = directory / ".egregore" / "manifest.json"
        if candidate.exists():
            return candidate
    return cwd / ".egregore" / "manifest.json"


def main() -> None:
    """SessionStart hook entry point."""
    try:
        json.load(sys.stdin)  # consume stdin
    except (json.JSONDecodeError, ValueError):
        pass

    manifest_path = find_manifest()
    if not manifest_path.exists():
        sys.exit(0)

    try:
        data = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    items = data.get("work_items", [])
    active = [i for i in items if i.get("status") in ("active", "paused")]

    if not active:
        sys.exit(0)

    current = active[0]
    summary = (
        f"Egregore session resuming. "
        f"{len(active)} active work item(s). "
        f"Current: {current.get('id', '?')} at "
        f"{current.get('pipeline_stage', '?')}/"
        f"{current.get('pipeline_step', '?')}. "
        f"Invoke Skill(egregore:summon) to continue."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
