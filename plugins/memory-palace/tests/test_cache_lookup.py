"""Tests for unified cache lookup functionality."""

from pathlib import Path

import pytest
from memory_palace.corpus.cache_lookup import CacheLookup


@pytest.fixture
def temp_corpus_dir(tmp_path):
    """Create temporary corpus directory with sample entries."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    # Create comprehensive knowledge entry
    franklin_entry = """---
title: Franklin Protocol - Learning Algorithms
tags: [learning, machine-learning, deliberate-practice, feedback-loops]
palace: Learning Techniques
district: Historical Methods
maturity: evergreen
queries:
  - How to improve writing skills systematically?
  - What is gradient descent for learning?
  - How did Benjamin Franklin learn?
  - Best practices for deliberate practice
---

# Franklin Protocol

Benjamin Franklin's learning method embodies **gradient descent**.
This demonstrates Machine Learning principles applied to human learning.

## Key Concepts

- Feature extraction
- Deliberate delay
- Error calculation
"""

    (corpus_dir / "franklin-protocol.md").write_text(franklin_entry)

    # Create another entry
    konmari_entry = """---
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

Marie Kondo's approach to **decluttering**.
Does it spark joy? The question of what to keep.
"""

    (corpus_dir / "konmari-method.md").write_text(konmari_entry)

    return corpus_dir


@pytest.fixture
def temp_index_dir(tmp_path):
    """Create temporary index directory."""
    index_dir = tmp_path / "indexes"
    index_dir.mkdir()
    return index_dir


@pytest.fixture
def cache_lookup(temp_corpus_dir, temp_index_dir):
    """Create and initialize CacheLookup instance."""
    lookup = CacheLookup(
        corpus_dir=str(temp_corpus_dir),
        index_dir=str(temp_index_dir)
    )
    # Build indexes
    lookup.build_indexes()
    return lookup


class TestCacheLookup:
    """Test suite for CacheLookup."""

    def test_initialization(self, temp_corpus_dir, temp_index_dir):
        """Test cache lookup initialization."""
        lookup = CacheLookup(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        assert lookup.corpus_dir == Path(temp_corpus_dir)
        assert lookup.index_dir == Path(temp_index_dir)
        assert lookup.keyword_indexer is not None
        assert lookup.query_manager is not None

    def test_build_indexes(self, temp_corpus_dir, temp_index_dir):
        """Test building both indexes."""
        lookup = CacheLookup(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        lookup.build_indexes()

        # Verify both index files exist
        keyword_index = temp_index_dir / "keyword-index.yaml"
        query_index = temp_index_dir / "query-templates.yaml"

        assert keyword_index.exists()
        assert query_index.exists()

    def test_search_by_keywords(self, cache_lookup):
        """Test search using keywords only."""
        results = cache_lookup.search(
            query="learning machine",
            mode="keywords"
        )

        assert len(results) > 0
        assert any("franklin" in r["entry_id"].lower() for r in results)

    def test_search_by_query_templates(self, cache_lookup):
        """Test search using query templates only."""
        results = cache_lookup.search(
            query="how to improve writing skills",
            mode="queries"
        )

        assert len(results) > 0
        assert any("franklin" in r["entry_id"].lower() for r in results)

    def test_search_unified(self, cache_lookup):
        """Test unified search combining both approaches."""
        results = cache_lookup.search(
            query="improve writing systematically",
            mode="unified"
        )

        assert len(results) > 0

        # Should have match scores
        for result in results:
            assert "match_score" in result
            assert 0.0 <= result["match_score"] <= 1.0

    def test_match_score_classification(self, cache_lookup):
        """Test that match scores are correctly classified."""
        # Strong match: query directly addresses indexed query
        strong_results = cache_lookup.search(
            query="how to improve writing skills systematically",
            mode="unified"
        )

        # Should have at least one strong match
        # Query template matching provides good semantic similarity
        assert len(strong_results) > 0
        assert any(r["match_score"] >= 0.6 for r in strong_results)

        # Partial match: some keywords match
        partial_results = cache_lookup.search(
            query="learning techniques",
            mode="unified"
        )

        # Should have partial matches
        assert len(partial_results) > 0

    def test_result_ranking(self, cache_lookup):
        """Test that results are ranked by match score."""
        results = cache_lookup.search(
            query="learning gradient descent machine",
            mode="unified"
        )

        # Results should be sorted by match_score (highest first)
        scores = [r["match_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_get_entry_content(self, cache_lookup):
        """Test retrieving full entry content."""
        # First search for an entry
        results = cache_lookup.search(
            query="franklin learning",
            mode="unified"
        )

        assert len(results) > 0

        # Get full content
        entry_id = results[0]["entry_id"]
        content = cache_lookup.get_entry_content(entry_id)

        assert content is not None
        assert "Franklin Protocol" in content
        assert "gradient descent" in content.lower()

    def test_get_entry_metadata(self, cache_lookup):
        """Test retrieving entry metadata."""
        results = cache_lookup.search(
            query="franklin",
            mode="keywords"
        )

        assert len(results) > 0

        # Get metadata
        entry_id = results[0]["entry_id"]
        metadata = cache_lookup.get_entry_metadata(entry_id)

        assert metadata is not None
        assert "title" in metadata
        assert "tags" in metadata
        assert "maturity" in metadata

    def test_search_no_results(self, cache_lookup):
        """Test search with no matching results."""
        results = cache_lookup.search(
            query="quantum physics black holes",
            mode="unified"
        )

        assert len(results) == 0

    def test_load_existing_indexes(self, temp_corpus_dir, temp_index_dir):
        """Test loading previously built indexes."""
        # Build indexes with first instance
        lookup1 = CacheLookup(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )
        lookup1.build_indexes()

        # Create new instance and load
        lookup2 = CacheLookup(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        # Should be able to search without rebuilding
        results = lookup2.search(query="learning", mode="keywords")
        assert len(results) > 0

    def test_match_score_thresholds(self, cache_lookup):
        """Test filtering by match score threshold."""
        # Get all results
        all_results = cache_lookup.search(
            query="learning",
            mode="unified"
        )

        # Filter for strong matches only
        strong_results = cache_lookup.search(
            query="learning",
            mode="unified",
            min_score=0.8
        )

        # Strong results should be subset of all results
        assert len(strong_results) <= len(all_results)

    def test_multiple_keyword_search(self, cache_lookup):
        """Test searching with multiple keywords (AND logic)."""
        results = cache_lookup.search(
            query=["learning", "deliberate"],
            mode="keywords"
        )

        # Should find entries containing both keywords
        assert len(results) > 0
        assert any("franklin" in r["entry_id"].lower() for r in results)

    def test_empty_query_handling(self, cache_lookup):
        """Test handling of empty queries."""
        results = cache_lookup.search(
            query="",
            mode="unified"
        )

        # Empty query should return no results
        assert len(results) == 0

    def test_result_deduplication(self, cache_lookup):
        """Test that results are deduplicated across search methods."""
        results = cache_lookup.search(
            query="learning machine franklin",
            mode="unified"
        )

        # Each entry should appear only once
        entry_ids = [r["entry_id"] for r in results]
        assert len(entry_ids) == len(set(entry_ids))
