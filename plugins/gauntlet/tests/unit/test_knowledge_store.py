"""Tests for KnowledgeStore persistence and query."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.models import KnowledgeEntry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_entry(
    entry_id: str = "ke-001",
    module: str = "billing",
    category: str = "business_logic",
    tags: list[str] = None,
    difficulty: int = 2,
    related_files: list[str] = None,
) -> KnowledgeEntry:
    return KnowledgeEntry(
        id=entry_id,
        category=category,
        module=module,
        concept="Test concept",
        detail="Test detail",
        difficulty=difficulty,
        extracted_at="2026-01-01T00:00:00",
        source="code",
        related_files=related_files or [],
        tags=tags or [],
        consumers=[],
    )


# ---------------------------------------------------------------------------
# Feature: Loading the knowledge store
# ---------------------------------------------------------------------------


class TestLoad:
    """
    Feature: Loading persisted knowledge entries

    As a gauntlet plugin
    I want to load knowledge entries from disk
    So that challenge generation has a stable knowledge base to draw from
    """

    @pytest.mark.unit
    def test_load_empty_returns_empty_list(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Loading when no knowledge.json exists
        Given a fresh .gauntlet/ directory with no knowledge.json
        When load() is called
        Then an empty list is returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.load()

        assert result == []

    @pytest.mark.unit
    def test_load_with_annotations_includes_curated_entries(
        self,
        tmp_gauntlet_dir: Path,
        sample_annotation: Path,
    ):
        """
        Scenario: Loading with annotations enabled
        Given a .gauntlet/ directory with a YAML annotation file
        When load(include_annotations=True) is called
        Then the curated entry from the annotation is included
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.load(include_annotations=True)

        assert len(result) == 1
        entry = result[0]
        assert entry.source == "curated"
        assert entry.module == "auth"
        assert entry.concept == "Token expiry rationale"

    @pytest.mark.unit
    def test_load_without_annotations_excludes_curated_entries(
        self,
        tmp_gauntlet_dir: Path,
        sample_annotation: Path,
    ):
        """
        Scenario: Loading without annotations
        Given a .gauntlet/ directory with a YAML annotation file but no knowledge.json
        When load() is called (default, no annotations)
        Then curated entries are not included
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.load()

        assert result == []


# ---------------------------------------------------------------------------
# Feature: Saving and loading entries
# ---------------------------------------------------------------------------


class TestSaveAndLoad:
    """
    Feature: Roundtrip persistence

    As a gauntlet plugin
    I want to save entries to disk and reload them
    So that knowledge survives between sessions
    """

    @pytest.mark.unit
    def test_save_and_load_roundtrip(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Single entry roundtrip
        Given one KnowledgeEntry in memory
        When save() is called and then load() is called
        Then the same entry is returned with identical fields
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        original = _make_entry(
            tags=["billing"], related_files=["src/billing/proration.py"]
        )

        store.save([original])
        loaded = store.load()

        assert len(loaded) == 1
        assert loaded[0].id == original.id
        assert loaded[0].category == original.category
        assert loaded[0].module == original.module
        assert loaded[0].tags == original.tags
        assert loaded[0].related_files == original.related_files

    @pytest.mark.unit
    def test_merge_automated_and_curated_returns_both_sources(
        self,
        tmp_gauntlet_dir: Path,
        sample_annotation: Path,
    ):
        """
        Scenario: Automated + curated entries both present
        Given a knowledge.json with one automated entry
        And an annotations/ directory with one curated YAML file
        When load(include_annotations=True) is called
        Then both entries are returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        automated = _make_entry(entry_id="ke-auto-001")
        store.save([automated])

        result = store.load(include_annotations=True)

        assert len(result) == 2
        sources = {e.source for e in result}
        assert "code" in sources
        assert "curated" in sources


# ---------------------------------------------------------------------------
# Feature: Curated entry ID generation
# ---------------------------------------------------------------------------


class TestCuratedEntryId:
    """
    Feature: Stable IDs for curated annotations

    As a gauntlet plugin
    I want curated entries to have deterministic IDs
    So that references remain stable across reloads
    """

    @pytest.mark.unit
    def test_curated_entry_id_has_expected_prefix(
        self,
        tmp_gauntlet_dir: Path,
        sample_annotation: Path,
    ):
        """
        Scenario: Curated ID prefix
        Given a YAML annotation file
        When load(include_annotations=True) is called
        Then the entry id starts with 'curated-'
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.load(include_annotations=True)

        assert result[0].id.startswith("curated-")


# ---------------------------------------------------------------------------
# Feature: Querying the knowledge store
# ---------------------------------------------------------------------------


class TestQuery:
    """
    Feature: Filtering knowledge entries

    As a gauntlet plugin
    I want to filter entries by file, category, tag, and difficulty
    So that challenge generation targets the right knowledge
    """

    @pytest.mark.unit
    def test_query_by_files_matches_module(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Filter by file matching module name
        Given a knowledge base with entries in different modules
        When query(files=['billing']) is called
        Then only entries whose module equals 'billing' are returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query(files=["billing"])

        assert len(result) >= 1
        for entry in result:
            assert entry.module == "billing" or "billing" in entry.related_files

    @pytest.mark.unit
    def test_query_by_files_matches_related_files(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Filter by file matching related_files list
        Given a knowledge base entry with related_files=['src/billing/proration.py']
        When query(files=['src/billing/proration.py']) is called
        Then that entry is returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query(files=["src/billing/proration.py"])

        assert len(result) >= 1
        ids = [e.id for e in result]
        assert "ke-001" in ids

    @pytest.mark.unit
    def test_query_by_files_excludes_non_matching(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Filter by file excludes unrelated entries
        Given a knowledge base with entries in billing, core, and auth modules
        When query(files=['billing']) is called
        Then entries from core and auth are not returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query(files=["billing"])

        modules = {e.module for e in result}
        assert "core" not in modules
        assert "auth" not in modules

    @pytest.mark.unit
    def test_query_by_category_filters_correctly(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Filter by category
        Given a knowledge base with entries in multiple categories
        When query(categories=['architecture']) is called
        Then only architecture entries are returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query(categories=["architecture"])

        assert len(result) >= 1
        for entry in result:
            assert entry.category == "architecture"

    @pytest.mark.unit
    def test_query_by_tags_filters_by_intersection(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Filter by tags using intersection
        Given a knowledge base where one entry has tags=['billing', 'subscription']
        When query(tags=['billing']) is called
        Then entries containing 'billing' in their tags are returned
        And entries without 'billing' in their tags are excluded
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query(tags=["billing"])

        assert len(result) >= 1
        for entry in result:
            assert "billing" in entry.tags

    @pytest.mark.unit
    def test_query_returns_all_when_no_filters(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Query with no filters
        Given a knowledge base with 3 entries
        When query() is called with no filter arguments
        Then all 3 entries are returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query()

        assert len(result) == 3

    @pytest.mark.unit
    def test_query_by_difficulty_range(
        self,
        tmp_gauntlet_dir: Path,
        sample_knowledge_base: Path,
    ):
        """
        Scenario: Filter by difficulty range
        Given a knowledge base with entries at difficulty 2, 3, and 2
        When query(min_difficulty=3, max_difficulty=5) is called
        Then only the difficulty-3 entry is returned
        """
        store = KnowledgeStore(tmp_gauntlet_dir)
        result = store.query(min_difficulty=3, max_difficulty=5)

        assert len(result) == 1
        assert result[0].difficulty == 3
