"""Answer scoring for the gauntlet plugin."""

from __future__ import annotations

from gauntlet.ml import get_blend_weights, score_answer_quality
from gauntlet.ml.features import _word_set
from gauntlet.models import Challenge, ChallengeResult, ChallengeType

# ---------------------------------------------------------------------------
# Scoring thresholds
# ---------------------------------------------------------------------------

# dependency_map: fraction of expected modules that must appear in the
# answer for a pass / partial verdict.
_DEPENDENCY_PASS_THRESHOLD = 0.8
_DEPENDENCY_PARTIAL_THRESHOLD = 0.3

# explain_why / trace / spot_bug / code_completion: blended
# word-overlap + ML quality score needed for a pass / partial verdict.
_OPEN_ENDED_PASS_THRESHOLD = 0.5
_OPEN_ENDED_PARTIAL_THRESHOLD = 0.2

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _word_overlap_ratio(reference: str, candidate: str) -> float:
    """Return |intersection| / |reference| for the two word sets."""
    ref = _word_set(reference)
    if not ref:
        return 0.0
    can = _word_set(candidate)
    return len(ref & can) / len(ref)


def _dep_set(text: str) -> set[str]:
    """Split a comma-separated list of module names into a set."""
    return {item.strip() for item in text.split(",") if item.strip()}


def _bucket_result(
    score: float, pass_threshold: float, partial_threshold: float
) -> ChallengeResult:
    """Map a numeric score to PASS/PARTIAL/FAIL using two thresholds."""
    if score >= pass_threshold:
        return ChallengeResult.PASS
    if score >= partial_threshold:
        return ChallengeResult.PARTIAL
    return ChallengeResult.FAIL


def _score_multiple_choice(challenge: Challenge, stripped: str) -> ChallengeResult:
    """Score a multiple_choice answer by case-insensitive letter match."""
    if not stripped:
        return ChallengeResult.FAIL
    if stripped.upper() == challenge.answer.upper():
        return ChallengeResult.PASS
    return ChallengeResult.FAIL


def _score_dependency_map(challenge: Challenge, stripped: str) -> ChallengeResult:
    """Score a dependency_map answer by set overlap against the expected modules."""
    expected = _dep_set(challenge.answer)
    if not expected:
        return ChallengeResult.FAIL
    given = _dep_set(stripped)
    overlap = len(expected & given) / len(expected)
    return _bucket_result(
        overlap, _DEPENDENCY_PASS_THRESHOLD, _DEPENDENCY_PARTIAL_THRESHOLD
    )


def _score_open_ended(challenge: Challenge, stripped: str) -> ChallengeResult:
    """Score an open-ended answer by blended word-overlap + ML quality.

    Falls back to word-overlap alone when the ML scorer is unavailable.
    """
    if not stripped:
        return ChallengeResult.FAIL

    ratio = _word_overlap_ratio(challenge.answer, stripped)

    ml_score = score_answer_quality(challenge, stripped)
    if ml_score is not None:
        wo_weight, ml_weight = get_blend_weights()
        combined = wo_weight * ratio + ml_weight * ml_score
    else:
        combined = ratio

    return _bucket_result(
        combined, _OPEN_ENDED_PASS_THRESHOLD, _OPEN_ENDED_PARTIAL_THRESHOLD
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_answer(challenge: Challenge, answer: str) -> ChallengeResult:
    """Return a :class:`ChallengeResult` for *answer* against *challenge*.

    Scoring rules by challenge type:

    - **multiple_choice**: exact letter match (case-insensitive).
    - **dependency_map**: set overlap.  >= 80% = pass, >= 30% = partial.
    - **explain_why / trace / spot_bug / code_completion**: blended
      word-overlap + ML quality score.  >= 0.5 = pass, >= 0.2 = partial.
      Falls back to word-overlap alone when ML is unavailable.
    """
    stripped = answer.strip()

    if challenge.type == ChallengeType.MULTIPLE_CHOICE:
        return _score_multiple_choice(challenge, stripped)

    if challenge.type == ChallengeType.DEPENDENCY_MAP:
        return _score_dependency_map(challenge, stripped)

    return _score_open_ended(challenge, stripped)
