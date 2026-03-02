"""Auto-trigger detection for War Room suggestions.

Contains should_suggest_war_room for analyzing user messages.
"""

from __future__ import annotations

from typing import Any


def should_suggest_war_room(
    user_message: str,
    complexity_threshold: float = 0.7,
) -> dict[str, Any]:
    """Determine if War Room should be suggested based on message analysis.

    Returns a dict with:
    - suggest: bool - whether to suggest War Room
    - confidence: float - confidence in suggestion (0-1)
    - reason: str - explanation for suggestion
    - keywords_matched: list[str] - which keywords triggered

    """
    message_lower = user_message.lower()

    # Strategic decision keywords
    strategic_keywords = [
        "architecture",
        "architectural",
        "trade-off",
        "tradeoff",
        "vs",
        "versus",
        "should we",
        "which approach",
        "best approach",
        "migration",
        "refactor",
        "rewrite",
        "platform",
        "strategic",
        "long-term",
        "irreversible",
        "breaking change",
    ]

    # High-stakes indicators
    stakes_keywords = [
        "critical",
        "important decision",
        "major",
        "significant",
        "risky",
        "uncertain",
        "complex",
        "complicated",
    ]

    # Multi-option indicators
    multi_option_keywords = [
        "options",
        "alternatives",
        "approaches",
        "microservices or monolith",
        "sql or nosql",
        "build or buy",
        "choice between",
    ]

    matched_strategic = [kw for kw in strategic_keywords if kw in message_lower]
    matched_stakes = [kw for kw in stakes_keywords if kw in message_lower]
    matched_multi = [kw for kw in multi_option_keywords if kw in message_lower]

    all_matched = matched_strategic + matched_stakes + matched_multi

    # Compute complexity score
    strategic_weight = len(matched_strategic) * 0.3
    stakes_weight = len(matched_stakes) * 0.25
    multi_weight = len(matched_multi) * 0.35

    complexity_score = min(1.0, strategic_weight + stakes_weight + multi_weight)

    suggest = complexity_score >= complexity_threshold

    if suggest:
        if matched_multi:
            reason = "Multiple approaches detected - War Room can help"
        elif matched_strategic:
            reason = "Strategic decision detected - expert council recommended"
        else:
            reason = "High-stakes decision - thorough analysis recommended"
    else:
        reason = "Standard task - War Room not needed"

    return {
        "suggest": suggest,
        "confidence": complexity_score,
        "reason": reason,
        "keywords_matched": all_matched,
    }
