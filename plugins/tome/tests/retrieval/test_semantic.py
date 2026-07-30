"""
Feature: semantic retrieval over findings (build increment 4)

As the tome research engine
I want findings ranked by embedding similarity to the query
So that relevant results surface even without lexical overlap,
reusing memory-palace's EmbeddingIndex (hash fallback, no hard deps).
"""

from __future__ import annotations

import importlib.util
import warnings
from typing import Any

import pytest

from tests.factories import make_finding
from tome.graph.palace_adapter import GraphBackendUnavailable
from tome.retrieval import semantic as semantic_module
from tome.retrieval.semantic import (
    Embedder,
    NonSemanticRetrievalWarning,
    SemanticRetriever,
    _cosine,
    best_available_provider,
    embedder_available,
    open_embedder,
)


class FakeEmbedder:
    """Deterministic embedder: 'match' texts align with 'match' queries."""

    def vectorize(self, text: str) -> list[float]:
        return [1.0, 0.0] if "match" in text else [0.0, 1.0]


class HashFallbackEmbedder(FakeEmbedder):
    """Stands in for an EmbeddingIndex opened on the hash fallback."""

    requested_provider = "none"


class RaggedEmbedder:
    """Returns vectors of differing width; models a corrupted index."""

    def vectorize(self, text: str) -> list[float]:
        return [1.0, 0.0] if "match" in text else [1.0]


class TestSemanticRetriever:
    @pytest.mark.unit
    def test_ranks_similar_findings_first(self) -> None:
        """
        Given a query and one matching, one non-matching finding
        When ranked semantically
        Then the matching finding comes first
        """
        retriever = SemanticRetriever(FakeEmbedder())
        hit = make_finding(0.5, title="match topic", summary="about match")
        miss = make_finding(0.5, title="unrelated", summary="other subject")

        ranked = retriever.rank("match", [miss, hit])

        assert ranked[0] is hit
        assert ranked[1] is miss

    @pytest.mark.unit
    def test_top_k_limits_results(self) -> None:
        retriever = SemanticRetriever(FakeEmbedder())
        findings = [make_finding(0.5, title=f"match {i}") for i in range(4)]

        assert len(retriever.rank("match", findings, top_k=2)) == 2

    @pytest.mark.unit
    def test_empty_findings_returns_empty(self) -> None:
        retriever = SemanticRetriever(FakeEmbedder())
        assert retriever.rank("match", []) == []

    @pytest.mark.unit
    def test_fake_satisfies_protocol(self) -> None:
        assert isinstance(FakeEmbedder(), Embedder)


class TestCosineDimensionInvariant:
    """A width mismatch is a backend defect, not a zero-similarity result."""

    @pytest.mark.unit
    def test_length_mismatch_raises(self) -> None:
        """
        Given two vectors of different width
        When cosine similarity is computed
        Then the dimension defect is raised, not scored as 0.0
        """
        with pytest.raises(ValueError, match="embedding dimension mismatch: 2 vs 1"):
            _cosine([1.0, 0.0], [1.0])

    @pytest.mark.unit
    def test_zero_norm_still_returns_zero(self) -> None:
        """Cosine of a zero vector is undefined; 0.0 stays the answer."""
        assert _cosine([0.0, 0.0], [1.0, 0.0]) == 0.0

    @pytest.mark.unit
    def test_ragged_embedder_surfaces_defect_through_rank(self) -> None:
        """A corrupted index fails loudly instead of silently sinking."""
        retriever = SemanticRetriever(RaggedEmbedder())

        with pytest.raises(ValueError, match="embedding dimension mismatch"):
            retriever.rank("match", [make_finding(0.5, title="unrelated")])


class TestRetrieverProviderAwareness:
    """The retriever knows whether its own ranking is meaningful (#642)."""

    @pytest.mark.unit
    def test_hash_backed_retriever_is_not_semantic(self) -> None:
        assert SemanticRetriever(HashFallbackEmbedder()).is_semantic is False

    @pytest.mark.unit
    def test_unknown_embedder_is_taken_at_its_word(self) -> None:
        """Embedders that declare no provider are not assumed degraded."""
        assert SemanticRetriever(FakeEmbedder()).is_semantic is True

    @pytest.mark.unit
    def test_explicit_override_wins(self) -> None:
        assert SemanticRetriever(FakeEmbedder(), is_semantic=False).is_semantic is False

    @pytest.mark.unit
    def test_ranking_over_hash_fallback_warns(self) -> None:
        """
        Given a retriever backed by the non-semantic hash provider
        When findings are ranked
        Then the meaningless ordering is surfaced as a warning
        """
        retriever = SemanticRetriever(HashFallbackEmbedder())

        with pytest.warns(NonSemanticRetrievalWarning, match="not semantic"):
            retriever.rank("match", [make_finding(0.5, title="match topic")])

    @pytest.mark.unit
    def test_semantic_ranking_stays_quiet(self) -> None:
        retriever = SemanticRetriever(FakeEmbedder())

        with warnings.catch_warnings():
            warnings.simplefilter("error", NonSemanticRetrievalWarning)
            retriever.rank("match", [make_finding(0.5, title="match topic")])

    @pytest.mark.unit
    def test_empty_findings_does_not_warn(self) -> None:
        """No ranking happened, so there is no degradation to report."""
        retriever = SemanticRetriever(HashFallbackEmbedder())

        with warnings.catch_warnings():
            warnings.simplefilter("error", NonSemanticRetrievalWarning)
            assert retriever.rank("match", []) == []


