#!/usr/bin/env python3
"""Post learnings to GitHub Discussions on session Stop.

Decoupled from the UserPromptSubmit aggregation hook to avoid the
2-second timeout.  Stop hooks run once per session and have a
separate timeout budget (10 s), which is enough for the 5 sequential
GraphQL calls that post_learnings requires.

Part of the improvement feedback loop (Issue #69).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_START = time.monotonic()
_BUDGET_SECONDS = 8.5  # Leave headroom within 10s hook timeout
# Skip the lens pass rather than start one that cannot finish in the budget.
_MIN_LENS_SECONDS = 2.0

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
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from shared.best_effort import best_effort  # noqa: E402 - import after path setup

_HOOK = "post_learnings_stop"

try:
    from auto_promote_learnings import (
        run_auto_promote as _promote,
    )
    from post_learnings_to_discussions import (
        post_learnings as _post_learnings,
    )

    _HAS_SCRIPTS = True
except ImportError:
    _HAS_SCRIPTS = False

try:
    from aggregate_skill_logs import aggregate_logs
    from insight_analyzer import build_context, run_analysis
    from insight_registry import InsightRegistry
    from post_insights_to_discussions import post_findings

    _HAS_INSIGHT_ENGINE = True
except ImportError:
    _HAS_INSIGHT_ENGINE = False

try:
    from insight_palace_bridge import ingest_findings as _ingest_to_palace

    _HAS_PALACE_BRIDGE = True
except ImportError:
    _HAS_PALACE_BRIDGE = False


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
    # Read and discard stdin (hook protocol sends JSON payload)
    try:
        raw = sys.stdin.read()
        if raw.strip():
            json.loads(raw)
    except (json.JSONDecodeError, ValueError, OSError, EOFError):
        pass  # Hook protocol: stdin may be empty, closed, or malformed

    if not _HAS_SCRIPTS or not _learnings_have_content():
        return

    # Auto-promote high-severity items to Issues
    best_effort(_HOOK, "auto-promote", _promote)

    # Post learnings summary to Discussions
    best_effort(_HOOK, "post-learnings", _post_learnings)

    # Run insight engine lenses if budget remains
    remaining = _BUDGET_SECONDS - (time.monotonic() - _START)
    if _HAS_INSIGHT_ENGINE and remaining > _MIN_LENS_SECONDS:
        best_effort(_HOOK, "insight-engine", _run_insight_lenses)
    elif _HAS_INSIGHT_ENGINE:
        print(
            f"[post_learnings_stop] skipping insight lenses "
            f"({remaining:.1f}s remaining)",
            file=sys.stderr,
        )


def _run_insight_lenses() -> None:
    """Run lightweight insight lenses and post findings."""
    result = aggregate_logs(days_back=30)
    registry = InsightRegistry()
    previous_snapshot = registry.load_snapshot()

    ctx = build_context(
        metrics=result.metrics_by_skill,
        trigger="stop",
        previous_snapshot=previous_snapshot if previous_snapshot else None,
    )

    findings = run_analysis(ctx, weight_filter="lightweight")
    if not findings:
        return

    posted = post_findings(findings, registry=registry)

    # Ingest findings into memory palace if available
    if _HAS_PALACE_BRIDGE:
        remaining = _BUDGET_SECONDS - (time.monotonic() - _START)
        best_effort(
            _HOOK,
            "palace-bridge",
            lambda: _ingest_to_palace(findings, budget_remaining=remaining),
        )

    # Save current metrics as snapshot for next delta comparison
    snapshot = {
        skill: {
            "success_rate": m.success_rate,
            "avg_duration_ms": m.avg_duration_ms,
        }
        for skill, m in result.metrics_by_skill.items()
    }
    registry.save_snapshot(snapshot)

    if posted:
        print(
            f"[post_learnings_stop] posted {len(posted)} insight(s)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
