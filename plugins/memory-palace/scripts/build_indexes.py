#!/usr/bin/env python3
"""Rebuild the corpus keyword index from captured research notes.

The keyword index was emptied in 1.5.0 when the knowledge-corpus
directory was removed during consolidation. Its own header named this
script as the way back, but the script was never written, so the index
stayed at ``entries: {}`` and ``cache_lookup`` searched nothing. Every
retrieval-driven subsystem downstream of it went dark with it.

The corpus is now the staging capture set: markdown notes with YAML
frontmatter written by the web research fetch hook. Entry IDs are
derived from the capture file path, which is the same key space the
retrieval layer returns to callers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent

# This script is the documented way back from an empty index, so it has to
# run under a bare system python, not only the venv. The venv resolves
# memory_palace through an editable-install .pth file. A system interpreter
# has nothing, so put the plugin's src on the path before importing it.
# Sibling scripts skip this because they are only ever run via the venv.
_SRC_DIR = str(PLUGIN_ROOT / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from memory_palace.corpus.keyword_index import KeywordIndexer

if str(PLUGIN_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "src"))

from memory_palace.paths import user_data_dir  # noqa: E402 - needs sys.path above

# The captures follow the persistent root: they are user data, and an
# install's PLUGIN_ROOT is version scoped, so indexing from it would read
# the tree the hooks stopped writing to (issue #661).
DEFAULT_CORPUS_DIR = user_data_dir(PLUGIN_ROOT) / "staging"

# The index directory does not. It holds tracked assets shipped with the
# version (query-templates.yaml, embeddings.yaml) and a keyword index
# rebuilt from the captures on demand, and research_interceptor reads it
# from PLUGIN_ROOT. Moving one side alone would split reader from writer.
DEFAULT_INDEX_DIR = PLUGIN_ROOT / "data" / "indexes"


def build_indexes(
    corpus_dir: Path,
    index_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build the keyword index and report what was found.

    Args:
        corpus_dir: Directory of markdown captures to index.
        index_dir: Directory the ``keyword-index.yaml`` is written to.
        dry_run: Compute the index and report without writing.

    Returns:
        Summary with entry and keyword totals and whether a write occurred.

    """
    indexer = KeywordIndexer(str(corpus_dir), str(index_dir))
    indexer.build_index(save=False)

    metadata = indexer.index.get("metadata", {})
    total_entries = int(metadata.get("total_entries", 0))
    total_keywords = int(metadata.get("total_keywords", 0))

    # An empty corpus produces an empty index, and writing that over a
    # populated one is exactly how the corpus went dark in 1.5.0. Report
    # it and leave the existing index alone.
    wrote = False
    if total_entries > 0 and not dry_run:
        indexer.save_index()
        wrote = True

    return {
        "corpus_dir": str(corpus_dir),
        "index_file": str(index_dir / "keyword-index.yaml"),
        "total_entries": total_entries,
        "total_keywords": total_keywords,
        "wrote": wrote,
        "dry_run": dry_run,
    }


def main() -> None:
    """Rebuild the keyword index and print a JSON summary."""
    parser = argparse.ArgumentParser(
        description="Rebuild the corpus keyword index from captured notes"
    )
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be indexed without writing the index.",
    )
    args = parser.parse_args()

    result = build_indexes(
        corpus_dir=args.corpus_dir,
        index_dir=args.index_dir,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
