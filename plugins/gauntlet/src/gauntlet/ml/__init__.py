"""ML-enhanced scoring for gauntlet challenges."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from gauntlet.ml.features import extract_answer_features
from gauntlet.ml.scorer import YamlScorer

if TYPE_CHECKING:
    from gauntlet.models import Challenge

_MODEL_PATH = str(Path(__file__).parent / "models" / "quality_v1.yaml")

_scorer: YamlScorer | None = None


def _get_scorer() -> YamlScorer:
    """Lazy-initialize the default scorer."""
    global _scorer  # noqa: PLW0603 - module-level singleton for lazy init
    if _scorer is None:
        _scorer = YamlScorer(_MODEL_PATH)
    return _scorer


def score_answer_quality(
    challenge: Challenge,
    answer: str,
) -> float | None:
    """Return a 0.0-1.0 quality score, or None if ML unavailable.

    Uses feature extraction and the default YamlScorer.
    Returns None when the model file is missing or corrupt,
    allowing callers to fall back to word-overlap scoring.
    """
    scorer = _get_scorer()
    if not scorer.available():
        return None
    features = extract_answer_features(challenge, answer)
    return scorer.score(features)
