"""Tests for query template functionality."""


# ruff: noqa: S101
from pathlib import Path

import pytest
import yaml

from memory_palace.corpus.query_templates import QueryTemplateManager


@pytest.fixture
def temp_corpus_dir(tmp_path):
    """Create temporary corpus directory with sample entries."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    # Create sample knowledge entry with query patterns
    sample_entry = """---
title: Franklin Protocol - Learning Algorithms
tags: [learning, machine-learning, deliberate-practice]
queries:
  - How to improve writing skills systematically?
  - What is gradient descent for learning?
  - How did Benjamin Franklin learn?
  - Best practices for deliberate practice
---

# Franklin Protocol

Benjamin Franklin's learning method.
"""

    (corpus_dir / "franklin-protocol.md").write_text(sample_entry)

    # Create another sample entry
    sample_entry_2 = """---
title: KonMari Method
tags: [tidying, curation]
queries:
  - How to declutter knowledge?
  - What is the KonMari method?
  - How to decide what to keep?
---

# KonMari Method

Tidying philosophy.
"""

    (corpus_dir / "konmari-method.md").write_text(sample_entry_2)

    return corpus_dir


@pytest.fixture
def temp_index_dir(tmp_path):
    """Create temporary index directory."""
    index_dir = tmp_path / "indexes"
    index_dir.mkdir()
    return index_dir


class TestQueryTemplateManager:
    """Test suite for QueryTemplateManager."""

    def test_initialization(self, temp_corpus_dir, temp_index_dir):
        """Test manager initialization."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        assert manager.corpus_dir == Path(temp_corpus_dir)
        assert manager.index_dir == Path(temp_index_dir)
        assert manager.index_file == Path(temp_index_dir) / "query-templates.yaml"

    def test_extract_queries_from_entry(self, temp_corpus_dir, temp_index_dir):
        """Test query extraction from a single entry."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        entry_path = temp_corpus_dir / "franklin-protocol.md"
        queries = manager.extract_queries(entry_path)

        # Should extract from queries field
        assert len(queries) == 4
        assert any("writing skills" in q.lower() for q in queries)
        assert any("gradient descent" in q.lower() for q in queries)
        assert any("benjamin franklin" in q.lower() for q in queries)

    def test_build_index(self, temp_corpus_dir, temp_index_dir):
        """Test building the full query template index."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager.build_index()

        # Check index file was created
        assert manager.index_file.exists()

        # Load and validate index structure
        with open(manager.index_file) as f:
            index = yaml.safe_load(f)

        assert "entries" in index
        assert "queries" in index
        assert "metadata" in index

        # Should have indexed both entries
        assert len(index["entries"]) == 2

        # Check entry structure
        for _entry_id, entry_data in index["entries"].items():
            assert "file" in entry_data
            assert "queries" in entry_data
            assert "title" in entry_data

        # Check query mappings
        assert len(index["queries"]) > 0

    def test_search_by_query(self, temp_corpus_dir, temp_index_dir):
        """Test searching the index by query text."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager.build_index()

        # Search for a query
        results = manager.search("how to improve writing")

        assert len(results) > 0
        assert any("franklin" in r["file"].lower() for r in results)

    def test_search_similarity_matching(self, temp_corpus_dir, temp_index_dir):
        """Test that similar queries match even without exact wording."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager.build_index()

        # Search with similar wording
        results = manager.search("declutter my notes")

        # Should match "How to declutter knowledge?"
        assert len(results) > 0

    def test_search_no_results(self, temp_corpus_dir, temp_index_dir):
        """Test searching for non-matching query."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager.build_index()

        # Search for query that doesn't match
        results = manager.search("quantum computing algorithms")

        assert len(results) == 0

    def test_load_existing_index(self, temp_corpus_dir, temp_index_dir):
        """Test loading an existing index from disk."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        # Build and save index
        manager.build_index()

        # Create new manager instance and load
        manager2 = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager2.load_index()

        # Should be able to search without rebuilding
        results = manager2.search("writing skills")
        assert len(results) > 0

    def test_metadata_tracking(self, temp_corpus_dir, temp_index_dir):
        """Test that index metadata is tracked correctly."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager.build_index()

        with open(manager.index_file) as f:
            index = yaml.safe_load(f)

        metadata = index["metadata"]
        assert "total_entries" in metadata
        assert "total_queries" in metadata
        assert "last_updated" in metadata
        assert metadata["total_entries"] == 2
        assert metadata["total_queries"] > 0

    def test_query_normalization(self, temp_corpus_dir, temp_index_dir):
        """Test that queries are normalized for better matching."""
        manager = QueryTemplateManager(
            corpus_dir=str(temp_corpus_dir),
            index_dir=str(temp_index_dir)
        )

        manager.build_index()

        # Different casing should still match
        results1 = manager.search("HOW TO IMPROVE WRITING")
        results2 = manager.search("how to improve writing")

        assert len(results1) == len(results2)
        assert len(results1) > 0
