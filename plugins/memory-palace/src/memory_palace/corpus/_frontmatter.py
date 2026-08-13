"""Shared frontmatter parsing for corpus entries."""

from __future__ import annotations

from typing import Any

import yaml

_FRONTMATTER_PARTS = 3


def _split_on_delimiter_line(content: str) -> tuple[str, str] | None:
    """Return (frontmatter, body) split at the closing ``---`` line.

    The delimiter must occupy a whole line. Splitting on ``---`` wherever
    it appears lets an ordinary value close the block early: a captured
    URL with a triple hyphen in its path is enough, and the entry then
    reads as having no frontmatter at all.

    Returns None when no closing delimiter line is present.
    """
    lines = content.split("\n")
    if lines[0].strip() != "---":
        return None
    for offset, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            # The body keeps the newline that ended the delimiter line, so
            # callers that already depend on the leading break still see it.
            body = "\n" + "\n".join(lines[offset + 1 :])
            return "\n".join(lines[1:offset]), body
    return None


def parse_entry_frontmatter(content: str) -> dict[str, Any] | None:
    """Parse YAML frontmatter from a corpus entry.

    Args:
        content: Raw text content of the entry.

    Returns:
        Parsed frontmatter dict, or None if missing/invalid.

    """
    split = _split_on_delimiter_line(content)
    if split is None:
        return None
    try:
        payload = yaml.safe_load(split[0])
        if isinstance(payload, dict):
            return payload
    except yaml.YAMLError:
        pass
    return None


def split_entry(content: str) -> tuple[dict[str, Any] | None, str]:
    """Split a corpus entry into frontmatter dict and body text.

    Args:
        content: Raw text content of the entry.

    Returns:
        Tuple of (metadata_dict_or_None, body_text).

    """
    split = _split_on_delimiter_line(content)
    if split is None:
        return None, content
    try:
        payload = yaml.safe_load(split[0])
        if isinstance(payload, dict):
            return payload, split[1]
    except yaml.YAMLError:
        pass
    return None, content
