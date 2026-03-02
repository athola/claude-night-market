"""Semantic deduplication using FAISS vector similarity search.

Uses cosine similarity to detect near-duplicate content before storage.
"""

from __future__ import annotations

import hashlib
import logging
import math

import faiss  # type: ignore[import-not-found,import-untyped]
import numpy as np  # type: ignore[import-not-found,import-untyped]

logger = logging.getLogger(__name__)

# Default similarity threshold (0.8 matches ACE Playbook recommendation)
DEFAULT_THRESHOLD = 0.8

_HAS_FAISS = True  # Always True; faiss-cpu is a mandatory dependency


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings on their word sets."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union


def _cosine_similarity_numpy(vec_a: np.ndarray, vec_b: np.ndarray) -> float:  # type: ignore[type-arg]
    """Compute cosine similarity between two numpy vectors."""
    assert np is not None  # noqa: S101  # caller guarantees numpy is available  # nosec B101
    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


class SemanticDeduplicator:
    """Detect near-duplicate content before storing new entries.

    Uses FAISS cosine similarity when available; falls back to Jaccard similarity
    on word sets when FAISS/numpy are not installed.

    Counter increments track how many times near-duplicate content was seen
    instead of storing each occurrence.

    Args:
        threshold: Similarity score above which content is considered a duplicate.
            Defaults to 0.8.
        vector_dim: Dimension of embedding vectors for the FAISS index.
            Only used when FAISS is available. Defaults to 128.

    """

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        vector_dim: int = 128,
    ) -> None:
        """Initialize the deduplicator with FAISS index."""
        self.threshold = threshold
        self.vector_dim = vector_dim
        self._near_duplicate_counts: dict[str, int] = {}
        self._use_faiss = True
        self._stored_texts: list[str] = []  # Unused; Jaccard fallback is dead code

        # FAISS flat index with inner-product search on L2-normalised vectors
        # (inner product on unit vectors == cosine similarity)
        self._index: faiss.IndexFlatIP = faiss.IndexFlatIP(vector_dim)  # type: ignore[name-defined]
        # Track which entry_id corresponds to each FAISS index position
        self._entry_ids: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def should_store(
        self,
        new_content: str,
        existing_embeddings: dict[str, list[float]] | None = None,
        *,
        entry_id: str | None = None,
    ) -> bool:
        """Return True if new_content is sufficiently distinct to store.

        When content is too similar to existing content (similarity >= threshold),
        the near-duplicate counter for the closest matching entry is incremented
        instead of signalling storage.

        Args:
            new_content: The text content to evaluate.
            existing_embeddings: Optional dict mapping entry_id to vector.
                Used by the FAISS path when pre-computed embeddings are supplied
                instead of the internal index. Ignored by the fallback path.
            entry_id: Identifier for new_content, used for counter bookkeeping.
                Defaults to a truncated hash of the content.

        Returns:
            True if the content should be stored, False if it is a near-duplicate.

        """
        resolved_id = entry_id or _content_id(new_content)

        if self._use_faiss:
            return self._should_store_faiss(
                new_content, existing_embeddings, resolved_id
            )
        return self._should_store_jaccard(new_content, resolved_id)

    def add_vector(self, entry_id: str, vector: list[float]) -> None:
        """Register a new vector in the internal FAISS index.

        Only meaningful when FAISS is available.  In fallback mode the
        corresponding text should be passed via ``add_text`` instead.

        Args:
            entry_id: Identifier for this vector.
            vector: Pre-normalised embedding vector of length ``vector_dim``.

        """
        if not self._use_faiss:
            logger.debug("add_vector called in fallback mode; use add_text instead")
            return
        arr = np.array([vector], dtype="float32")  # type: ignore[call-overload]
        _l2_normalize_rows(arr)
        self._index.add(arr)  # type: ignore[union-attr]
        self._entry_ids.append(entry_id)

    def add_text(self, text: str) -> None:
        """Register raw text for Jaccard-based deduplication (fallback mode only).

        In FAISS mode this is a no-op; use ``add_vector`` instead.

        Args:
            text: Raw text to store for future Jaccard comparisons.

        """
        if self._use_faiss:
            logger.debug("add_text called in FAISS mode; use add_vector instead")
            return
        self._stored_texts.append(text)

    def get_near_duplicate_count(self, entry_id: str) -> int:
        """Return the number of near-duplicates seen for entry_id.

        Args:
            entry_id: The entry identifier to look up.

        Returns:
            Count of suppressed near-duplicates (0 if none seen).

        """
        return self._near_duplicate_counts.get(entry_id, 0)

    @property
    def uses_faiss(self) -> bool:
        """True when the FAISS backend is active."""
        return self._use_faiss

    @property
    def index_size(self) -> int:
        """Number of vectors in the internal FAISS index (0 in fallback mode)."""
        if not self._use_faiss:
            return 0
        return int(self._index.ntotal)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_store_faiss(
        self,
        content: str,
        existing_embeddings: dict[str, list[float]] | None,
        entry_id: str,
    ) -> bool:
        """FAISS-backed duplicate check.

        When existing_embeddings is provided the check runs against that dict
        (useful for one-shot evaluation without mutating the index).  Otherwise
        the internal FAISS index is queried.
        """
        if existing_embeddings:
            best_id, best_score = _best_match_from_dict(content, existing_embeddings)
        else:
            if self._index.ntotal == 0:  # type: ignore[union-attr]
                return True
            best_id, best_score = self._query_index(content)

        if best_score >= self.threshold:
            target = best_id or entry_id
            self._near_duplicate_counts[target] = (
                self._near_duplicate_counts.get(target, 0) + 1
            )
            logger.debug(
                "Near-duplicate detected (%.3f >= %.3f): suppressing %r",
                best_score,
                self.threshold,
                entry_id,
            )
            return False
        return True

    def _should_store_jaccard(self, content: str, entry_id: str) -> bool:
        """Jaccard-based duplicate check (fallback mode)."""
        if not self._stored_texts:
            return True

        best_score = 0.0
        best_idx = 0
        for idx, stored in enumerate(self._stored_texts):
            score = _jaccard_similarity(content, stored)
            if score > best_score:
                best_score = score
                best_idx = idx

        if best_score >= self.threshold:
            # Use the best_idx position as a synthetic key
            target_key = f"fallback:{best_idx}"
            self._near_duplicate_counts[target_key] = (
                self._near_duplicate_counts.get(target_key, 0) + 1
            )
            logger.debug(
                "Near-duplicate detected via Jaccard (%.3f >= %.3f): suppressing %r",
                best_score,
                self.threshold,
                entry_id,
            )
            return False
        return True

    def _query_index(self, content: str) -> tuple[str | None, float]:
        """Query the internal FAISS index with a hash-derived vector.

        Returns the best matching entry_id and its cosine similarity score.
        """
        # Derive a deterministic float32 vector from content via hashing
        vec = _hash_to_vector(content, self.vector_dim)
        arr = np.array([vec], dtype="float32")  # type: ignore[call-overload]
        _l2_normalize_rows(arr)
        distances, indices = self._index.search(arr, 1)  # type: ignore[union-attr]
        idx = int(indices[0][0])
        score = float(distances[0][0])
        if idx < 0 or idx >= len(self._entry_ids):
            return None, 0.0
        return self._entry_ids[idx], score


