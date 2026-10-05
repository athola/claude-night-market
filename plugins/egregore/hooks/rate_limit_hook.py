#!/usr/bin/env python3
"""Egregore StopFailure hook: record a rate limit in budget.json.

The summon loop asks the model to record a rate limit, but the turn that
hits the limit ends on the API error and cannot act. StopFailure runs in
place of Stop when that happens, with ``error`` naming the cause, so this
hook writes the cooldown the watchdog reads before it relaunches.

The payload carries no reset time. The cooldown recorded is the
padding configured in ``.egregore/config.json``
(``budget.cooldown_padding_minutes``, default 10), and it only ever
extends: a later cooldown already on record, such as a reset instant
read from a response header, is kept. Claude Code ignores this hook's
output and exit code, so it only writes, and fails open.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _manifest_utils import (  # noqa: E402 - sibling module on the hook's own path
    find_manifest,
    has_active_work,
    read_stdin_payload,
)
from budget import load_budget, save_budget  # noqa: E402 - scripts/ added above
from config import BudgetConfig, load_config  # noqa: E402 - scripts/ added above


def _padding_minutes(config_path: Path) -> int:
    """Return the configured padding, or the default when config is unreadable.

    A corrupt config must not stop the cooldown being recorded: the
    watchdog would then relaunch straight into the limit.
    """
    try:
        return load_config(config_path).budget.cooldown_padding_minutes
    except (OSError, ValueError) as exc:
        print(f"egregore: using default cooldown padding: {exc}", file=sys.stderr)
        return BudgetConfig().cooldown_padding_minutes


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
        recorded = budget.cooldown_until
        budget.record_rate_limit(_padding_minutes(manifest_path.parent / "config.json"))
        padded = budget.cooldown_until
        if recorded is not None and padded is not None:
            budget.cooldown_until = max(recorded, padded, key=datetime.fromisoformat)
        save_budget(budget, budget_path)
    except (OSError, ValueError) as exc:
        print(f"egregore: could not record rate limit: {exc}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
