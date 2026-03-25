"""Query template management for memory palace corpus.

Maps "questions this knowledge answers" to corpus entries for semantic query matching.
Uses simple keyword-based similarity scoring without requiring external dependencies.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from memory_palace.corpus._frontmatter import parse_entry_frontmatter

MIN_WORD_LEN = 3


class QueryTemplateManager:
    """Manage query templates mapping questions to knowledge entries.

    This manager processes markdown files with YAML frontmatter, extracting
    query patterns (questions) that each entry can answer. Enables matching
    user queries to relevant knowledge based on semantic similarity.
    """

    def __init__(self, corpus_dir: str, index_dir: str) -> None:
        """Initialize the query template manager.

        Args:
            corpus_dir: Directory containing knowledge corpus markdown files
            index_dir: Directory where index files will be stored

        """
        self.corpus_dir = Path(corpus_dir)
        self.index_dir = Path(index_dir)
        self.index_file = self.index_dir / "query-templates.yaml"
        self.index: dict[str, Any] = {"entries": {}, "queries": {}, "metadata": {}}
        # Pre-computed keyword frozensets for each indexed query string.
        # Populated by load_index() and build_index() to avoid re-extracting
        # keywords on every call to search().
        self._keyword_cache: dict[str, frozenset[str]] = {}

    def extract_queries(
        self, entry_path: Path, content: str | None = None
    ) -> list[str]:
        """Extract query templates from a single knowledge entry.

        Args:
            entry_path: Path to the markdown file.
            content: File content string. When provided, skips disk read.

        Returns:
            List of query strings this entry can answer

        """
        queries = []

        try:
            if content is None:
                content = entry_path.read_text()

            # Parse frontmatter for query templates
            metadata = parse_entry_frontmatter(content)
            if (
                metadata
                and "queries" in metadata
                and isinstance(metadata["queries"], list)
            ):
                queries = metadata["queries"]

        except Exception:
            # Treat unreadable files as no queries.
            return queries

        return queries

    def _normalize_query(self, query: str) -> str:
        """Normalize a query for matching.

        Args:
            query: Raw query string

        Returns:
            Normalized query (lowercase, cleaned)

        """
        # Convert to lowercase
        normalized = query.lower()

        # Remove punctuation except spaces and hyphens
        normalized = re.sub(r"[^\w\s-]", " ", normalized)

        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip()

    def _extract_query_keywords(self, query: str) -> set[str]:
        """Extract significant keywords from a query.

        Args:
            query: Query string

        Returns:
            Set of keywords (3+ chars, excluding stop words)

        """
        # Normalize and split
        normalized = self._normalize_query(query)
        words = normalized.split()

        # Filter stop words
        stop_words = {
            "the",
            "and",
            "for",
            "that",
            "this",
            "with",
            "from",
            "are",
            "was",
            "were",
            "been",
            "have",
            "has",
            "had",
            "not",
            "but",
            "can",
            "will",
            "what",
            "when",
            "where",
            "who",
            "why",
            "how",
            "all",
            "each",
            "which",
            "their",
            "said",
            "them",
            "these",
            "than",
            "into",
            "very",
            "her",
            "our",
            "out",
            "only",
            "does",
            "did",
            "should",
            "could",
            "would",
        }

        return {w for w in words if len(w) >= MIN_WORD_LEN and w not in stop_words}

    def _calculate_similarity(
        self,
        query1: str,
        query2: str,
        keywords1: frozenset[str] | None = None,
        keywords2: frozenset[str] | None = None,
    ) -> float:
        """Calculate similarity score between two queries.

        Uses keyword overlap as a simple similarity measure.

        Args:
            query1: First query string (used only when keywords1 is None).
            query2: Second query string (used only when keywords2 is None).
            keywords1: Pre-extracted keyword set for query1 (optional).
            keywords2: Pre-extracted keyword set for query2 (optional).

        Returns:
            Similarity score between 0.0 and 1.0

        """
        kw1 = (
            keywords1 if keywords1 is not None else self._extract_query_keywords(query1)
        )
        kw2 = (
            keywords2 if keywords2 is not None else self._extract_query_keywords(query2)
        )

        if not kw1 or not kw2:
            return 0.0

        # Calculate Jaccard similarity (intersection over union)
        intersection = kw1 & kw2
        union = kw1 | kw2

        return len(intersection) / len(union) if union else 0.0

    def build_index(self) -> None:
        """Build the complete query template index from all corpus entries.

        Scans the corpus directory for markdown files, extracts query templates,
        and creates mappings from queries to entries.
        """
        entries = {}
        query_mappings = defaultdict(list)

        # Find all markdown files in corpus directory
        md_files = sorted(self.corpus_dir.rglob("*.md"))

        total_queries = 0

        for md_file in md_files:
            if md_file.name.lower() == "readme.md":
                continue
            # Create entry ID from filename
            relative = md_file.relative_to(self.corpus_dir)
            relative_str = relative.as_posix()
            entry_id = relative_str.removesuffix(".md").replace("/", "-")

            # Read file once; pass content to both query extraction and
            # frontmatter parsing to avoid a second disk read.
            file_content = md_file.read_text()
            queries = self.extract_queries(md_file, content=file_content)

            title = entry_id

            metadata = parse_entry_frontmatter(file_content)
            if metadata:
                title = metadata.get("title", title)

            # Store entry data
            entries[entry_id] = {
                "file": str(md_file.relative_to(self.corpus_dir.parent)),
                "queries": queries,
                "title": title,
            }

            # Build query mappings
            for query in queries:
                normalized = self._normalize_query(query)
                query_mappings[normalized].append(entry_id)
                total_queries += 1

        # Update index
        self.index = {
            "entries": entries,
            "queries": dict(query_mappings),
            "metadata": {
                "total_entries": len(entries),
                "total_queries": total_queries,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Rebuild keyword cache for the new index.
        self._rebuild_keyword_cache()

        # Save to disk
        self.save_index()

    def save_index(self) -> None:
        """Save the index to disk as YAML."""
        self.index_dir.mkdir(parents=True, exist_ok=True)

        with open(self.index_file, "w") as f:
            yaml.safe_dump(self.index, f, default_flow_style=False, sort_keys=False)

    def _rebuild_keyword_cache(self) -> None:
        """Precompute keyword frozensets for all indexed query strings."""
        self._keyword_cache = {
            q: frozenset(self._extract_query_keywords(q))
            for q in self.index.get("queries", {})
        }

    def load_index(self) -> None:
        """Load the index from disk."""
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = yaml.safe_load(f) or {
                    "entries": {},
                    "queries": {},
                    "metadata": {},
                }
        self._rebuild_keyword_cache()

    def search(self, query: str, threshold: float = 0.3) -> list[dict[str, Any]]:
        """Search for entries that answer the given query.

        Uses keyword-based similarity matching to find relevant entries.

        Args:
            query: Query string (e.g., "how to improve writing skills?")
            threshold: Minimum similarity score to include (0.0 to 1.0)

        Returns:
            List of matching entries with their metadata, sorted by similarity

        """
        if not self.index.get("queries"):
            self.load_index()

        # Extract keywords for the user query once; reuse for all comparisons.
        user_keywords: frozenset[str] = frozenset(self._extract_query_keywords(query))

        # Calculate similarity scores for all indexed queries
        matches = []

        for indexed_query, entry_ids in self.index.get("queries", {}).items():
            # Use the pre-cached keyword set for the indexed query when available.
            indexed_keywords = self._keyword_cache.get(indexed_query)
            similarity = self._calculate_similarity(
                query,
                indexed_query,
                keywords1=user_keywords,
                keywords2=indexed_keywords,
            )

            if similarity >= threshold:
                for entry_id in entry_ids:
                    if entry_id in self.index.get("entries", {}):
                        entry_data = self.index["entries"][entry_id].copy()
                        entry_data["entry_id"] = entry_id
                        entry_data["similarity"] = similarity
                        entry_data["matched_query"] = indexed_query
                        matches.append(entry_data)

        # Sort by similarity (highest first) and deduplicate
        seen_entries = set()
        unique_matches = []

        for match in sorted(matches, key=lambda x: x["similarity"], reverse=True):
            if match["entry_id"] not in seen_entries:
                seen_entries.add(match["entry_id"])
                unique_matches.append(match)

        return unique_matches
