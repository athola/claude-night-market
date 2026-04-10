"""Decision engine for research cache interception.

Determines whether to block, augment, or proceed with web
searches based on local cache matches, novelty scoring,
domain alignment, and autonomy governance.
"""

from __future__ import annotations

from typing import Any

from .query_classifier import is_evergreen, needs_freshness


def classify_redundancy(score: float, RedundancyLevel: Any) -> Any:
    """Map a match score to a RedundancyLevel enum value."""
    if score >= 0.9:
        return RedundancyLevel.EXACT_MATCH
    if score >= 0.8:
        return RedundancyLevel.HIGHLY_REDUNDANT
    if score >= 0.4:
        return RedundancyLevel.PARTIAL_OVERLAP
    return RedundancyLevel.NOVEL


def calculate_novelty_and_duplicates(
    results: list[dict[str, Any]],
    *,
    RedundancyLevel: Any,
    novelty_by_redundancy: dict[Any, float],
) -> tuple[float, list[str]]:
    """Compute novelty score and collect duplicate entry IDs."""
    if not results:
        return 1.0, []

    best_score = float(results[0].get("match_score") or 0.0)
    redundancy = classify_redundancy(best_score, RedundancyLevel)
    novelty = (
        novelty_by_redundancy.get(redundancy, 0.5) if redundancy is not None else 0.5
    )

    duplicate_entry_ids: list[str] = []
    for entry in results:
        entry_score = float(entry.get("match_score") or 0.0)
        if entry_score >= 0.9:
            entry_id = entry.get("entry_id")
            if entry_id:
                duplicate_entry_ids.append(entry_id)

    return max(0.0, min(novelty, 1.0)), duplicate_entry_ids


def detect_domain_alignment(
    query: str,
    domains: list[str],
    DomainAlignment: Any,
) -> Any:
    """Match query against configured domains of interest."""
    normalized_query = query.lower()
    matched = [
        domain for domain in domains if domain and domain.lower() in normalized_query
    ]
    return DomainAlignment(configured_domains=domains, matched_domains=matched)


def build_delta_reasoning(
    *,
    should_flag: bool,
    novelty_score: float,
    alignment: Any,
    duplicate_entry_ids: list[str],
    total_matches: int,
) -> str:
    """Build a human-readable reasoning string for intake decisions."""
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


def finalize_decision(
    *,
    decision: Any,
    query: str,
    results: list[dict[str, Any]],
    config: dict[str, Any] | None,
    autonomy_profile: Any | None = None,
    # Injected type references (avoids circular imports)
    AutonomyProfile: Any,
    DomainAlignment: Any,
    IntakeFlagPayload: Any,
    RedundancyLevel: Any,
    novelty_by_redundancy: dict[Any, float],
) -> Any:
    """Apply novelty scoring, domain alignment, and autonomy overrides."""
    cfg = config or {}
    novelty_score, duplicate_entry_ids = calculate_novelty_and_duplicates(
        results,
        RedundancyLevel=RedundancyLevel,
        novelty_by_redundancy=novelty_by_redundancy,
    )
    alignment = detect_domain_alignment(
        query, cfg.get("domains_of_interest", []), DomainAlignment
    )
    intake_threshold = int(cfg.get("intake_threshold", 70))

    effective_domains = alignment.matched_domains
    if autonomy_profile is None:
        fallback_level = int(cfg.get("autonomy_level", 0) or 0)
        autonomy_profile = AutonomyProfile(
            global_level=fallback_level, domain_controls={}
        )

    assert autonomy_profile is not None  # guaranteed by fallback above
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

    delta_reasoning = build_delta_reasoning(
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
    autonomy_profile: Any | None = None,
    *,
    # Injected types and state
    CacheInterceptDecision: Any,
    AutonomyProfile: Any,
    DomainAlignment: Any,
    IntakeFlagPayload: Any,
    RedundancyLevel: Any,
    novelty_by_redundancy: dict[Any, float],
) -> Any:
    """Make decision based on cache results and mode."""
    freshness_required = needs_freshness(query)
    evergreen_topic = is_evergreen(query)
    decision = CacheInterceptDecision(
        action="proceed",
        freshness_required=freshness_required,
        evergreen_topic=evergreen_topic,
        total_matches=len(results),
    )

    finalize_kwargs = {
        "decision": decision,
        "query": query,
        "results": results,
        "config": config,
        "autonomy_profile": autonomy_profile,
        "AutonomyProfile": AutonomyProfile,
        "DomainAlignment": DomainAlignment,
        "IntakeFlagPayload": IntakeFlagPayload,
        "RedundancyLevel": RedundancyLevel,
        "novelty_by_redundancy": novelty_by_redundancy,
    }

    if mode == "web_only":
        return finalize_decision(**finalize_kwargs)

    best_match = results[0] if results else None

    if not best_match:
        if mode == "cache_only":
            decision.action = "block"
            msg = (
                "Memory Palace (cache_only mode): No local knowledge found"
                " for this query. Web search blocked. Consider switching to"
                " cache_first mode or adding knowledge manually."
            )
            decision.context.append(msg)
        else:
            decision.should_flag_for_intake = True
            decision.context.append(
                "Memory Palace: No cached knowledge found. Proceeding with"
                " web search. Result will be flagged for potential knowledge"
                " intake.",
            )
        return finalize_decision(**finalize_kwargs)

    match_score = best_match.get("match_score", 0.0)
    decision.match_score = match_score
    decision.match_strength = best_match.get("match_strength", "weak")

    if match_score > 0.8:
        _handle_strong_match(
            decision,
            best_match,
            mode,
            evergreen_topic,
            freshness_required,
            results,
        )
    elif match_score >= 0.4:
        _handle_partial_match(decision, best_match, mode, results)
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

    return finalize_decision(**finalize_kwargs)


