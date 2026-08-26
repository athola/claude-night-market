"""Run a hook side-effect without letting its failure block the user.

Every hook in this plugin wraps its optional work in the same shape: call
it, and on any exception print a labelled traceback to stderr rather than
raising. Ten copies of that block lived across ``aggregate_learnings_daily``
and ``post_learnings_stop`` before this module.

The broad ``except Exception`` is deliberate and is the one place it is
correct: a hook that raises blocks the user's prompt, so the boundary
swallows everything and makes it visible on stderr instead.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def best_effort(hook: str, label: str, fn: Callable[[], T]) -> T | None:
    """Call ``fn``, reporting any failure to stderr.

    Args:
        hook: Hook name used as the log prefix, e.g. ``post_learnings_stop``.
        label: What was being attempted, e.g. ``auto-promote``.
        fn: Zero-argument callable to run.

    Returns:
        Whatever ``fn`` returned, or ``None`` if it raised.

    """
    try:
        return fn()
    except Exception:
        print(f"[{hook}] {label}: {traceback.format_exc()}", file=sys.stderr)
        return None
