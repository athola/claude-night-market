#!/usr/bin/env python3
"""Remove all # noqa comments from plugin source files.

Strips inline noqa directives so that per-file-ignores in
pyproject.toml handle rule suppression instead.
"""

from __future__ import annotations

import re
from pathlib import Path


def remove_noqa_from_file(filepath: Path) -> int:
    """Remove # noqa comments from a file, return count removed."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0

    lines = content.splitlines(keepends=True)
    count = 0
    new_lines = []

    for line in lines:
        # Match # noqa patterns - but preserve # type: ignore
        # Pattern: # noqa or # noqa: RULE1, RULE2
        new_line = re.sub(
            r"\s*#\s*noqa(?::\s*[A-Z0-9, ]+)?(?=\s*$|\s*#)",
            "",
            line,
        )
        # Also handle noqa at end of line with nothing after
        new_line = re.sub(
            r"\s*#\s*noqa(?::\s*[A-Z0-9, ]+)?\s*$",
            "\n" if line.endswith("\n") else "",
            new_line,
        )
        if new_line != line:
            count += 1
        new_lines.append(new_line)

    if count > 0:
        filepath.write_text("".join(new_lines), encoding="utf-8")

    return count


def main() -> None:
    """Remove noqa from all plugin source files."""
    plugins_dir = Path("plugins")
    total = 0

    for py_file in sorted(plugins_dir.rglob("*.py")):
        # Skip .venv, __pycache__, node_modules
        parts = py_file.parts
        if any(
            p in parts for p in (".venv", "__pycache__", "node_modules", ".uv-cache")
        ):
            continue

        removed = remove_noqa_from_file(py_file)
        if removed > 0:
            print(f"  {py_file}: {removed} noqa removed")
            total += removed

    print(f"\nTotal: {total} noqa comments removed")


if __name__ == "__main__":
    main()
