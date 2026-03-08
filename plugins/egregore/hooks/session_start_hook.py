#!/usr/bin/env python3
"""Egregore SessionStart hook: resumes orchestration on boot.

When a session starts or resumes after crash/relaunch,
checks for an active egregore manifest and injects context
to resume the pipeline.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""

from __future__ import annotations

import json
import sys

from _manifest_utils import consume_stdin, find_manifest, load_manifest_data


def main() -> None:
    """SessionStart hook entry point."""
    consume_stdin()

    manifest_path = find_manifest()
    if not manifest_path.exists():
        sys.exit(0)

    data = load_manifest_data(manifest_path)
    if data is None:
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
