"""Feature extraction for ML-enhanced answer scoring."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gauntlet.models import Challenge

_WORD_RE = re.compile(r"[a-z0-9]+")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_CODE_BLOCK_RE = re.compile(r"```")
_BULLET_RE = re.compile(r"^\s*[-*]\s", re.MULTILINE)
_NEGATION_WORDS = frozenset(
    {
        "not",
        "no",
        "never",
        "none",
        "neither",
        "nor",
        "cannot",
        "cant",
        "dont",
        "doesnt",
        "wont",
        "isnt",
        "arent",
        "wasnt",
        "werent",
    }
)


def _word_set(text: str) -> set[str]:
    """Normalise text to a set of lowercase word tokens."""
    return set(_WORD_RE.findall(text.lower()))


def _word_list(text: str) -> list[str]:
    """Normalise text to a list of lowercase word tokens."""
    return _WORD_RE.findall(text.lower())


def extract_answer_features(
    challenge: Challenge,
    answer: str,
) -> dict[str, float]:
    """Extract 7 numeric features from a challenge-answer pair."""
    if not answer.strip():
        return {
            "word_overlap_ratio": 0.0,
            "length_ratio": 0.0,
            "keyword_coverage": 0.0,
            "structural_depth": 0.0,
            "unique_word_ratio": 0.0,
            "negation_density": 0.0,
            "numeric_match": 0.0,
        }

    ref_words = _word_set(challenge.answer)
    ans_words = _word_set(answer)
    ans_word_list = _word_list(answer)

    if ref_words:
        word_overlap_ratio = len(ref_words & ans_words) / len(ref_words)
    else:
        word_overlap_ratio = 0.0

    ref_len = len(challenge.answer.strip())
    if ref_len > 0:
        length_ratio = len(answer.strip()) / ref_len
    else:
        length_ratio = 0.0

    ctx_words = _word_set(challenge.context)
    if ctx_words:
        keyword_coverage = len(ctx_words & ans_words) / len(ctx_words)
    else:
        keyword_coverage = 0.0

    code_blocks = len(_CODE_BLOCK_RE.findall(answer)) // 2
    bullets = len(_BULLET_RE.findall(answer))
    structural_depth = float(code_blocks + bullets)

    if ans_word_list:
        unique_word_ratio = len(set(ans_word_list)) / len(ans_word_list)
    else:
        unique_word_ratio = 0.0

    if ans_word_list:
        neg_count = sum(1 for w in ans_word_list if w in _NEGATION_WORDS)
        negation_density = neg_count / len(ans_word_list)
    else:
        negation_density = 0.0

    ref_nums = set(_NUM_RE.findall(challenge.answer))
    if ref_nums:
        ans_nums = set(_NUM_RE.findall(answer))
        numeric_match = len(ref_nums & ans_nums) / len(ref_nums)
    else:
        numeric_match = 0.0

    return {
        "word_overlap_ratio": word_overlap_ratio,
        "length_ratio": length_ratio,
        "keyword_coverage": keyword_coverage,
        "structural_depth": structural_depth,
        "unique_word_ratio": unique_word_ratio,
        "negation_density": negation_density,
        "numeric_match": numeric_match,
    }
