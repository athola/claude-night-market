#!/usr/bin/env python3
"""Egregore UserPromptSubmit hook: preserves orchestration loop.

When a user sends a prompt during an active egregore session,
this hook injects context telling the model to resume the
orchestration loop after handling the user's request.

Without this hook, user prompts break the autonomous loop:
the model handles the request, emits end_turn, and never
re-enters the pipeline.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""

from __future__ import annotations

import json
import sys

from _manifest_utils import (
    ACTIVE_STATUSES,
    consume_stdin,
    find_manifest,
    get_items,
    load_manifest_data,
)


def main() -> None:
    """UserPromptSubmit hook entry point."""
    consume_stdin()

    manifest_path = find_manifest()
    if not manifest_path.exists():
        sys.exit(0)

    data = load_manifest_data(manifest_path)
    if data is None:
        sys.exit(0)

    items = get_items(data)
    remaining = [i for i in items if i.get("status") in ACTIVE_STATUSES]

    if not remaining:
        sys.exit(0)

    # Build a concise summary of remaining work
    current = remaining[0]
    item_id = current.get("id", "?")
    stage = current.get("pipeline_stage", "?")
    step = current.get("pipeline_step", "?")

    context = (
        f"EGREGORE SESSION ACTIVE: {len(remaining)} work item(s) remaining. "
        f"Next: {item_id} at {stage}/{step}. "
        f"After handling this user request, you MUST resume the "
        f"egregore orchestration loop. Read .egregore/manifest.json "
        f"and continue processing work items. Do NOT end your turn "
        f"until all manifest items are completed or failed."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
