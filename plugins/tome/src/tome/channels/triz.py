"""TRIZ cross-domain analysis engine.

Provides pure-function utilities for applying Altshuller's TRIZ
methodology to software research topics.  No HTTP calls are made
here; this module produces query strings and Finding objects that
an agent passes to WebSearch/WebFetch tool calls.
"""

from __future__ import annotations

import csv
import functools
import re
from importlib import resources
from typing import Any

from tome.models import Finding

# ---------------------------------------------------------------------------
# Altshuller's 40 Inventive Principles
# ---------------------------------------------------------------------------

INVENTIVE_PRINCIPLES: dict[int, tuple[str, str]] = {
    1: ("Segmentation", "Divide an object into independent parts"),
    2: ("Taking out", "Separate an interfering part or property"),
    3: ("Local quality", "Transition from homogeneous to heterogeneous structure"),
    4: ("Asymmetry", "Change symmetric form to asymmetric"),
    5: ("Merging", "Combine identical or similar objects or operations"),
    6: ("Universality", "Make a part perform multiple functions"),
    7: ("Nested doll", "Place one object inside another"),
    8: ("Anti-weight", "Compensate for weight with another force"),
    9: ("Preliminary anti-action", "Pre-stress to counter known harmful effects"),
    10: ("Preliminary action", "Perform required changes in advance"),
    11: ("Beforehand cushioning", "Prepare emergency measures in advance"),
    12: ("Equipotentiality", "Change conditions to eliminate lifting or lowering"),
    13: ("The other way round", "Invert the action or make movable parts fixed"),
    14: (
        "Spheroidality",
        "Use curves instead of straight lines, spheres instead of cubes",
    ),
    15: ("Dynamics", "Allow characteristics to change to optimal at each stage"),
    16: ("Partial or excessive action", "If 100% is hard, use slightly less or more"),
    17: ("Another dimension", "Move to multi-dimensional space"),
    18: ("Mechanical vibration", "Cause an object to oscillate or vibrate"),
    19: ("Periodic action", "Use periodic or pulsating actions instead of continuous"),
    20: (
        "Continuity of useful action",
        "Carry on work continuously, eliminate idle motions",
    ),
    21: ("Skipping", "Conduct a process at high speed to skip harmful effects"),
    22: ("Blessing in disguise", "Use harmful factors to achieve a positive effect"),
    23: ("Feedback", "Introduce feedback to improve a process"),
    24: ("Intermediary", "Use an intermediate carrier or process"),
    25: (
        "Self-service",
        "Make an object service itself and perform auxiliary functions",
    ),
    26: ("Copying", "Use simplified and inexpensive copies"),
    27: (
        "Cheap short-living",
        "Replace an expensive object with cheap disposable ones",
    ),
    28: ("Mechanics substitution", "Replace mechanical means with sensory means"),
    29: ("Pneumatics and hydraulics", "Use gas or liquid parts instead of solid"),
    30: (
        "Flexible shells and thin films",
        "Use flexible shells and thin films instead of 3D",
    ),
    31: ("Porous materials", "Make an object porous or add porous elements"),
    32: ("Color changes", "Change the color or transparency"),
    33: ("Homogeneity", "Make interacting objects from the same material"),
    34: ("Discarding and recovering", "Discard or modify portions after use"),
    35: ("Parameter changes", "Change physical state, concentration, flexibility"),
    36: ("Phase transitions", "Use phenomena during phase transitions"),
    37: ("Thermal expansion", "Use thermal expansion or contraction"),
    38: ("Strong oxidants", "Use enriched atmosphere or interactions"),
    39: ("Inert atmosphere", "Use inert atmosphere or add inert parts"),
    40: ("Composite materials", "Use composite materials"),
}

# ---------------------------------------------------------------------------
# Adjacent field mapping
# ---------------------------------------------------------------------------

FIELD_ADJACENCY: dict[str, list[str]] = {
    "ui-ux": ["cognitive psychology", "architecture", "industrial design"],
    "algorithm": ["operations research", "genetics", "physics"],
    "architecture": ["civil engineering", "biology", "urban planning"],
    "data-structure": ["logistics", "materials science", "library science"],
    "scientific": ["engineering", "philosophy of science", "mathematics"],
    "financial": ["game theory", "ecology", "thermodynamics"],
    "devops": ["manufacturing", "supply chain management", "aerospace"],
    "security": ["military strategy", "immunology", "cryptography"],
    "ai-agents": ["cognitive science", "control theory", "organizational design"],
    "methodology": ["operations research", "cognitive psychology", "design theory"],
    "general": ["systems theory", "design thinking", "biomimicry"],
}

