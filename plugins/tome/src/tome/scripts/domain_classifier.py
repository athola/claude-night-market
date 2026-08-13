"""Classify a research topic string into a domain category.

Uses keyword frequency matching against per-domain vocabularies.
The domain with the highest keyword hit count wins, provided it
meets a minimum match count and confidence threshold; otherwise
the topic falls back to the "general" domain.
"""

from __future__ import annotations

from tome.models import DomainClassification

# ---------------------------------------------------------------------------
# Domain vocabularies
# ---------------------------------------------------------------------------

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "ui-ux": [
        "react",
        "vue",
        "angular",
        "css",
        "tailwind",
        "component",
        "layout",
        "design",
        "responsive",
        "accessibility",
        "ux",
        "frontend",
        "widget",
    ],
    "algorithm": [
        "sort",
        "search",
        "graph",
        "tree",
        "hash",
        "dynamic programming",
        "complexity",
        "optimization",
        "pathfinding",
        "scheduling",
        "concurrent",
        "async",
        "parallel",
        "pattern",
        "consensus",
        "algorithm",
    ],
    "architecture": [
        "microservice",
        "monolith",
        "event-driven",
        "cqrs",
        "hexagonal",
        "layered",
        "api gateway",
        "service mesh",
        "distributed",
        "scalability",
        "load balancing",
    ],
    "data-structure": [
        "cache",
        "eviction",
        "index",
        "b-tree",
        "skip list",
        "bloom filter",
        "trie",
        "queue",
        "stack",
        "heap",
        "linked list",
    ],
    "scientific": [
        "physics",
        "chemistry",
        "biology",
        "simulation",
        "numerical",
        "differential equation",
        "finite element",
        "monte carlo",
        "neural network",
        "deep learning",
        "machine learning",
    ],
    "financial": [
        "trading",
        "portfolio",
        "risk",
        "pricing",
        "options",
        "derivatives",
        "backtesting",
        "quantitative",
        "market",
        "volatility",
        "hedge",
    ],
    "devops": [
        "ci/cd",
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "monitoring",
        "logging",
        "deployment",
        "pipeline",
        "infrastructure",
    ],
    "ai-agents": [
        "agent",
        "llm",
        "prompt",
        "embedding",
        "retrieval",
        "rag",
        "memory",
        "recall",
        "context window",
        "fine-tuning",
        "transformer",
        "inference",
        "vector database",
        "semantic search",
        "hallucination",
        "session memory",
    ],
    "security": [
        "encryption",
        "authentication",
        "authorization",
        "vulnerability",
        "penetration",
        "xss",
        "sql injection",
        "csrf",
        "tls",
        "certificate",
    ],
}

# ---------------------------------------------------------------------------
# TRIZ depth per domain
# ---------------------------------------------------------------------------

_DEPTH_RANK: dict[str, int] = {"light": 0, "medium": 1, "deep": 2, "maximum": 3}

# Match count at which purity is trusted at face value. Below it,
# confidence is scaled down: two hits in one domain is thin evidence
# even though it is perfectly pure.
_CONFIDENT_MATCHES = 3

_TRIZ_DEPTH: dict[str, str] = {
    "ui-ux": "light",
    "algorithm": "medium",
    "architecture": "medium",
    "data-structure": "deep",
    "scientific": "deep",
    "financial": "medium",
    "devops": "light",
    "security": "medium",
    "ai-agents": "deep",
    "general": "light",
}

# ---------------------------------------------------------------------------
# Channel weights per domain
# ---------------------------------------------------------------------------

