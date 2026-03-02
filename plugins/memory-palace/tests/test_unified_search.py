"""Tests for unified search with optional embeddings."""

from __future__ import annotations

import pytest

from memory_palace.corpus.cache_lookup import CacheLookup
from memory_palace.corpus.embedding_index import EmbeddingIndex

CONCURRENCY_ENTRY = """\
---
title: Structured Concurrency Patterns
tags: [concurrency, async, cancellation, python]
palace: Engineering
district: Async Patterns
maturity: evergreen
queries:
  - How does structured concurrency handle cancellation?
  - What is task scope in async programming?
---

# Structured Concurrency

Structured concurrency ensures that spawned tasks are cancelled when the
enclosing scope exits. Cancellation propagates through the task hierarchy.
"""

KONMARI_ENTRY = """\
---
title: KonMari Method - Knowledge Tidying
tags: [konmari, tidying, curation, philosophy, decluttering]
palace: Governance Techniques
district: Curation Philosophy
maturity: evergreen
queries:
  - How to declutter knowledge base?
  - What is the KonMari method?
  - How to decide what to keep?
  - Philosophy of tidying
---

# KonMari Method

Marie Kondo's approach to decluttering.
Does it spark joy? The question of what knowledge to keep.
"""


@pytest.fixture()
def corpus_dir(tmp_path):
    """Temporary corpus directory populated with test entries."""
    c_dir = tmp_path / "corpus"
    c_dir.mkdir()
    (c_dir / "concurrency.md").write_text(CONCURRENCY_ENTRY, encoding="utf-8")
    (c_dir / "konmari.md").write_text(KONMARI_ENTRY, encoding="utf-8")
    return c_dir


@pytest.fixture()
def index_dir(tmp_path):
    """Temporary index directory."""
    i_dir = tmp_path / "indexes"
    i_dir.mkdir()
    return i_dir


def test_embedding_search_returns_matches(corpus_dir, index_dir) -> None:
    """Embedding-based search returns matches when entries are indexed."""
    lookup = CacheLookup(
        corpus_dir=str(corpus_dir),
        index_dir=str(index_dir),
        embedding_provider="local",
    )
    # Build keyword index so entry metadata is available for embedding results
    lookup.build_indexes()

    # Build embedding index separately (vectorize each corpus entry)
    embeddings_path = index_dir / "embeddings.yaml"
    emb_index = EmbeddingIndex(str(embeddings_path), provider="local")
    vectors: dict[str, list[float]] = {}
    for md_path in sorted(corpus_dir.glob("*.md")):
        entry_id = md_path.stem
        vectors[entry_id] = emb_index.vectorize(md_path.read_text(encoding="utf-8"))
    emb_index.export(provider="local", entries=vectors)

    # Reload CacheLookup so it picks up the newly written embedding index
    lookup2 = CacheLookup(
        corpus_dir=str(corpus_dir),
        index_dir=str(index_dir),
        embedding_provider="local",
    )
    results = lookup2.search("structured concurrency cancellation", mode="embeddings")
    assert results
    assert results[0]["source"] == "embeddings"


def test_keyword_search_still_works_without_embeddings(corpus_dir, index_dir) -> None:
    """Keyword search works without an embedding provider configured."""
    lookup = CacheLookup(
        corpus_dir=str(corpus_dir),
        index_dir=str(index_dir),
        embedding_provider="none",
    )
    lookup.build_indexes()
    # Query uses terms present in the konmari entry's keyword index
    results = lookup.search("konmari knowledge tidying", mode="unified")
    assert results
