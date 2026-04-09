"""Query classification and freshness detection for research interception."""

from __future__ import annotations

import re
from typing import Any

# Freshness indicators - if present, likely needs web
_FRESHNESS_PATTERNS = re.compile(
    r"\b(latest|recent|new|current|2025|2024|today|now|update)\b",
    re.IGNORECASE,
)

# Evergreen indicators - timeless concepts that cache well
_EVERGREEN_PATTERNS = re.compile(
    r"\b(patterns?|principles?|concept|theory|fundamental|basic|how to|guide|"
    r"tutorial)\b",
    re.IGNORECASE,
)


def extract_query_intent(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Extract the query intent from tool parameters."""
    if tool_name == "WebSearch":
        return tool_input.get("query", "")
    if tool_name == "WebFetch":
        prompt = tool_input.get("prompt", "")
        url = tool_input.get("url", "")
        return prompt or url
    return ""


def needs_freshness(query: str) -> bool:
    """Check if query likely needs fresh data from web."""
    return bool(_FRESHNESS_PATTERNS.search(query))


def is_evergreen(query: str) -> bool:
    """Check if query is about timeless concepts."""
    return bool(_EVERGREEN_PATTERNS.search(query))
