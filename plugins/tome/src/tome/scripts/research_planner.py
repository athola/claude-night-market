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

from tome.models import DomainClassification, Finding, ResearchPlan

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


def replan(
    original: ResearchPlan,
    partial_results: dict[str, list[Finding]],
    outcomes: dict[str, str] | None = None,
) -> ResearchPlan:
    """Adjust channel weights based on partial results.

    Channels that yielded more findings gain weight; channels that
    searched cleanly and returned nothing lose weight. If all channels
    are empty, weights remain equal.

    ``outcomes`` (from ``tome.synthesis.quality.channel_outcomes``)
    decides which zero counts as evidence. Without it, every empty
    channel is down-weighted, which is right for a channel that ran and
    found nothing and backwards for one that never ran: an outage would
    teach the next pass to query the broken source less. A channel whose
    outcome is not ``ok`` or ``empty`` keeps its original weight,
    because nothing was learned about its usefulness for this topic.

    Args:
        original: The plan from the first research pass.
        partial_results: Channel name to findings list.
        outcomes: Channel name to derived status. Optional; callers
            written before outcome tracking keep the old behavior.

    Returns:
        A new ResearchPlan with adjusted weights.
    """
    if not original.channels:
        return original

    outcomes = outcomes or {}
    # A channel is re-weightable only when its zero is informative.
    # Absent outcomes every channel qualifies, which is the old rule.
    informative = {
        ch: outcomes.get(ch, "empty") in ("ok", "empty") for ch in original.channels
    }

    counts = {ch: len(partial_results.get(ch, [])) for ch in original.channels}
    total_findings = sum(counts.values())

    if total_findings == 0:
        # No results anywhere: keep equal weights
        equal = 1.0 / len(original.channels)
        weights = dict.fromkeys(original.channels, equal)
    else:
        # Blend: 50% original weight + 50% proportional to findings,
        # but only for channels whose emptiness means something.
        raw: dict[str, float] = {}
        for ch in original.channels:
            if not informative[ch]:
                raw[ch] = original.weights.get(ch, 0.0)
                continue
            proportion = counts[ch] / total_findings
            raw[ch] = 0.5 * original.weights.get(ch, 0.0) + 0.5 * proportion

        total = sum(raw.values())
        weights = (
            {ch: w / total for ch, w in raw.items()}
            if total
            else {ch: 1.0 / len(original.channels) for ch in original.channels}
        )

    return ResearchPlan(
        channels=list(original.channels),
        weights=weights,
        triz_depth=original.triz_depth,
        estimated_budget=original.estimated_budget,
    )