# Pairs of (domain_a, domain_b) whose adjacency lists are considered maximally
# different.  Used when building the "distant fields" for maximum depth.
_DISTANT_DOMAIN_PAIRS: list[tuple[str, str]] = [
    ("algorithm", "ui-ux"),
    ("algorithm", "financial"),
    ("security", "financial"),
    ("devops", "scientific"),
    ("data-structure", "ui-ux"),
    ("architecture", "financial"),
]

# ---------------------------------------------------------------------------
# Contradiction catalogue
# ---------------------------------------------------------------------------
# Each entry: (improving_label, worsening_label, keywords_that_trigger_it)
# Keywords are matched case-insensitively against the topic string.

_CONTRADICTION_CATALOGUE: list[tuple[str, str, list[str]]] = [
    ("speed", "memory usage", ["cache", "performance", "fast", "speed", "latency"]),
    ("throughput", "latency", ["throughput", "bandwidth", "pipeline", "queue"]),
    (
        "security",
        "usability",
        ["security", "auth", "authentication", "password", "encrypt"],
    ),
    (
        "consistency",
        "availability",
        ["consistency", "consensus", "replication", "distributed"],
    ),
    (
        "readability",
        "performance",
        ["readability", "clean code", "refactor", "maintainab"],
    ),
    # Research-workflow trade-offs. ADR-0024 found the workflow's own
    # four contradictions all fell through to the fallback below.
    (
        "coverage",
        "cost",
        ["coverage", "recall", "token budget", "search budget", "retrieval", "toolset"],
    ),
    (
        "declarative metadata",
        "drift",
        ["metadata", "schema drift", "manifest", "declarative", "tool card", "drift"],
    ),
    (
        "early stopping",
        "completeness",
        ["stopping", "when to stop", "termination", "verifier", "multi-pass"],
    ),
    (
        "idea generation",
        "evidence",
        ["generative", "analogy", "analogies", "ideation", "hallucinat"],
    ),
    (
        "flexibility",
        "complexity",
        [],
    ),  # fallback: empty keyword list means never matches
]

# Ideal result templates indexed by (improving, worsening)
_IDEAL_RESULT_TEMPLATES: dict[tuple[str, str], str] = {
    ("speed", "memory usage"): (
        "The system achieves maximum speed without increasing memory usage"
    ),
    ("throughput", "latency"): (
        "The system sustains high throughput without increasing latency"
    ),
    ("security", "usability"): (
        "The system enforces strong security without degrading usability"
    ),
    ("consistency", "availability"): (
        "The system maintains consistency without reducing availability"
    ),
    ("readability", "performance"): (
        "The system is readable and maintainable without sacrificing performance"
    ),
    ("flexibility", "complexity"): (
        "The system achieves full flexibility without increasing complexity"
    ),
    ("coverage", "cost"): (
        "The search finds everything the evidence requires without a query beyond that"
    ),
    ("declarative metadata", "drift"): (
        "The description stays true to the code without anyone maintaining it"
    ),
    ("early stopping", "completeness"): (
        "The search stops the moment it is complete and never before"
    ),
    ("idea generation", "evidence"): (
        "Every generated idea arrives with its prior art already checked"
    ),
}


def _keyword_hits(topic_lower: str, keywords: tuple[str, ...] | list[str]) -> int:
    """The one exact-match predicate. The near-miss search must agree with it."""
    return sum(1 for kw in keywords if kw in topic_lower)


def _contradiction(
    topic: str, domain: str, improving: str, worsening: str, matched: str = "keyword"
) -> dict[str, str]:
    ideal_result = _IDEAL_RESULT_TEMPLATES.get(
        (improving, worsening),
        f"The system achieves {improving} without increasing {worsening}",
    )
    return {
        "system": f"{topic} in the {domain} domain",
        "improving": improving,
        "worsening": worsening,
        "ideal_result": ideal_result,
        "contradiction": f"Improving {improving} worsens {worsening}",
        # "keyword" when a catalogue row matched, "fallback" when none did,
        # so a reader can tell a described topic from an undescribed one
        # (ADR-0026).
        "matched": matched,
    }


def formulate_contradictions(
    topic: str, domain: str, limit: int = 3
) -> list[dict[str, str]]:
    """Rank candidate contradictions for the topic, best supported first.

    Every catalogue pair with a keyword hit is a candidate, ordered by
    how many of its keywords the topic contains, then by catalogue
    order. TRIZ-GPT (arXiv 2408.05897) measured GPT-4 mapping free text
    onto contradiction parameters at recall 0.69 and precision 0.31,
    about three candidates per correct one, so the agent is handed the
    ranked few rather than the first hit. With no hit at all the list
    holds only the flexibility/complexity fallback.

    Args:
        topic: Free-text research topic.
        domain: Domain classification string (used for system description).
        limit: Maximum number of candidates to return.

    Returns:
        Non-empty list of dicts, each with keys: system, improving,
        worsening, ideal_result, contradiction, matched.
    """
    topic_lower = topic.lower()
    scored = [
        (_keyword_hits(topic_lower, keywords), position, imp, wors)
        for position, (imp, wors, keywords) in enumerate(_CONTRADICTION_CATALOGUE)
    ]
    hits = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], s[1]))
    if not hits:
        return [
            _contradiction(
                topic, domain, "flexibility", "complexity", matched="fallback"
            )
        ]
    return [
        _contradiction(topic, domain, imp, wors)
        for _, _, imp, wors in hits[: max(1, limit)]
    ]


