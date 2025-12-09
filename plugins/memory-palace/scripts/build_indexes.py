#!/usr/bin/env python3
"""Build keyword and query template indexes from knowledge corpus."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory_palace.corpus import CacheLookup


def main():
    """Build indexes from knowledge corpus."""
    # Paths
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "docs" / "knowledge-corpus"
    index_dir = project_root / "data" / "indexes"

    print(f"Building indexes from: {corpus_dir}")
    print(f"Output directory: {index_dir}")

    # Create cache lookup and build indexes
    lookup = CacheLookup(
        corpus_dir=str(corpus_dir),
        index_dir=str(index_dir)
    )

    print("\nBuilding indexes...")
    lookup.build_indexes()

    print("\n✓ Keyword index created:")
    print(f"  {index_dir / 'keyword-index.yaml'}")

    print("\n✓ Query template index created:")
    print(f"  {index_dir / 'query-templates.yaml'}")

    # Show some stats
    lookup.keyword_indexer.load_index()
    lookup.query_manager.load_index()

    keyword_meta = lookup.keyword_indexer.index.get("metadata", {})
    query_meta = lookup.query_manager.index.get("metadata", {})

    print("\nIndex Statistics:")
    print(f"  Total entries: {keyword_meta.get('total_entries', 0)}")
    print(f"  Total keywords: {keyword_meta.get('total_keywords', 0)}")
    print(f"  Total queries: {query_meta.get('total_queries', 0)}")

    # Test a search
    print("\n--- Testing Search ---")
    print("Query: 'how to learn effectively'")
    results = lookup.search("how to learn effectively", mode="unified")

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Match Score: {result['match_score']:.2f} ({result['match_strength']})")
        print(f"   File: {result['file']}")


if __name__ == "__main__":
    main()