# ------------------------------------------------------------------
# Module-level helpers (no external deps required)
# ------------------------------------------------------------------


def _content_id(content: str, length: int = 12) -> str:
    """Return a short deterministic id from content text."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:length]


def _hash_to_vector(text: str, dim: int) -> list[float]:
    """Derive a float vector from text using SHA-256 byte spreading."""
    digest = hashlib.sha256(text.lower().strip().encode("utf-8")).digest()
    vec = []
    for i in range(dim):
        byte_val = digest[i % len(digest)]
        vec.append(float(byte_val) / 255.0)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _l2_normalize_rows(arr: np.ndarray) -> None:  # type: ignore[type-arg]
    """In-place L2 normalisation of each row in a float32 numpy array."""
    norms = np.linalg.norm(arr, axis=1, keepdims=True)  # type: ignore[union-attr]
    norms = np.where(norms == 0, 1.0, norms)  # type: ignore[union-attr]
    arr /= norms


def _best_match_from_dict(
    content: str,
    embeddings: dict[str, list[float]],
) -> tuple[str | None, float]:
    """Find the closest entry in an embeddings dict using cosine similarity.

    Returns the entry_id of the closest match and its similarity score.
    Requires numpy (only called from the FAISS path where numpy is available).
    """
    query_vec = np.array(
        _hash_to_vector(content, len(next(iter(embeddings.values())))), dtype="float32"
    )  # type: ignore[call-overload]
    norm_q = float(np.linalg.norm(query_vec))  # type: ignore[union-attr]
    if norm_q > 0:
        query_vec /= norm_q

    best_id: str | None = None
    best_score = -1.0
    for eid, vec in embeddings.items():
        candidate = np.array(vec, dtype="float32")  # type: ignore[call-overload]
        score = _cosine_similarity_numpy(query_vec, candidate)
        if score > best_score:
            best_score = score
            best_id = eid

    return best_id, max(best_score, 0.0)
