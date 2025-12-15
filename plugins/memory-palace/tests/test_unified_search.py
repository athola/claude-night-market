"""Tests for unified search with optional embeddings."""

from __future__ import annotations

from pathlib import Path

from memory_palace.corpus.cache_lookup import CacheLookup

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PLUGIN_ROOT / "docs" / "knowledge-corpus"
INDEX_DIR = PLUGIN_ROOT / "data" / "indexes"


def test_embedding_search_returns_matches() -> None:
    """Test that embedding search returns matches."""
    lookup = CacheLookup(
        corpus_dir=str(CORPUS_DIR),
        index_dir=str(INDEX_DIR),
        embedding_provider="local",
    )
    results = lookup.search("structured concurrency cancellation", mode="embeddings")
    assert results
    assert results[0]["source"] == "embeddings"


def test_keyword_search_still_works_without_embeddings() -> None:
    """Test that keyword search works without embeddings."""
    lookup = CacheLookup(
        corpus_dir=str(CORPUS_DIR),
        index_dir=str(INDEX_DIR),
        embedding_provider="none",
    )
    results = lookup.search("konmari knowledge tidy", mode="unified")
    assert results