def _handle_strong_match(
    decision: Any,
    best_match: dict[str, Any],
    mode: str,
    evergreen_topic: bool,
    freshness_required: bool,
    results: list[dict[str, Any]],
) -> None:
    """Apply decision logic for strong cache matches (>0.8)."""
    match_score = best_match.get("match_score", 0.0)
    title = best_match.get("title", "Untitled")

    if evergreen_topic or not freshness_required:
        if mode == "cache_only":
            decision.action = "block"
            decision.context.append(
                f"Memory Palace (cache_only): Found strong match"
                f" ({match_score:.0%}) - '{title}'. Web search blocked.",
            )
        elif mode == "augment":
            decision.action = "augment"
            decision.context.append(
                f"Memory Palace: Found strong cached match"
                f" ({match_score:.0%}) - '{title}'."
                " Combining with web search.",
            )
            decision.cached_entries = results[:3]
        else:
            decision.action = "augment"
            decision.context.append(
                f"Memory Palace: Found strong cached match"
                f" ({match_score:.0%}) - '{title}'. "
                "This may answer your question."
                " Proceeding with web verification.",
            )
            decision.cached_entries = results[:1]
    else:
        decision.action = "augment"
        decision.context.append(
            "Memory Palace: Found cached match but query needs fresh"
            " data. Combining cache with web search.",
        )
        decision.cached_entries = results[:2]


def _handle_partial_match(
    decision: Any,
    best_match: dict[str, Any],
    mode: str,
    results: list[dict[str, Any]],
) -> None:
    """Apply decision logic for partial cache matches (0.4-0.8)."""
    match_score = best_match.get("match_score", 0.0)
    title = best_match.get("title", "Untitled")

    if mode == "cache_only":
        decision.action = "block"
        decision.context.append(
            f"Memory Palace (cache_only): Found partial match"
            f" ({match_score:.0%}) - '{title}'. Web search blocked.",
        )
    elif mode == "augment":
        decision.action = "augment"
        decision.context.append(
            f"Memory Palace: Found partial match ({match_score:.0%})"
            f" - '{title}'. Augmenting with web search.",
        )
        decision.cached_entries = results[:3]
    else:
        decision.action = "augment"
        decision.context.append(
            f"Memory Palace: Found partial match ({match_score:.0%})."
            " Injecting cached knowledge and proceeding with web"
            " search.",
        )
        decision.cached_entries = results[:2]
        decision.should_flag_for_intake = True
