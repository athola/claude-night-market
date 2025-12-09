"""Tests for keyword indexing functionality."""

from pathlib import Path

import pytest
import yaml

from memory_palace.corpus.keyword_index import KeywordIndexer


@pytest.fixture
def temp_corpus_dir(tmp_path):
    """Create temporary corpus directory with sample entries."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    # Create sample knowledge entry
    sample_entry = """---
title: Franklin Protocol - Learning Algorithms
tags: [learning, machine-learning, deliberate-practice, feedback-loops]
palace: Learning Techniques
district: Historical Methods
maturity: evergreen
---

# Franklin Protocol

Benjamin Franklin's learning method embodies **gradient descent**.
Compare output to exemplar, calculate error, adjust parameters, iterate.

This method demonstrates Gradient Descent principles applied to human learning.

## Key Concepts

- Feature extraction
- Deliberate delay
- Reconstruction from memory
- Error calculation
- Parameter update
"""

    (corpus_dir / "franklin-protocol.md").write_text(sample_entry)

    # Create another sample entry
    sample_entry_2 = """---
title: KonMari Method - Knowledge Tidying
tags: [konmari, tidying, curation, philosophy]
palace: Governance Techniques
district: Curation Philosophy
maturity: evergreen
---

# KonMari Method

Marie Kondo's approach to decluttering, adapted for knowledge governance.

Does it spark joy? The question of what to keep.
"""

    (corpus_dir / "konmari-method.md").write_text(sample_entry_2)

    return corpus_dir


@pytest.fixture
def temp_index_dir(tmp_path):
    """Create temporary index directory."""
    index_dir = tmp_path / "indexes"
    index_dir.mkdir()
    return index_dir


class TestKeywordIndexer:
    """Test suite for KeywordIndexer."""

    def test_initialization(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test indexer initialization."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        assert indexer.corpus_dir == Path(temp_corpus_dir)
        assert indexer.index_dir == Path(temp_index_dir)
        assert indexer.index_file == Path(temp_index_dir) / "keyword-index.yaml"

    def test_extract_keywords_from_entry(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test keyword extraction from a single entry."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        entry_path = temp_corpus_dir / "franklin-protocol.md"
        keywords = indexer.extract_keywords(entry_path)

        # Should extract from tags
        assert "learning" in keywords
        assert "machine-learning" in keywords
        assert "deliberate-practice" in keywords

        # Should extract from metadata
        assert "franklin protocol" in keywords or "franklin" in keywords

        # Should extract key concepts from content
        # "gradient descent" appears in the content
        assert "gradient" in keywords or "descent" in keywords

    def test_build_index(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test building the full keyword index."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        indexer.build_index()

        # Check index file was created
        assert indexer.index_file.exists()

        # Load and validate index structure
        with open(indexer.index_file) as f:
            index = yaml.safe_load(f)

        assert "entries" in index
        assert "keywords" in index
        assert "metadata" in index

        # Should have indexed both entries
        assert len(index["entries"]) == 2

        # Check entry structure
        for entry_data in index["entries"].values():
            assert "file" in entry_data
            assert "keywords" in entry_data
            assert "title" in entry_data
            assert "tags" in entry_data

        # Check reverse keyword index
        assert len(index["keywords"]) > 0

        # Keywords should map to entry IDs
        for entry_ids in index["keywords"].values():
            assert isinstance(entry_ids, list)
            assert len(entry_ids) > 0

    def test_keyword_deduplication(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test that keywords are deduplicated and normalized."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        entry_path = temp_corpus_dir / "franklin-protocol.md"
        keywords = indexer.extract_keywords(entry_path)

        # Keywords should be unique
        assert len(keywords) == len(set(keywords))

        # Keywords should be lowercase
        assert all(k.islower() for k in keywords)

    def test_search_by_keyword(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test searching the index by keyword."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        indexer.build_index()

        # Search for a keyword
        results = indexer.search("learning")

        assert len(results) > 0
        assert any("franklin" in r["file"].lower() for r in results)

    def test_search_multiple_keywords(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test searching with multiple keywords (AND logic)."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        indexer.build_index()

        # Search for multiple keywords
        results = indexer.search(["learning", "gradient"])

        # Should find entries containing both keywords
        assert len(results) > 0

    def test_search_no_results(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test searching for non-existent keyword."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        indexer.build_index()

        # Search for keyword that doesn't exist
        results = indexer.search("quantum-physics")

        assert len(results) == 0

    def test_load_existing_index(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test loading an existing index from disk."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        # Build and save index
        indexer.build_index()

        # Create new indexer instance and load
        indexer2 = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        indexer2.load_index()

        # Should be able to search without rebuilding
        results = indexer2.search("learning")
        assert len(results) > 0

    def test_metadata_tracking(self, temp_corpus_dir, temp_index_dir) -> None:
        """Test that index metadata is tracked correctly."""
        indexer = KeywordIndexer(corpus_dir=str(temp_corpus_dir), index_dir=str(temp_index_dir))

        indexer.build_index()

        with open(indexer.index_file) as f:
            index = yaml.safe_load(f)

        metadata = index["metadata"]
        assert "total_entries" in metadata
        assert "total_keywords" in metadata
        assert "last_updated" in metadata
        assert metadata["total_entries"] == 2
        assert metadata["total_keywords"] > 0
