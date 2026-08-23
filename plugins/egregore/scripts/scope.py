"""Scope enforcement for a night-shift work item.

Two independent checks, in this order:

1. A builtin denylist that no handoff document can relax. These are the
   paths where an unattended overnight edit is unrecoverable or changes
   the rules the harness itself runs under.
2. The handoff's own ``allow_paths``, which bounds an item to the files
   its tasks declared.

The denylist is checked first and separately so that a handoff naming a
denied path is *rejected* rather than obeyed. That ordering is the whole
point: an allowlist that could authorize its own escape hatch is not a
boundary.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import PurePosixPath

#: Paths no handoff may authorize, as POSIX-style glob patterns matched
#: against the repository-relative path of each changed file.
#:
#: - CI and workflow definitions decide what gates the work at all.
#: - Lockfiles are a supply-chain surface; see
#:   ``Skill(leyline:supply-chain-advisory)``.
#: - The constitution and settings files are the rules the harness runs
#:   under. A loop that can edit its own constraints has none.
#: - Hooks execute on every tool call in every future session.
DENY_PATTERNS = (
    ".github/**",
    "**/uv.lock",
    "**/package-lock.json",
    "**/poetry.lock",
    "**/Cargo.lock",
    "**/yarn.lock",
    "CONSTITUTION.md",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/rules/**",
    "**/hooks/**",
)


@dataclass
class ScopeResult:
    """Outcome of a scope check over one set of changed paths."""

    ok: bool
    violating: list[str] = field(default_factory=list)
    reason: str = ""


def _match_segments(pattern: Sequence[str], target: Sequence[str]) -> bool:
    """Match path segments, where ``**`` spans zero or more segments.

    ``PurePath.match`` is not used here: before Python 3.13 it treats
    ``**`` as a single component, so ``**/uv.lock`` would not match a
    bare ``uv.lock`` and ``.github/**`` would not match a nested file.
    """
    if not pattern:
        return not target
    if pattern[0] == "**":
        if len(pattern) == 1:
            return True
        return any(
            _match_segments(pattern[1:], target[i:]) for i in range(len(target) + 1)
        )
    if not target:
        return False
    if not fnmatch.fnmatchcase(target[0], pattern[0]):
        return False
    return _match_segments(pattern[1:], target[1:])


def is_denied(path: str) -> bool:
    """Return True when ``path`` matches the un-overridable denylist.

    ``removeprefix`` rather than ``lstrip`` because ``lstrip`` strips a
    character set, so ``".github/..."`` would lose its leading dot and
    stop matching the pattern written to catch it.
    """
    target = path.removeprefix("./").split("/")
    return any(_match_segments(pattern.split("/"), target) for pattern in DENY_PATTERNS)


def within(allowed: str, path: str) -> bool:
    """Return True when ``path`` is ``allowed`` or sits beneath it.

    Comparison is segment-wise, so ``plugins/conjure`` does not authorize
    ``plugins/conjure-extra``. A trailing slash on ``allowed`` is treated
    the same as its absence; both mean "this path or anything under it".
    """
    allowed_parts = PurePosixPath(allowed.rstrip("/")).parts
    path_parts = PurePosixPath(path).parts
    return path_parts[: len(allowed_parts)] == allowed_parts


def check(allow_paths: Sequence[str], changed: Sequence[str]) -> ScopeResult:
    """Check ``changed`` against the denylist, then against ``allow_paths``.

    An empty ``changed`` set is not a violation. A task that produced no
    diff has failed to do its job, which the driver handles as a task
    failure; it has not breached anything.
    """
    denied = [p for p in changed if is_denied(p)]
    if denied:
        return ScopeResult(ok=False, violating=denied, reason="denylist")

    outside = [p for p in changed if not any(within(a, p) for a in allow_paths if a)]
    if outside:
        return ScopeResult(ok=False, violating=outside, reason="outside_allowlist")

    return ScopeResult(ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    """Check newline-separated paths on stdin against an allowlist."""
    parser = argparse.ArgumentParser(description="Night-shift scope check")
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        help="An allowed path prefix. Repeatable.",
    )
    args = parser.parse_args(argv)

    changed = [line.strip() for line in sys.stdin if line.strip()]
    result = check(args.allow, changed)
    print(
        json.dumps(
            {
                "ok": result.ok,
                "violating": result.violating,
                "reason": result.reason,
            }
        )
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
