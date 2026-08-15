#!/usr/bin/env python3
"""Record Notification events so a stalled background agent is visible.

``Notification`` fires when a background agent needs input or finishes
(Claude Code 2.1.218). Completion already reaches the model as a task
notification, so the case worth catching is the other one: an agent
blocked waiting for input is invisible, and the session stalls with
nothing on screen explaining why.

WHY THIS RECORDS RATHER THAN INTERPRETS
---------------------------------------

Anthropic documents how to register this hook and what it is for. The
fields it puts on stdin are not published anywhere this repo can check.
Reading ``payload["message"]`` would be a guess dressed as an interface,
and a guessed key fails silently: the hook keeps exiting 0 while logging
``unknown`` forever.

So the payload is written through verbatim, with its keys recorded
alongside. The log is the schema discovery mechanism. Once a real event
has been captured, ``observed_keys`` says what to name, and acting on a
specific field becomes a change backed by evidence rather than by
optimism.

Nothing is injected into the session. The model is already told when a
background agent completes, and a second copy in ``additionalContext``
would spend context to repeat it.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_NAME = "notifications.jsonl"


def log_dir() -> Path:
    """Where the log lives, resolved per call rather than at import.

    A module-level constant freezes the project root at import time,
    which makes the destination untestable and silently wrong for any
    caller that sets ``CLAUDE_PROJECT_DIR`` afterwards.
    """
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PWD") or "."
    return Path(root) / ".claude" / "logs"


def build_entry(payload: object) -> dict:
    """Wrap a payload in a record that keeps every field it arrived with.

    ``observed_keys`` is the discovery aid: it answers "what does this
    event actually carry" without anyone having to open the log and read
    a nested blob. A payload that is not a mapping still gets recorded,
    because an unexpected shape is itself the finding.
    """
    keys = sorted(payload.keys()) if isinstance(payload, dict) else []
    return {
        "event": "Notification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "observed_keys": keys,
        "payload": payload,
    }


def main() -> None:
    """Append one record per event, then get out of the way."""
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        sys.exit(0)

    entry = build_entry(payload)
    try:
        target = log_dir()
        target.mkdir(parents=True, exist_ok=True)
        with (target / LOG_NAME).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except OSError as error:
        # Observability is never load-bearing. A read-only checkout or a
        # path collision must not take the session down with it.
        print(f"[Notification] could not write log: {error}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    main()
