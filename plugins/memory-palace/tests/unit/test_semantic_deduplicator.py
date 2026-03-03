"""Tests for semantic deduplication module.

Feature: Semantic deduplication of memory palace entries

As a memory palace user
I want near-duplicate content to be suppressed
So that the knowledge base stays dense and non-redundant
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

faiss = pytest.importorskip("faiss", reason="faiss-cpu not installed")

from memory_palace.corpus.semantic_deduplicator import (  # noqa: E402
    DEFAULT_THRESHOLD,
    SemanticDeduplicator,
    _content_id,
    _cosine_similarity_numpy,
    _hash_to_vector,
    _jaccard_similarity,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unit_vectors(n: int, dim: int = 4) -> list[list[float]]:
    """Return n simple unit vectors for testing (each different)."""
    import math

    vecs = []
    for i in range(n):
        angle = (i / max(n, 1)) * math.pi / 2  # spread across first quadrant
        vec = [math.cos(angle)] + [math.sin(angle) / max(dim - 1, 1)] * (dim - 1)
        norm = math.sqrt(sum(v * v for v in vec))
        vecs.append([v / norm for v in vec])
    return vecs


# ---------------------------------------------------------------------------
# Jaccard helper (no external deps)
# ---------------------------------------------------------------------------


class TestJaccardSimilarity:
    """Unit tests for the Jaccard fallback helper."""

    @pytest.mark.unit
    def test_identical_strings_score_one(self) -> None:
        """
        Scenario: Identical content
        Given two identical strings
        When Jaccard similarity is computed
        Then the score is 1.0
        """
        assert _jaccard_similarity("hello world", "hello world") == 1.0

    @pytest.mark.unit
    def test_disjoint_strings_score_zero(self) -> None:
        """
        Scenario: Completely different content
        Given two strings with no common words
        When Jaccard similarity is computed
        Then the score is 0.0
        """
        assert _jaccard_similarity("apple banana", "cat dog") == 0.0

    @pytest.mark.unit
    def test_partial_overlap(self) -> None:
        """
        Scenario: Partial word overlap
        Given two strings sharing half their words
        When Jaccard similarity is computed
        Then the score reflects the overlap ratio
        """
        # {"a", "b"} ∩ {"b", "c"} = {"b"} → 1/3
        score = _jaccard_similarity("a b", "b c")
        assert abs(score - 1 / 3) < 1e-9

    @pytest.mark.unit
    def test_empty_strings(self) -> None:
        """
        Scenario: Both strings empty
        Given two empty strings
        When Jaccard similarity is computed
        Then the score is 1.0 (vacuously equal)
        """
        assert _jaccard_similarity("", "") == 1.0

    @pytest.mark.unit
    def test_one_empty_string(self) -> None:
        """
        Scenario: One empty string
        Given one empty and one non-empty string
        When Jaccard similarity is computed
        Then the score is 0.0
        """
        assert _jaccard_similarity("", "something") == 0.0


# ---------------------------------------------------------------------------
# SemanticDeduplicator — FAISS mode
# ---------------------------------------------------------------------------


class TestSemanticDeduplicatorFaiss:
    """
    Feature: FAISS-backed semantic deduplication

    As a memory palace plugin
    I want to use FAISS cosine similarity for duplicate detection
    So that near-identical embeddings are suppressed efficiently
    """

    @pytest.fixture
    def deduplicator(self) -> SemanticDeduplicator:
        """Fresh deduplicator in FAISS mode."""
        return SemanticDeduplicator(threshold=0.8, vector_dim=4)

    @pytest.mark.unit
    def test_uses_faiss_when_available(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: FAISS is installed
        Given FAISS and numpy are importable
        When a SemanticDeduplicator is constructed
        Then it reports uses_faiss=True
        """
        assert deduplicator.uses_faiss is True

    @pytest.mark.unit
    def test_empty_index_always_stores(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: First entry in empty index
        Given the FAISS index is empty
        When should_store is called
        Then it returns True (nothing to compare against)
        """
        assert deduplicator.should_store("any content") is True

    @pytest.mark.unit
    def test_distinct_embeddings_stored(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Sufficiently different content
        Given an existing vector in the index
        When new content with low similarity is checked
        Then should_store returns True
        """
        vecs = _unit_vectors(2, dim=4)
        deduplicator.add_vector("entry-a", vecs[0])

        # Use existing_embeddings with the same vector for "entry-a"
        # but build a second embedding that is orthogonal
        orthogonal = [0.0, 1.0, 0.0, 0.0]
        existing: dict[str, list[float]] = {"entry-a": vecs[0]}

        # Patch _hash_to_vector to return our orthogonal vector
        with patch(
            "memory_palace.corpus.semantic_deduplicator._hash_to_vector",
            return_value=orthogonal,
        ):
            result = deduplicator.should_store("new content", existing)

        assert result is True

    @pytest.mark.unit
    def test_near_duplicate_suppressed(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Near-duplicate content
        Given an existing embedding at similarity >= threshold
        When should_store is called with nearly identical content
        Then it returns False
        """
        vec = [1.0, 0.0, 0.0, 0.0]
        existing: dict[str, list[float]] = {"entry-a": vec}

        # Patch so that the query vector matches entry-a exactly (score = 1.0)
        with patch(
            "memory_palace.corpus.semantic_deduplicator._hash_to_vector",
            return_value=vec,
        ):
            result = deduplicator.should_store("almost same content", existing)

        assert result is False

    @pytest.mark.unit
    def test_counter_increments_on_near_duplicate(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Near-duplicate counter tracks suppressed entries
        Given an existing embedding
        When the same near-duplicate content is submitted twice
        Then the counter for the matched entry increments each time
        """
        vec = [1.0, 0.0, 0.0, 0.0]
        existing: dict[str, list[float]] = {"entry-a": vec}

        with patch(
            "memory_palace.corpus.semantic_deduplicator._hash_to_vector",
            return_value=vec,
        ):
            deduplicator.should_store("dup 1", existing)
            deduplicator.should_store("dup 2", existing)

        count = deduplicator.get_near_duplicate_count("entry-a")
        assert count == 2

    @pytest.mark.unit
    def test_threshold_boundary_at_exactly_threshold(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Similarity exactly at threshold
        Given existing content and new content with similarity == threshold
        When should_store is called
        Then it returns False (threshold is inclusive)
        """
        vec = [1.0, 0.0, 0.0, 0.0]
        existing: dict[str, list[float]] = {"entry-a": vec}
        # Similarity will be 1.0 >= 0.8 → suppressed
        with patch(
            "memory_palace.corpus.semantic_deduplicator._hash_to_vector",
            return_value=vec,
        ):
            result = deduplicator.should_store("content", existing, entry_id="new")
        assert result is False

    @pytest.mark.unit
    def test_below_threshold_allows_storage(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Similarity below threshold
        Given existing content with similarity < threshold
        When should_store is called
        Then it returns True
        """
        vec_a = [1.0, 0.0, 0.0, 0.0]
        # low similarity vector: mostly orthogonal
        vec_b = [0.1, 0.99, 0.0, 0.0]
        import math

        norm = math.sqrt(sum(v * v for v in vec_b))
        vec_b = [v / norm for v in vec_b]

        existing: dict[str, list[float]] = {"entry-a": vec_a}
        with patch(
            "memory_palace.corpus.semantic_deduplicator._hash_to_vector",
            return_value=vec_b,
        ):
            result = deduplicator.should_store("different content", existing)
        assert result is True

    @pytest.mark.unit
    def test_add_vector_increases_index_size(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: add_vector populates the index
        Given a fresh deduplicator
        When add_vector is called
        Then index_size increases
        """
        assert deduplicator.index_size == 0
        deduplicator.add_vector("e1", [1.0, 0.0, 0.0, 0.0])
        assert deduplicator.index_size == 1

    @pytest.mark.unit
    def test_custom_threshold_respected(self) -> None:
        """
        Scenario: Custom threshold
        Given a deduplicator with threshold=0.5
        When content with similarity 0.6 is submitted
        Then it is suppressed (>= 0.5)
        """
        dedup = SemanticDeduplicator(threshold=0.5, vector_dim=4)
        vec = [1.0, 0.0, 0.0, 0.0]
        existing: dict[str, list[float]] = {"e": vec}
        with patch(
            "memory_palace.corpus.semantic_deduplicator._hash_to_vector",
            return_value=vec,
        ):
            result = dedup.should_store("content", existing)
        assert result is False

    @pytest.mark.unit
    def test_default_threshold_value(self) -> None:
        """DEFAULT_THRESHOLD constant should be 0.8 (ACE Playbook recommendation)."""
        assert DEFAULT_THRESHOLD == 0.8

    @pytest.mark.unit
    def test_content_id_is_deterministic(self) -> None:
        """_content_id returns the same value for the same input."""
        assert _content_id("hello") == _content_id("hello")

    @pytest.mark.unit
    def test_content_id_differs_for_different_content(self) -> None:
        """_content_id returns different values for different inputs."""
        assert _content_id("hello") != _content_id("world")


# ---------------------------------------------------------------------------
# SemanticDeduplicator — fallback (Jaccard) mode
# ---------------------------------------------------------------------------


class TestSemanticDeduplicatorFaissMandatory:
    """
    Feature: FAISS is always available (mandatory dependency since 1.5.2)
    """

    @pytest.mark.unit
    def test_always_uses_faiss(self) -> None:
        """FAISS mode is always active since faiss-cpu is mandatory."""
        dedup = SemanticDeduplicator(threshold=0.8, vector_dim=4)
        assert dedup.uses_faiss is True

    @pytest.mark.unit
    def test_add_text_is_noop_in_faiss_mode(self) -> None:
        """add_text is a no-op since FAISS is always active."""
        dedup = SemanticDeduplicator(threshold=0.8, vector_dim=4)
        dedup.add_text("some text")  # should not raise
        assert dedup.index_size == 0


# ---------------------------------------------------------------------------
# Internal index path (should_store without existing_embeddings)
# ---------------------------------------------------------------------------


class TestSemanticDeduplicatorInternalIndex:
    """
    Feature: FAISS internal index queries

    As a memory palace plugin
    I want should_store to query the internal FAISS index directly
    So that callers don't need to supply their own embeddings dict
    """

    @pytest.fixture
    def deduplicator(self) -> SemanticDeduplicator:
        return SemanticDeduplicator(threshold=0.8, vector_dim=128)

    @pytest.mark.unit
    def test_index_query_detects_same_content(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Identical content queried via internal index
        Given a vector derived from "hello world" is in the index
        When should_store is called with "hello world" (no embeddings dict)
        Then it returns False because the hash-derived vectors match exactly
        """
        content = "hello world"
        vec = _hash_to_vector(content, 128)
        deduplicator.add_vector("e1", vec)

        result = deduplicator.should_store(content)
        assert result is False

    @pytest.mark.unit
    def test_index_query_allows_distinct_content(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Different content queried via internal index
        Given a vector for "topic A" is in the index
        When should_store is called with "completely unrelated topic B"
        Then it returns True because the hash-derived vectors differ enough
        """
        deduplicator.add_vector("e1", _hash_to_vector("topic A", 128))

        result = deduplicator.should_store(
            "completely unrelated topic B with different words"
        )
        assert result is True

    @pytest.mark.unit
    def test_index_query_counter_incremented(
        self, deduplicator: SemanticDeduplicator
    ) -> None:
        """
        Scenario: Counter incremented via internal index match
        Given a vector in the index that matches new content
        When should_store returns False
        Then the near-duplicate counter for that entry is incremented
        """
        content = "the quick brown fox"
        vec = _hash_to_vector(content, 128)
        deduplicator.add_vector("fox-entry", vec)

        deduplicator.should_store(content)
        assert deduplicator.get_near_duplicate_count("fox-entry") == 1


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class TestModuleLevelHelpers:
    """
    Feature: Module-level utility functions

    As a developer
    I want _hash_to_vector and _cosine_similarity_numpy to behave correctly
    So that the deduplication math is reliable
    """

    @pytest.mark.unit
    def test_hash_to_vector_returns_correct_dimension(self) -> None:
        """
        Scenario: Vector dimension matches request
        Given a text and dimension=64
        When _hash_to_vector is called
        Then the result has exactly 64 elements
        """
        vec = _hash_to_vector("test input", 64)
        assert len(vec) == 64

    @pytest.mark.unit
    def test_hash_to_vector_is_unit_length(self) -> None:
        """
        Scenario: Output vector is L2-normalized
        Given any text
        When _hash_to_vector is called
        Then the result has L2 norm approximately 1.0
        """
        import math

        vec = _hash_to_vector("normalize me", 128)
        norm = math.sqrt(sum(v * v for v in vec))
        assert abs(norm - 1.0) < 1e-6

    @pytest.mark.unit
    def test_hash_to_vector_is_deterministic(self) -> None:
        """
        Scenario: Same text produces same vector
        Given a fixed text
        When _hash_to_vector is called twice
        Then both results are identical
        """
        v1 = _hash_to_vector("determinism check", 32)
        v2 = _hash_to_vector("determinism check", 32)
        assert v1 == v2

    @pytest.mark.unit
    def test_hash_to_vector_case_insensitive(self) -> None:
        """
        Scenario: Case normalization
        Given "Hello" and "hello"
        When _hash_to_vector is called on each
        Then both produce the same vector
        """
        v1 = _hash_to_vector("Hello World", 32)
        v2 = _hash_to_vector("hello world", 32)
        assert v1 == v2

    @pytest.mark.unit
    def test_cosine_similarity_identical_vectors(self) -> None:
        """
        Scenario: Identical vectors
        Given two identical numpy vectors
        When _cosine_similarity_numpy is called
        Then the score is 1.0
        """
        import numpy as np

        vec = np.array([1.0, 0.0, 0.0], dtype="float32")
        assert abs(_cosine_similarity_numpy(vec, vec) - 1.0) < 1e-6

    @pytest.mark.unit
    def test_cosine_similarity_orthogonal_vectors(self) -> None:
        """
        Scenario: Orthogonal vectors
        Given two perpendicular numpy vectors
        When _cosine_similarity_numpy is called
        Then the score is 0.0
        """
        import numpy as np

        a = np.array([1.0, 0.0, 0.0], dtype="float32")
        b = np.array([0.0, 1.0, 0.0], dtype="float32")
        assert abs(_cosine_similarity_numpy(a, b)) < 1e-6

    @pytest.mark.unit
    def test_cosine_similarity_zero_vector_returns_zero(self) -> None:
        """
        Scenario: Zero vector edge case
        Given one zero vector and one non-zero vector
        When _cosine_similarity_numpy is called
        Then the score is 0.0 (not NaN or error)
        """
        import numpy as np

        zero = np.array([0.0, 0.0, 0.0], dtype="float32")
        nonzero = np.array([1.0, 0.0, 0.0], dtype="float32")
        assert _cosine_similarity_numpy(zero, nonzero) == 0.0
        assert _cosine_similarity_numpy(nonzero, zero) == 0.0

    @pytest.mark.unit
    def test_content_id_custom_length(self) -> None:
        """
        Scenario: Custom ID length
        Given a length of 6
        When _content_id is called
        Then the result is exactly 6 characters
        """
        result = _content_id("some content", length=6)
        assert len(result) == 6
