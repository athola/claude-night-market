#!/usr/bin/env python3
"""Pre-commit check: flag when the locked ruff lags the latest PyPI release.

The repo pins a single uv-managed ruff in ``uv.lock`` shared by this gate
and ``make format`` / ``uv run ruff`` (see .pre-commit-config.yaml). This
hook surfaces when that ruff has fallen behind upstream so it gets bumped
deliberately rather than silently drifting.

Advisory by design: it prints a prominent notice with the exact bump
command when the locked ruff is older than the latest PyPI release, but
always exits 0 so it never hard-blocks a commit. Ruff ships weekly and a
minor bump can carry a migration (0.14 -> 0.15 added 9 StrEnum findings),
so blocking on every release would force that work on whoever next
touches a dependency. Set ``OUTDATED_IS_BLOCKING`` to True to enforce.

Runs only when ``pyproject.toml`` or ``uv.lock`` is staged (see the
hook's ``files:`` filter), so ordinary commits pay no network cost.
Skips cleanly when offline or when the locked version cannot be read.

Exit codes:
    0 - current, or advisory-only, or unable to check (offline)
    1 - only when OUTDATED_IS_BLOCKING and the locked ruff is behind
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request

PYPI_URL = "https://pypi.org/pypi/ruff/json"
UV_LOCK = "uv.lock"
OUTDATED_IS_BLOCKING = False


def locked_version() -> str | None:
    """Return the ruff version pinned in uv.lock, or None."""
    try:
        text = open(UV_LOCK, encoding="utf-8").read()
    except OSError:
        return None
    for block in text.split("[[package]]"):
        if re.search(r'^name = "ruff"$', block, re.MULTILINE):
            match = re.search(r'^version = "([^"]+)"', block, re.MULTILINE)
            if match:
                return match.group(1)
    return None


def latest_version() -> str | None:
    """Return the latest ruff version on PyPI, or None (offline/error)."""
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=5) as response:
            return json.load(response)["info"]["version"]
    except Exception:
        return None


def _as_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", version))


def main() -> int:
    locked = locked_version()
    if not locked:
        print("check_ruff_version: could not resolve locked ruff; skipping")
        return 0
    latest = latest_version()
    if not latest:
        print(
            f"check_ruff_version: PyPI unreachable (offline?); "
            f"ruff {locked} locked, skipping"
        )
        return 0
    if _as_tuple(locked) >= _as_tuple(latest):
        print(f"check_ruff_version: ruff {locked} is current (latest {latest}).")
        return 0

    message = (
        f"check_ruff_version: ruff {locked} is locked but {latest} is "
        f"available.\n"
        f"  Bump with: uv lock --upgrade-package ruff\n"
        f"  Then verify: uv run ruff format --config pyproject.toml "
        f"--check . && uv run ruff check --config pyproject.toml ."
    )
    print(message, file=sys.stderr)
    return 1 if OUTDATED_IS_BLOCKING else 0


if __name__ == "__main__":
    raise SystemExit(main())
