"""Scorer protocol and YAML-backed implementation."""

from __future__ import annotations

import json as _json
import logging
import math
from pathlib import Path as _Path
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

import yaml

_log = logging.getLogger(__name__)


class Scorer(Protocol):
    """Inference backend contract.

    Phase 1: YamlScorer (pure Python dot product).
    Phase 2: OnnxSidecarScorer (HTTP to localhost daemon).
    """

    def score(self, features: dict[str, float]) -> float:
        """Return a score for the given feature vector."""
        ...  # pragma: no cover

    def available(self) -> bool:
        """Return True if the scorer is ready for inference."""
        ...  # pragma: no cover

    @property
    def blend_weights(self) -> tuple[float, float]:
        """Return (word_overlap_weight, ml_weight) blend weights."""
        ...  # pragma: no cover


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
            wo = max(0.0, float(blend.get("word_overlap_weight", 0.5)))
            ml = max(0.0, float(blend.get("ml_weight", 0.5)))
            total = wo + ml
            if total > 0:
                wo, ml = wo / total, ml / total
            else:
                wo, ml = 0.5, 0.5
            self._blend = (wo, ml)
            self._loaded = bool(self._weights)
        except (OSError, yaml.YAMLError, ValueError, TypeError) as exc:
            _log.warning("Failed to load model from %s: %s", model_path, exc)
            self._loaded = False

    def score(self, features: dict[str, float]) -> float:
        """Compute dot product of weights and features, plus intercept."""
        if not self._loaded:
            return 0.0
        linear = sum(w * features.get(name, 0.0) for name, w in self._weights.items())
        linear += self._intercept
        if self._use_sigmoid:
            # Numerically stable sigmoid: avoids OverflowError from
            # math.exp() when |linear| > ~709.
            if linear >= 0:
                return 1.0 / (1.0 + math.exp(-linear))
            z = math.exp(linear)
            return z / (1.0 + z)
        return linear

    def available(self) -> bool:
        """Return True if model loaded successfully."""
        return self._loaded

    @property
    def blend_weights(self) -> tuple[float, float]:
        """Return (word_overlap_weight, ml_weight) tuple."""
        return self._blend


class OnnxSidecarScorer:
    """Delegates inference to the oracle daemon over HTTP.

    NOTE: This class intentionally duplicates HTTP logic found in
    ``oracle.client.OracleClient``.  Per ADR-0001 (Plugin Dependency
    Isolation), gauntlet must not import from oracle.  If a third
    plugin needs the same client, extract it into leyline.
    """

    def __init__(  # noqa: D107 - params documented in class docstring
        self,
        port_file: _Path,
        model: str = "quality_v1",
        timeout: float = 2.0,
    ) -> None:
        self._port_file = port_file
        self._model = model
        self._timeout = timeout
        self._base_url: str | None = None
        self._blend: tuple[float, float] | None = None

    def _resolve_url(self) -> str | None:
        """Read port file and return base URL."""
        if self._base_url is not None:
            return self._base_url
        try:
            if not self._port_file.exists():
                return None
            port = int(self._port_file.read_text().strip())
            self._base_url = f"http://127.0.0.1:{port}"
            return self._base_url
        except (OSError, ValueError):
            return None

    def available(self) -> bool:
        """Check if the oracle daemon is running."""
        base = self._resolve_url()
        if base is None:
            return False
        try:
            req = Request(f"{base}/health")  # noqa: S310 - host hardcoded to 127.0.0.1, port from state file
            with urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 - host hardcoded to 127.0.0.1, port from state file
                data = _json.loads(resp.read())
                return bool(data.get("status") == "ok")
        except (URLError, OSError, _json.JSONDecodeError):
            self._base_url = None
            return False

    def score(self, features: dict[str, float]) -> float:
        """Send features to daemon and return score.

        Also caches blend weights from the response so
        ``blend_weights`` reflects the model's configuration.
        """
        base = self._resolve_url()
        if base is None:
            return 0.0
        try:
            body = _json.dumps(
                {
                    "model": self._model,
                    "features": features,
                }
            ).encode()
            req = Request(  # noqa: S310 - host hardcoded to 127.0.0.1, port from state file
                f"{base}/infer",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req, timeout=self._timeout) as resp:  # noqa: S310 - host hardcoded to 127.0.0.1, port from state file
                data = _json.loads(resp.read())
                blend = data.get("blend", {})
                if blend:
                    self._blend = (
                        float(blend.get("word_overlap_weight", 0.5)),
                        float(blend.get("ml_weight", 0.5)),
                    )
                return float(data.get("score", 0.0))
        except (URLError, OSError, _json.JSONDecodeError, ValueError):
            self._base_url = None
            return 0.0

    @property
    def blend_weights(self) -> tuple[float, float]:
        """Return blend weights from the daemon's model config.

        Falls back to (0.5, 0.5) until the first successful
        ``score()`` call populates the cache.
        """
        if self._blend is not None:
            return self._blend
        return (0.5, 0.5)
