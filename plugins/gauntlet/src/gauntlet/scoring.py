"""Answer scoring for the gauntlet plugin."""

from __future__ import annotations

from gauntlet.ml import get_blend_weights, score_answer_quality
from gauntlet.ml.features import _word_set
from gauntlet.models import Challenge

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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_answer(challenge: Challenge, answer: str) -> str:
    """Return 'pass', 'partial', or 'fail' for *answer* against *challenge*.

    Scoring rules by challenge type:

    - **multiple_choice**: exact letter match (case-insensitive).
    - **dependency_map**: set overlap.  >= 80% = pass, >= 30% = partial.
    - **explain_why / trace / spot_bug / code_completion**: blended
      word-overlap + ML quality score.  >= 0.5 = pass, >= 0.2 = partial.
      Falls back to word-overlap alone when ML is unavailable.
    """
    stripped = answer.strip()

    if challenge.type == "multiple_choice":
        if not stripped:
            return "fail"
        return "pass" if stripped.upper() == challenge.answer.upper() else "fail"

    if challenge.type == "dependency_map":
        expected = _dep_set(challenge.answer)
        if not expected:
            return "fail"
        given = _dep_set(stripped)
        overlap = len(expected & given) / len(expected)
        if overlap >= 0.8:
            return "pass"
        if overlap >= 0.3:
            return "partial"
        return "fail"

    # Open-ended types: explain_why, trace, spot_bug, code_completion
    if not stripped:
        return "fail"

    ratio = _word_overlap_ratio(challenge.answer, stripped)

    # ML quality refinement (graceful degradation)
    ml_score = score_answer_quality(challenge, stripped)
    if ml_score is not None:
        wo_weight, ml_weight = get_blend_weights()
        combined = wo_weight * ratio + ml_weight * ml_score
    else:
        combined = ratio

    if combined >= 0.5:
        return "pass"
    if combined >= 0.2:
        return "partial"
    return "fail"
