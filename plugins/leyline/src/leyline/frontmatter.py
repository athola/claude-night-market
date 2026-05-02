"""Canonical YAML frontmatter parser for the night-market ecosystem."""

from __future__ import annotations

import re
from typing import Any

_yaml: Any = None
try:
    import yaml as _yaml
except ImportError:
    pass

# Matches a frontmatter block at the start of a document. The closing
# ``\n`` is consumed so callers can take ``content[match.end():]`` as
# the body without leading whitespace artefacts.
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content: str) -> dict[str, Any] | None:
    """Parse YAML frontmatter from markdown content.

    Returns the frontmatter as a dict, or None if no valid
    frontmatter block is present.

    When PyYAML is unavailable, falls back to a minimal parser
    that handles simple ``key: value`` pairs (no nested structures).
    """
    stripped = content.strip()
    if not stripped.startswith("---"):
        return None
    lines = stripped.split("\n")
    try:
        end_index = next(
            i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        return None
    raw = "\n".join(lines[1:end_index])
    if _yaml is not None:
        try:
            return _yaml.safe_load(raw) or {}
        except _yaml.YAMLError:
            return None
    # Minimal fallback: simple key-value pairs only
    return _fallback_parse(raw)


def parse_frontmatter_with_body(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and return ``(meta, body)``.

    Returns ``({}, content)`` if no valid frontmatter is found, or
    if the YAML payload is unparseable. Body is the remainder of
    ``content`` after the closing ``---`` line, including any
    trailing whitespace -- byte-equivalent to
    ``content[FRONTMATTER_RE.match(content).end():]``.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content
    raw = match.group(1)
    body = content[match.end() :]
    if _yaml is not None:
        try:
            meta = _yaml.safe_load(raw) or {}
        except _yaml.YAMLError:
            return {}, content
    else:
        meta = _fallback_parse(raw)
    if not isinstance(meta, dict):
        return {}, content
    return meta, body


def _fallback_parse(raw: str) -> dict[str, Any]:
    """Best-effort parser when PyYAML is not installed."""
    result: dict[str, Any] = {}
    for raw_line in raw.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip()
    return result
