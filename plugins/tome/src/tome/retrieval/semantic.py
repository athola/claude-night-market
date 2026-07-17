"""Semantic ranking of findings over an embedding backend.

Reuses memory-palace's ``EmbeddingIndex`` (which ships a dependency-free
SHA-256 hash-vector fallback, so no new hard dependency). The backend is
optional and loaded via a guarded import; its absence is an explicit
failure, matching the graph seam.
"""

from __future__ import annotations

import importlib.util
import math
from typing import Protocol, runtime_checkable

from tome.graph.palace_adapter import GraphBackendUnavailable
from tome.models import Finding

try:  # memory-palace is an optional, co-installed backend
    from memory_palace import EmbeddingIndex as _EmbeddingIndex
except ImportError:
    _EmbeddingIndex = None


@runtime_checkable
class Embedder(Protocol):
    """The minimal surface tome needs to embed text."""

    def vectorize(self, text: str) -> list[float]: ...


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors; 0.0 if either is degenerate."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


_HASH_PROVIDER = "none"
_MODEL_PROVIDER = "local"


def embedder_available() -> bool:
    """Return whether the embedding backend is importable."""
    return _EmbeddingIndex is not None


def best_available_provider() -> str:
    """Pick the real embedding provider when possible, else the fallback.

    ``"local"`` (sentence-transformers) produces semantically meaningful
    vectors. ``"none"`` is the dependency-free SHA-256 fallback: it is
    deterministic but NOT semantic, so ranking over it is not meaningful.
    Pass the result to :func:`open_embedder` to use the real model
    whenever it is installed.
    """
    try:
        found = importlib.util.find_spec("sentence_transformers") is not None
    except (ImportError, ValueError):
        return _HASH_PROVIDER
    return _MODEL_PROVIDER if found else _HASH_PROVIDER


def open_embedder(embeddings_path: str, provider: str = _HASH_PROVIDER) -> Embedder:
    """Open a memory-palace ``EmbeddingIndex``.

    Args:
        embeddings_path: Where the index persists its vectors.
        provider: ``"local"`` for sentence-transformers (real semantic
            vectors) or ``"none"`` for the hash fallback. Call
            :func:`best_available_provider` to auto-select.

    Raises:
        GraphBackendUnavailable: When memory-palace is not installed.
    """
    if _EmbeddingIndex is None:
        raise GraphBackendUnavailable(
            "semantic retrieval requires memory-palace, which is not installed"
        )
    embedder: Embedder = _EmbeddingIndex(embeddings_path, provider=provider)
    return embedder


class SemanticRetriever:
    """Rank findings by embedding similarity to a query."""

    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder

    def rank(
        self, query: str, findings: list[Finding], top_k: int | None = None
    ) -> list[Finding]:
        """Return findings ordered by cosine similarity to ``query``."""
        if not findings:
            return []
        query_vec = self._embedder.vectorize(query)
        scored: list[tuple[Finding, float]] = [
            (finding, _cosine(query_vec, self._embedder.vectorize(self._text(finding))))
            for finding in findings
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        ranked = [finding for finding, _ in scored]
        return ranked[:top_k] if top_k is not None else ranked

    @staticmethod
    def _text(finding: Finding) -> str:
        return f"{finding.title}. {finding.summary}"
