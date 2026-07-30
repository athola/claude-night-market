#!/usr/bin/env python3
"""Block a commit that would carry undrained captures.

The capture index is tracked so the drain has something to converge on.
That only means anything if what lands is drained, so this gate asserts
the invariant directly: zero ``pending`` entries in the index the commit
is about to carry.

It runs after the promote and prune-orphans cycles in
``precommit_palace_maintenance.sh``, which resolve everything they can.
What survives is the promoter's ``hold`` case: a capture whose score sits
below the promote threshold that is neither stale enough to archive nor
orphaned. No amount of re-running the drain moves it. It needs a call
from a person, and this gate is where that call gets asked for.

Read-only and deterministic: it reports and exits, and never edits the
index.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from memory_palace.corpus.index_analytics import (
    INERT_ROUTING_TYPE,
    load_capture_index,
)

DEFAULT_INDEX = (
    Path(__file__).resolve().parents[1] / "hooks" / "memory-palace-index.yaml"
)

# Keys listed before the report truncates. A backlog the size of the one
# drained in 2ed3737b (47 entries) would otherwise bury the remediation
# line under its own output.
MAX_LISTED = 10

_DRAIN_COMMAND = (
    "    cd plugins/memory-palace && uv run python scripts/memory_palace_cli.py "
    "index promote --apply --top 0"
)


def pending_keys(index: dict) -> list[str]:
    """Return the keys of entries the drain has not routed.

    Keyed on ``routing_type`` alone. ``index_analytics._is_inert`` also
    requires the default maturity and importance score, which describes
    a capture nothing has touched. An entry that was scored but never
    routed is not inert by that definition and is still work the drain
    owes, so this gate uses the looser test. A missing ``routing_type``
    counts as pending: entries predate the field, and reading absence as
    "already routed" would let the backlog back in through the gap.
    """
    return sorted(
        key
        for key, entry in index.get("entries", {}).items()
        if entry.get("routing_type", INERT_ROUTING_TYPE) == INERT_ROUTING_TYPE
    )


def _report(pending: list[str]) -> None:
    """Print the blocked-commit message and how to clear it."""
    count = len(pending)
    noun = "entry" if count == 1 else "entries"
    print(
        f"[memory-palace] capture index is not drained: {count} pending {noun}.",
        file=sys.stderr,
    )
    for key in pending[:MAX_LISTED]:
        print(f"    {key}", file=sys.stderr)
    if count > MAX_LISTED:
        print(f"    ... and {count - MAX_LISTED} more", file=sys.stderr)
    print("\n  Drain them:", file=sys.stderr)
    print(_DRAIN_COMMAND, file=sys.stderr)
    print(
        "\n  What survives the drain is held on purpose: middling score, "
        "not stale,\n  not orphaned. Score or archive those with "
        "Skill(memory-palace:palace-index-curator).",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    """Exit nonzero when the index carries undrained captures."""
    parser = argparse.ArgumentParser(description="Check the capture index is drained.")
    parser.add_argument(
        "index_path",
        nargs="?",
        default=str(DEFAULT_INDEX),
        help="Capture index to check (default: the plugin's own).",
    )
    args = parser.parse_args(argv)

    path = Path(args.index_path)
    if not path.exists():
        # A tree without the capture corpus has nothing to drain. The
        # prune guard (test_index_prune_cli_guard) establishes that such
        # a tree must not fail the commit.
        return 0

    pending = pending_keys(load_capture_index(path))
    if not pending:
        return 0

    _report(pending)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
