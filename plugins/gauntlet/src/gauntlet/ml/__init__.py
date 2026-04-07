"""ML-enhanced scoring for gauntlet challenges."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from gauntlet.ml.features import extract_answer_features
from gauntlet.ml.scorer import SidecarScorer, YamlScorer

if TYPE_CHECKING:
    from gauntlet.ml.scorer import Scorer
    from gauntlet.models import Challenge

_MODEL_PATH = str(Path(__file__).parent / "models" / "quality_v1.yaml")

_log = logging.getLogger(__name__)

_scorer: Scorer | None = None


def _get_oracle_port_file() -> Path | None:
    """Find the oracle daemon's port file if it exists."""
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if plugin_data:
        oracle_port = Path(plugin_data).parent / "oracle" / "daemon.port"
        if oracle_port.exists():
            return oracle_port
    fallback = Path.home() / ".oracle-inference" / "daemon.port"
    if fallback.exists():
        return fallback
    return None


def _get_scorer() -> Scorer:
    """Lazy-initialize the scorer. Tries oracle sidecar first."""
    global _scorer  # noqa: PLW0603 - module-level singleton for lazy init
    if _scorer is not None:
        return _scorer

    port_file = _get_oracle_port_file()
    if port_file is not None:
        sidecar = SidecarScorer(port_file)
        if sidecar.available():
            _log.info("Scoring backend: oracle sidecar via %s", port_file)
            _scorer = sidecar
            return _scorer
        _log.info("Oracle port file found but sidecar unavailable, falling back")

    _scorer = YamlScorer(_MODEL_PATH)
    if _scorer.available():
        _log.info("Scoring backend: YAML model from %s", _MODEL_PATH)
    else:
        _log.warning("No scoring backend available, falling back to word-overlap")
    return _scorer


def get_blend_weights() -> tuple[float, float]:
    """Return (word_overlap_weight, ml_weight) from the active model."""
    scorer = _get_scorer()
    if not scorer.available():
        return (1.0, 0.0)  # fallback: 100% word-overlap
    return scorer.blend_weights


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
