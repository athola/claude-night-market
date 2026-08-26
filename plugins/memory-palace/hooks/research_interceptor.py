#!/usr/bin/env python3
"""Research interceptor hook for PreToolUse (WebSearch/WebFetch)."""

# pyright: reportPossiblyUnboundVariable=false, reportOptionalMemberAccess=false, reportMissingImports=false
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared import config as shared_config
from shared.decision_engine import DecisionDeps, DecisionRequest
from shared.decision_engine import make_decision as _make_decision
from shared.formatting import format_cached_entry_context  # noqa: F401 - re-export
from shared.hook_output import (
    IntakeContext,
    build_hook_payload,
    build_response_parts,
    queue_for_intake,
)
from shared.query_classifier import (
    extract_query_intent,  # noqa: F401 - re-export
    is_evergreen,  # noqa: F401 - re-export
    needs_freshness,  # noqa: F401 - re-export
)
from shared.telemetry import emit_telemetry_event

logger = logging.getLogger(__name__)
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# PLUGIN_ROOT is version scoped: hooks run from cache/<marketplace>/
# <plugin>/<version>/, so user data written under it is invisible to
# the next release (issue #661). DATA_ROOT is the version-independent
# root, and equals PLUGIN_ROOT in a source checkout.
#
# Not everything under data/ moves. The wiki corpus and the index
# directory stay on PLUGIN_ROOT: they hold shipped, tracked assets
# (embeddings.yaml, query-templates.yaml) plus content regenerated from
# the palaces by sync_wiki. Losing those to an update costs a re-sync,
# not a capture. What moves is the content nothing can rebuild.
from memory_palace.paths import persistent_root

DATA_ROOT = persistent_root(PLUGIN_ROOT)

_HAS_MEMORY_PALACE = False
try:
    from memory_palace.corpus.cache_lookup import CacheLookup
    from memory_palace.corpus.marginal_value import RedundancyLevel
    from memory_palace.curation import DomainAlignment, IntakeFlagPayload
    from memory_palace.lifecycle.autonomy_state import (
        AutonomyProfile,
        AutonomyStateStore,
    )
    from memory_palace.observability.telemetry import (
        ResearchTelemetryEvent,
        TelemetryLogger,
        resolve_telemetry_path,
    )

    _HAS_MEMORY_PALACE = True
except (ImportError, ModuleNotFoundError) as e:
    logger.debug("memory_palace package not available: %s", e)
    from shared.fallback_stubs import (  # type: ignore[assignment]  # conditional stubs for graceful degradation
        AutonomyProfile,
        AutonomyStateStore,
        CacheLookup,
        DomainAlignment,
        IntakeFlagPayload,
        RedundancyLevel,
        ResearchTelemetryEvent,
        TelemetryLogger,
        resolve_telemetry_path,
    )


@dataclass
class CacheInterceptDecision:
    action: str = "proceed"
    context: list[str] = field(default_factory=list)
    cached_entries: list[dict[str, Any]] = field(default_factory=list)
    should_flag_for_intake: bool = False
    freshness_required: bool = False
    evergreen_topic: bool = False
    match_score: float | None = None
    match_strength: str | None = None
    total_matches: int = 0
    novelty_score: float | None = None
    aligned_domains: list[str] = field(default_factory=list)
    delta_reasoning: str | None = None
    intake_payload: IntakeFlagPayload | None = None
    autonomy_level: int = 0
    autonomy_domains: list[str] = field(default_factory=list)


_NOVELTY_BY_REDUNDANCY: dict[Any, float] = {
    RedundancyLevel.EXACT_MATCH: 0.05,
    RedundancyLevel.HIGHLY_REDUNDANT: 0.15,
    RedundancyLevel.PARTIAL_OVERLAP: 0.45,
    RedundancyLevel.NOVEL: 0.9,
}


