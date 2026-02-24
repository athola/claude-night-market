"""Keyword indexing for memory palace corpus entries.

Extracts and indexes keywords from knowledge corpus entries (markdown files with YAML frontmatter)
to enable fast keyword-based lookup without requiring embeddings or external dependencies.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

MIN_WORD_LEN = 3
FRONTMATTER_PARTS = 3


class KeywordIndexer:
    """Extract and index keywords from palace entries for fast lookup.

    This indexer processes markdown files with YAML frontmatter, extracting keywords from:
    - YAML tags
    - Title and metadata fields
    - Key concepts from content (headings, emphasized text)

    The index is stored as YAML for human readability and ease of inspection.
    """

    def __init__(self, corpus_dir: str, index_dir: str) -> None:
        """Initialize the keyword indexer.

        Args:
            corpus_dir: Directory containing knowledge corpus markdown files
            index_dir: Directory where index files will be stored

        """
        self.corpus_dir = Path(corpus_dir)
        self.index_dir = Path(index_dir)
        self.index_file = self.index_dir / "keyword-index.yaml"
        self.index: dict[str, Any] = {
            "entries": {},
            "keywords": defaultdict(list),
            "metadata": {},
        }

    def extract_keywords(self, entry_path: Path) -> list[str]:
        """Extract keywords from a single knowledge entry.

        Args:
            entry_path: Path to the markdown file

        Returns:
            List of extracted keywords (lowercase, deduplicated)

        """
        keywords: set[str] = set()

        try:
            content = entry_path.read_text()

            # Split frontmatter and content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= FRONTMATTER_PARTS:
                    frontmatter = parts[1]
                    body = parts[2]

                    # Parse YAML frontmatter
                    try:
                        metadata = yaml.safe_load(frontmatter)
                        if metadata:
                            # Extract from tags
                            if "tags" in metadata and isinstance(
                                metadata["tags"], list
                            ):
                                keywords.update(tag.lower() for tag in metadata["tags"])

                            # Extract from title
                            if "title" in metadata:
                                title = metadata["title"].lower()
                                title_words = re.findall(
                                    rf"\b[a-z]{{{MIN_WORD_LEN},}}\b", title
                                )
                                keywords.update(title_words)

                            # Extract from palace/district
                            if "palace" in metadata:
                                palace_words = re.findall(
                                    rf"\b[a-z]{{{MIN_WORD_LEN},}}\b",
                                    metadata["palace"].lower(),
                                )
                                keywords.update(palace_words)

                            if "district" in metadata:
                                district_words = re.findall(
                                    rf"\b[a-z]{{{MIN_WORD_LEN},}}\b",
                                    metadata["district"].lower(),
                                )
                                keywords.update(district_words)

                    except yaml.YAMLError:
                        # Skip if YAML parsing fails
                        # YAML parsing errors are expected and can be safely ignored
                        pass

                    # Extract from content
                    # Get headings (## Something)
                    headings = re.findall(r"^#{1,3}\s+(.+)$", body, re.MULTILINE)
                    for heading in headings:
                        heading_words = re.findall(r"\b[a-z]{3,}\b", heading.lower())
                        keywords.update(heading_words)

                    # Get emphasized terms (**term** or *term*)
                    emphasized = re.findall(r"\*\*([^*]+)\*\*|\*([^*]+)\*", body)
                    for match in emphasized:
                        term = match[0] or match[1]
                        term_words = re.findall(r"\b[a-z]{3,}\b", term.lower())
                        keywords.update(term_words)

                    # Extract key technical terms (hyphenated, camelCase)
                    technical_terms = re.findall(
                        r"\b[a-z]+(?:-[a-z]+)+\b", body.lower()
                    )
                    keywords.update(technical_terms)

                    # Extract significant noun phrases (consecutive capitalized words)
                    # Helps catch phrases like "Gradient Descent" or "Machine Learning"
                    noun_phrases = re.findall(
                        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", body
                    )
                    for phrase in noun_phrases:
                        # Add both the phrase and individual words
                        phrase_words = re.findall(r"\b[a-z]{3,}\b", phrase.lower())
                        keywords.update(phrase_words)

        except Exception:
            # File read errors are expected in some tests; treat as no keywords.
            return []

        # Remove common stop words
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
        }
        keywords = {k for k in keywords if k not in stop_words}

        return sorted(keywords)

    def build_index(self) -> None:
        """Build the complete keyword index from all corpus entries.

        Scans the corpus directory for markdown files, extracts keywords from each,
        and creates both forward (entry -> keywords) and reverse (keyword -> entries) indexes.
        """
        entries = {}
        keyword_to_entries = defaultdict(list)

        # Find all markdown files in corpus directory (including subdirectories)
        md_files = sorted(self.corpus_dir.rglob("*.md"))

        for md_file in md_files:
            if md_file.name.lower() == "readme.md":
                continue
            # Create entry ID from filename
            relative = md_file.relative_to(self.corpus_dir)
            relative_str = relative.as_posix()
            entry_id = relative_str.removesuffix(".md").replace("/", "-")

            # Extract keywords
            keywords = self.extract_keywords(md_file)

            # Read frontmatter for additional metadata
            content = md_file.read_text()
            title = entry_id
            tags = []

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= FRONTMATTER_PARTS:
                    try:
                        metadata = yaml.safe_load(parts[1])
                        if metadata:
                            title = metadata.get("title", title)
                            tags = metadata.get("tags", [])
                    except yaml.YAMLError:
                        pass

            # Store entry data
            entries[entry_id] = {
                "file": str(md_file.relative_to(self.corpus_dir.parent)),
                "keywords": keywords,
                "title": title,
                "tags": tags,
            }

            # Build reverse index
            for keyword in keywords:
                keyword_to_entries[keyword].append(entry_id)

        # Update index
        self.index = {
            "entries": entries,
            "keywords": dict(keyword_to_entries),
            "metadata": {
                "total_entries": len(entries),
                "total_keywords": len(keyword_to_entries),
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
                self.index = yaml.safe_load(f) or {
                    "entries": {},
                    "keywords": {},
                    "metadata": {},
                }

    def search(self, query: str | list[str]) -> list[dict[str, Any]]:
        """Search the index by keyword(s).

        Args:
            query: Single keyword string or list of keywords for AND search

        Returns:
            List of matching entries with their metadata

        Note:
            Keyword search uses AND logic (all keywords must match) and requires
            exact term matching with no stemming. For example, "writing" will not
            match "write". Keywords are normalized to lowercase during indexing.

        """
        if not self.index.get("keywords"):
            self.load_index()

        # Normalize query to list
        keywords = (
            [query.lower()] if isinstance(query, str) else [k.lower() for k in query]
        )

        # Find entries matching ALL keywords (AND logic)
        matching_entry_ids = None

        for keyword in keywords:
            entry_ids = set(self.index.get("keywords", {}).get(keyword, []))

            if matching_entry_ids is None:
                matching_entry_ids = entry_ids
            else:
                matching_entry_ids &= entry_ids

        if matching_entry_ids is None:
            return []

        # Collect entry details
        results = []
        for entry_id in matching_entry_ids:
            if entry_id in self.index.get("entries", {}):
                entry_data = self.index["entries"][entry_id].copy()
                entry_data["entry_id"] = entry_id
                results.append(entry_data)

        return results
