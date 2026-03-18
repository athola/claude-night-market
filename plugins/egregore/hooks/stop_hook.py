#!/usr/bin/env python3
"""Egregore Stop hook: blocks exit when work remains.

Like ralph-wiggum's stop hook but state-aware. Reads the
egregore manifest to decide whether to block the exit and
re-inject the orchestration prompt.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""

from __future__ import annotations

import json
import sys

from _manifest_utils import consume_stdin, find_manifest, has_active_work


def main() -> None:
    """Stop hook entry point."""
    consume_stdin()

    manifest_path = find_manifest()

    if not has_active_work(manifest_path):
        print(json.dumps({"decision": "approve"}))
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
