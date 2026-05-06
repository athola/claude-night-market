"""Shared private helpers for sanctum validators (AR-F3).

Helpers that more than one validator module needs. Underscore-
prefixed names live here instead of leaking across siblings via
``from .skill import _foo``.
"""

from __future__ import annotations

import re


def _extract_skill_refs_from_content(content: str) -> list[str]:
    """Extract skill references from content.

    Finds all ``Skill(plugin:skill-name)`` patterns and returns the
    skill name portion (after the colon when present).
    """
    refs: list[str] = []
    matches = re.findall(r"Skill\(([^)]+)\)", content)
    for match in matches:
        if ":" in match:
            refs.append(match.split(":")[1])
        else:
            refs.append(match)
    return refs


__all__ = ["_extract_skill_refs_from_content"]
