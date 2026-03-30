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

# Matches: # type: ignore[code] - some explanation
_JUSTIFIED_TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore\[[^\]]+\]\s+-\s+\S")


def _is_justified(line: str, label: str) -> bool:
    """Return True if the suppression includes a justification."""
    if label == "# noqa":
        return bool(_JUSTIFIED_NOQA.search(line))
    if label == "# type: ignore":
        return bool(_JUSTIFIED_TYPE_IGNORE.search(line))
    return False


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
                if _is_justified(line, label):
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
