"""Query template management for memory palace corpus.

Maps "questions this knowledge answers" to corpus entries for semantic query matching.
Uses simple keyword-based similarity scoring without requiring external dependencies.
"""

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


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

    def extract_queries(self, entry_path: Path) -> list[str]:
        """Extract query templates from a single knowledge entry.

        Args:
            entry_path: Path to the markdown file

        Returns:
            List of query strings this entry can answer

        """
        queries = []

        try:
            content = entry_path.read_text()

            # Split frontmatter and content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]

                    # Parse YAML frontmatter
                    try:
                        metadata = yaml.safe_load(frontmatter)
                        if metadata and "queries" in metadata:
                            if isinstance(metadata["queries"], list):
                                queries = metadata["queries"]

                    except yaml.YAMLError:
                        pass  # Skip if YAML parsing fails

        except Exception:
            # If file read fails, return empty list
            pass

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

        return {w for w in words if len(w) >= 3 and w not in stop_words}

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity score between two queries.

        Uses keyword overlap as a simple similarity measure.

        Args:
            query1: First query string
            query2: Second query string

        Returns:
            Similarity score between 0.0 and 1.0

        """
        keywords1 = self._extract_query_keywords(query1)
        keywords2 = self._extract_query_keywords(query2)

        if not keywords1 or not keywords2:
            return 0.0

        # Calculate Jaccard similarity (intersection over union)
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        return len(intersection) / len(union) if union else 0.0

    def build_index(self) -> None:
        """Build the complete query template index from all corpus entries.

        Scans the corpus directory for markdown files, extracts query templates,
        and creates mappings from queries to entries.
        """
        entries = {}
        query_mappings = defaultdict(list)

        # Find all markdown files in corpus directory
        md_files = list(self.corpus_dir.glob("*.md"))

        total_queries = 0

        for md_file in md_files:
            # Create entry ID from filename
            entry_id = md_file.stem

            # Extract queries
            queries = self.extract_queries(md_file)

            # Read frontmatter for additional metadata
            content = md_file.read_text()
            title = entry_id

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1])
                        if metadata:
                            title = metadata.get("title", title)
                    except yaml.YAMLError:
                        pass

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
                "last_updated": datetime.now().isoformat(),
            },
        }

        # Save to disk
        self.save_index()

    def save_index(self) -> None:
        """Save the index to disk as YAML."""
        self.index_dir.mkdir(parents=True, exist_ok=True)

        with open(self.index_file, "w") as f:
            yaml.safe_dump(self.index, f, default_flow_style=False, sort_keys=False)

    def load_index(self) -> None:
        """Load the index from disk."""
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = yaml.safe_load(f) or {"entries": {}, "queries": {}, "metadata": {}}

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

        # Calculate similarity scores for all indexed queries
        matches = []

        for indexed_query, entry_ids in self.index.get("queries", {}).items():
            similarity = self._calculate_similarity(query, indexed_query)

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
