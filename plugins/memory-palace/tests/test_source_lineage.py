"""Tests for hybrid source lineage tracking.

Tests the SourceLineageManager which implements full and simple
lineage tracking based on source importance.
"""

from datetime import datetime, timezone

import pytest

from memory_palace.corpus.source_lineage import (
    FullLineage,
    SimpleLineage,
    SourceLineageManager,
    SourceReference,
    SourceType,
)


class TestSourceType:
    """Test SourceType enum."""

    def test_all_source_types_defined(self) -> None:
        """Should have all expected source types."""
        assert SourceType.WEB_ARTICLE.value == "web_article"
        assert SourceType.DOCUMENTATION.value == "documentation"
        assert SourceType.RESEARCH_PAPER.value == "research_paper"
        assert SourceType.CODE_EXAMPLE.value == "code_example"
        assert SourceType.USER_INPUT.value == "user_input"
        assert SourceType.DERIVED.value == "derived"


class TestSourceReference:
    """Test SourceReference dataclass."""

    def test_create_minimal_reference(self) -> None:
        """Should create reference with required fields only."""
        ref = SourceReference(
            source_id="src-1",
            source_type=SourceType.WEB_ARTICLE,
        )
        assert ref.source_id == "src-1"
        assert ref.source_type == SourceType.WEB_ARTICLE
        assert ref.url is None
        assert ref.title is None
        assert ref.author is None
        assert ref.confidence == 1.0
        assert isinstance(ref.retrieved_at, datetime)

    def test_create_full_reference(self) -> None:
        """Should create reference with all fields."""
        ref = SourceReference(
            source_id="src-2",
            source_type=SourceType.RESEARCH_PAPER,
            url="https://arxiv.org/abs/1234.5678",
            title="Deep Learning for Knowledge Management",
            author="Smith, J.",
            confidence=0.95,
        )
        assert ref.url == "https://arxiv.org/abs/1234.5678"
        assert ref.title == "Deep Learning for Knowledge Management"
        assert ref.author == "Smith, J."
        assert ref.confidence == 0.95


class TestFullLineage:
    """Test FullLineage dataclass."""

    def test_create_full_lineage(self) -> None:
        """Should create full lineage with primary source."""
        primary = SourceReference(
            source_id="src-1",
            source_type=SourceType.RESEARCH_PAPER,
            url="https://arxiv.org/paper",
            title="Original Paper",
        )
        lineage = FullLineage(
            entry_id="entry-1",
            primary_source=primary,
        )
        assert lineage.entry_id == "entry-1"
        assert lineage.primary_source == primary
        assert lineage.derived_from == []
        assert lineage.transformations == []
        assert lineage.validation_chain == []

    def test_full_lineage_with_derivation(self) -> None:
        """Should track derivation chain."""
        primary = SourceReference(
            source_id="src-1",
            source_type=SourceType.DOCUMENTATION,
        )
        lineage = FullLineage(
            entry_id="entry-1",
            primary_source=primary,
            derived_from=["entry-0", "entry-base"],
            transformations=["summarization", "extraction"],
        )
        assert len(lineage.derived_from) == 2
        assert len(lineage.transformations) == 2

    def test_full_lineage_with_validation(self) -> None:
        """Should track validation chain."""
        primary = SourceReference(
            source_id="src-1",
            source_type=SourceType.RESEARCH_PAPER,
        )
        lineage = FullLineage(
            entry_id="entry-1",
            primary_source=primary,
            validation_chain=[
                {"validator": "user-1", "date": "2025-01-01", "status": "approved"},
                {"validator": "user-2", "date": "2025-01-02", "status": "verified"},
            ],
        )
        assert len(lineage.validation_chain) == 2


class TestSimpleLineage:
    """Test SimpleLineage dataclass."""

    def test_create_simple_lineage(self) -> None:
        """Should create simple lineage with minimal fields."""
        lineage = SimpleLineage(
            entry_id="entry-1",
            source_type=SourceType.WEB_ARTICLE,
            source_url="https://example.com/article",
            retrieved_at=datetime.now(timezone.utc),
        )
        assert lineage.entry_id == "entry-1"
        assert lineage.source_type == SourceType.WEB_ARTICLE
        assert lineage.source_url == "https://example.com/article"

    def test_simple_lineage_no_url(self) -> None:
        """Should allow None URL for user input."""
        lineage = SimpleLineage(
            entry_id="entry-1",
            source_type=SourceType.USER_INPUT,
            source_url=None,
            retrieved_at=datetime.now(timezone.utc),
        )
        assert lineage.source_url is None


