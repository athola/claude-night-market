"""Pure functions for integration routing and decision explanation.

Extracted from MarginalValueFilter so that the 7-branch routing logic
and human-readable explanation generation can be tested independently
of any I/O or corpus state.
"""

from __future__ import annotations

from memory_palace.corpus._mv_models import (
    DeltaAnalysis,
    DeltaType,
    IntegrationDecision,
    IntegrationPlan,
    RedundancyCheck,
    RedundancyLevel,
)


def decide_integration(  # noqa: PLR0911 - explicit branch decisions for clarity
    redundancy: RedundancyCheck,
    delta: DeltaAnalysis | None,
) -> IntegrationPlan:
    """Decide how to integrate new knowledge (or skip it).

    Routes on redundancy level and delta type directly:

    1. Exact match -> SKIP (confidence 1.0)
    2. Highly redundant -> SKIP (confidence 0.9)
    3. Novel -> STANDALONE (confidence 0.9)
    4. Partial + novel insight -> STANDALONE (confidence 0.8)
    5. Partial + contradicts -> REPLACE (confidence 0.6)
    6. Partial + more examples -> MERGE (confidence 0.7)
    7. Partial + no delta -> SKIP (confidence 0.7)
    8. Default (partial, different framing) -> MERGE (confidence 0.5)

    Args:
        redundancy: Redundancy check result.
        delta: Delta analysis (None if exact match or novel).

    Returns:
        IntegrationPlan with decision, target entries, rationale,
        and confidence.

    """
    if redundancy.level == RedundancyLevel.EXACT_MATCH:
        return IntegrationPlan(
            decision=IntegrationDecision.SKIP,
            target_entries=redundancy.matching_entries,
            rationale="Exact duplicate of existing content",
            confidence=1.0,
        )

    if redundancy.level == RedundancyLevel.HIGHLY_REDUNDANT:
        return IntegrationPlan(
            decision=IntegrationDecision.SKIP,
            target_entries=redundancy.matching_entries,
            rationale=(
                "80%+ overlap with existing entries: "
                f"{', '.join(redundancy.matching_entries[:3])}"
            ),
            confidence=0.9,
        )

    if redundancy.level == RedundancyLevel.NOVEL:
        return IntegrationPlan(
            decision=IntegrationDecision.STANDALONE,
            target_entries=[],
            rationale="Novel content with no significant overlap",
            confidence=0.9,
        )

    if delta:
        if delta.delta_type == DeltaType.NOVEL_INSIGHT:
            return IntegrationPlan(
                decision=IntegrationDecision.STANDALONE,
                target_entries=[],
                rationale=f"Novel insights justify standalone: {delta.teaching_delta}",
                confidence=0.8,
            )

        if delta.delta_type == DeltaType.CONTRADICTS:
            return IntegrationPlan(
                decision=IntegrationDecision.REPLACE,
                target_entries=redundancy.matching_entries[:1],
                rationale=f"Contradicts/corrects existing: {delta.teaching_delta}",
                confidence=0.6,
            )

        if delta.delta_type == DeltaType.MORE_EXAMPLES:
            return IntegrationPlan(
                decision=IntegrationDecision.MERGE,
                target_entries=redundancy.matching_entries[:1],
                rationale=f"Enhances existing with examples: {delta.teaching_delta}",
                confidence=0.7,
            )

        if delta.delta_type == DeltaType.NONE:
            return IntegrationPlan(
                decision=IntegrationDecision.SKIP,
                target_entries=redundancy.matching_entries,
                rationale=f"Insufficient marginal value: {delta.teaching_delta}",
                confidence=0.7,
            )

    return IntegrationPlan(
        decision=IntegrationDecision.MERGE,
        target_entries=redundancy.matching_entries[:1]
        if redundancy.matching_entries
        else [],
        rationale="Partial overlap suggests merge, but needs human review",
        confidence=0.5,
    )


def explain_decision(
    redundancy: RedundancyCheck,
    delta: DeltaAnalysis | None,
    integration: IntegrationPlan,
) -> str:
    """Generate a human-readable explanation of the filtering decision.

    Args:
        redundancy: Redundancy check result.
        delta: Delta analysis (if applicable).
        integration: Integration decision.

    Returns:
        Formatted multi-line explanation string.

    """
    lines: list[str] = []
    lines.append("=== Marginal Value Assessment ===\n")

    lines.append(f"Redundancy: {redundancy.level.value}")
    lines.append(f"Overlap: {redundancy.overlap_score:.0%}")
    if redundancy.matching_entries:
        lines.append(f"Matches: {', '.join(redundancy.matching_entries[:5])}")
    for reason in redundancy.reasons:
        lines.append(f"  - {reason}")
    lines.append("")

    if delta:
        lines.append(f"Delta Type: {delta.delta_type.value}")
        lines.append(f"Value Score: {delta.value_score:.0%}")
        lines.append(f"Teaching Delta: {delta.teaching_delta}")

        if delta.novel_aspects:
            lines.append("Novel aspects:")
            for aspect in delta.novel_aspects[:3]:
                lines.append(f"  + {aspect}")

        if delta.redundant_aspects:
            lines.append("Already covered:")
            for aspect in delta.redundant_aspects[:3]:
                lines.append(f"  - {aspect}")
        lines.append("")

    lines.append(f"Decision: {integration.decision.value.upper()}")
    lines.append(f"Confidence: {integration.confidence:.0%}")
    lines.append(f"Rationale: {integration.rationale}")
    if integration.target_entries:
        lines.append(f"Target entries: {', '.join(integration.target_entries)}")

    return "\n".join(lines)
