"""Canonical YAML frontmatter parser for the night-market ecosystem."""

from __future__ import annotations

from typing import Any

_yaml: Any = None
try:
    import yaml as _yaml
except ImportError:
    pass


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