def search_local_knowledge(query: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Search local knowledge corpus for matches."""
    corpus_dir_rel = config.get("corpus_dir", "data/wiki")
    if not corpus_dir_rel:
        return []
    try:
        corpus_dir = PLUGIN_ROOT / corpus_dir_rel
        if not corpus_dir.is_dir():
            return []
        index_dir = PLUGIN_ROOT / config.get("indexes_dir", "data/indexes")
        provider = config.get("embedding_provider", "none")
        lookup = CacheLookup(
            str(corpus_dir), str(index_dir), embedding_provider=provider
        )
        return lookup.search(query, mode="unified", min_score=0.0)
    except Exception as e:
        logger.warning("research_interceptor: Failed to search local knowledge: %s", e)
        return []


def make_decision(
    query: str,
    results: list[dict[str, Any]],
    mode: str,
    config: dict[str, Any] | None = None,
    autonomy_profile: AutonomyProfile | None = None,
) -> CacheInterceptDecision:
    """Make decision based on cache results and mode."""
    # _make_decision is declared `-> Any` (it injects the decision type at call
    # time); pin the result to the real return type before handing it back.
    decision: CacheInterceptDecision = _make_decision(
        DecisionRequest(
            query=query,
            results=results,
            mode=mode,
            config=config,
            autonomy_profile=autonomy_profile,
        ),
        DecisionDeps(
            CacheInterceptDecision=CacheInterceptDecision,
            AutonomyProfile=AutonomyProfile,
            DomainAlignment=DomainAlignment,
            IntakeFlagPayload=IntakeFlagPayload,
            RedundancyLevel=RedundancyLevel,
            novelty_by_redundancy=_NOVELTY_BY_REDUNDANCY,
        ),
    )
    return decision


@dataclass(frozen=True)
class TelemetryContext:
    """Per-request fields for a research telemetry event."""

    query_id: str
    query: str
    tool_name: str
    mode: str
    decision: CacheInterceptDecision
    results: list[dict[str, Any]]
    latency_ms: int


def _load_autonomy(
    config: dict[str, Any],
    feature_flags: dict[str, Any],
) -> tuple[AutonomyStateStore | None, AutonomyProfile | None]:
    """Load the autonomy store and profile (best-effort).

    Returns ``(None, None)`` when the autonomy feature is disabled or the
    profile cannot be built, leaving governance off without failing the hook.
    """
    if not feature_flags.get("autonomy", True):
        return None, None
    try:
        store = AutonomyStateStore(plugin_root=DATA_ROOT)
        profile = store.build_profile(config_level=config.get("autonomy_level"))
    except Exception as e:
        logger.warning(
            "research_interceptor: Failed to load autonomy profile; "
            "autonomy governance disabled: %s",
            e,
        )
        return None, None
    return store, profile


def main() -> None:
    """Intercept research requests through the hook."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.warning("research_interceptor: Failed to parse payload: %s", e)
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    if tool_name not in ("WebFetch", "WebSearch") or not _HAS_MEMORY_PALACE:
        sys.exit(0)

    config = shared_config.get_config()
    if not config.get("enabled", True):
        sys.exit(0)
    feature_flags = dict(config.get("feature_flags") or {})
    if not feature_flags.get("cache_intercept", True):
        sys.exit(0)

    # Load autonomy profile (best-effort)
    autonomy_store, autonomy_profile = _load_autonomy(config, feature_flags)

    telemetry_logger: TelemetryLogger | None = None
    telemetry_config = config.get("telemetry", {})
    if telemetry_config.get("enabled", True):
        telemetry_logger = TelemetryLogger(
            resolve_telemetry_path(DATA_ROOT, telemetry_config)
        )

    mode = config.get("research_mode", "cache_first")
    if mode == "web_only":
        sys.exit(0)
    query = extract_query_intent(tool_name, tool_input)
    if not query or len(query) < 3:
        sys.exit(0)

    query_id = uuid.uuid4().hex
    search_started = time.perf_counter()
    results = search_local_knowledge(query, config)
    decision = make_decision(
        query, results, mode, config=config, autonomy_profile=autonomy_profile
    )
    latency_ms = int((time.perf_counter() - search_started) * 1000)

    # Record autonomy decision (best-effort)
    if autonomy_store is not None:
        try:
            autonomy_store.record_decision(
                auto_approved=not decision.should_flag_for_intake,
                flagged=decision.should_flag_for_intake,
                blocked=decision.action == "block",
                domains=decision.autonomy_domains or decision.aligned_domains,
            )
        except Exception as e:
            logger.warning("research_interceptor: Failed to record decision: %s", e)

    response_parts = build_response_parts(decision, format_cached_entry_context)
    hook_payload = build_hook_payload(decision, response_parts)
    if hook_payload:
        print(json.dumps(hook_payload))

    emit_telemetry_event(
        telemetry_logger,
        TelemetryContext(
            query_id=query_id,
            query=query,
            tool_name=tool_name,
            mode=mode,
            decision=decision,
            results=results,
            latency_ms=latency_ms,
        ),
        research_telemetry_event_cls=ResearchTelemetryEvent,
    )
    queue_for_intake(
        DATA_ROOT,
        decision,
        IntakeContext(
            query_id=query_id,
            tool_name=tool_name,
            query=query,
            tool_input=tool_input,
        ),
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