class TestOpenEmbedder:
    @pytest.mark.unit
    def test_raises_explicitly_when_absent(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Absence is simulated, not inherited from the environment, so
        this branch stays reachable in the dev setup where memory-palace
        is installed for the contract tests."""
        monkeypatch.setattr(semantic_module, "_EmbeddingIndex", None)
        with pytest.raises(GraphBackendUnavailable, match="memory-palace"):
            open_embedder(str(tmp_path / "tome-emb.yaml"))

    @pytest.mark.unit
    def test_availability_tracks_the_backend_alias(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The predicate reports the backend it actually guards, so it
        cannot drift from the branch ``open_embedder`` takes."""
        monkeypatch.setattr(semantic_module, "_EmbeddingIndex", None)
        assert embedder_available() is False

        monkeypatch.setattr(semantic_module, "_EmbeddingIndex", object())
        assert embedder_available() is True


class TestRealEmbedderContract:
    """Runs only where memory-palace is installed (combined CI)."""

    @pytest.mark.integration
    def test_real_embedding_index_ranks(self, tmp_path: Any) -> None:
        pytest.importorskip("memory_palace")
        embedder = open_embedder(str(tmp_path / "emb.yaml"))
        retriever = SemanticRetriever(embedder)

        findings = [
            make_finding(0.5, title="graph neural networks", summary="gnn"),
            make_finding(0.5, title="baking sourdough bread", summary="yeast"),
        ]
        ranked = retriever.rank("graph neural networks", findings, top_k=2)

        assert len(ranked) == 2
        assert {f.title for f in ranked} == {f.title for f in findings}


class TestProviderSelection:
    @pytest.mark.unit
    def test_best_available_provider_is_valid(self) -> None:
        """Auto-selection returns a provider EmbeddingIndex understands."""
        assert best_available_provider() in {"none", "local"}

    @pytest.mark.unit
    def test_falls_back_to_hash_without_sentence_transformers(self) -> None:
        """
        Given sentence-transformers is not installed (tome's isolated venv)
        Then the auto-selected provider is the hash fallback
        """
        if importlib.util.find_spec("sentence_transformers") is not None:
            pytest.skip("sentence-transformers installed; cannot test fallback")
        assert best_available_provider() == "none"


class TestProviderPlumbing:
    """Runs only where memory-palace is installed (combined CI)."""

    @pytest.mark.integration
    def test_provider_is_passed_to_backend(self, tmp_path: Any) -> None:
        pytest.importorskip("memory_palace")
        embedder: Any = open_embedder(str(tmp_path / "e.yaml"), provider="local")

        assert embedder.requested_provider == "local"

    @pytest.mark.integration
    def test_default_provider_is_hash(self, tmp_path: Any) -> None:
        pytest.importorskip("memory_palace")
        embedder: Any = open_embedder(str(tmp_path / "e2.yaml"))

        assert embedder.requested_provider == "none"


class TestDegradationObservability:
    """The non-semantic fallback must be surfaced, not silent (#642)."""

    @pytest.mark.integration
    def test_hash_provider_emits_warning(self, tmp_path: Any) -> None:
        """Opening the hash fallback warns so degradation is observable."""
        pytest.importorskip("memory_palace")
        with pytest.warns(NonSemanticRetrievalWarning, match="not semantic"):
            open_embedder(str(tmp_path / "w.yaml"), provider="none")

    @pytest.mark.integration
    def test_real_provider_does_not_warn(self, tmp_path: Any) -> None:
        """The semantic provider path stays quiet."""
        pytest.importorskip("memory_palace")
        with warnings.catch_warnings():
            warnings.simplefilter("error", NonSemanticRetrievalWarning)
            open_embedder(str(tmp_path / "q.yaml"), provider="local")
