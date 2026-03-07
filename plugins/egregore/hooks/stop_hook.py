#!/usr/bin/env python3
"""Egregore Stop hook: blocks exit when work remains.

Like ralph-wiggum's stop hook but state-aware. Reads the
egregore manifest to decide whether to block the exit and
re-inject the orchestration prompt.

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


def has_active_work(manifest_path: Path) -> bool:
    """Check if manifest has active or paused work items."""
    if not manifest_path.exists():
        return False
    try:
        data = json.loads(manifest_path.read_text())
        items = data.get("work_items", [])
        return any(item.get("status") in ("active", "paused") for item in items)
    except (json.JSONDecodeError, OSError):
        return False


def main() -> None:
    """Stop hook entry point."""
    try:
        json.load(sys.stdin)  # consume stdin
    except (json.JSONDecodeError, ValueError):
        pass

    manifest_path = find_manifest()

    if not has_active_work(manifest_path):
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Active work remains: block exit and re-inject prompt
    relaunch_path = manifest_path.parent / "relaunch-prompt.md"
    if relaunch_path.exists():
        reason = relaunch_path.read_text()
    else:
        reason = (
            "Egregore has active work items. "
            "Read .egregore/manifest.json and continue "
            "the pipeline from the current step. "
            "Invoke Skill(egregore:summon) to resume."
        )

    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
