#!/usr/bin/env python3
"""Verify workflow completion hook for Stop event.

Provides a final reminder about the post-implementation protocol.
This is a backup safeguard - Stop hooks cannot block, only inform.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

REMINDER = """
## Post-Implementation Checklist Reminder

If you just completed a feature implementation or plan execution,
verify you ran these commands:

- [ ] `/sanctum:update-docs`
- [ ] `/abstract:make-dogfood`
- [ ] `/sanctum:update-readme`
- [ ] `/sanctum:update-tests`

If not applicable (simple fix, research, etc.), disregard this reminder.
""".strip()


def main() -> None:
    """Provide workflow reminder at session end."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No payload or invalid JSON - still provide reminder
        pass

    response = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": REMINDER
        }
    }
    print(json.dumps(response))
    sys.exit(0)


if __name__ == '__main__':
    main()
