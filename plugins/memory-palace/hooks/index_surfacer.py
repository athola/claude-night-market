#!/usr/bin/env python3
"""Surface promoted captures at session start (SessionStart hook).

Turns the capture index from a write-only buffer into an active prompt:
when the session begins, it injects a short note about the highest-value
already-promoted captures so the model knows what curated knowledge is
on hand. Pending and archived entries are never surfaced.

Disabled by default. Enable via ``feature_flags.context_injection: true``
in ``memory-palace-config.yaml``. Every failure path exits silently so a
SessionStart hook can never block a session.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from shared.config import get_config
from shared.deduplication import _load_index

if TYPE_CHECKING:
    from typing import Any

# Only entries at or above this importance are worth interrupting for.
DEFAULT_MIN_IMPORTANCE = 70
# How many captures to name at most.
DEFAULT_LIMIT = 5
# Routing types that mean "not part of the active corpus".
_EXCLUDED_ROUTING = frozenset({"pending", "archived"})


def select_surfaced_entries(
    index: dict[str, Any],
    limit: int = DEFAULT_LIMIT,
    min_importance: int = DEFAULT_MIN_IMPORTANCE,
) -> list[dict[str, Any]]:
    """Pick promoted entries worth surfacing, highest importance first.

    Pending and archived entries are excluded, as are entries below the
    importance floor. Returns at most ``limit`` entries, each a copy of
    the entry dict with its index key added under ``key``.
    """
    eligible: list[dict[str, Any]] = []
    for key, entry in index.get("entries", {}).items():
        if entry.get("routing_type") in _EXCLUDED_ROUTING:
            continue
        if int(entry.get("importance_score", 0)) < min_importance:
            continue
        eligible.append({"key": key, **entry})

    eligible.sort(key=lambda entry: int(entry.get("importance_score", 0)), reverse=True)
    return eligible[:limit]


def format_context(entries: list[dict[str, Any]]) -> str:
    """Render selected entries into a SessionStart context string."""
    lines = [
        f"Memory Palace: {len(entries)} curated capture(s) on hand "
        "(promoted from the research index):",
    ]
    for entry in entries:
        title = entry.get("title", entry.get("key", "untitled"))
        score = entry.get("importance_score", "?")
        lines.append(f"  - {title} (importance {score})")
    lines.append(
        "Search them with /memory-palace:knowledge-locator before "
        "researching these topics anew.",
    )
    return "\n".join(lines)


def build_session_context(
    index: dict[str, Any],
    enabled: bool,
    limit: int = DEFAULT_LIMIT,
    min_importance: int = DEFAULT_MIN_IMPORTANCE,
) -> str | None:
    """Build the additionalContext string, or None to stay silent.

    Returns None when the feature is disabled or when nothing qualifies,
    so the hook only speaks up when it has something useful to add.
    """
    if not enabled:
        return None
    entries = select_surfaced_entries(index, limit=limit, min_importance=min_importance)
    if not entries:
        return None
    return format_context(entries)


def main() -> None:
    """Run the SessionStart hook entry point."""
    try:
        json.load(sys.stdin)  # Drain the event payload; we key off config + index.
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    try:
        config = get_config()
        enabled = bool(config.get("feature_flags", {}).get("context_injection", False))
        context = build_session_context(_load_index(), enabled=enabled)
    except Exception:  # noqa: BLE001 - a SessionStart hook must never block
        sys.exit(0)

    if context:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context,
                    },
                }
            )
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
