"""Readers for the imbue markdown that the contract tests check.

imbue ships skills, commands and agents as markdown, so the contract tests
read the shipped files. Importable as a top-level module because pytest
puts this directory on sys.path for the conftest beside it.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


def load(path: Path) -> tuple[dict, str]:
    """Split a markdown definition into its frontmatter and body."""
    _, frontmatter, body = path.read_text().split("---\n", 2)
    return yaml.safe_load(frontmatter), body


def section(body: str, heading_prefix: str) -> str:
    """Return the text under the first ## heading starting with the prefix.

    Single-# lines are skipped: in these files they are shell comments
    inside fenced examples, not headings.
    """
    match = re.search(
        rf"^#{{2,}} {re.escape(heading_prefix)}[^\n]*\n(.*?)(?=^#{{2,}} |\Z)",
        body,
        re.DOTALL | re.MULTILINE,
    )
    assert match, f"heading starting {heading_prefix!r} not found"
    return match.group(1)


def section_to_same_level(body: str, heading: str) -> str:
    """Return the text under a heading, up to the next heading of its level.

    Matches the whole heading text. Lines inside code fences are never
    headings, so subsections and fenced shell comments stay in the result.
    """
    lines = body.split("\n")
    in_fence = False
    start = level = None
    for index, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        match = None if in_fence else re.match(r"^(#+) (.*)$", line)
        if not match:
            continue
        if start is None and match.group(2) == heading:
            start, level = index + 1, len(match.group(1))
        elif start is not None and len(match.group(1)) <= level:
            return "\n".join(lines[start:index])
    assert start is not None, f"heading {heading!r} not found"
    return "\n".join(lines[start:])


def flat(text: str) -> str:
    """Collapse whitespace so a markdown reflow does not break an assert."""
    return " ".join(text.split())
