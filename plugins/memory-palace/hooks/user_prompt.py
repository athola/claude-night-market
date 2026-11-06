#!/usr/bin/env python3
"""Single UserPromptSubmit entry point for memory-palace.

URL detection and +recall used to be two registrations, which cost two
interpreter start-ups on every prompt (#779). This reads the payload
once and joins whatever each one contributes into one response. Both
modules keep their deferred imports, so the quiet path stays as cheap
as either was alone.
"""

from __future__ import annotations

import json
import sys

import _recall
import _url_detector


def main() -> None:
    """Emit one combined context, or nothing when neither feature fires."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)

    contexts = [
        context
        for context in (
            _url_detector.prompt_context(payload),
            _recall.prompt_context(payload),
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
