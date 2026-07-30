"""Semantic ranking of findings over an embedding backend.

Reuses memory-palace's ``EmbeddingIndex`` (which ships a dependency-free
SHA-256 hash-vector fallback, so no new hard dependency). The backend is
optional and loaded via a guarded import; its absence is an explicit
failure, matching the graph seam.
"""

from __future__ import annotations

import importlib.util
import math
import warnings
from typing import Any, Literal, Protocol, runtime_checkable

from tome.graph.palace_adapter import GraphBackendUnavailable
from tome.models import Finding


class NonSemanticRetrievalWarning(UserWarning):
    """Emitted when retrieval runs over the non-semantic hash fallback.

    Ranking over the SHA-256 hash provider is deterministic but not
    semantically meaningful. The degradation is surfaced rather than
    silent so callers can install ``sentence_transformers`` or filter
    this category deliberately.
    """


# memory-palace is an optional, co-installed backend. See the note in
# graph/palace_adapter.py for why the alias is declared ``Any``.
_EmbeddingIndex: Any
try:
    from memory_palace import EmbeddingIndex as _mp_embedding_index
except ImportError:
    _EmbeddingIndex = None
else:
    _EmbeddingIndex = _mp_embedding_index


@runtime_checkable
class Embedder(Protocol):
    """The minimal surface tome needs to embed text."""

    def vectorize(self, text: str) -> list[float]: ...


def _cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors; 0.0 if either vector is zero.

    Raises:
        ValueError: When the vectors differ in width. One embedder
            vectorizes the query and every finding, so a mismatch can
            only mean a backend defect (stale persisted vectors, a
            provider dimensionality change). Scoring it ``0.0`` would
            sink the finding indistinguishably from a genuinely
            irrelevant one, so the defect is raised at its origin.
    """
    if len(a) != len(b):
        raise ValueError(f"embedding dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


Provider = Literal["local", "none"]

_HASH_PROVIDER: Provider = "none"
_MODEL_PROVIDER: Provider = "local"


def embedder_available() -> bool:
    """Return whether the embedding backend is importable."""
    return _EmbeddingIndex is not None


def best_available_provider() -> Provider:
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


def open_embedder(
    embeddings_path: str, provider: Provider = _HASH_PROVIDER
) -> Embedder:
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
    if provider == _HASH_PROVIDER:
        warnings.warn(
            "Opening a non-semantic embedder (provider='none'): ranking over "
            "the SHA-256 hash fallback is deterministic but not semantic. "
            "Install sentence-transformers for meaningful semantic retrieval.",
            NonSemanticRetrievalWarning,
            stacklevel=2,
        )
    embedder: Embedder = _EmbeddingIndex(embeddings_path, provider=provider)
    return embedder


class SemanticRetriever:
    """Rank findings by embedding similarity to a query.

    The retriever knows whether its own ranking is meaningful. Ordering
    by cosine over the SHA-256 hash fallback produces a stable but
    arbitrary sequence, so that case is reported through
    :class:`NonSemanticRetrievalWarning` rather than passed off as a
    relevance ranking.
    """

    def __init__(self, embedder: Embedder, *, is_semantic: bool | None = None) -> None:
        """Wrap ``embedder``, recording whether its vectors are semantic.

        Args:
            embedder: The backend that vectorizes query and findings.
            is_semantic: Whether ``embedder`` produces semantically
                meaningful vectors. Left unset, it is read off the
                embedder's ``requested_provider`` when it publishes one
                (memory-palace's ``EmbeddingIndex`` does); embedders
                that declare no provider are taken at their word rather
                than presumed degraded.
        """
        self._embedder = embedder
        self.is_semantic: bool = (
            self._infer_semantic(embedder) if is_semantic is None else is_semantic
        )

    @staticmethod
    def _infer_semantic(embedder: Embedder) -> bool:
        """Read semantic status off a backend that publishes its provider."""
        return (
            getattr(embedder, "requested_provider", _MODEL_PROVIDER) != _HASH_PROVIDER
        )

    def rank(
        self, query: str, findings: list[Finding], top_k: int | None = None
    ) -> list[Finding]:
        """Return findings ordered by cosine similarity to ``query``.

        Warns:
            NonSemanticRetrievalWarning: When ranking over the
                non-semantic hash fallback, where the resulting order
                carries no relevance signal.
        """
        if not findings:
            return []
        if not self.is_semantic:
            warnings.warn(
                "Ranking over a non-semantic embedder: the SHA-256 hash "
                "fallback is deterministic but not semantic, so this order "
                "carries no relevance signal. Install sentence-transformers "
                "and open the embedder with provider='local'.",
                NonSemanticRetrievalWarning,
                stacklevel=2,
            )
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
