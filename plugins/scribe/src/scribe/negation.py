"""Measure how much of a document is framed in the negative.

The Tier 5 regex categories catch particular constructions: double
negation, negation clichés, capability stated only as absence. None of
them can answer the question those patterns were added for, which is
whether a document *overly relies* on the negative. That is a property
of the whole page. A reference doc where most sentences say what
something will not do reads as evasive even when every sentence is
individually correct, because the reader finishes it still not knowing
what to do next.

So this is a counting check rather than a pattern, in the shape of
``scribe.ste.check_sentence_length``: it reports a ratio and the
arithmetic behind it, and leaves the judgment to a person.

Advisory by construction. Precise negation is how contracts,
invariants and trust boundaries are written, and a document full of
them is doing its job. Never gate a merge on this.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_THRESHOLD = 0.35
DEFAULT_MIN_SENTENCES = 8

_FENCED_CODE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Markers that put a sentence in the negative. Contractions are matched
# through the apostrophe class so "doesn't" and "doesn’t" count alike.
_NEGATION = re.compile(
    r"\b(?:not|no|never|none|neither|nor|cannot|without|lacks?|absent"
    r"|un(?:able|available)|fails?\s+to)\b|n['’]t\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DensityFinding:
    """One document-level reading, reported rather than corrected."""

    rule: str
    negative_sentences: int
    total_sentences: int
    ratio: float
    threshold: float
    detail: str
    confidence: str


def _prose_only(text: str) -> str:
    """Drop code spans, where negation is syntax rather than stance."""
    return _INLINE_CODE.sub(" ", _FENCED_CODE.sub(" ", text))


def _sentences(text: str) -> list[str]:
    """Split prose into sentences, dropping anything with no words."""
    flattened = " ".join(_prose_only(text).split())
    if not flattened:
        return []
    return [part for part in _SENTENCE_SPLIT.split(flattened) if part.strip()]


def check_negation_density(
    text: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    min_sentences: int = DEFAULT_MIN_SENTENCES,
) -> list[DensityFinding]:
    """Report when more than *threshold* of sentences are negative.

    Returns a list of at most one finding, matching the other checks in
    this package so a caller can concatenate results.

    Passages shorter than *min_sentences* return nothing: two negative
    sentences in a row are a coincidence, and a ratio over a handful of
    sentences says more about the sample than the writing.
    """
    sentences = _sentences(text)
    total = len(sentences)
    if total < min_sentences:
        return []

    negative = sum(1 for sentence in sentences if _NEGATION.search(sentence))
    ratio = negative / total
    if ratio <= threshold:
        return []

    return [
        DensityFinding(
            rule="negation_density",
            negative_sentences=negative,
            total_sentences=total,
            ratio=ratio,
            threshold=threshold,
            detail=(
                f"{negative} of {total} sentences ({ratio:.0%}) are framed in "
                f"the negative, against an advisory bar of {threshold:.0%}. "
                "Reread for places where saying what the thing does would be "
                "shorter than saying what it does not."
            ),
            confidence="low",
        )
    ]
