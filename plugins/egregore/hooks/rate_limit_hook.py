#!/usr/bin/env python3
"""Egregore StopFailure hook: record a rate limit in budget.json.

The summon loop asks the model to record a rate limit, but the turn that
hits the limit ends on the API error and cannot act. StopFailure runs in
place of Stop when that happens, with ``error`` naming the cause, so this
hook writes the cooldown the watchdog reads before it relaunches.

The payload carries no reset time. The cooldown recorded is the
configured padding (``BudgetConfig.cooldown_padding_minutes``), a floor:
a later, better-informed record overwrites it. Claude Code ignores this
hook's output and exit code, so it only writes, and fails open.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _manifest_utils import (  # noqa: E402 - sibling module on the hook's own path
    find_manifest,
    has_active_work,
    read_stdin_payload,
)
from budget import load_budget, save_budget  # noqa: E402 - scripts/ added above
from config import BudgetConfig  # noqa: E402 - scripts/ added above


def main() -> None:
    """Record the cooldown when an active loop's turn hit a rate limit."""
    payload = read_stdin_payload()
    if payload.get("error") != "rate_limit":
        sys.exit(0)
    manifest_path = find_manifest()
    if not has_active_work(manifest_path):
        sys.exit(0)
    budget_path = manifest_path.parent / "budget.json"
    try:
        budget = load_budget(budget_path)
        budget.record_rate_limit(BudgetConfig().cooldown_padding_minutes)
        save_budget(budget, budget_path)
    except (OSError, ValueError) as exc:
        print(f"egregore: could not record rate limit: {exc}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
