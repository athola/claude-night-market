#!/usr/bin/env python3
"""Re-quote capture frontmatter that unescaped interpolation corrupted.

The capture hooks used to build frontmatter by interpolating page titles
and queries straight into a YAML double-quoted scalar. Any value holding
a quote closed the scalar early, and the reader then saw the file as
having no frontmatter at all, which drops the whole document from the
keyword index rather than merely losing its topic.

The writers escape their scalars now, but that fix only protects
captures made after it. These files are fetched web content with no
upstream copy, so the ones already on disk are repaired in place or
stay invisible.

The repair re-quotes the broken scalar and changes nothing else. A file
whose corruption this pass does not model is refused rather than
rewritten: turning an invisible capture into a subtly wrong one would be
worse than leaving it alone.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# A frontmatter line whose value is wrapped in double quotes. The greedy
# body deliberately spans interior quotes, which is exactly the shape the
# corruption takes.
# How many repair candidates to name before summarising the rest.
_PREVIEW_LIMIT = 5

_QUOTED_LINE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*): "(.*)"$')


def _split_frontmatter(text: str) -> tuple[list[str], int, int] | None:
    """Locate the frontmatter block as (lines, first_index, last_index).

    The delimiter must be a whole line: a captured URL containing a
    triple hyphen would otherwise appear to close the block.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for offset, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines, 1, offset
    return None


def repair_text(text: str) -> str | None:
    """Return *text* with its frontmatter re-quoted, or None to skip.

    None means "leave this file alone": either it already parses, it has
    no frontmatter, or the repair could not be verified.
    """
    split = _split_frontmatter(text)
    if split is None:
        return None
    lines, start, end = split

    block = "\n".join(lines[start:end])
    try:
        if isinstance(yaml.safe_load(block), dict):
            return None  # Already readable; nothing to do.
    except yaml.YAMLError:
        pass

    repaired = list(lines)
    for index in range(start, end):
        match = _QUOTED_LINE.match(lines[index])
        if match:
            key, value = match.group(1), match.group(2)
            repaired[index] = f"{key}: {json.dumps(value)}"

    candidate = "\n".join(repaired[start:end])
    try:
        parsed = yaml.safe_load(candidate)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict):
        return None

    return "\n".join(repaired)


def _iter_captures(corpus: Path) -> list[Path]:
    """Every markdown capture in *corpus*, in a stable order."""
    return sorted(corpus.glob("*.md"))


def main() -> int:
    """Report or apply repairs across a capture directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "staging",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the repairs; without it nothing is modified",
    )
    args = parser.parse_args()

    if not args.corpus.is_dir():
        print(f"no such corpus directory: {args.corpus}", file=sys.stderr)
        return 1

    captures = _iter_captures(args.corpus)
    repairs: list[tuple[Path, str]] = []
    for path in captures:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        repaired = repair_text(text)
        if repaired is not None:
            repairs.append((path, repaired))

    print(f"captures scanned: {len(captures)}")
    print(f"repairable:       {len(repairs)}")

    if not args.apply:
        for path, _ in repairs[:_PREVIEW_LIMIT]:
            print(f"  would repair: {path.name}")
        if len(repairs) > _PREVIEW_LIMIT:
            print(f"  ... and {len(repairs) - _PREVIEW_LIMIT} more")
        print("\nDRY RUN - no changes written. Re-run with --apply.")
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    backup = args.corpus.parent / "backups" / f"staging-frontmatter-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    written = 0
    for path, repaired in repairs:
        shutil.copy2(path, backup / path.name)
        path.write_text(repaired, encoding="utf-8")
        written += 1

    print(f"repaired:         {written}")
    print(f"backup:           {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
