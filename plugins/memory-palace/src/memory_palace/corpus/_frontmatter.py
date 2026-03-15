"""Shared frontmatter parsing for corpus entries."""

from __future__ import annotations

from typing import Any

import yaml

_FRONTMATTER_PARTS = 3


def parse_entry_frontmatter(content: str) -> dict[str, Any] | None:
    """Parse YAML frontmatter from a corpus entry.

    Args:
        content: Raw text content of the entry.

    Returns:
        Parsed frontmatter dict, or None if missing/invalid.

    """
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < _FRONTMATTER_PARTS:
        return None
    try:
        payload = yaml.safe_load(parts[1])
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
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < _FRONTMATTER_PARTS:
        return None, content
    try:
        payload = yaml.safe_load(parts[1])
        if isinstance(payload, dict):
            return payload, parts[2]
    except yaml.YAMLError:
        pass
    return None, content
