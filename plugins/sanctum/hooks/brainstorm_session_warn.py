#!/usr/bin/env python3
"""SessionStart hook: warn about abandoned brainstorm sessions.

The superpowers brainstorming skill creates per-session directories at
``<project>/.superpowers/brainstorm/<id>/`` and writes a
``state/server-stopped`` marker when the brainstorm UI server exits.
Abandoned sessions accumulate when the workflow is interrupted, and
the on-disk artefacts (HTML pages, logs) drift out of sync with the
git-tracked design that ultimately landed.

This hook scans the project root on session start, lists any session
directories that carry the abandonment marker, and surfaces a warning
to Claude via ``additionalContext`` so the next agent run can offer
to clean them up. The hook never deletes anything itself: cleanup is
an irreversible action and stays under user control.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path


def find_stale_sessions(project_dir: Path) -> list[Path]:
    """Return brainstorm session directories with abandonment markers.

    A session is considered stale if its
    ``state/server-stopped`` marker file exists. Live sessions
    (no marker) are not returned; we never assume a session is dead
    just because its pid file is present, because we cannot
    distinguish a crashed pid from an actively running one without
    OS-specific introspection.
    """
    root = project_dir / ".superpowers" / "brainstorm"
    if not root.exists():
        return []

    stale: list[Path] = []
    for session_dir in sorted(root.iterdir()):
        if not session_dir.is_dir():
            continue
        marker = session_dir / "state" / "server-stopped"
        if marker.exists():
            stale.append(session_dir)
    return stale


def _format_warning(stale: list[Path], project_dir: Path) -> str:
    """Build the additionalContext block listing stale sessions."""
    lines = [
        "## Abandoned brainstorm sessions detected",
        "",
        (
            "The following ``.superpowers/brainstorm/`` directories"
            " carry a ``state/server-stopped`` marker, indicating an"
            " abandoned brainstorm. They are not deleted automatically."
        ),
        "",
    ]
    rels: list[str] = []
    for d in stale:
        try:
            rel = d.relative_to(project_dir)
        except ValueError:
            rel = d
        rels.append(str(rel))
        lines.append(f"- `{rel}`")

    # Emit a single copy-pasteable cleanup line so the next agent (or
    # the user) can act in one shell invocation instead of composing
    # one ``rm -rf`` per session by hand. shlex.quote keeps unusual
    # session ids (spaces, shell metacharacters) safe.
    cleanup_cmd = "rm -rf " + " ".join(shlex.quote(r) for r in rels)
    lines.extend(
        [
            "",
            "To remove all listed sessions in one go, run:",
            "",
            "```",
            cleanup_cmd,
            "```",
            "",
            (
                "Do not run this without confirming the brainstorm"
                " landed (or is no longer needed) -- the HTML/log"
                " artefacts may still be useful for retrospective"
                " review."
            ),
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Emit an additionalContext warning when stale brainstorms exist."""
    try:
        sys.stdin.read()  # SessionStart payload is unused but must be consumed.
    except (OSError, ValueError):
        sys.exit(0)

    project_dir_str = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PWD", ".")
    project_dir = Path(project_dir_str)

    try:
        stale = find_stale_sessions(project_dir)
    except OSError:
        sys.exit(0)  # Non-critical -- never block session start.

    if not stale:
        sys.exit(0)

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": _format_warning(stale, project_dir),
        }
    }
    print(json.dumps(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
