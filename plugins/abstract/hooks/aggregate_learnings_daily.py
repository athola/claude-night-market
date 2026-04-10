#!/usr/bin/env python3
"""Daily learning aggregation hook for UserPromptSubmit.

Runs aggregate_skill_logs.py on a daily cadence (once per 24h) to generate
LEARNINGS.md, then chains to auto_promote_learnings.py for severity-based
issue creation.

Must complete in <2s with no user-visible output.

Part of the improvement feedback loop (Issue #69).
"""

from __future__ import annotations

# pyright: reportPossiblyUnboundVariable=false
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any

# Add sibling directories to path for imports.
# In plugin-cache context, __file__ may not be adjacent to scripts/.
# Try both the cached location and the original plugin layout.
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
    from aggregate_skill_logs import (
        aggregate_logs,
        extract_pinned_section,
        generate_learnings_md,
        get_learnings_path,
        get_log_directory,
    )
    from auto_promote_learnings import run_auto_promote as _promote
    from post_learnings_to_discussions import (
        post_learnings as _post_learnings,
    )

    _HAS_SCRIPTS = True
except ImportError as _imp_err:
    _HAS_SCRIPTS = False
    print(
        f"[aggregate_learnings_daily] script imports unavailable: {_imp_err}",
        file=sys.stderr,
    )

# 24 hours in seconds
CADENCE_SECONDS = 24 * 3600


def get_timestamp_path() -> Path:
    """Get path to the last-aggregation timestamp file."""
    return Path.home() / ".claude" / "skills" / "logs" / ".last_aggregation"


def should_aggregate() -> bool:
    """Check if aggregation is due (>24h since last run).

    Returns:
        True if aggregation should run.

    """
    ts_path = get_timestamp_path()

    if not ts_path.exists():
        return True

    try:
        last_run = float(ts_path.read_text().strip())
        elapsed = time.time() - last_run
        return elapsed >= CADENCE_SECONDS
    except (ValueError, OSError) as exc:
        # Corrupt or unreadable file — treat as never run
        print(f"[aggregate_learnings_daily] timestamp read: {exc}", file=sys.stderr)
        return True


def has_logs_to_aggregate() -> bool:
    """Check if there are any log files to aggregate.

    Returns:
        True if JSONL log files exist in the log directory.

    """
    if not _HAS_SCRIPTS:
        return False

    log_dir = get_log_directory()

    if not log_dir.exists():
        return False

    # Look for any .jsonl files in plugin/skill subdirectories
    return any(log_dir.rglob("*.jsonl"))


def update_timestamp() -> None:
    """Update the last-aggregation timestamp to now."""
    ts_path = get_timestamp_path()
    ts_path.parent.mkdir(parents=True, exist_ok=True)
    ts_path.write_text(str(time.time()))


def format_hook_output() -> str:
    """Format the UserPromptSubmit hook response.

    UserPromptSubmit hooks use hookSpecificOutput schema, not
    the PreToolUse decision schema.
    """
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "",
            }
        }
    )


def _run_aggregate() -> Any:
    """Run the aggregation logic from aggregate_skill_logs.py.

    Returns:
        AggregationResult from the aggregation.

    """
    return aggregate_logs(days_back=30)


def _write_learnings(result: Any) -> None:
    """Write LEARNINGS.md from aggregation result.

    Reads any existing Pinned Learnings section before
    regenerating so that pinned entries survive the 30-day
    rolling window.
    """
    learnings_path = get_learnings_path()
    existing_pinned = ""
    if learnings_path.exists():
        existing_pinned = extract_pinned_section(learnings_path.read_text())
    content = generate_learnings_md(result, existing_pinned=existing_pinned)
    learnings_path.parent.mkdir(parents=True, exist_ok=True)
    learnings_path.write_text(content)


def run_aggregation() -> bool:
    """Execute the aggregation pipeline.

    Returns:
        True if aggregation succeeded, False on error.

    """
    try:
        result = _run_aggregate()
        _write_learnings(result)
        return True
    except Exception:
        # Hook must not block the user, but log to stderr for diagnostics
        print(
            f"[aggregate_learnings_daily] aggregation: {traceback.format_exc()}",
            file=sys.stderr,
        )
        return False


def run_auto_promote() -> None:
    """Chain to auto-promotion after successful aggregation."""
    if not _HAS_SCRIPTS:
        return
    try:
        _promote()
    except Exception:
        # Promotion is best-effort, but log to stderr for diagnostics
        print(
            f"[aggregate_learnings_daily] auto-promote: {traceback.format_exc()}",
            file=sys.stderr,
        )


def run_post_learnings() -> None:
    """Chain to learnings Discussion posting after aggregation."""
    if not _HAS_SCRIPTS:
        return
    try:
        _post_learnings()
    except Exception:
        # Posting is best-effort; log for diagnostics
        print(
            f"[aggregate_learnings_daily] post-learnings: {traceback.format_exc()}",
            file=sys.stderr,
        )


def run_daily_pipeline() -> None:
    """Main pipeline: check cadence → aggregate.

    Called on every UserPromptSubmit. Skips quickly if not due.
    Network-heavy operations (auto_promote, post_learnings) are
    handled by the Stop hook (post_learnings_stop.py) to avoid
    exceeding the 2-second UserPromptSubmit timeout.
    """
    if not should_aggregate():
        return

    if not has_logs_to_aggregate():
        return

    success = run_aggregation()
    if success:
        update_timestamp()


def main() -> None:
    """Hook entry point — reads stdin, runs pipeline, outputs JSON."""
    # Read and discard stdin (hook protocol)
    try:
        sys.stdin.read()
    except Exception:
        print(
            f"[aggregate_learnings_daily] stdin read: {traceback.format_exc()}",
            file=sys.stderr,
        )

    # Run the daily pipeline (silent, fast)
    try:
        run_daily_pipeline()
    except Exception:
        print(
            f"[aggregate_learnings_daily] pipeline: {traceback.format_exc()}",
            file=sys.stderr,
        )

    # Always allow the prompt through
    print(format_hook_output())


if __name__ == "__main__":
    main()
