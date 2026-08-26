"""Telemetry emission for research interception events."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from research_interceptor import CacheInterceptDecision, TelemetryContext

logger = logging.getLogger(__name__)


def emit_telemetry_event(
    telemetry_logger: Any | None,
    ctx: TelemetryContext,
    *,
    research_telemetry_event_cls: Any,
) -> None:
    """Best-effort telemetry emission.

    Takes the ``TelemetryContext`` directly: the per-request fields travel as
    one cohesive bundle rather than being expanded into a long kwarg list.
    """
    if telemetry_logger is None:
        return

    decision: CacheInterceptDecision = ctx.decision
    results = ctx.results
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

        event = research_telemetry_event_cls.build(
            query_id=ctx.query_id,
            query=ctx.query,
            tool_name=ctx.tool_name,
            mode=ctx.mode,
            decision=decision.action,
            cache_hits=len(results),
            returned_entries=len(decision.cached_entries),
            top_entry_id=top_entry_id,
            match_score=decision.match_score,
            match_strength=decision.match_strength,
            freshness_required=decision.freshness_required,
            evergreen_topic=decision.evergreen_topic,
            should_flag_for_intake=decision.should_flag_for_intake,
            latency_ms=ctx.latency_ms,
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
