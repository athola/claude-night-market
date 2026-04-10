"""Telemetry emission for research interception events."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from research_interceptor import CacheInterceptDecision

logger = logging.getLogger(__name__)


def emit_telemetry_event(  # noqa: PLR0913 - telemetry events need all context fields
    telemetry_logger: Any | None,
    *,
    query_id: str,
    query: str,
    tool_name: str,
    mode: str,
    decision: CacheInterceptDecision,
    results: list[dict[str, Any]],
    latency_ms: int,
    ResearchTelemetryEvent: Any,
) -> None:
    """Best-effort telemetry emission."""
    if telemetry_logger is None:
        return

    try:
        if decision.cached_entries:
            top_entry_id = decision.cached_entries[0].get("entry_id")
        elif results:
            top_entry_id = results[0].get("entry_id")
        else:
            top_entry_id = None

        duplicate_ids = None
        if decision.intake_payload and decision.intake_payload.duplicate_entry_ids:
            duplicate_ids = "|".join(decision.intake_payload.duplicate_entry_ids)

        event = ResearchTelemetryEvent.build(
            query_id=query_id,
            query=query,
            tool_name=tool_name,
            mode=mode,
            decision=decision.action,
            cache_hits=len(results),
            returned_entries=len(decision.cached_entries),
            top_entry_id=top_entry_id,
            match_score=decision.match_score,
            match_strength=decision.match_strength,
            freshness_required=decision.freshness_required,
            evergreen_topic=decision.evergreen_topic,
            should_flag_for_intake=decision.should_flag_for_intake,
            latency_ms=latency_ms,
            novelty_score=decision.novelty_score,
            aligned_domains="|".join(decision.aligned_domains)
            if decision.aligned_domains
            else None,
            intake_delta_reasoning=decision.delta_reasoning,
            duplicate_entry_ids=duplicate_ids,
        )
        telemetry_logger.log_event(event)
    except Exception as e:
        logger.warning("Failed to emit telemetry: %s", e)
