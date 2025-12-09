#!/usr/bin/env python3
"""Build keyword and query template indexes from knowledge corpus."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory_palace.corpus import CacheLookup


def main() -> None:
    """Build indexes from knowledge corpus."""
    # Paths
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "docs" / "knowledge-corpus"
    index_dir = project_root / "data" / "indexes"

    # Create cache lookup and build indexes
    lookup = CacheLookup(corpus_dir=str(corpus_dir), index_dir=str(index_dir))

    lookup.build_indexes()

    # Show some stats
    lookup.keyword_indexer.load_index()
    lookup.query_manager.load_index()

    lookup.keyword_indexer.index.get("metadata", {})
    lookup.query_manager.index.get("metadata", {})

    # Test a search
    results = lookup.search("How to improve writing skills systematically", mode="unified")

    for _i, _result in enumerate(results, 1):
        pass


if __name__ == "__main__":
    main()
