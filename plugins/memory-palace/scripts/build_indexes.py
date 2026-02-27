#!/usr/bin/env python3
"""Build keyword and query template indexes from knowledge corpus.

NOTE: The docs/knowledge-corpus/ directory was removed in 1.5.0.
This script will gracefully exit if no corpus directory is configured.
To re-enable, set corpus_dir in memory-palace-config.yaml and repopulate.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory_palace.corpus import CacheLookup


def main() -> None:
    """Build indexes from knowledge corpus."""
    project_root = Path(__file__).parent.parent
    corpus_dir = project_root / "docs" / "knowledge-corpus"
    index_dir = project_root / "data" / "indexes"

    if not corpus_dir.is_dir():
        print(
            f"Corpus directory not found: {corpus_dir}\n"
            "knowledge-corpus was removed in 1.5.0. "
            "Set corpus_dir in config and repopulate to re-enable."
        )
        return

    lookup = CacheLookup(corpus_dir=str(corpus_dir), index_dir=str(index_dir))
    lookup.build_indexes()
    print("Indexes built successfully.")


if __name__ == "__main__":
    main()
