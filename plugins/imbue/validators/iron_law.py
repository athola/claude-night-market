#!/usr/bin/env python3
"""Nen Court validator: Iron Law commit-order audit (issue #406).

Graduates "Iron Law (no impl without failing test)" from Soft Vow to
Nen Court.  Audits the first-touch timestamps of implementation files
versus their corresponding test files within a commit range.

Verdict rules:

- ``pass``         -- every implementation file has a matching test
                      committed first (or in the same commit).
- ``violation``    -- at least one implementation file was committed
                      strictly before its test.
- ``inconclusive`` -- one or more implementation files have no
                      matching test in the audited range.

Contract:

    input  (stdin JSON):
      {"commits": [
         {"sha": "...", "ts": <unix-seconds>, "files": ["...", ...]},
         ...
      ]}

    output (stdout JSON):
      {
        "verdict": "pass" | "violation" | "inconclusive",
        "evidence": [
          {"impl_file": "...", "impl_commit": "...", "impl_ts": N,
           "test_file": "..." | null, "test_commit": "..." | null,
           "test_ts": N | null, "reason": "..."},
          ...
        ],
        "recommendation": "..."
      }

    exit code:
      0 = pass, 1 = violation, 2 = inconclusive
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

_TEST_DIR_NAMES = {"tests", "test"}


def _is_test_path(path: str) -> bool:
    """Return True iff *path* looks like a test file."""
    parts = path.split(os.sep) if os.sep in path else path.split("/")
    if any(p in _TEST_DIR_NAMES for p in parts):
        return True
    base = parts[-1] if parts else path
    return base.startswith("test_") or base.endswith("_test.py")


def impl_to_test_paths(impl_path: str) -> list[str]:
    """Return candidate test file paths for an implementation file.

    Returns an empty list for non-Python files or files that already
    look like tests.
    """
    if _is_test_path(impl_path):
        return []
    if not impl_path.endswith(".py"):
        return []
    parts = impl_path.split("/")
    base = parts[-1]
    test_base = f"test_{base}"
    candidates: list[str] = []
    # Mirror src/ -> tests/ (preserving subpath after src/).
    if "src" in parts:
        idx = parts.index("src")
        sub = parts[idx + 1 : -1]
        candidates.append("/".join(["tests", *sub, test_base]))
        candidates.append("/".join(["tests", "unit", *sub, test_base]))
    # Sibling tests/ directory at the same depth.
    candidates.append("/".join([*parts[:-1], "tests", test_base]))
    candidates.append("/".join(["tests", test_base]))
    candidates.append("/".join(["tests", "unit", test_base]))
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def analyze_commit_order(commits: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyse commit ordering for Iron Law compliance.

    *commits* is a list of {"sha", "ts", "files"} dicts.  Order is
    chronological by ``ts``.  Returns a verdict dict.
    """
    # Sort defensively in case caller passed unordered commits.
    commits = sorted(commits, key=lambda c: c.get("ts", 0))
    # First-touch records: file -> (sha, ts).
    first_touch: dict[str, tuple[str, int]] = {}
    for c in commits:
        sha = str(c.get("sha", ""))
        ts = int(c.get("ts", 0))
        for f in c.get("files", []):
            first_touch.setdefault(f, (sha, ts))

    impl_files = [f for f in first_touch if not _is_test_path(f) and f.endswith(".py")]
    if not impl_files:
        return {"verdict": "pass", "evidence": [], "recommendation": ""}

    violations: list[dict[str, Any]] = []
    inconclusive: list[dict[str, Any]] = []

    for impl in impl_files:
        impl_sha, impl_ts = first_touch[impl]
        candidates = impl_to_test_paths(impl)
        matching_test = next((t for t in candidates if t in first_touch), None)
        if matching_test is None:
            inconclusive.append(
                {
                    "impl_file": impl,
                    "impl_commit": impl_sha,
                    "impl_ts": impl_ts,
                    "test_file": None,
                    "test_commit": None,
                    "test_ts": None,
                    "reason": (
                        f"no test file found for {impl} in range "
                        f"(checked {len(candidates)} candidate paths)"
                    ),
                }
            )
            continue
        test_sha, test_ts = first_touch[matching_test]
        if test_ts > impl_ts:
            violations.append(
                {
                    "impl_file": impl,
                    "impl_commit": impl_sha,
                    "impl_ts": impl_ts,
                    "test_file": matching_test,
                    "test_commit": test_sha,
                    "test_ts": test_ts,
                    "reason": (
                        f"impl {impl} ({impl_sha[:8]}@{impl_ts}) committed "
                        f"before test {matching_test} ({test_sha[:8]}@{test_ts})"
                    ),
                }
            )

    if violations:
        return {
            "verdict": "violation",
            "evidence": violations,
            "recommendation": (
                "Iron Law: write a failing test BEFORE the implementation. "
                "If the impl-before-test pattern was deliberate (refactor "
                "without behaviour change), document it in the commit "
                "message and re-run the audit."
            ),
        }
    if inconclusive:
        return {
            "verdict": "inconclusive",
            "evidence": inconclusive,
            "recommendation": (
                "One or more implementations have no matching test in the "
                "audited commit range.  Either add tests, exclude the "
                "files (config, generated code), or extend the audit "
                "range to include the test commits."
            ),
        }
    return {"verdict": "pass", "evidence": [], "recommendation": ""}


def main() -> None:
    """Entry point for stdin-driven validator invocation."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {
                    "verdict": "inconclusive",
                    "evidence": [{"error": f"invalid JSON on stdin: {exc}"}],
                    "recommendation": "Send a JSON object with 'commits'.",
                }
            )
        )
        sys.exit(2)

    commits = payload.get("commits")
    if commits is None:
        print(
            json.dumps(
                {
                    "verdict": "inconclusive",
                    "evidence": [{"error": "missing 'commits' key"}],
                    "recommendation": (
                        "Send a JSON object with 'commits': [{sha, ts, files}, ...]."
                    ),
                }
            )
        )
        sys.exit(2)

    result = analyze_commit_order(list(commits))
    print(json.dumps(result))
    if result["verdict"] == "pass":
        sys.exit(0)
    if result["verdict"] == "violation":
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
