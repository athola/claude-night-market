"""Safety controls: confirmation gates and action filtering.

Provides human-in-the-loop confirmation before dangerous actions
and region-based blocking to prevent clicking sensitive UI areas.

.. warning::
   ``no_confirm`` approves everything. Supply your own
   ``ConfirmCallback`` for real human-in-the-loop safety.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

# Region = (x1, y1, x2, y2) top-left to bottom-right inclusive
Region = tuple[int, int, int, int]

# Confirmation callback: receives action dict, returns True to allow
ConfirmCallback = Callable[[dict[str, Any]], bool]


def no_confirm(action: dict[str, Any]) -> bool:
    """Always approve - no confirmation required.

    Use this when an explicit "no gating" semantic is desired.
    """
    return True


class ActionFilter:
    """Block actions targeting forbidden screen regions.

    Useful for preventing clicks on sensitive UI areas like
    logout buttons, payment forms, or system controls.
    """

    def __init__(self, blocked_regions: Sequence[Region] = ()) -> None:
        self.blocked_regions = list(blocked_regions)

    def is_allowed(self, action: dict[str, Any]) -> bool:
        """Check if an action is allowed given blocked regions.

        Every coordinate the action carries is checked: ``coordinate``
        (click, release point of a drag, scroll) and ``start_coordinate``
        (press point of a drag). A drag that presses inside a blocked
        region is blocked wherever it releases. Non-coordinate actions
        (type, key, screenshot) always pass.
        """
        for key in ("coordinate", "start_coordinate"):
            coord = action.get(key)
            if coord is None or len(coord) != 2:
                continue
            x, y = int(coord[0]), int(coord[1])
            for x1, y1, x2, y2 in self.blocked_regions:
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return False

        return True


class ConfirmationGate:
    """Human-in-the-loop confirmation before executing actions.

    Wraps a callback function that receives the action dict and
    returns True (proceed) or False (reject). Tracks rejection
    counts for diagnostics.
    """

    def __init__(self, callback: ConfirmCallback = no_confirm) -> None:
        self.callback = callback
        self.rejection_count: int = 0
        self.approval_count: int = 0

    def check(self, action: dict[str, Any]) -> bool:
        """Check if the action is approved.

        Returns True if the callback approves, False if rejected.
        """
        approved = self.callback(action)
        if approved:
            self.approval_count += 1
        else:
            self.rejection_count += 1
        return approved