class TestSourceLineageManager:
    """Test SourceLineageManager functionality."""

    @pytest.fixture
    def manager(self) -> SourceLineageManager:
        """Create a fresh SourceLineageManager instance."""
        return SourceLineageManager()

    def test_full_lineage_criteria(self, manager: SourceLineageManager) -> None:
        """Should have defined criteria for full lineage."""
        assert hasattr(manager, "FULL_LINEAGE_CRITERIA")
        criteria = manager.FULL_LINEAGE_CRITERIA
        assert "importance_threshold" in criteria
        assert "source_types" in criteria

    def test_should_use_full_lineage_by_type(
        self, manager: SourceLineageManager
    ) -> None:
        """Research papers and documentation should use full lineage."""
        assert manager.should_use_full_lineage(
            source_type=SourceType.RESEARCH_PAPER,
            importance_score=0.5,
        )
        assert manager.should_use_full_lineage(
            source_type=SourceType.DOCUMENTATION,
            importance_score=0.5,
        )

    def test_should_use_full_lineage_by_importance(
        self, manager: SourceLineageManager
    ) -> None:
        """High importance entries should use full lineage."""
        threshold = manager.FULL_LINEAGE_CRITERIA["importance_threshold"]
        assert manager.should_use_full_lineage(
            source_type=SourceType.WEB_ARTICLE,
            importance_score=threshold + 0.1,
        )

    def test_should_use_simple_lineage(self, manager: SourceLineageManager) -> None:
        """Low importance web articles should use simple lineage."""
        threshold = manager.FULL_LINEAGE_CRITERIA["importance_threshold"]
        assert not manager.should_use_full_lineage(
            source_type=SourceType.WEB_ARTICLE,
            importance_score=threshold - 0.1,
        )

    def test_create_lineage_full(self, manager: SourceLineageManager) -> None:
        """Should create full lineage when criteria met."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.RESEARCH_PAPER,
            url="https://arxiv.org/paper",
            title="Important Research",
        )
        lineage = manager.create_lineage(
            entry_id="entry-1",
            source=source,
            importance_score=0.9,
        )
        assert isinstance(lineage, FullLineage)
        assert lineage.entry_id == "entry-1"
        assert lineage.primary_source == source

    def test_create_lineage_simple(self, manager: SourceLineageManager) -> None:
        """Should create simple lineage when criteria not met."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.WEB_ARTICLE,
            url="https://blog.example.com/post",
        )
        lineage = manager.create_lineage(
            entry_id="entry-1",
            source=source,
            importance_score=0.3,
        )
        assert isinstance(lineage, SimpleLineage)
        assert lineage.entry_id == "entry-1"
        assert lineage.source_url == "https://blog.example.com/post"

    def test_register_lineage(self, manager: SourceLineageManager) -> None:
        """Should register and retrieve lineage."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.DOCUMENTATION,
        )
        lineage = manager.create_lineage("entry-1", source, 0.8)
        manager.register_lineage(lineage)

        retrieved = manager.get_lineage("entry-1")
        assert isinstance(retrieved, (FullLineage, SimpleLineage))
        assert retrieved.entry_id == "entry-1"

    def test_get_lineage_unknown_entry(self, manager: SourceLineageManager) -> None:
        """Should return None for unknown entries."""
        lineage = manager.get_lineage("nonexistent")
        assert lineage is None

    def test_upgrade_to_full_lineage(self, manager: SourceLineageManager) -> None:
        """Should upgrade simple to full lineage when needed."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.WEB_ARTICLE,
            url="https://blog.example.com/post",
        )
        # Create simple lineage
        simple = manager.create_lineage("entry-1", source, 0.3)
        assert isinstance(simple, SimpleLineage)
        manager.register_lineage(simple)

        # Upgrade to full
        manager.upgrade_to_full_lineage("entry-1")

        retrieved = manager.get_lineage("entry-1")
        assert isinstance(retrieved, FullLineage)

    def test_export_lineage(self, manager: SourceLineageManager) -> None:
        """Should export lineage as serializable data."""
        source = SourceReference(
            source_id="src-1",
            source_type=SourceType.DOCUMENTATION,
            url="https://docs.example.com",
        )
        lineage = manager.create_lineage("entry-1", source, 0.8)
        manager.register_lineage(lineage)

        exported = manager.export_lineage()
        assert isinstance(exported, dict)
        assert "entry-1" in exported

    def test_import_lineage(self, manager: SourceLineageManager) -> None:
        """Should import lineage from serializable data."""
        lineage_data = {
            "entry-1": {
                "type": "full",
                "entry_id": "entry-1",
                "primary_source": {
                    "source_id": "src-1",
                    "source_type": "documentation",
                    "url": "https://docs.example.com",
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                },
                "derived_from": [],
                "transformations": [],
                "validation_chain": [],
            },
            "entry-2": {
                "type": "simple",
                "entry_id": "entry-2",
                "source_type": "web_article",
                "source_url": "https://blog.example.com",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        manager.import_lineage(lineage_data)
        assert isinstance(manager.get_lineage("entry-1"), FullLineage)
        assert isinstance(manager.get_lineage("entry-2"), SimpleLineage)

    def test_confidence_propagation(self, manager: SourceLineageManager) -> None:
        """Should calculate propagated confidence through derivation."""
        source0 = SourceReference("src-0", SourceType.RESEARCH_PAPER, confidence=0.95)
        source1 = SourceReference("src-1", SourceType.DERIVED, confidence=0.9)

        lin0 = FullLineage("entry-0", source0)
        lin1 = FullLineage("entry-1", source1, derived_from=["entry-0"])

        manager.register_lineage(lin0)
        manager.register_lineage(lin1)

        # Derived confidence should be product of chain
        confidence = manager.get_propagated_confidence("entry-1")
        expected = 0.95 * 0.9  # Multiply through chain
        assert confidence == pytest.approx(expected, abs=0.01)
