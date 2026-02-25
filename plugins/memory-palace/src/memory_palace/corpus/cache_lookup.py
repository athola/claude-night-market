"""Unified cache lookup combining keyword and query template search.

Provides a single interface for searching the knowledge corpus using both
keyword indexing and query template matching, with intelligent scoring
to classify matches as strong (>80%), partial (40-80%), or weak (<40%).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from memory_palace.corpus.embedding_index import EmbeddingIndex
from memory_palace.corpus.keyword_index import KeywordIndexer
from memory_palace.corpus.query_templates import QueryTemplateManager

MATCH_LEN_MIN = 3
MATCH_STRONG = 0.8
MATCH_PARTIAL = 0.4
FRONTMATTER_PARTS = 3


class CacheLookup:
    """Unified search interface for memory palace knowledge corpus.

    Combines keyword-based search and query template matching to find
    relevant knowledge entries. Returns results with match scores that
    indicate confidence level:
    - Strong match: >80% (direct answer to query)
    - Partial match: 40-80% (related knowledge)
    - Weak match: <40% (tangentially related)
    """

    def __init__(
        self, corpus_dir: str, index_dir: str, embedding_provider: str = "none"
    ) -> None:
        """Initialize the cache lookup system.

        Args:
            corpus_dir: Directory containing knowledge corpus markdown files
            index_dir: Directory where index files are stored
            embedding_provider: Active embedding provider name (if configured)

        """
        self.corpus_dir = Path(corpus_dir)
        self.index_dir = Path(index_dir)

        # Initialize both search components
        self.keyword_indexer = KeywordIndexer(corpus_dir, index_dir)
        self.query_manager = QueryTemplateManager(corpus_dir, index_dir)

        resolved_provider = (embedding_provider or "none").strip().lower()
        if resolved_provider == "env":
            env_value = os.getenv("MEMORY_PALACE_EMBEDDINGS_PROVIDER", "none")
            resolved_provider = (env_value or "none").strip().lower()

        self.embedding_provider = resolved_provider
        embeddings_path = self.index_dir / "embeddings.yaml"
        self.embedding_index = None
        if resolved_provider != "none":
            self.embedding_index = EmbeddingIndex(
                str(embeddings_path), provider=resolved_provider
            )

    def build_indexes(self) -> None:
        """Build both keyword and query template indexes."""
        self.keyword_indexer.build_index()
        self.query_manager.build_index()

    def search(
        self,
        query: str | list[str],
        mode: str = "unified",
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Search the knowledge corpus.

        Args:
            query: Search query (string or list of keywords)
            mode: Search mode - "keywords", "queries", or "unified"
            min_score: Minimum match score to include (0.0 to 1.0)

        Returns:
            List of matching entries with metadata and match scores,
            sorted by score (highest first)

        """
        if isinstance(query, str) and not query.strip():
            return []

        results = []

        if mode in ("keywords", "unified"):
            keyword_results = self._search_keywords(query)
            results.extend(keyword_results)

        if mode in ("queries", "unified"):
            query_results = self._search_queries(query)
            results.extend(query_results)

        if self.embedding_index and mode in ("embeddings", "unified"):
            embedding_results = self._search_embeddings(query)
            results.extend(embedding_results)

        # Deduplicate and merge scores
        merged_results = self._merge_and_score_results(results)

        # Filter by minimum score
        filtered_results = [r for r in merged_results if r["match_score"] >= min_score]

        # Sort by score (highest first)
        return sorted(filtered_results, key=lambda x: x["match_score"], reverse=True)

    def _search_keywords(self, query: str | list[str]) -> list[dict[str, Any]]:
        """Search using keyword index.

        Args:
            query: Keyword(s) to search for

        Returns:
            List of matching entries with keyword_score

        """
        # Convert string query to list of keywords
        if isinstance(query, str):
            # Split into words and filter short words
            keywords = [w for w in query.lower().split() if len(w) >= MATCH_LEN_MIN]
            if not keywords:
                return []
            search_query = keywords
        else:
            search_query = query

        keyword_results = self.keyword_indexer.search(search_query)

        # Add keyword score
        for result in keyword_results:
            # Calculate score based on keyword overlap
            if isinstance(query, str):
                query_keywords = set(query.lower().split())
            else:
                query_keywords = {k.lower() for k in query}

            entry_keywords = set(result.get("keywords", []))

            if query_keywords and entry_keywords:
                overlap = len(query_keywords & entry_keywords)
                union = len(query_keywords | entry_keywords)
                result["keyword_score"] = overlap / union if union > 0 else 0.0
            else:
                result["keyword_score"] = 0.0

            result["source"] = "keywords"

        return keyword_results

    def _search_queries(self, query: str | list[str]) -> list[dict[str, Any]]:
        """Search using query templates.

        Args:
            query: Query string to match against templates

        Returns:
            List of matching entries with query_score

        """
        # Convert list to string for query matching
        query_str = " ".join(query) if isinstance(query, list) else query

        query_results = self.query_manager.search(query_str)

        # Rename similarity to query_score
        for result in query_results:
            result["query_score"] = result.pop("similarity", 0.0)
            result["source"] = "queries"

        return query_results

    def _search_embeddings(self, query: str | list[str]) -> list[dict[str, Any]]:
        """Search using embeddings if configured."""
        if not self.embedding_index:
            return []
        if not self.keyword_indexer.index.get("entries"):
            self.keyword_indexer.load_index()
        query_text = " ".join(query) if isinstance(query, list) else query
        scores = self.embedding_index.search(query_text)
        results = []
        for entry_id, score in scores:
            entry_data = self.keyword_indexer.index.get("entries", {}).get(entry_id)
            if not entry_data:
                continue
            results.append(
                {
                    "entry_id": entry_id,
                    "title": entry_data.get("title"),
                    "file": entry_data.get("file"),
                    "match_score": 0.6 + 0.4 * score,
                    "match_strength": "partial",
                    "source": "embeddings",
                    "query_score": score,
                },
            )
        return results

    def _merge_and_score_results(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge duplicate entries and calculate unified match scores.

        Args:
            results: List of results from different search methods

        Returns:
            Deduplicated list with unified match_score

        """
        # Group by entry_id
        entry_groups: dict[str, list[dict[str, Any]]] = {}

        for result in results:
            entry_id = result["entry_id"]
            if entry_id not in entry_groups:
                entry_groups[entry_id] = []
            entry_groups[entry_id].append(result)

        # Merge and score
        merged = []

        for group in entry_groups.values():
            # Start with the first result as base
            merged_entry = group[0].copy()

            # Collect scores
            keyword_score = 0.0
            query_score = 0.0

            for result in group:
                keyword_score = max(keyword_score, result.get("keyword_score", 0.0))
                query_score = max(query_score, result.get("query_score", 0.0))

            # Calculate unified match score
            # Query matches are weighted higher (70%) than keyword matches (30%)
            # because they indicate semantic relevance
            if query_score > 0:
                match_score = (0.7 * query_score) + (0.3 * keyword_score)
            else:
                match_score = keyword_score

            merged_entry["match_score"] = match_score
            merged_entry["keyword_score"] = keyword_score
            merged_entry["query_score"] = query_score

            # Classify match strength
            if match_score > MATCH_STRONG:
                merged_entry["match_strength"] = "strong"
            elif match_score >= MATCH_PARTIAL:
                merged_entry["match_strength"] = "partial"
            else:
                merged_entry["match_strength"] = "weak"

            merged.append(merged_entry)

        return merged

    def get_entry_content(self, entry_id: str) -> str | None:
        """Retrieve full content of a knowledge entry.

        Args:
            entry_id: Entry identifier

        Returns:
            Full markdown content of the entry, or None if not found

        """
        # Look up entry in keyword index to find file path
        self.keyword_indexer.load_index()

        entries = self.keyword_indexer.index.get("entries", {})
        if not isinstance(entries, dict):
            return None
        entry_data = entries.get(entry_id)
        if not isinstance(entry_data, dict):
            return None
        file_value = entry_data.get("file")
        if not isinstance(file_value, str):
            return None
        file_path = self.corpus_dir.parent / file_value

        if file_path.exists():
            return file_path.read_text(encoding="utf-8")

        return None

    def get_entry_metadata(self, entry_id: str) -> dict[str, Any] | None:
        """Retrieve metadata from a knowledge entry.

        Args:
            entry_id: Entry identifier

        Returns:
            Dictionary of metadata from YAML frontmatter, or None if not found

        """
        content = self.get_entry_content(entry_id)
        if content and content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= FRONTMATTER_PARTS:
                try:
                    payload = yaml.safe_load(parts[1])
                    if isinstance(payload, dict):
                        return payload
                except yaml.YAMLError:
                    # YAML parsing errors are expected and can be safely ignored
                    pass

        return None
