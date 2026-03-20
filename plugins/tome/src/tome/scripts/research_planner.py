"""Create a ResearchPlan from a DomainClassification.

Channel inclusion rules:
- code and discourse are always included
- academic is included when triz_depth is medium, deep, or maximum
- triz is included when triz_depth is deep or maximum

Weights for the active channels are taken from the classification and
renormalised so they sum to exactly 1.0.

Budget (estimated token usage):
- light:   2000
- medium:  4000
- deep:    6000
- maximum: 8000
"""

from __future__ import annotations

from tome.models import DomainClassification, ResearchPlan

_BUDGET: dict[str, int] = {
    "light": 2000,
    "medium": 4000,
    "deep": 6000,
    "maximum": 8000,
}

# Depth ordinal used for threshold comparisons.
_DEPTH_ORDER: dict[str, int] = {
    "light": 0,
    "medium": 1,
    "deep": 2,
    "maximum": 3,
}


def plan(classification: DomainClassification) -> ResearchPlan:
    """Create a ResearchPlan from *classification*.

    The active channel set is determined by TRIZ depth; weights for
    inactive channels are dropped and the remaining weights are
    renormalised to sum to 1.0.
    """
    depth_ord = _DEPTH_ORDER.get(classification.triz_depth, 0)

    channels: list[str] = ["code", "discourse"]
    if depth_ord >= _DEPTH_ORDER["medium"]:
        channels.append("academic")
    if depth_ord >= _DEPTH_ORDER["deep"]:
        channels.append("triz")

    # Slice and renormalise weights for the active channels only.
    raw: dict[str, float] = {
        ch: classification.channel_weights.get(ch, 0.0) for ch in channels
    }
    total = sum(raw.values())
    if total == 0.0:
        # Fallback: equal weights when all source weights are zero.
        normalised: dict[str, float] = {ch: 1.0 / len(channels) for ch in channels}
    else:
        normalised = {ch: w / total for ch, w in raw.items()}

    return ResearchPlan(
        channels=channels,
        weights=normalised,
        triz_depth=classification.triz_depth,
        estimated_budget=_BUDGET.get(classification.triz_depth, 2000),
    )
