"""Ideation methods catalogue, diverse selector, and scoring.

This channel generalizes the single-method ``triz`` channel into a small
catalogue of ideation methods that port to technical problem-solving.
The research synthesis
(``docs/research/2026-06-04-ideation-methods-for-workflows.md``) found
that the value is the meta-pattern, not the method bundle:

- :func:`select_methods` picks methods from DIFFERENT categories so a
  single pass spans distinct reasoning modes.
- :func:`rotation_plan` schedules methods across passes so none repeats
  until the catalogue is exhausted. Code-backed rotation is the gap no
  prior art fills; everyone else enforces it by prompt alone.
- :func:`score_idea` applies weighted scoring (per
  ``leyline:evaluation-framework``) with an anti-inflation rule: a high
  novelty claim without supporting evidence is capped.

Design rule from "The Price of Format" (arXiv 2505.18949): each method
carries a REASONING prompt, never a rigid output schema. Structuring the
output collapses the diversity the method is meant to create.
"""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

# Weighted scoring criteria for technical ideas (weights sum to 1.0).
# Mirrors leyline:evaluation-framework's pattern with tome-specific axes.
IDEATION_CRITERIA: dict[str, float] = {
    "novelty": 0.25,
    "fit": 0.20,
    "feasibility": 0.20,
    "simplicity": 0.15,
    "reversibility": 0.10,
    "impact": 0.10,
}

# Anti-inflation: a novelty score at or above this is capped to the cap
# value unless the caller supplies evidence the idea is genuinely novel
# (the corpus-free analogue of creative-director's originality cap).
_NOVELTY_CLAIM_THRESHOLD = 8.0
_NOVELTY_CAP = 7.0

_METHODS_CACHE: list[dict[str, Any]] | None = None


def load_methods() -> list[dict[str, Any]]:
    """Load and cache the curated ideation methods catalogue.

    Returns:
        A list of method dicts in catalogue order, each with at least
        ``id``, ``name``, ``category``, ``evidence``, ``ports``, and
        ``prompt``.
    """
    global _METHODS_CACHE
    if _METHODS_CACHE is not None:
        return _METHODS_CACHE

    data_file = resources.files("tome.channels.ideation_data").joinpath("methods.yaml")
    raw = yaml.safe_load(data_file.read_text(encoding="utf-8")) or {}
    _METHODS_CACHE = list(raw.get("methods", []))
    return _METHODS_CACHE


def get_method(method_id: str) -> dict[str, Any] | None:
    """Return the method with ``method_id``, or ``None`` if absent."""
    for method in load_methods():
        if method.get("id") == method_id:
            return method
    return None


def list_categories() -> list[str]:
    """Return the distinct categories in catalogue first-appearance order."""
    seen: list[str] = []
    for method in load_methods():
        category = method.get("category", "")
        if category and category not in seen:
            seen.append(category)
    return seen


def _diverse_order(methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reorder methods round-robin across categories.

    The result interleaves categories so any prefix spans as many
    distinct categories as possible. Order within a category is the
    catalogue order. Deterministic.
    """
    by_category: dict[str, list[dict[str, Any]]] = {}
    for method in methods:
        by_category.setdefault(method.get("category", ""), []).append(method)

    ordered: list[dict[str, Any]] = []
    while by_category:
        for category in list(by_category):
            bucket = by_category[category]
            ordered.append(bucket.pop(0))
            if not bucket:
                del by_category[category]
    return ordered


def select_methods(
    n: int,
    exclude: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Select up to ``n`` methods spanning distinct categories.

    The first ``len(categories)`` picks each come from a different
    category, so a single pass spans distinct reasoning modes. Pass the
    ids used in a prior pass via ``exclude`` to rotate.

    Args:
        n: Maximum number of methods to return.
        exclude: Method ids to skip (for rotation across passes).

    Returns:
        Up to ``n`` method dicts, deterministically ordered, no
        duplicates.
    """
    excluded = set(exclude or ())
    candidates = [m for m in load_methods() if m.get("id") not in excluded]
    return _diverse_order(candidates)[: max(0, n)]


def rotation_plan(passes: int, n_per_pass: int) -> list[list[str]]:
    """Schedule method ids across passes, avoiding repeats until exhausted.

    Walks the category-diverse ordering, handing out ``n_per_pass`` ids
    per pass and wrapping to the start only after every method has been
    used once.

    Args:
        passes: Number of passes to schedule.
        n_per_pass: Methods per pass.

    Returns:
        A list of ``passes`` lists, each holding ``n_per_pass`` ids.
    """
    order = [m["id"] for m in _diverse_order(load_methods())]
    if not order:
        return [[] for _ in range(max(0, passes))]

    plan: list[list[str]] = []
    cursor = 0
    for _ in range(max(0, passes)):
        current: list[str] = []
        for _ in range(max(0, n_per_pass)):
            current.append(order[cursor % len(order)])
            cursor += 1
        plan.append(current)
    return plan


def score_idea(
    scores: dict[str, float],
    novelty_evidence: bool = False,
) -> dict[str, Any]:
    """Compute a weighted idea score with an anti-inflation novelty cap.

    Args:
        scores: Per-criterion scores (0 to 10) keyed by the criteria in
            :data:`IDEATION_CRITERIA`. Missing criteria default to 0.
        novelty_evidence: True if the caller has concrete evidence the
            idea is novel (for example, no prior art found). When False,
            a novelty score at or above the claim threshold is capped.

    Returns:
        Dict with ``weighted_total`` (float), ``adjusted_scores`` (the
        scores after any cap), and ``capped`` (bool).
    """
    adjusted = {
        criterion: float(scores.get(criterion, 0.0)) for criterion in IDEATION_CRITERIA
    }

    capped = False
    if (
        not novelty_evidence
        and adjusted.get("novelty", 0.0) >= _NOVELTY_CLAIM_THRESHOLD
    ):
        adjusted["novelty"] = _NOVELTY_CAP
        capped = True

    weighted_total = sum(
        adjusted[criterion] * weight for criterion, weight in IDEATION_CRITERIA.items()
    )

    return {
        "weighted_total": weighted_total,
        "adjusted_scores": adjusted,
        "capped": capped,
    }
