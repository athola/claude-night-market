"""
Feature: semantic retrieval over findings (build increment 4)

As the tome research engine
I want findings ranked by embedding similarity to the query
So that relevant results surface even without lexical overlap,
reusing memory-palace's EmbeddingIndex (hash fallback, no hard deps).
"""

from __future__ import annotations

from typing import Any

import pytest
from tome.retrieval.semantic import (
    Embedder,
    SemanticRetriever,
    embedder_available,
    open_embedder,
)

from tests.factories import make_finding


class FakeEmbedder:
    """Deterministic embedder: 'match' texts align with 'match' queries."""

    def vectorize(self, text: str) -> list[float]:
        return [1.0, 0.0] if "match" in text else [0.0, 1.0]


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


class TestOpenEmbedder:
    @pytest.mark.unit
    def test_raises_explicitly_when_absent(self) -> None:
        if embedder_available():
            pytest.skip("memory-palace installed; cannot test absent path")
        with pytest.raises(Exception, match="memory-palace"):
            open_embedder("/tmp/tome-emb.yaml")


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
