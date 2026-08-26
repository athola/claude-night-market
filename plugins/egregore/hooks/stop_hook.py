#!/usr/bin/env python3
"""Egregore Stop hook: blocks exit while the loop is advancing.

Like ralph-wiggum's stop hook but state-aware. Reads the
egregore manifest to decide whether to block the exit and
re-inject the orchestration prompt.

The block is bounded. A manifest with active work is a static
condition, so blocking on it alone re-injects forever: a session
that cannot advance the pipeline still gets handed the prompt
back every time it tries to stop. Dogfooding measured that at ten
turns and roughly $0.70 for a one-word prompt on Opus. The bound
is stall detection: the manifest fingerprint is progress, and
after EGREGORE_STOP_MAX_STALLS blocks without it changing, the
hook lets the session stop. A watchdog relaunch is a new session
and starts with a fresh budget.

The bound needs durable state. When that state cannot be written,
the hook approves the stop rather than blocking: an unbounded
block is the failure being fixed here, while a released stop is
recoverable, since the watchdog relaunches the session.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from _manifest_utils import find_manifest, has_active_work, read_stdin_payload

STATE_FILENAME = "stop-hook-state.json"
DEFAULT_MAX_STALLS = 3


def max_stalls() -> int:
    """Read the stall budget from the environment."""
    try:
        configured = int(os.environ.get("EGREGORE_STOP_MAX_STALLS", ""))
    except ValueError:
        return DEFAULT_MAX_STALLS
    return configured if configured > 0 else DEFAULT_MAX_STALLS


def manifest_fingerprint(manifest_path: Path) -> str:
    """Hash the manifest bytes; the hash changing is what counts as progress."""
    try:
        return hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    except OSError:
        return ""


def load_state(state_path: Path) -> dict:
    """Read stall state, treating anything unreadable as no state."""
    try:
        state = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def save_state(state_path: Path, state: dict) -> bool:
    """Write stall state. Returns False when it could not be persisted."""
    try:
        state_path.write_text(json.dumps(state, indent=2))
    except OSError:
        return False
    return True


def consecutive_blocks(state: dict, session_id: str, fingerprint: str) -> int:
    """Count blocks already spent on this session and this manifest state."""
    if state.get("session_id") != session_id:
        return 0
    if state.get("fingerprint") != fingerprint:
        return 0
    try:
        return int(state.get("consecutive_blocks", 0))
    except (TypeError, ValueError):
        return 0


def block_reason(manifest_path: Path) -> str:
    """Build the prompt to re-inject: the relaunch prompt, or a default."""
    relaunch_path = manifest_path.parent / "relaunch-prompt.md"
    if relaunch_path.exists():
        return relaunch_path.read_text()
    return (
        "Egregore has active work items. "
        "Read .egregore/manifest.json and continue "
        "the pipeline from the current step. "
        "Invoke Skill(egregore:summon) to resume."
    )


def approve() -> None:
    """Let the session stop."""
    print(json.dumps({"decision": "approve"}))
    sys.exit(0)


def main() -> None:
    """Stop hook entry point."""
    payload = read_stdin_payload()
    session_id = str(payload.get("session_id") or "unknown")

    manifest_path = find_manifest()

    if not has_active_work(manifest_path):
        approve()

    state_path = manifest_path.parent / STATE_FILENAME
    fingerprint = manifest_fingerprint(manifest_path)
    state = load_state(state_path)
    spent = consecutive_blocks(state, session_id, fingerprint)

    if spent >= max_stalls():
        save_state(
            state_path,
            {
                "session_id": session_id,
                "fingerprint": fingerprint,
                "consecutive_blocks": spent,
                "released": True,
                "reason": (
                    f"Released after {spent} blocks with no manifest "
                    "progress. Raise EGREGORE_STOP_MAX_STALLS for "
                    "slower steps."
                ),
            },
        )
        approve()

    persisted = save_state(
        state_path,
        {
            "session_id": session_id,
            "fingerprint": fingerprint,
            "consecutive_blocks": spent + 1,
            "released": False,
        },
    )
    if not persisted:
        approve()

    print(json.dumps({"decision": "block", "reason": block_reason(manifest_path)}))
    sys.exit(0)


if __name__ == "__main__":
    main()
