#!/usr/bin/env python3
"""Post learnings to GitHub Discussions on session Stop.

Decoupled from the UserPromptSubmit aggregation hook to avoid the
2-second timeout.  Stop hooks run once per session and have a
separate timeout budget (10 s), which is enough for the 5 sequential
GraphQL calls that post_learnings requires.

Part of the improvement feedback loop (Issue #69).
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# ------------------------------------------------------------------
# Path setup — same pattern as aggregate_learnings_daily.py
# ------------------------------------------------------------------
_hooks_dir = Path(__file__).resolve().parent
_candidate_dirs = [
    _hooks_dir.parent / "scripts",
    _hooks_dir.parent.parent / "scripts",
    _hooks_dir / "scripts",
]
for _d in _candidate_dirs:
    if _d.is_dir() and str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

try:
    from auto_promote_learnings import (  # noqa: E402
        run_auto_promote as _promote,
    )
    from post_learnings_to_discussions import (  # noqa: E402
        post_learnings as _post_learnings,
    )

    _HAS_SCRIPTS = True
except ImportError:
    _HAS_SCRIPTS = False


def _learnings_have_content() -> bool:
    """Check whether LEARNINGS.md has skills worth posting."""
    learnings = Path.home() / ".claude" / "skills" / "LEARNINGS.md"
    if not learnings.exists():
        return False
    try:
        text = learnings.read_text()
        # The aggregator writes "Skills Analyzed: 0" when empty
        return "**Skills Analyzed**: 0" not in text
    except OSError:
        return False


def main() -> None:
    """Stop-hook entry point: promote and post learnings."""
    # Read and discard stdin (hook protocol)
    try:
        sys.stdin.read()
    except (OSError, EOFError):
        pass  # Hook protocol: stdin may be empty or closed

    if not _HAS_SCRIPTS or not _learnings_have_content():
        return

    # Auto-promote high-severity items to Issues
    try:
        _promote()
    except Exception:
        print(
            f"[post_learnings_stop] auto-promote: {traceback.format_exc()}",
            file=sys.stderr,
        )

    # Post learnings summary to Discussions
    try:
        _post_learnings()
    except Exception:
        print(
            f"[post_learnings_stop] post-learnings: {traceback.format_exc()}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