_CHANNEL_WEIGHTS: dict[str, dict[str, float]] = {
    "ui-ux": {"code": 0.35, "discourse": 0.40, "academic": 0.15, "triz": 0.10},
    "algorithm": {"code": 0.25, "discourse": 0.20, "academic": 0.40, "triz": 0.15},
    "architecture": {"code": 0.30, "discourse": 0.30, "academic": 0.20, "triz": 0.20},
    "data-structure": {"code": 0.25, "discourse": 0.15, "academic": 0.35, "triz": 0.25},
    "scientific": {"code": 0.15, "discourse": 0.10, "academic": 0.50, "triz": 0.25},
    "financial": {"code": 0.20, "discourse": 0.30, "academic": 0.35, "triz": 0.15},
    "devops": {"code": 0.35, "discourse": 0.40, "academic": 0.10, "triz": 0.15},
    "security": {"code": 0.30, "discourse": 0.25, "academic": 0.30, "triz": 0.15},
    "ai-agents": {
        "code": 0.25,
        "discourse": 0.30,
        "academic": 0.30,
        "triz": 0.15,
    },
    "general": {"code": 0.30, "discourse": 0.35, "academic": 0.20, "triz": 0.15},
}

_MIN_MATCHES = 2
_MIN_CONFIDENCE = 0.6


def _count_matches(topic_lower: str, keywords: list[str]) -> int:
    """Count how many keywords from the list appear in the topic string.

    Multi-word keywords (e.g. "dynamic programming") are matched as
    substrings so the topic does not need exact word boundaries.
    """
    return sum(1 for kw in keywords if kw in topic_lower)


def classify(topic: str) -> DomainClassification:
    """Classify *topic* into a research domain.

    Algorithm:
    1. Lowercase the topic and count keyword hits per domain.
    2. Pick the domain with the most hits.
    3. Compute confidence as best_count / total_hits (across all domains).
    4. If best_count < _MIN_MATCHES or confidence < _MIN_CONFIDENCE,
       fall back to "general".

    Returns a DomainClassification with domain, triz_depth,
    channel_weights, and confidence.
    """
    topic_lower = topic.lower()

    scores: dict[str, int] = {
        domain: _count_matches(topic_lower, keywords)
        for domain, keywords in _DOMAIN_KEYWORDS.items()
    }

    best_domain = max(scores, key=lambda d: scores[d])
    best_count = scores[best_domain]
    total_hits = sum(scores.values())

    # Purity alone rewards thin evidence: two hits in exactly one
    # domain is perfectly pure but weakly supported. Scaling by match
    # count makes confidence rise with evidence rather than with the
    # absence of competing evidence.
    if total_hits == 0:
        confidence = 0.0
    else:
        purity = best_count / total_hits
        saturation = min(1.0, best_count / _CONFIDENT_MATCHES)
        confidence = purity * saturation

    confident = best_count >= _MIN_MATCHES and confidence >= _MIN_CONFIDENCE
    if confident:
        return DomainClassification(
            domain=best_domain,
            triz_depth=_TRIZ_DEPTH[best_domain],
            channel_weights=dict(_CHANNEL_WEIGHTS[best_domain]),
            confidence=confidence,
            candidates=[],
        )

    candidates = sorted(
        (d for d, count in scores.items() if count > 0),
        key=lambda d: (-scores[d], d),
    )
    if not candidates:
        # No signal at all. There is nothing to refine toward, and
        # escalating gibberish to four channels would spend budget on
        # noise, so the cheap plan is correct here.
        return DomainClassification(
            domain="general",
            triz_depth=_TRIZ_DEPTH["general"],
            channel_weights=dict(_CHANNEL_WEIGHTS["general"]),
            confidence=confidence,
            candidates=[],
        )

    # Refine rather than reject. The topic has support across several
    # vocabularies, which is what cross-domain research is for, so the
    # plan takes the deepest candidate's depth and a support-weighted
    # blend of their channel weights. Narrowing coverage because a
    # topic was hard to place is backwards.
    depth = max((_TRIZ_DEPTH[d] for d in candidates), key=lambda d: _DEPTH_RANK[d])
    total = sum(scores[d] for d in candidates)
    blended: dict[str, float] = {}
    for candidate in candidates:
        share = scores[candidate] / total
        for channel, weight in _CHANNEL_WEIGHTS[candidate].items():
            blended[channel] = blended.get(channel, 0.0) + weight * share
    normalizer = sum(blended.values()) or 1.0
    blended = {c: w / normalizer for c, w in blended.items()}

    return DomainClassification(
        domain="general",
        triz_depth=depth,
        channel_weights=blended,
        confidence=confidence,
        candidates=candidates,
    )
