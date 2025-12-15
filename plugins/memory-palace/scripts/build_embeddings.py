#!/usr/bin/env python3
"""Build or benchmark the embedding index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_palace.corpus.embedding_index import EmbeddingIndex

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PLUGIN_ROOT / "docs" / "knowledge-corpus"
EMBEDDINGS_PATH = PLUGIN_ROOT / "data" / "indexes" / "embeddings.yaml"


def _entry_id_for(path: Path) -> str:
    """Derive a stable entry_id from a markdown path relative to the corpus."""
    relative = path.relative_to(CORPUS_DIR)
    return relative.as_posix().removesuffix(".md").replace("/", "-")


def load_entries() -> dict[str, Path]:
    """Load all markdown entries from the corpus directory."""
    entries: dict[str, Path] = {}
    for path in sorted(CORPUS_DIR.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        entries[_entry_id_for(path)] = path
    return entries


def build_embeddings(provider: str) -> dict[str, list[float]]:
    """Build embeddings for all corpus entries."""
    index = EmbeddingIndex(str(EMBEDDINGS_PATH), provider=provider)
    vectors: dict[str, list[float]] = {}
    for entry_id, path in load_entries().items():
        text = path.read_text(encoding="utf-8")
        vectors[entry_id] = index.vectorize(text)
    index.export(provider=provider, entries=vectors)
    print(f"[embeddings] wrote {len(vectors)} entries for provider '{provider}'")
    return vectors


def benchmark(query_file: Path, provider: str, top_k: int) -> None:
    """Benchmark the embedding index with test queries."""
    queries = json.loads(query_file.read_text(encoding="utf-8"))
    index = EmbeddingIndex(str(EMBEDDINGS_PATH), provider=provider)
    results = {}
    for query in queries:
        matches = index.search(query, top_k=top_k)
        results[query] = matches
    print(json.dumps(results, indent=2))


def main() -> None:
    """Build or benchmark embeddings from the command line."""
    parser = argparse.ArgumentParser(description="Embedding builder/benchmark")
    parser.add_argument(
        "--provider",
        default="hash",
        choices=["hash", "local"],
        help="Choose hashing fallback or local sentence-transformer provider.",
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        help="Optional path to queries.json for benchmarking current vectors.",
    )
    parser.add_argument(
        "--benchmark-top-k",
        type=int,
        default=5,
        help="Number of matches to emit for each benchmark query.",
    )
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help="Skip rebuild and only benchmark existing embeddings.",
    )
    args = parser.parse_args()

    if not args.benchmark_only:
        build_embeddings(args.provider)
    if args.benchmark:
        benchmark(args.benchmark, args.provider, args.benchmark_top_k)


if __name__ == "__main__":
    main()
