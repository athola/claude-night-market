"""Shared text utilities for memory-palace hooks and scripts."""

from __future__ import annotations

import re


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    slug = slug.strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    return slug or "untitled"
