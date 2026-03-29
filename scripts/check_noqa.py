#!/usr/bin/env python3
"""Pre-commit hook: reject inline lint suppression directives.

Scans staged Python files for ``# noqa``, ``# type: ignore``,
``# pylint: disable``, and other inline suppression comments.

Uses the same detection logic as the leyline PreToolUse hook
(``plugins/leyline/hooks/noqa_guard.py``).

Exit codes:
    0 - no suppressions found
    1 - suppressions detected (commit blocked)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"#\s*noqa\b"), "# noqa"),
    (re.compile(r"#\s*type:\s*ignore"), "# type: ignore"),
    (re.compile(r"#\s*pylint:\s*disable"), "# pylint: disable"),
    (re.compile(r"#\[allow\("), "#[allow(...)]"),
    (re.compile(r"//\s*eslint-disable"), "eslint-disable"),
    (re.compile(r"//\s*@ts-ignore"), "@ts-ignore"),
    (re.compile(r"//\s*@ts-expect-error"), "@ts-expect-error"),
    (re.compile(r"//\s*nolint"), "//nolint"),
]


def check_file(path: Path) -> list[str]:
    """Return suppression descriptions found in a file."""
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        for pattern, label in _PATTERNS:
            if pattern.search(line):
                stripped = line.strip()
                hits.append(f"  {path}:{i} ({label}): {stripped[:80]}")
                break
    return hits


def main(argv: list[str] | None = None) -> int:
    """Scan files for inline lint suppressions."""
    files = argv if argv is not None else sys.argv[1:]
    if not files:
        return 0

    all_hits: list[str] = []
    for f in files:
        all_hits.extend(check_file(Path(f)))

    if all_hits:
        print(
            "BLOCKED: inline lint suppression comments are not allowed.\n"
            "Fix the issue directly, or add the rule to the project\n"
            "config file (pyproject.toml per-file-ignores, .eslintrc,\n"
            "Cargo.toml, etc.).\n"
        )
        print("Detected suppressions:")
        for hit in all_hits:
            print(hit)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
