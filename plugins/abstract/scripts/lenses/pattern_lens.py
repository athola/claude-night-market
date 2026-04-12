"""PatternLens: groups errors and friction across skills.

Identifies shared failure modes by finding common terms
in error messages and friction points across different
skills. Surfaces cross-cutting issues that individual
skill analysis would miss.
"""

from __future__ import annotations

import re
from typing import Any

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "pattern-lens",
    "insight_types": ["Pattern"],
    "weight": "lightweight",
    "description": "Finds shared failure modes across skills",
}

# Minimum skills sharing an error for it to be a pattern
MIN_PATTERN_SKILLS = 2
MIN_TERM_LENGTH = 3
SIMILARITY_THRESHOLD = 0.3
HIGH_SEVERITY_SKILL_COUNT = 3

# Common stop words to exclude from term matching
_STOP_WORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "shall",
        "not",
        "no",
        "and",
        "or",
        "but",
        "if",
        "then",
        "else",
        "when",
        "while",
        "with",
        "from",
        "by",
        "as",
        "this",
        "that",
        "it",
        "its",
        "error",
        "failed",
        "failure",
    }
)


def _extract_key_terms(text: str) -> set[str]:
    """Extract meaningful terms from an error or friction string."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]+", text)
    return {
        w.lower()
        for w in words
        if len(w) >= MIN_TERM_LENGTH and w.lower() not in _STOP_WORDS
    }


def _term_overlap(terms_a: set[str], terms_b: set[str]) -> float:
    """Jaccard similarity between two term sets."""
    if not terms_a or not terms_b:
        return 0.0
    intersection = terms_a & terms_b
    union = terms_a | terms_b
    return len(intersection) / len(union)


def analyze(context: AnalysisContext) -> list[Finding]:
    """Find shared error and friction patterns across skills."""
    if not context.metrics:
        return []

    findings: list[Finding] = []
    findings.extend(_find_error_patterns(context.metrics))
    findings.extend(_find_friction_patterns(context.metrics))
    return findings


def _find_error_patterns(
    metrics: dict[str, Any],
) -> list[Finding]:
    """Group skills by shared error terms."""
    # Collect all errors with their skills
    error_entries: list[tuple[str, str, set[str]]] = []
    for skill_key, summary in metrics.items():
        for error in getattr(summary, "recent_errors", []):
            terms = _extract_key_terms(error)
            if terms:
                error_entries.append((skill_key, error, terms))

    if len(error_entries) < MIN_PATTERN_SKILLS:
        return []

    # Group by similarity
    groups: list[list[tuple[str, str]]] = []
    used: set[int] = set()

    for i, (skill_i, err_i, terms_i) in enumerate(error_entries):
        if i in used:
            continue
        group = [(skill_i, err_i)]
        used.add(i)
        for j, (skill_j, err_j, terms_j) in enumerate(error_entries):
            if j in used or skill_j == skill_i:
                continue
            if _term_overlap(terms_i, terms_j) >= SIMILARITY_THRESHOLD:
                group.append((skill_j, err_j))
                used.add(j)
        if len(group) >= MIN_PATTERN_SKILLS:
            groups.append(group)

    findings: list[Finding] = []
    for group in groups:
        skills = sorted({s for s, _ in group})
        sample_error = group[0][1][:100]
        findings.append(
            Finding(
                type="Pattern",
                severity=(
                    "high" if len(skills) >= HIGH_SEVERITY_SKILL_COUNT else "medium"
                ),
                skill="",
                summary=f"{len(skills)} skills share similar errors",
                evidence=(
                    f"Affected skills: {', '.join(skills)}\n"
                    f"Sample error: {sample_error}"
                ),
                recommendation=(
                    "Investigate the shared root cause. These skills "
                    "may depend on a common service or pattern that "
                    "is failing."
                ),
                source="pattern-lens",
            )
        )

    return findings


def _find_friction_patterns(
    metrics: dict[str, Any],
) -> list[Finding]:
    """Group skills by shared friction points."""
    friction_entries: list[tuple[str, str, set[str]]] = []
    for skill_key, summary in metrics.items():
        for friction in getattr(summary, "common_friction", []):
            terms = _extract_key_terms(friction)
            if terms:
                friction_entries.append((skill_key, friction, terms))

    if len(friction_entries) < MIN_PATTERN_SKILLS:
        return []

    # Group by similarity
    groups: list[list[tuple[str, str]]] = []
    used: set[int] = set()

    for i, (skill_i, fric_i, terms_i) in enumerate(friction_entries):
        if i in used:
            continue
        group = [(skill_i, fric_i)]
        used.add(i)
        for j, (skill_j, fric_j, terms_j) in enumerate(friction_entries):
            if j in used or skill_j == skill_i:
                continue
            if _term_overlap(terms_i, terms_j) >= SIMILARITY_THRESHOLD:
                group.append((skill_j, fric_j))
                used.add(j)
        if len(group) >= MIN_PATTERN_SKILLS:
            groups.append(group)

    findings: list[Finding] = []
    for group in groups:
        skills = sorted({s for s, _ in group})
        sample_friction = group[0][1][:100]
        findings.append(
            Finding(
                type="Pattern",
                severity="medium",
                skill="",
                summary=f"{len(skills)} skills share friction: {sample_friction[:50]}",
                evidence=(
                    f"Affected skills: {', '.join(skills)}\n"
                    f"Sample friction: {sample_friction}"
                ),
                recommendation=(
                    "Address the shared friction point. Consider a "
                    "cross-cutting improvement that benefits all "
                    "affected skills."
                ),
                source="pattern-lens",
            )
        )

    return findings