def formulate_contradiction(topic: str, domain: str) -> dict[str, str]:
    """The best-supported contradiction for the topic.

    Equivalent to ``formulate_contradictions(topic, domain)[0]``. Kept
    for callers that need one pair; the agent prompt uses the list.

    Returns:
        Dict with keys: system, improving, worsening, ideal_result,
        contradiction.
    """
    return formulate_contradictions(topic, domain, limit=1)[0]


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance, small strings only."""
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            )
        previous = current
    return previous[-1]


_NEAR_MIN_TOKEN = 4


def near_resolutions(
    topic: str, max_distance: int = 2, limit: int = 3
) -> list[dict[str, Any]]:
    """Catalogue rows a small change to the topic would have matched.

    The exact matcher keeps only the zero set: a topic either contains a
    row's keyword or it does not, and when nothing matches the fallback
    fires. This keeps the residual instead (the level-set reading of
    Madrigal's article): for each row with no exact hit, the smallest
    edit distance between one of its keywords and one of the topic's
    tokens. A row at distance 1 or 2 is the article's underwater
    island, a formulation that would have matched under a nameable
    change.

    Satisficing governs the widening (Simon): when any row matches
    exactly this returns nothing, so the existing contract holds; then
    radius 1 is tried, then 2, stopping at the first radius that yields
    a candidate and never past ``limit``. Tokens shorter than four
    characters are ignored, since two edits from three letters reach
    everything.

    Returns:
        Up to ``limit`` dicts with ``improving``, ``worsening``,
        ``keyword``, ``term``, ``distance``, best first, catalogue
        order on ties.
    """
    topic_lower = topic.lower()
    if any(
        _keyword_hits(topic_lower, keywords)
        for _, _, keywords in _CONTRADICTION_CATALOGUE
    ):
        return []
    tokens = [
        t for t in re.findall(r"[a-z][a-z-]+", topic_lower) if len(t) >= _NEAR_MIN_TOKEN
    ]
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for position, (imp, wors, keywords) in enumerate(_CONTRADICTION_CATALOGUE):
        best: tuple[int, str, str] | None = None
        for keyword in keywords:
            for word in keyword.split():
                if len(word) < _NEAR_MIN_TOKEN:
                    continue
                for token in tokens:
                    distance = _edit_distance(word, token)
                    if best is None or distance < best[0]:
                        best = (distance, keyword, token)
        if best is not None and best[0] <= max_distance:
            candidates.append(
                (
                    best[0],
                    position,
                    {
                        "improving": imp,
                        "worsening": wors,
                        "keyword": best[1],
                        "term": best[2],
                        "distance": best[0],
                    },
                )
            )
    for radius in range(1, max_distance + 1):
        within = sorted(
            (c for c in candidates if c[0] <= radius), key=lambda c: (c[0], c[1])
        )
        if within:
            return [c[2] for c in within[:limit]]
    return []


# Opposed demands on one quantity: two names for how much of one thing,
# which is a physical contradiction however the row is labeled. ARIZ-85C
# step 3.3 triages these before any principle lookup. Advisory, and
# syntactic: a contradiction that is vacuous for semantic reasons passes
# through, and an empty matrix cell is never the signal.
_OPPOSED_ON_ONE_QUANTITY: frozenset[frozenset[str]] = frozenset(
    {
        frozenset({"early stopping", "completeness"}),
        frozenset({"coverage", "cost"}),
        frozenset({"consistency", "availability"}),
    }
)


def physical_contradiction(contradiction: dict[str, str]) -> bool:
    """Is this two demands on one quantity rather than two parameters?

    True when the pair is in the opposed-demands table or the two
    labels share a word. Route a true result to
    ``separation_strategies`` or ``formulate_ideality`` instead of the
    principle search. The ``infeasible`` reformulation probe says how.
    """
    improving = contradiction.get("improving", "").lower()
    worsening = contradiction.get("worsening", "").lower()
    if frozenset({improving, worsening}) in _OPPOSED_ON_ONE_QUANTITY:
        return True
    shared = set(improving.split()) & set(worsening.split())
    return any(len(word) >= _NEAR_MIN_TOKEN for word in shared)


def formulate_ideality(topic: str, contradiction: dict[str, str]) -> dict[str, str]:
    """Formulate the Ideal Final Result (IFR) for a contradiction.

    Ideality in TRIZ is the ratio of useful functions to the sum of
    harmful functions and cost.  The Ideal Final Result is the limiting
    case: the system delivers its useful function without the system
    itself existing.  This is the most portable TRIZ idea, so it is a
    first-class step here, applied downstream of contradiction
    formulation rather than buried inside it.

    Args:
        topic: The system or problem being researched.
        contradiction: A dict as produced by ``formulate_contradiction``;
            the ``improving`` and ``worsening`` keys are reused.

    Returns:
        Dict with keys: ifr_statement, ideality_question,
        ideality_ratio_hint.
    """
    improving = contradiction.get("improving", "the useful function")
    worsening = contradiction.get("worsening", "any cost")

    ifr_statement = (
        f"The ideal {topic} delivers {improving} on its own, without the "
        f"{topic} existing and without incurring {worsening}"
    )
    ideality_question = (
        f"What would make the {topic} unnecessary while {improving} still happens?"
    )
    ideality_ratio_hint = (
        "Ideality = sum of useful functions / (sum of harmful functions "
        "+ cost); raise it by adding useful function or by removing "
        "harmful function and cost"
    )

    return {
        "ifr_statement": ifr_statement,
        "ideality_question": ideality_question,
        "ideality_ratio_hint": ideality_ratio_hint,
    }


# ---------------------------------------------------------------------------
# Separation principles (for physical contradictions)
# ---------------------------------------------------------------------------
# A physical contradiction asks one parameter to take two opposite values.
# TRIZ resolves it by separating the conflicting demands along one of four
# canonical axes rather than compromising between them.

SEPARATION_PRINCIPLES: tuple[str, ...] = ("time", "space", "condition", "system/scale")

_SEPARATION_HINTS: dict[str, str] = {
    "time": "at different times (one demand early, the other late)",
    "space": "in different places (one region serves each demand)",
    "condition": "on a condition (a property or input selects which demand wins)",
    "system/scale": "at different scales (part versus whole, or sub- versus super-system)",
}


_AXIS_HINT_WORDS: dict[str, tuple[str, ...]] = {
    "time": (
        "schedule",
        "batch",
        "nightly",
        "phase",
        "lifecycle",
        "period",
        "startup",
        "shutdown",
    ),
    "space": (
        "boundary",
        "layer",
        "module",
        "region",
        "edge",
        "partition",
        "tier",
        "zone",
    ),
    "condition": ("flag", "mode", "input", "request", "tenant", "profile", "role"),
    "system/scale": ("cluster", "subsystem", "supersystem", "fleet", "single", "whole"),
}


def separation_strategies(contradiction: dict[str, str]) -> list[dict[str, str]]:
    """Return the four TRIZ separation principles for a contradiction.

    When a single parameter is required to hold two opposite values, the
    classical resolution is to separate the demands along one of four
    axes (time, space, condition, system/scale) instead of compromising.

    Args:
        contradiction: A dict as produced by ``formulate_contradiction``;
            the ``improving`` and ``worsening`` keys are reused.

    Returns:
        A list of four dicts, each with keys ``axis`` and ``prompt``.
    """
    improving = contradiction.get("improving", "the requirement")
    worsening = contradiction.get("worsening", "its opposite")
    system = contradiction.get("system", "").lower()

    # The axis the system description points at comes first. A region
    # with no solution still has a shape (the saddle-node reading in
    # ADR-0026), and words like "schedule" or "boundary" say which way it
    # points. Ties keep the canonical order.
    strategies: list[dict[str, str]] = []
    for axis in SEPARATION_PRINCIPLES:
        hits = [w for w in _AXIS_HINT_WORDS[axis] if re.search(rf"\b{w}s?\b", system)]
        prompt = (
            f"Can you separate {improving} and {worsening} {_SEPARATION_HINTS[axis]}?"
        )
        strategies.append({"axis": axis, "prompt": prompt, "why": ", ".join(hits)})
    strategies.sort(key=lambda s: -len(s["why"].split(", ")) if s["why"] else 0)
    return strategies


# ---------------------------------------------------------------------------
# Reformulation probes
# ---------------------------------------------------------------------------
# A contradiction record is a binary statement: improving X worsens Y.
# "The Shadows Lurking in the Equations" (Madrigal, 2025) makes the case
# for equations that the exact statement hides three things a relaxed
# one shows: near-solutions that a small parameter shift surfaces,
# structure visible only in a rearranged form, and regions where no
# solution exists at all. Each of those is an operation TRIZ already
# names, and the literature behind the article formalizes each one, so
# the probes below carry a principle number and a dated source rather
# than the article's metaphors. ADR-0026 records the mapping.

_PROBE_SOURCES: dict[str, str] = {
    "swap": (
        "Duncker, On Problem-Solving (1945), restructuring; Liberti, "
        "Reformulations in Mathematical Programming (LIX survey, 2009)"
    ),
    "relax": (
        "Chinneck, Feasibility and Infeasibility in Optimization (2008); "
        "Madrigal, The Shadows Lurking in the Equations (2025)"
    ),
    "shift": (
        "Allgower and Georg, Numerical Continuation Methods (1990); "
        "Chinneck (2008), sensitivity filter"
    ),
    "dynamize": (
        "Leibniz integral rule as Feynman's parameter trick (Woods, "
        "Advanced Calculus, 1926); Sotiriou and Faraoni, f(R) Theories of "
        "Gravity (2010)"
    ),
    "infeasible": (
        "Chinneck (2008), irreducible infeasible subsystems; Hipple, TRIZ "
        "Separation Principles (2012)"
    ),
}


def _principle_label(number: int) -> str:
    name, _ = INVENTIVE_PRINCIPLES[number]
    return f"{name} (#{number})"


def reformulation_probes(contradiction: dict[str, str]) -> list[dict[str, Any]]:
    """Five probes that reshape a contradiction before analogies are sought.

    Returned in a fixed order so an agent answers or dismisses each one:

    ``swap``
        Write the contradiction the other way round. Which parameter is
        called "improving" is a choice, and the principles a formulation
        suggests follow from it (the other way round, #13).
    ``relax``
        Replace the exact statement with a range: how much of the
        worsening is tolerable before the improvement stops paying
        (partial or excessive action, #16).
    ``shift``
        Name the fixed parameter whose small move would dissolve the
        trade-off, and the direction (parameter changes, #35). This is
        the near-solution the article calls an underwater island, and
        continuation methods follow it formally.
    ``dynamize``
        Promote a constant in the statement to a variable or a function
        of the situation (dynamization, #15): the constant-as-variable
        move behind Feynman's parameter trick and f(R) gravity.
    ``infeasible``
        Ask whether any value satisfies both demands inside the current
        system. When none does, searching harder is the wrong move: the
        statement is a physical contradiction, resolved by separation
        along one of the four axes, or the system is at the end of its
        curve and the ideal final result names its successor.

    Args:
        contradiction: A dict as produced by ``formulate_contradiction``;
            the ``improving`` and ``worsening`` keys are reused.

    Returns:
        Five dicts with keys ``kind``, ``principle``, ``question``,
        ``rationale``, ``source``.
    """
    improving = contradiction.get("improving", "the improving parameter")
    worsening = contradiction.get("worsening", "the worsening parameter")
    axes = ", ".join(SEPARATION_PRINCIPLES)
    probes: list[dict[str, Any]] = [
        {
            "kind": "swap",
            "principle": _principle_label(13),
            "question": (
                f"Restate it the other way round: improving {worsening} "
                f"worsens {improving}. Which principles does that formulation "
                "suggest that the first did not?"
            ),
            "rationale": (
                "The picture depends on how the statement is arranged. A "
                "rearrangement can expose structure the first form hid, and "
                "the same trade-off written two ways yields different "
                "principle suggestions."
            ),
        },
        {
            "kind": "relax",
            "principle": _principle_label(16),
            "question": (
                f"Relax the exact statement: how much {worsening} is "
                f"tolerable before {improving} stops paying, and where along "
                "that range does the trade-off stop being one?"
            ),
            "rationale": (
                "An exact contradiction hides near-resolutions. Plotting the "
                "error instead of the equality shows where a partial or "
                "excessive action already satisfies the need."
            ),
        },
        {
            "kind": "shift",
            "principle": _principle_label(35),
            "question": (
                f"Which fixed parameter of the system, moved slightly and in "
                f"which direction, would let {improving} rise without "
                f"{worsening} rising? Name the parameter and the direction."
            ),
            "rationale": (
                "A near-solution surfaces when a parameter shifts a little "
                "(the article's 2.7 becoming 2.8). Continuation methods "
                "follow a solution as a parameter moves; a sensitivity "
                "ranking says which parameter to move first."
            ),
        },
        {
            "kind": "dynamize",
            "principle": _principle_label(15),
            "question": (
                f"Which constant in the statement of {improving} versus "
                f"{worsening} could become a variable, or a function of the "
                "situation, instead of a fixed value?"
            ),
            "rationale": (
                "Promoting a constant to a variable is the general move behind "
                "the parameter trick for integrals and f(R) gravity: the "
                "problem gains a dimension in which a solution may exist."
            ),
        },
        {
            "kind": "infeasible",
            "principle": "Physical contradiction: separation, or the ideal final result",
            "question": (
                f"Is there any value at which {improving} and {worsening} are "
                "both acceptable inside the current system? If none, stop "
                "searching harder: separate the two demands in "
                f"{axes}, or state the ideal final result and ask what "
                "system delivers it without this one."
            ),
            "rationale": (
                "A region with no solution still has a shape. In optimization "
                "an irreducible infeasible subsystem names the demand whose "
                "removal restores feasibility; in TRIZ that removal is a "
                "separation, and a system at the end of its curve is replaced "
                "rather than tuned."
            ),
        },
    ]
    for probe in probes:
        probe["source"] = _PROBE_SOURCES[probe["kind"]]
    # ARIZ-85C step 1.1 writes both contradictions and step 1.4 picks
    # one. The display rule that makes that cheap for a reader: show the
    # inverted form only when its principle set differs.
    original = [p["number"] for p in suggest_inventive_principles(improving, worsening)]
    swapped = [p["number"] for p in suggest_inventive_principles(worsening, improving)]
    probes[0]["principles"] = original
    probes[0]["swapped_principles"] = swapped
    probes[0]["principle_set_differs"] = set(original) != set(swapped)
    return probes


def get_adjacent_fields(domain: str, depth: str) -> list[str]:
    """Get adjacent fields based on domain and TRIZ search depth.

    Depth controls how many cross-domain fields to include:
    - light    -> 1 field
    - medium   -> 2 fields
    - deep     -> 3 fields
    - maximum  -> all 3 primary fields + 2 deliberately distant fields

    For the maximum depth, two fields are taken from the adjacency list of
    a domain considered maximally different from the requested one.  If no
    explicit distant-domain mapping exists, the first other known domain is
    used as the distant source.

    Args:
        domain: Domain key from FIELD_ADJACENCY (unknown keys fall back to
            "general").
        depth: One of "light", "medium", "deep", "maximum".

    Returns:
        List of adjacent field strings, deduplicated, ordered by closeness
        then distance.
    """
    primary = FIELD_ADJACENCY.get(domain, FIELD_ADJACENCY["general"])

    depth_to_count: dict[str, int] = {
        "light": 1,
        "medium": 2,
        "deep": 3,
    }

    if depth in depth_to_count:
        return primary[: depth_to_count[depth]]

    # maximum depth: all primary fields + 2 distant fields
    fields: list[str] = list(primary)

    distant_domain: str | None = None
    for dom_a, dom_b in _DISTANT_DOMAIN_PAIRS:
        if domain == dom_a:
            distant_domain = dom_b
            break
        if domain == dom_b:
            distant_domain = dom_a
            break

    if distant_domain is None:
        # Pick any domain that isn't ours; FIELD_ADJACENCY always has entries
        # so this expression always resolves to a real domain key.
        distant_domain = next(
            (k for k in FIELD_ADJACENCY if k != domain and k != "general"),
            "general",
        )

    distant_fields = FIELD_ADJACENCY.get(distant_domain, FIELD_ADJACENCY["general"])

    # Add up to 2 distant fields that are not already in the list
    added = 0
    for df in distant_fields:
        if df not in fields and added < 2:
            fields.append(df)
            added += 1

    return fields


def build_cross_domain_search_queries(
    topic: str,
    adjacent_fields: list[str],
    contradiction: dict[str, str],
) -> list[str]:
    """Build WebSearch queries for finding cross-domain solutions.

    For each adjacent field two queries are generated:
    1. A tradeoff-focused query: "{field} solution to {improving} vs
       {worsening} tradeoff"
    2. An abstracted-problem query: "{field} {topic} approach"

    Args:
        topic: Original research topic.
        adjacent_fields: List of cross-domain fields to search in.
        contradiction: Dict containing at least "improving" and "worsening".

    Returns:
        List of query strings, two per adjacent field.  Returns an empty
        list when adjacent_fields is empty.
    """
    if not adjacent_fields:
        return []

    improving = contradiction.get("improving", "performance")
    worsening = contradiction.get("worsening", "complexity")

    queries: list[str] = []
    for field in adjacent_fields:
        queries.append(f"{field} solution to {improving} vs {worsening} tradeoff")
        queries.append(f"{field} {topic} approach")

    return queries


# ---------------------------------------------------------------------------
# Principle suggestion
# ---------------------------------------------------------------------------

# Map contradiction keys (normalised) to lists of principle numbers.
# Keys are (improving_fragment, worsening_fragment) pairs; matching is
# done by checking whether the fragment is a substring of the actual
# improving/worsening strings.
_PRINCIPLE_MAPPINGS: list[tuple[tuple[str, str], list[int]]] = [
    (("speed", "memory"), [1, 15, 27]),
    (("throughput", "latency"), [19, 20, 21]),
    (("security", "usab"), [3, 24, 25]),
    (("consistency", "avail"), [15, 16, 24]),
    (("readab", "performance"), [1, 7, 26]),
    (("flexibility", "complexity"), [1, 5, 6]),
    # Principles the ADR-0024 triz pass assigned to each workflow bridge.
    (("coverage", "cost"), [16, 3, 1]),
    (("declarative metadata", "drift"), [25, 23, 19]),
    (("early stopping", "completeness"), [23, 10, 2]),
    (("idea generation", "evidence"), [2, 1, 24]),
]

_DEFAULT_PRINCIPLES: list[int] = [1, 13, 22, 25]

# Application hints per (principle_number, contradiction_key), keyed by
# principle number and contradiction improving fragment.
_APPLICATION_HINTS: dict[tuple[int, str], str] = {
    (1, "speed"): (
        "Partition your cache into independent segments so each segment "
        "can be sized to its access pattern"
    ),
    (1, "flexibility"): (
        "Break a monolithic module into independently composable parts "
        "to increase flexibility without adding global complexity"
    ),
    (1, "readab"): (
        "Split large functions into named segments so each segment is "
        "readable in isolation without slowing execution"
    ),
    (15, "speed"): (
        "Allow cache entry sizes or eviction policies to adapt dynamically "
        "based on current memory pressure"
    ),
    (15, "consistency"): (
        "Let the consistency level vary per operation based on current network partition status"
    ),
    (27, "speed"): (
        "Use ephemeral, short-lived cache objects that are cheap to "
        "create and discard rather than long-lived structures"
    ),
    (19, "throughput"): (
        "Switch from continuous processing to batched periodic bursts so "
        "the system can drain queues without sustained latency spikes"
    ),
    (20, "throughput"): (
        "Eliminate blocking idle waits by keeping the processing pipeline "
        "continuously fed with pre-fetched work"
    ),
    (21, "throughput"): (
        "Execute at-risk operations at high speed and skip costly "
        "validation until after throughput targets are met"
    ),
    (3, "security"): (
        "Apply strong security checks only in the sensitive zone while "
        "keeping the public interface frictionless"
    ),
    (24, "security"): (
        "Introduce a dedicated security proxy that handles auth so the "
        "core application stays simple and usable"
    ),
    (24, "consistency"): (
        "Use a coordinator process as an intermediary to sequence writes without blocking readers"
    ),
    (25, "security"): (
        "Design components to self-verify their own integrity rather than "
        "relying on centralised gatekeeping"
    ),
    (16, "consistency"): (
        "Allow slightly-stale reads (partial consistency) when full "
        "consistency would require blocking all writes"
    ),
    (7, "readab"): (
        "Nest performance-critical inner loops inside clean outer "
        "abstractions so fast paths stay hidden from readers"
    ),
    (26, "readab"): (
        "Keep a simplified readable reference implementation alongside "
        "the optimised one that is tested against it"
    ),
    (5, "flexibility"): (
        "Merge related variation points into a single configurable "
        "abstraction to reduce the overall count of moving parts"
    ),
    (6, "flexibility"): (
        "Give each module the ability to serve multiple roles through "
        "a common interface to avoid proliferating specialised types"
    ),
    (13, "flexibility"): (
        "Invert control so callers inject their own logic rather than "
        "the system accumulating switch statements for every case"
    ),
    (22, "flexibility"): (
        "Turn the source of complexity (diverse requirements) into a "
        "driver for a richer, more composable abstraction"
    ),
    (25, "flexibility"): (
        "Allow components to self-configure from environment metadata "
        "so flexibility comes free with no manual wiring"
    ),
}


def _default_application(principle_number: int, improving: str) -> str:
    """Generate a generic application hint when no specific hint exists."""
    name, description = INVENTIVE_PRINCIPLES[principle_number]
    return (
        f"Apply {name} to the {improving} problem: {description.lower()} "
        f"in order to resolve the contradiction"
    )


def suggest_inventive_principles(
    improving: str,
    worsening: str,
) -> list[dict[str, Any]]:
    """Suggest relevant TRIZ inventive principles based on the contradiction.

    Selects 3-5 principle numbers by matching the improving/worsening pair
    against a catalogue of known software contradictions.  Falls back to a
    default set when no match is found.

    Args:
        improving: The parameter being improved (e.g. "speed").
        worsening: The parameter that worsens (e.g. "memory usage").

    Returns:
        List of dicts, each with keys: number, name, description,
        application.
    """
    improving_lower = improving.lower()
    worsening_lower = worsening.lower()

    selected_numbers: list[int] = []
    for (imp_frag, wors_frag), numbers in _PRINCIPLE_MAPPINGS:
        if imp_frag in improving_lower and wors_frag in worsening_lower:
            selected_numbers = numbers
            break

    if not selected_numbers:
        selected_numbers = _DEFAULT_PRINCIPLES

    results: list[dict[str, Any]] = []
    for num in selected_numbers:
        name, description = INVENTIVE_PRINCIPLES[num]
        # Look up the most specific application hint available
        application: str | None = None
        for (pnum, imp_frag), hint in _APPLICATION_HINTS.items():
            if pnum == num and imp_frag in improving_lower:
                application = hint
                break

        if application is None:
            application = _default_application(num, improving)

        results.append(
            {
                "number": num,
                "name": name,
                "description": description,
                "application": application,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Optional canonical contradiction-matrix lookup
# ---------------------------------------------------------------------------
# Vendored data: NickScherbakov/Heinrich-The-Inventing-Machine (Apache-2.0).
# See triz_data/NOTICE.  This is a sparse subset of Altshuller's classical
# 39x39 engineering-parameter matrix and is OPTIONAL grounding, secondary to
# the software-friendly suggest_inventive_principles catalogue above.


@functools.cache
def _load_canonical_matrix() -> dict[tuple[int, int], list[int]]:
    """Lazily load and cache the vendored sparse contradiction matrix.

    Returns an empty dict (and caches it) when the data file is absent, so
    the optional lookup degrades gracefully rather than raising.
    """
    matrix: dict[tuple[int, int], list[int]] = {}
    try:
        data_file = resources.files("tome.channels.triz_data").joinpath(
            "contradiction_matrix.csv"
        )
        text = data_file.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return matrix

    for row in csv.DictReader(text.splitlines()):
        try:
            improving = int(row["improving_parameter"])
            worsening = int(row["worsening_parameter"])
            principles = [
                int(n) for n in row["recommended_principles"].split(";") if n.strip()
            ]
        except (KeyError, ValueError, AttributeError):
            # A missing column, non-integer parameter, or non-integer
            # principle token drops just this row, honoring the documented
            # graceful-degradation contract for this OPTIONAL lookup.
            continue
        matrix[(improving, worsening)] = principles

    return matrix


def lookup_canonical_principles(
    improving_param: int,
    worsening_param: int,
) -> list[int]:
    """Look up inventive principles for a canonical matrix cell.

    OPTIONAL grounding lookup, SECONDARY to ``suggest_inventive_principles``.
    The matrix is Altshuller's classical 39x39 engineering-parameter table,
    frozen since 1985, mapping engineering rather than software parameters.

    An empty cell does NOT mean "no solution": by the empty-box convention
    any of the 40 principles may apply.  This function returns ``[]`` for
    both empty cells and out-of-range indices, so callers branch on a
    single "no recommendation" signal.

    Args:
        improving_param: Engineering parameter to improve (1-39).
        worsening_param: Engineering parameter that worsens (1-39).

    Returns:
        A list of inventive-principle numbers (1-40), or ``[]`` when the
        cell is empty or either index is out of range.
    """
    if not (1 <= improving_param <= 39 and 1 <= worsening_param <= 39):
        return []
    matrix = _load_canonical_matrix()
    return list(matrix.get((improving_param, worsening_param), []))


# ---------------------------------------------------------------------------
# Bridge statement
# ---------------------------------------------------------------------------


def format_bridge_statement(
    source_field: str,
    source_solution: str,
    target_domain: str,
    application: str,
    confidence: float,
) -> Finding:
    """Create a Finding representing a TRIZ cross-domain bridge mapping.

    The Finding encodes an analogical leap from a solved problem in one
    field to an unsolved problem in the target domain.

    Args:
        source_field: The field where the analogical solution exists.
        source_solution: Brief description of the solution in that field.
        target_domain: The domain being researched.
        application: How the source solution applies to the target domain.
        confidence: Estimated confidence of the analogy on [0.0, 1.0].

    Returns:
        A Finding with source="triz", channel="triz", and metadata
        recording bridge_confidence, source_field, and target_field.
    """
    title = f"Bridge: {source_field} to {target_domain}"
    summary = (
        f"In {source_field}, {source_solution}. "
        f"This maps to {target_domain} as {application}."
    )
    url = f"triz://bridge/{source_field.replace(' ', '-')}/{target_domain}"

    return Finding(
        source="triz",
        channel="triz",
        title=title,
        url=url,
        relevance=confidence,
        summary=summary,
        metadata={
            "source_field": source_field,
            "target_field": target_domain,
            "bridge_confidence": confidence,
        },
    )
