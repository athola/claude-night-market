#!/usr/bin/env python3
"""Single UserPromptSubmit entry point for memory-palace.

URL detection and +recall share one registration, so a prompt pays one
interpreter start-up (#779). This reads the payload once and joins
whatever each feature contributes into one response. Both modules keep
their deferred imports, so the quiet path stays as cheap as either
alone. A feature that raises is reported on stderr and the other still
runs, as it would in a process of its own.
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Callable

import _recall
import _url_detector


def _context(prompt_context: Callable[[dict], str | None], payload: dict) -> str | None:
    """Run one feature's prompt_context, isolating its failure."""
    try:
        return prompt_context(payload)
    except Exception:  # noqa: BLE001 - one feature must not take down the other
        traceback.print_exc(file=sys.stderr)
        return None


def main() -> None:
    """Emit one combined context, or nothing when neither feature fires."""
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)

    contexts = [
        context
        for context in (
            _context(_url_detector.prompt_context, payload),
            _context(_recall.prompt_context, payload),
        )
        if context
    ]
    if contexts:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": "\n\n".join(contexts),
                    }
                }
            )
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
