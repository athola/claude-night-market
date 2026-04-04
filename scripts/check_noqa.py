#!/usr/bin/env python3
"""Pre-commit hook: reject inline lint suppression directives.

Scans staged Python files for ``# noqa``, ``# type: ignore``,
``# pylint: disable``, and other inline suppression comments.

Suppressions with an explanation after `` - `` are allowed::

    # noqa: PLR0912 - parsing logic requires many branches  (OK)
    # noqa: E402  (BLOCKED - no explanation)
    # noqa  (BLOCKED - bare noqa)

Uses the same detection logic as the leyline PreToolUse hook
(``plugins/leyline/hooks/noqa_guard.py``).

Exit codes:
    0 - no suppressions found (or all justified)
    1 - unjustified suppressions detected (commit blocked)
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

# Matches: # noqa: CODE1, CODE2 - some explanation
_JUSTIFIED_NOQA = re.compile(
    r"#\s*noqa:\s*[A-Z][A-Z0-9]+(?:,\s*[A-Z][A-Z0-9]+)*\s+-\s+\S"
)

# Matches: # type: ignore[code] - explanation  OR  # type: ignore[code]  # explanation
# Both forms accepted because mypy rejects the dash form as invalid syntax.
_JUSTIFIED_TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore\[[^\]]+\]\s+(?:-\s+\S|#\s+\S)")


def _is_justified(line: str, label: str) -> bool:
    """Return True if the suppression includes a justification."""
    if label == "# noqa":
        return bool(_JUSTIFIED_NOQA.search(line))
    if label == "# type: ignore":
        return bool(_JUSTIFIED_TYPE_IGNORE.search(line))
    return False


def _match_is_in_string(line: str, match_start: int) -> bool:
    """Return True if the match position is inside a string literal."""
    in_single = False
    in_double = False
    i = 0
    while i < match_start:
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            i += 2
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        i += 1
    return in_single or in_double


def check_file(path: Path) -> list[str]:
    """Return suppression descriptions found in a file."""
    hits: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return hits

    # Track multi-line string state (triple-quoted docstrings)
    in_triple_double = False
    in_triple_single = False
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        # Count triple-quote toggles on this line
        td_count = line.count('"""')
        ts_count = line.count("'''")
        if td_count % 2 == 1:
            in_triple_double = not in_triple_double
        if ts_count % 2 == 1:
            in_triple_single = not in_triple_single

        # Skip lines inside docstrings/triple-quoted strings
        if in_triple_double or in_triple_single:
            continue
        # Also skip lines that just closed a triple-quote block
        # (the closing """ line itself is part of the docstring)
        if td_count % 2 == 1 or ts_count % 2 == 1:
            continue

        for pattern, label in _PATTERNS:
            m = pattern.search(line)
            if m:
                if _is_justified(line, label):
                    break
                if _match_is_in_string(line, m.start()):
                    break
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
            "BLOCKED: unjustified inline lint suppressions found.\n"
            "Either fix the issue directly, or add an explanation:\n"
            "  # noqa: PLR0912 - parsing requires many branches\n"
        )
        print("Detected suppressions:")
        for hit in all_hits:
            print(hit)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
