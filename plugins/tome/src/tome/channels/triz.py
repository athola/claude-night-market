"""TRIZ cross-domain analysis engine.

Provides pure-function utilities for applying Altshuller's TRIZ
methodology to software research topics.  No HTTP calls are made
here; this module produces query strings and Finding objects that
an agent passes to WebSearch/WebFetch tool calls.
"""

from __future__ import annotations

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
    (
        "flexibility",
        "complexity",
        [],
    ),  # fallback — empty keyword list means never matches
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
}


def formulate_contradiction(topic: str, domain: str) -> dict[str, str]:
    """Formulate a TRIZ technical contradiction from the topic.

    Uses keyword analysis to select the most likely contradiction from a
    catalogue of common software trade-offs.  Falls back to the
    flexibility/complexity contradiction when no keywords match.

    Args:
        topic: Free-text research topic.
        domain: Domain classification string (used for system description).

    Returns:
        Dict with keys: system, improving, worsening, ideal_result,
        contradiction.
    """
    topic_lower = topic.lower()

    improving = "flexibility"
    worsening = "complexity"

    for imp, wors, keywords in _CONTRADICTION_CATALOGUE:
        if any(kw in topic_lower for kw in keywords):
            improving = imp
            worsening = wors
            break

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
    }


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
]

_DEFAULT_PRINCIPLES: list[int] = [1, 13, 22, 25]

# Application hints per (principle_number, contradiction_key) — keyed by
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
        hint_key: tuple[int, str] | None = None
        for (pnum, imp_frag), _ in _APPLICATION_HINTS.items():
            if pnum == num and imp_frag in improving_lower:
                hint_key = (pnum, imp_frag)
                break

        if hint_key is not None:
            application = _APPLICATION_HINTS[hint_key]
        else:
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
    title = f"Bridge: {source_field} -> {target_domain}"
    summary = f"In {source_field}, {source_solution}. This maps to {target_domain} as {application}."
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
