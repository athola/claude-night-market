#!/usr/bin/env python3
"""Research interceptor hook for PreToolUse (WebSearch/WebFetch)."""

from __future__ import annotations

import json
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PLUGIN_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import contextlib

from memory_palace.corpus.cache_lookup import CacheLookup
from memory_palace.corpus.marginal_value import RedundancyLevel
from memory_palace.curation import DomainAlignment, IntakeFlagPayload
from memory_palace.lifecycle.autonomy_state import AutonomyProfile, AutonomyStateStore
from memory_palace.observability.telemetry import (
    ResearchTelemetryEvent,
    TelemetryLogger,
    resolve_telemetry_path,
)

# Freshness indicators - if present, likely needs web
_FRESHNESS_PATTERNS = re.compile(
    r"\b(latest|recent|new|current|2025|2024|today|now|update)\b",
    re.IGNORECASE,
)

# Evergreen indicators - timeless concepts that cache well
_EVERGREEN_PATTERNS = re.compile(
    r"\b(patterns?|principles?|concept|theory|fundamental|basic|how to|guide|tutorial)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class CacheInterceptDecision:
    """Structured result describing cache interception behavior."""

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


_NOVELTY_BY_REDUNDANCY = {
    RedundancyLevel.EXACT_MATCH: 0.05,
    RedundancyLevel.HIGHLY_REDUNDANT: 0.15,
    RedundancyLevel.PARTIAL_OVERLAP: 0.45,
    RedundancyLevel.NOVEL: 0.9,
}


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


def search_local_knowledge(query: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Search local knowledge corpus for matches."""
    try:
        corpus_dir = PLUGIN_ROOT / config.get("corpus_dir", "docs/knowledge-corpus/")
        index_dir = PLUGIN_ROOT / config.get("indexes_dir", "data/indexes")
        lookup = CacheLookup(str(corpus_dir), str(index_dir))
        return lookup.search(query, mode="unified", min_score=0.0)
    except Exception:
        return []


def _classify_redundancy(score: float) -> RedundancyLevel:
    if score >= 0.9:
        return RedundancyLevel.EXACT_MATCH
    if score >= 0.8:
        return RedundancyLevel.HIGHLY_REDUNDANT
    if score >= 0.4:
        return RedundancyLevel.PARTIAL_OVERLAP
    return RedundancyLevel.NOVEL


def _calculate_novelty_and_duplicates(results: list[dict[str, Any]]) -> tuple[float, list[str]]:
    if not results:
        return 1.0, []

    best_score = float(results[0].get("match_score") or 0.0)
    redundancy = _classify_redundancy(best_score)
    novelty = _NOVELTY_BY_REDUNDANCY.get(redundancy, 0.5)

    duplicate_entry_ids: list[str] = []
    for entry in results:
        entry_score = float(entry.get("match_score") or 0.0)
        if entry_score >= 0.9:
            entry_id = entry.get("entry_id")
            if entry_id:
                duplicate_entry_ids.append(entry_id)

    return max(0.0, min(novelty, 1.0)), duplicate_entry_ids


def _detect_domain_alignment(query: str, domains: list[str]) -> DomainAlignment:
    normalized_query = query.lower()
    matched = [domain for domain in domains if domain and domain.lower() in normalized_query]
    return DomainAlignment(configured_domains=domains, matched_domains=matched)


def _build_delta_reasoning(
    *,
    should_flag: bool,
    novelty_score: float,
    alignment: DomainAlignment,
    duplicate_entry_ids: list[str],
    total_matches: int,
) -> str:
    parts = [
        f"novelty_score={novelty_score:.2f}",
        f"total_matches={total_matches}",
        f"intake_flag={'on' if should_flag else 'off'}",
    ]

    if alignment.configured_domains:
        if alignment.is_aligned:
            parts.append(f"domains_aligned={','.join(alignment.matched_domains)}")
        else:
            parts.append("domains_aligned=none")

    if duplicate_entry_ids:
        parts.append(f"duplicates={','.join(duplicate_entry_ids[:3])}")

    return "; ".join(parts)


def _finalize_decision(
    *,
    decision: CacheInterceptDecision,
    query: str,
    results: list[dict[str, Any]],
    config: dict[str, Any] | None,
    autonomy_profile: AutonomyProfile | None = None,
) -> CacheInterceptDecision:
    cfg = config or {}
    novelty_score, duplicate_entry_ids = _calculate_novelty_and_duplicates(results)
    alignment = _detect_domain_alignment(query, cfg.get("domains_of_interest", []))
    intake_threshold = int(cfg.get("intake_threshold", 70))

    effective_domains = alignment.matched_domains
    effective_level = 0
    if autonomy_profile is None:
        fallback_level = int(cfg.get("autonomy_level", 0) or 0)
        autonomy_profile = AutonomyProfile(global_level=fallback_level, domain_controls={})

    effective_level = autonomy_profile.effective_level_for(effective_domains)

    should_flag = decision.should_flag_for_intake
    if (
        should_flag
        and duplicate_entry_ids
        and novelty_score * 100 < intake_threshold
        and not alignment.is_aligned
    ):
        should_flag = False

    override_reason: str | None = None
    if should_flag:
        if duplicate_entry_ids and autonomy_profile.should_auto_approve_duplicates(
            effective_domains
        ):
            should_flag = False
            override_reason = "duplicate override"
        elif (
            decision.match_score is not None
            and decision.match_score >= 0.4
            and autonomy_profile.should_auto_approve_partial(effective_domains)
        ):
            should_flag = False
            override_reason = "partial match override"
        elif autonomy_profile.should_auto_approve_all(effective_domains):
            should_flag = False
            override_reason = "trusted override"

    delta_reasoning = _build_delta_reasoning(
        should_flag=should_flag,
        novelty_score=novelty_score,
        alignment=alignment,
        duplicate_entry_ids=duplicate_entry_ids,
        total_matches=decision.total_matches,
    )

    payload = IntakeFlagPayload(
        query=query,
        should_flag_for_intake=should_flag,
        novelty_score=novelty_score,
        domain_alignment=alignment,
        delta_reasoning=delta_reasoning,
        duplicate_entry_ids=duplicate_entry_ids,
    )

    decision.should_flag_for_intake = should_flag
    decision.novelty_score = novelty_score
    decision.aligned_domains = alignment.matched_domains
    decision.delta_reasoning = delta_reasoning
    decision.intake_payload = payload
    decision.autonomy_level = effective_level
    decision.autonomy_domains = alignment.matched_domains
    if override_reason:
        decision.context.append(
            f"[Autonomy L{effective_level}] Intake gating relaxed ({override_reason})."
        )
    return decision


def make_decision(
    query: str,
    results: list[dict[str, Any]],
    mode: str,
    config: dict[str, Any] | None = None,
    autonomy_profile: AutonomyProfile | None = None,
) -> CacheInterceptDecision:
    """Make decision based on cache results and mode."""
    freshness_required = needs_freshness(query)
    evergreen_topic = is_evergreen(query)
    decision = CacheInterceptDecision(
        action="proceed",
        freshness_required=freshness_required,
        evergreen_topic=evergreen_topic,
        total_matches=len(results),
    )

    if mode == "web_only":
        return _finalize_decision(
            decision=decision,
            query=query,
            results=results,
            config=config,
            autonomy_profile=autonomy_profile,
        )

    best_match = results[0] if results else None

    if not best_match:
        if mode == "cache_only":
            decision.action = "block"
            decision.context.append(
                "Memory Palace (cache_only mode): No local knowledge found for this query. "
                "Web search blocked. Consider switching to cache_first mode or adding knowledge manually.",
            )
        else:
            decision.should_flag_for_intake = True
            decision.context.append(
                "Memory Palace: No cached knowledge found. Proceeding with web search. "
                "Result will be flagged for potential knowledge intake.",
            )
        return _finalize_decision(
            decision=decision,
            query=query,
            results=results,
            config=config,
            autonomy_profile=autonomy_profile,
        )

    match_score = best_match.get("match_score", 0.0)
    decision.match_score = match_score
    decision.match_strength = best_match.get("match_strength", "weak")

    if match_score > 0.8:
        if evergreen_topic or not freshness_required:
            if mode == "cache_only":
                decision.action = "block"
                decision.context.append(
                    f"Memory Palace (cache_only): Found strong match ({match_score:.0%}) - "
                    f"'{best_match.get('title', 'Untitled')}'. Web search blocked.",
                )
            elif mode == "augment":
                decision.action = "augment"
                decision.context.append(
                    f"Memory Palace: Found strong cached match ({match_score:.0%}) - "
                    f"'{best_match.get('title', 'Untitled')}'. Combining with web search.",
                )
                decision.cached_entries = results[:3]
            else:
                decision.action = "augment"
                decision.context.append(
                    f"Memory Palace: Found strong cached match ({match_score:.0%}) - "
                    f"'{best_match.get('title', 'Untitled')}'. "
                    "This may answer your question. Proceeding with web verification.",
                )
                decision.cached_entries = results[:1]
        else:
            decision.action = "augment"
            decision.context.append(
                "Memory Palace: Found cached match but query needs fresh data. Combining cache with web search.",
            )
            decision.cached_entries = results[:2]

    elif match_score >= 0.4:
        if mode == "cache_only":
            decision.action = "block"
            decision.context.append(
                f"Memory Palace (cache_only): Found partial match ({match_score:.0%}) - "
                f"'{best_match.get('title', 'Untitled')}'. Web search blocked.",
            )
        elif mode == "augment":
            decision.action = "augment"
            decision.context.append(
                f"Memory Palace: Found partial match ({match_score:.0%}) - "
                f"'{best_match.get('title', 'Untitled')}'. Augmenting with web search.",
            )
            decision.cached_entries = results[:3]
        else:
            decision.action = "augment"
            decision.context.append(
                f"Memory Palace: Found partial match ({match_score:.0%}). "
                "Injecting cached knowledge and proceeding with web search.",
            )
            decision.cached_entries = results[:2]
            decision.should_flag_for_intake = True

    elif mode == "cache_only":
        decision.action = "block"
        decision.context.append(
            "Memory Palace (cache_only): Only weak matches found. Web search blocked.",
        )
    else:
        decision.should_flag_for_intake = True
        decision.context.append(
            "Memory Palace: Weak cache match. Proceeding with full web search.",
        )

    return _finalize_decision(
        decision=decision,
        query=query,
        results=results,
        config=config,
        autonomy_profile=autonomy_profile,
    )


def format_cached_entry_context(entry: dict[str, Any]) -> str:
    """Format a cached entry for context injection."""
    title = entry.get("title", "Untitled")
    file_path = entry.get("file", "unknown")
    match_score = entry.get("match_score", 0.0)

    excerpt = ""
    if "content" in entry:
        content = entry["content"]
        excerpt = content[:200].strip()
        if len(content) > 200:
            excerpt += "..."

    parts = [
        f"\n--- Cached Knowledge: {title} ({match_score:.0%} match) ---",
        f"Source: {file_path}",
    ]

    if excerpt:
        parts.append(f"Excerpt: {excerpt}")

    parts.append("---")
    return "\n".join(parts)


def emit_telemetry_event(
    logger: TelemetryLogger | None,
    *,
    query_id: str,
    query: str,
    tool_name: str,
    mode: str,
    decision: CacheInterceptDecision,
    results: list[dict[str, Any]],
    latency_ms: int,
) -> None:
    """Best-effort telemetry emission."""
    if logger is None:
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
        logger.log_event(event)
    except Exception:
        return


def main() -> None:
    """Main hook entry point."""
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if tool_name not in ("WebFetch", "WebSearch"):
        sys.exit(0)

    from shared.config import get_config

    config = get_config()
    if not config.get("enabled", True):
        sys.exit(0)

    autonomy_profile: AutonomyProfile | None = None
    autonomy_store: AutonomyStateStore | None = None
    try:
        autonomy_store = AutonomyStateStore(plugin_root=PLUGIN_ROOT)
        autonomy_profile = autonomy_store.build_profile(config_level=config.get("autonomy_level"))
    except Exception:
        autonomy_profile = None
        autonomy_store = None

    telemetry_config = config.get("telemetry", {})
    telemetry_logger: TelemetryLogger | None = None
    if telemetry_config.get("enabled", True):
        telemetry_path = resolve_telemetry_path(PLUGIN_ROOT, telemetry_config)
        telemetry_logger = TelemetryLogger(telemetry_path)

    mode = config.get("research_mode", "cache_first")
    if mode == "web_only":
        sys.exit(0)

    query = extract_query_intent(tool_name, tool_input)
    if not query or len(query) < 3:
        sys.exit(0)

    query_id = uuid.uuid4().hex
    search_started = time.perf_counter()
    results = search_local_knowledge(query, config)
    decision = make_decision(query, results, mode, config=config, autonomy_profile=autonomy_profile)
    latency_ms = int((time.perf_counter() - search_started) * 1000)

    if autonomy_store is not None:
        with contextlib.suppress(Exception):
            autonomy_store.record_decision(
                auto_approved=not decision.should_flag_for_intake,
                flagged=decision.should_flag_for_intake,
                blocked=decision.action == "block",
                domains=decision.autonomy_domains or decision.aligned_domains,
            )

    response_parts: list[str] = []
    if decision.context:
        response_parts.extend(decision.context)

    if decision.cached_entries:
        response_parts.append("\n--- Relevant Cached Knowledge ---")
        for entry in decision.cached_entries:
            response_parts.append(format_cached_entry_context(entry))

    if decision.delta_reasoning:
        response_parts.append(f"[Memory Palace Intake] {decision.delta_reasoning}")

    def _build_hook_output(permission: str) -> dict[str, Any]:
        output: dict[str, Any] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": permission,
            "additionalContext": "\n".join(response_parts),
        }
        if permission == "deny":
            output["permissionDecisionReason"] = "cache_only mode: local knowledge available"
        if decision.intake_payload:
            output["intakeFlagPayload"] = decision.intake_payload.to_dict()
        if decision.delta_reasoning:
            output["intakeDecisionRationale"] = decision.delta_reasoning
        return output

    if decision.action == "block":
        {"hookSpecificOutput": _build_hook_output("deny")}
    elif decision.action == "augment" or decision.should_flag_for_intake:
        {"hookSpecificOutput": _build_hook_output("allow")}

    emit_telemetry_event(
        telemetry_logger,
        query_id=query_id,
        query=query,
        tool_name=tool_name,
        mode=mode,
        decision=decision,
        results=results,
        latency_ms=latency_ms,
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
