"""Scorer protocol and YAML-backed implementation."""

from __future__ import annotations

import math
from typing import Protocol

import yaml


class Scorer(Protocol):
    """Inference backend contract.

    Phase 1: YamlScorer (pure Python dot product).
    Phase 2: OnnxSidecarScorer (HTTP to localhost daemon).
    """

    def score(self, features: dict[str, float]) -> float:
        """Return a score for the given feature vector."""
        ...

    def available(self) -> bool:
        """Return True if the scorer is ready for inference."""
        ...


class YamlScorer:
    """Pure-Python logistic regression from exported YAML coefficients.

    Computes: sigmoid(dot(weights, features) + intercept)
    Zero external dependencies beyond pyyaml.
    """

    def __init__(self, model_path: str) -> None:
        """Load model coefficients from the given YAML path."""
        self._weights: dict[str, float] = {}
        self._intercept: float = 0.0
        self._use_sigmoid: bool = True
        self._blend: tuple[float, float] = (0.5, 0.5)
        self._loaded: bool = False
        self._load(model_path)

    def _load(self, model_path: str) -> None:
        """Load model coefficients from YAML."""
        try:
            with open(model_path) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return
            self._weights = {
                str(k): float(v) for k, v in data.get("weights", {}).items()
            }
            self._intercept = float(data.get("intercept", 0.0))
            self._use_sigmoid = bool(data.get("sigmoid", True))
            blend = data.get("blend", {})
            self._blend = (
                float(blend.get("word_overlap_weight", 0.5)),
                float(blend.get("ml_weight", 0.5)),
            )
            self._loaded = bool(self._weights)
        except (OSError, yaml.YAMLError, ValueError, TypeError):
            self._loaded = False

    def score(self, features: dict[str, float]) -> float:
        """Compute dot product of weights and features, plus intercept."""
        if not self._loaded:
            return 0.0
        linear = sum(w * features.get(name, 0.0) for name, w in self._weights.items())
        linear += self._intercept
        if self._use_sigmoid:
            return 1.0 / (1.0 + math.exp(-linear))
        return linear

    def available(self) -> bool:
        """Return True if model loaded successfully."""
        return self._loaded

    @property
    def blend_weights(self) -> tuple[float, float]:
        """Return (word_overlap_weight, ml_weight) tuple."""
        return self._blend
