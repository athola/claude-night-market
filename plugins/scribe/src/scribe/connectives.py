"""Measure how often a document explains itself with ", so".

``tier5.so_connective`` marks each consequence tail ("the index was
stale, so the lookup missed"). One is ordinary English. What reads as
generated is the habit: every fact followed by its consequence, joined
with a comma. That is a rate over the page, the same kind of reading as
``scribe.negation.check_negation_density``, and it is advisory for the
same reason. The regex is read from ``en.yaml`` and the two checks
therefore cannot drift apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .markdown_spans import FENCED_CODE, INLINE_CODE
from .pattern_loader import get_tier5_patterns, load_language_patterns

DEFAULT_THRESHOLD = 2.0
# 500 words at a bar of 2.0 per 1000 means one tail never fires.
DEFAULT_MIN_WORDS = 500


@dataclass(frozen=True)
class SoDensityFinding:
    """One document-level reading, reported rather than corrected."""

    rule: str
    hits: int
    words: int
    per_thousand: float
    threshold: float
    detail: str
    confidence: str


@lru_cache(maxsize=1)
def _so_pattern() -> re.Pattern[str]:
    entries = get_tier5_patterns(load_language_patterns("en"))
    (entry,) = [e for e in entries if e["category"] == "so_connective"]
    flags = re.IGNORECASE if entry.get("ignore_case") else 0
    return re.compile("|".join(entry["patterns"]), flags)


def check_so_density(
    text: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    min_words: int = DEFAULT_MIN_WORDS,
) -> list[SoDensityFinding]:
    """Report when ", so" tails exceed *threshold* per 1000 words.

    Returns at most one finding, like the other document checks in this
    package. The finding types differ, so a caller handles each check's
    results on their own.
    """
    prose = INLINE_CODE.sub(" ", FENCED_CODE.sub(" ", text))
    words = len(prose.split())
    if words < min_words:
        return []

    hits = len(_so_pattern().findall(prose))
    per_thousand = hits * 1000 / words
    if per_thousand <= threshold:
        return []

    return [
        SoDensityFinding(
            rule="so_density",
            hits=hits,
            words=words,
            per_thousand=per_thousand,
            threshold=threshold,
            detail=(
                f'{hits} ", so" tails in {words} words ({per_thousand:.1f} '
                f"per 1000 words), against an advisory bar of {threshold:.1f}. "
                "For each one, ask whether the reader needs the consequence "
                "stated. Where it does, give the consequence its own sentence "
                "or lead with the cause."
            ),
            confidence="low",
        )
    ]
