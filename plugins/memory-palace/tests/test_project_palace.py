"""Tests for the ProjectPalaceManager and PR Review Room functionality."""

import json
from unittest.mock import patch

import pytest

from memory_palace.project_palace import (
    PROJECT_PALACE_ROOMS,
    REVIEW_CHAMBER_ROOMS,
    ProjectPalaceManager,
    ReviewEntry,
    capture_pr_review_knowledge,
)


@pytest.fixture
def temp_palaces_dir(tmp_path):
    """Create a temporary directory for palace storage."""
    palaces_dir = tmp_path / "memory-palaces"
    palaces_dir.mkdir()
    return str(palaces_dir)


@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file."""
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True)
    config = {
        "storage": {"palace_directory": str(tmp_path / "memory-palaces")},
        "review_chamber": {
            "auto_capture": True,
            "capture_threshold": 60,
        },
    }
    config_path.write_text(json.dumps(config))
    return str(config_path)


@pytest.fixture
def manager(config_file, temp_palaces_dir):
    """Create a ProjectPalaceManager instance."""
    return ProjectPalaceManager(config_file, temp_palaces_dir)


class TestReviewEntry:
    """Tests for ReviewEntry class."""

    def test_create_entry(self):
        """Test creating a review entry."""
        entry = ReviewEntry(
            source_pr="#42 - Add authentication",
            title="JWT over sessions",
            room_type="decisions",
            content={
                "decision": "Chose JWT tokens for stateless scaling",
                "context": ["Reviewer asked about sessions"],
            },
            participants=["alice", "bob"],
            tags=["security", "auth"],
        )

        assert entry.source_pr == "#42 - Add authentication"
        assert entry.title == "JWT over sessions"
        assert entry.room_type == "decisions"
        assert len(entry.id) == 12
        assert "alice" in entry.participants

    def test_entry_serialization(self):
        """Test serializing and deserializing entry."""
        entry = ReviewEntry(
            source_pr="#42 - Test",
            title="Test Entry",
            room_type="patterns",
            content={"decision": "Test decision"},
        )

        data = entry.to_dict()
        restored = ReviewEntry.from_dict(data)

        assert restored.id == entry.id
        assert restored.title == entry.title
        assert restored.room_type == entry.room_type

    def test_entry_to_markdown(self):
        """Test generating markdown from entry."""
        entry = ReviewEntry(
            source_pr="#42 - Add auth",
            title="JWT Decision",
            room_type="decisions",
            content={
                "decision": "Use JWT tokens",
                "context": ["Discussion about sessions"],
                "captured_knowledge": {"pattern": "JWT + refresh tokens"},
                "connected_concepts": ["auth-patterns"],
            },
            participants=["alice"],
            tags=["security"],
        )

        md = entry.to_markdown()

        assert "JWT Decision" in md
        assert "#42 - Add auth" in md
        assert "Use JWT tokens" in md
        assert "auth-patterns" in md


class TestProjectPalaceManager:
    """Tests for ProjectPalaceManager class."""

    def test_create_project_palace(self, manager):
        """Test creating a project palace."""
        palace = manager.create_project_palace(
            repo_name="owner/test-repo",
            repo_url="https://github.com/owner/test-repo",
            description="Test repository",
        )

        assert palace["name"] == "owner/test-repo"
        assert palace["type"] == "project"
        assert "review-chamber" in palace["rooms"]
        assert "decisions" in palace["rooms"]["review-chamber"]["subrooms"]

    def test_load_project_palace(self, manager):
        """Test loading a project palace by ID."""
        created = manager.create_project_palace("owner/repo")
        loaded = manager.load_project_palace(created["id"])

        assert isinstance(loaded, dict)
        assert loaded["id"] == created["id"]
        assert loaded["name"] == "owner/repo"

    def test_find_project_palace(self, manager):
        """Test finding a project palace by name."""
        manager.create_project_palace("owner/repo1")
        manager.create_project_palace("owner/repo2")

        found = manager.find_project_palace("owner/repo2")

        assert isinstance(found, dict)
        assert found["name"] == "owner/repo2"

    def test_get_or_create_project_palace(self, manager):
        """Test get_or_create returns existing palace."""
        created = manager.create_project_palace("owner/repo")
        retrieved = manager.get_or_create_project_palace("owner/repo")

        assert retrieved["id"] == created["id"]

    def test_add_review_entry(self, manager):
        """Test adding a review entry to palace."""
        palace = manager.create_project_palace("owner/repo")

        entry = ReviewEntry(
            source_pr="#42 - Test",
            title="Test Entry",
            room_type="decisions",
            content={"decision": "Test"},
            participants=["alice"],
        )

        result = manager.add_review_entry(palace["id"], entry)
        assert result is True

        # Reload and verify
        updated = manager.load_project_palace(palace["id"])
        decisions = updated["rooms"]["review-chamber"]["subrooms"]["decisions"]
        assert len(decisions["entries"]) == 1
        assert decisions["entries"][0]["title"] == "Test Entry"

    def test_add_review_entry_invalid_room(self, manager):
        """Test adding entry with invalid room type."""
        palace = manager.create_project_palace("owner/repo")

        entry = ReviewEntry(
            source_pr="#42",
            title="Test",
            room_type="invalid_room",
            content={},
        )

        result = manager.add_review_entry(palace["id"], entry)
        assert result is False

    def test_search_review_chamber(self, manager):
        """Index two review entries and assert keyword search returns the expected one."""
        palace = manager.create_project_palace("owner/repo")

        # Add entries
        entry1 = ReviewEntry(
            source_pr="#42",
            title="JWT Authentication",
            room_type="decisions",
            content={"decision": "Use JWT for auth"},
            tags=["security", "auth"],
        )
        entry2 = ReviewEntry(
            source_pr="#43",
            title="Error Handling Pattern",
            room_type="patterns",
            content={"decision": "Use structured errors"},
            tags=["api"],
        )

        manager.add_review_entry(palace["id"], entry1)
        manager.add_review_entry(palace["id"], entry2)

        # Search
        results = manager.search_review_chamber(palace["id"], "jwt")
        assert len(results) == 1
        assert results[0]["entry"]["title"] == "JWT Authentication"

        # Search with room filter
        results = manager.search_review_chamber(
            palace["id"], "structured", room_type="patterns"
        )
        assert len(results) == 1

        # Search with tags
        results = manager.search_review_chamber(palace["id"], "", tags=["security"])
        assert len(results) == 1

    def test_get_review_chamber_stats(self, manager):
        """Test getting review chamber statistics."""
        palace = manager.create_project_palace("owner/repo")

        # Add entries
        for i in range(3):
            entry = ReviewEntry(
                source_pr=f"#{i}",
                title=f"Entry {i}",
                room_type="decisions",
                content={},
                tags=["tag1", "tag2"] if i < 2 else ["tag3"],
                participants=["alice"],
            )
            manager.add_review_entry(palace["id"], entry)

        stats = manager.get_review_chamber_stats(palace["id"])

        assert stats["total_entries"] == 3
        assert stats["by_room"]["decisions"] == 3
        assert "alice" in stats["contributors"]
        assert stats["top_tags"]["tag1"] == 2

    def test_list_project_palaces(self, manager):
        """Test listing all project palaces."""
        manager.create_project_palace("owner/repo1")
        manager.create_project_palace("owner/repo2")

        palaces = manager.list_project_palaces()

        assert len(palaces) == 2
        names = [p["name"] for p in palaces]
        assert "owner/repo1" in names
        assert "owner/repo2" in names


class TestCaptureFunction:
    """Tests for the capture_pr_review_knowledge function."""

    def test_capture_blocking_finding(self, config_file, temp_palaces_dir):
        """Test capturing a BLOCKING finding."""
        findings = [
            {
                "title": "Security vulnerability",
                "description": "Missing input validation",
                "severity": "BLOCKING",
                "category": "security/architecture",
                "file": "auth.py",
                "line": 42,
                "tags": ["security"],
            }
        ]

        created = capture_pr_review_knowledge(
            repo_name="owner/repo",
            pr_number=42,
            pr_title="Add authentication",
            findings=findings,
            participants=["alice", "bob"],
            config_path=config_file,
        )

        assert len(created) == 1

        # Verify stored
        manager = ProjectPalaceManager(config_file, temp_palaces_dir)
        palace = manager.find_project_palace("owner/repo")
        decisions = palace["rooms"]["review-chamber"]["subrooms"]["decisions"]
        assert len(decisions["entries"]) == 1

    def test_capture_skips_low_value_finding(self, config_file, temp_palaces_dir):
        """Test that low-value findings are not captured."""
        findings = [
            {
                "title": "Typo in comment",
                "severity": "SUGGESTION",
                "category": "style",
            }
        ]

        created = capture_pr_review_knowledge(
            repo_name="owner/repo",
            pr_number=42,
            pr_title="Fix typo",
            findings=findings,
            participants=["alice"],
            config_path=config_file,
        )

        assert len(created) == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_load_nonexistent_palace(self, manager):
        """Load palace returns None when palace ID doesn't exist."""
        result = manager.load_project_palace("nonexistent-id")
        assert result is None

    def test_add_review_entry_to_nonexistent_palace(self, manager):
        """Add review entry returns False when palace ID doesn't exist."""
        entry = ReviewEntry(
            source_pr="#42",
            title="Test",
            room_type="decisions",
            content={},
        )
        result = manager.add_review_entry("nonexistent-id", entry)
        assert result is False

    def test_search_review_chamber_nonexistent_palace(self, manager):
        """Search review chamber returns empty list when palace ID doesn't exist."""
        results = manager.search_review_chamber("nonexistent-id", "query")
        assert results == []

    def test_get_review_chamber_stats_nonexistent_palace(self, manager):
        """Get review chamber stats returns empty dict when palace ID doesn't exist."""
        stats = manager.get_review_chamber_stats("nonexistent-id")
        assert stats == {}


class TestFindingClassification:
    """Tests for _classify_finding function covering all classification paths."""

    def test_classify_pattern_finding(self, config_file, temp_palaces_dir):
        """IN-SCOPE severity with pattern category classifies as 'patterns'."""
        findings = [
            {
                "title": "Recurring error handling",
                "description": "Same error pattern seen multiple times",
                "severity": "IN-SCOPE",
                "category": "recurring/pattern",
                "tags": ["pattern"],
            }
        ]

        created = capture_pr_review_knowledge(
            repo_name="owner/test-patterns",
            pr_number=100,
            pr_title="Fix patterns",
            findings=findings,
            participants=["dev"],
            config_path=config_file,
        )

        assert len(created) == 1

        # Verify it was placed in patterns room
        manager = ProjectPalaceManager(config_path=config_file)
        palace = manager.find_project_palace("owner/test-patterns")
        patterns = palace["rooms"]["review-chamber"]["subrooms"]["patterns"]
        assert len(patterns["entries"]) == 1

    def test_classify_standards_finding(self, config_file, temp_palaces_dir):
        """IN-SCOPE severity with quality category classifies as 'standards'."""
        findings = [
            {
                "title": "API Error Format Convention",
                "description": "Use structured error responses",
                "severity": "IN-SCOPE",
                "category": "quality/convention",
                "tags": ["api", "quality"],
            }
        ]

        created = capture_pr_review_knowledge(
            repo_name="owner/test-standards",
            pr_number=101,
            pr_title="API cleanup",
            findings=findings,
            participants=["dev"],
            config_path=config_file,
        )

        assert len(created) == 1

        manager = ProjectPalaceManager(config_path=config_file)
        palace = manager.find_project_palace("owner/test-standards")
        standards = palace["rooms"]["review-chamber"]["subrooms"]["standards"]
        assert len(standards["entries"]) == 1

    def test_classify_lessons_finding(self, config_file, temp_palaces_dir):
        """Finding with lesson/learning category classifies as 'lessons'."""
        findings = [
            {
                "title": "Outage Retrospective Insight",
                "description": "Key learning from incident",
                "severity": "SUGGESTION",
                "category": "lesson/retrospective",
                "tags": ["postmortem"],
            }
        ]

        created = capture_pr_review_knowledge(
            repo_name="owner/test-lessons",
            pr_number=102,
            pr_title="Post-mortem docs",
            findings=findings,
            participants=["dev"],
            config_path=config_file,
        )

        assert len(created) == 1

        manager = ProjectPalaceManager(config_path=config_file)
        palace = manager.find_project_palace("owner/test-lessons")
        lessons = palace["rooms"]["review-chamber"]["subrooms"]["lessons"]
        assert len(lessons["entries"]) == 1

    def test_classify_blocking_without_keywords_as_patterns(
        self, config_file, temp_palaces_dir
    ):
        """BLOCKING findings without specific keywords fall back to 'patterns'."""
        findings = [
            {
                "title": "Critical Issue Found",
                "description": "Important blocking issue",
                "severity": "BLOCKING",
                "category": "general",
                "tags": ["critical"],
            }
        ]

        created = capture_pr_review_knowledge(
            repo_name="owner/test-fallback",
            pr_number=103,
            pr_title="Fix critical",
            findings=findings,
            participants=["dev"],
            config_path=config_file,
        )

        assert len(created) == 1

        manager = ProjectPalaceManager(config_path=config_file)
        palace = manager.find_project_palace("owner/test-fallback")
        patterns = palace["rooms"]["review-chamber"]["subrooms"]["patterns"]
        assert len(patterns["entries"]) == 1


class TestReviewEntryImportance:
    """Test importance scoring on ReviewEntry."""

    def test_default_importance_score(self) -> None:
        """Non-decision entries default to importance 40."""
        entry = ReviewEntry(
            source_pr="#1 - Test",
            title="Test Entry",
            room_type="patterns",
            content={"decision": "test"},
        )
        assert entry.importance_score == 40

    def test_decisions_get_boost(self) -> None:
        """Decision entries get boosted importance of at least 70."""
        entry = ReviewEntry(
            source_pr="#1 - Arch",
            title="Use hexagonal",
            room_type="decisions",
            content={"decision": "hexagonal"},
        )
        assert entry.importance_score >= 70

    def test_explicit_importance(self) -> None:
        """Explicit importance_score overrides defaults."""
        entry = ReviewEntry(
            source_pr="#1 - Test",
            title="Test",
            room_type="patterns",
            content={"decision": "test"},
            importance_score=85,
        )
        assert entry.importance_score == 85

    def test_importance_in_serialization(self) -> None:
        """Importance score survives to_dict/from_dict round-trip."""
        entry = ReviewEntry(
            source_pr="#1 - Test",
            title="Test",
            room_type="patterns",
            content={"decision": "test"},
            importance_score=85,
        )
        data = entry.to_dict()
        assert data["importance_score"] == 85

        restored = ReviewEntry.from_dict(data)
        assert restored.importance_score == 85

    def test_importance_in_markdown(self) -> None:
        """Importance score appears in markdown output."""
        entry = ReviewEntry(
            source_pr="#1 - Test",
            title="Test",
            room_type="decisions",
            content={"decision": "test"},
            importance_score=90,
        )
        md = entry.to_markdown()
        assert "importance_score: 90" in md


class TestSearchSortByImportance:
    """Test sort_by='importance' in search_review_chamber."""

    def test_sort_by_importance(self, manager):
        """Results sorted by importance_score descending."""
        palace = manager.create_project_palace("owner/sort-repo")

        # Low importance entry added first
        low = ReviewEntry(
            source_pr="#1",
            title="Low priority pattern",
            room_type="patterns",
            content={"decision": "low"},
            importance_score=20,
        )
        # High importance entry added second
        high = ReviewEntry(
            source_pr="#2",
            title="High priority pattern",
            room_type="patterns",
            content={"decision": "high"},
            importance_score=95,
        )

        manager.add_review_entry(palace["id"], low)
        manager.add_review_entry(palace["id"], high)

        results = manager.search_review_chamber(palace["id"], "", sort_by="importance")
        assert len(results) == 2
        assert results[0]["entry"]["title"] == "High priority pattern"
        assert results[1]["entry"]["title"] == "Low priority pattern"

    def test_default_sort_is_recency(self, manager):
        """Default sort_by='recency' preserves original order."""
        palace = manager.create_project_palace("owner/recency-repo")

        entry = ReviewEntry(
            source_pr="#1",
            title="Some pattern",
            room_type="patterns",
            content={"decision": "test"},
        )
        manager.add_review_entry(palace["id"], entry)

        # Should work without sort_by parameter
        results = manager.search_review_chamber(palace["id"], "")
        assert len(results) == 1


class TestSemanticSearchSortByImportance:
    """Test that semantic search respects sort_by='importance'."""

    def test_semantic_sort_by_importance(self, manager):
        """Semantic results re-sorted by importance_score descending."""
        palace = manager.create_project_palace("owner/semantic-repo")

        low = ReviewEntry(
            source_pr="#10",
            title="Low priority finding",
            room_type="patterns",
            content={"decision": "minor tweak"},
            importance_score=15,
        )
        mid = ReviewEntry(
            source_pr="#11",
            title="Mid priority finding",
            room_type="patterns",
            content={"decision": "moderate change"},
            importance_score=55,
        )
        high = ReviewEntry(
            source_pr="#12",
            title="High priority finding",
            room_type="patterns",
            content={"decision": "critical fix"},
            importance_score=90,
        )

        manager.add_review_entry(palace["id"], low)
        manager.add_review_entry(palace["id"], mid)
        manager.add_review_entry(palace["id"], high)

        # Mock _search_review_chamber_semantic to return results
        # in similarity order (low, high, mid) -- NOT importance order
        def fake_semantic(  # noqa: PLR0913 - matches _search_review_chamber_semantic signature
            self_inner, palace_arg, chamber, query, room_type, tags, sort_by
        ):
            # Return in similarity order (NOT importance order).
            # The production search_review_chamber must apply the sort.
            return [
                {
                    "room": "review-chamber/patterns",
                    "entry": low.to_dict(),
                    "palace_id": palace["id"],
                    "palace_name": palace["name"],
                    "score": 0.99,
                },
                {
                    "room": "review-chamber/patterns",
                    "entry": high.to_dict(),
                    "palace_id": palace["id"],
                    "palace_name": palace["name"],
                    "score": 0.85,
                },
                {
                    "room": "review-chamber/patterns",
                    "entry": mid.to_dict(),
                    "palace_id": palace["id"],
                    "palace_name": palace["name"],
                    "score": 0.70,
                },
            ]

        with patch.object(
            ProjectPalaceManager,
            "_search_review_chamber_semantic",
            fake_semantic,
        ):
            results = manager.search_review_chamber(
                palace["id"],
                "finding",
                semantic=True,
                sort_by="importance",
            )

        assert len(results) == 3
        scores = [r["entry"]["importance_score"] for r in results]
        assert scores == [90, 55, 15]

    def test_semantic_default_sort_preserves_similarity_order(self, manager):
        """Without sort_by=importance, semantic results keep similarity order."""
        palace = manager.create_project_palace("owner/semantic-default")

        low = ReviewEntry(
            source_pr="#20",
            title="Low importance but high similarity",
            room_type="patterns",
            content={"decision": "test"},
            importance_score=10,
        )
        high = ReviewEntry(
            source_pr="#21",
            title="High importance but low similarity",
            room_type="patterns",
            content={"decision": "test"},
            importance_score=99,
        )

        manager.add_review_entry(palace["id"], low)
        manager.add_review_entry(palace["id"], high)

        # Return low-importance first (higher similarity score)
        def fake_semantic(  # noqa: PLR0913 - matches _search_review_chamber_semantic signature
            self_inner, palace_arg, chamber, query, room_type, tags, sort_by
        ):
            # Return in similarity order (low-importance first).
            # The production search_review_chamber must NOT re-sort
            # when sort_by is not IMPORTANCE.
            return [
                {
                    "room": "review-chamber/patterns",
                    "entry": low.to_dict(),
                    "palace_id": palace["id"],
                    "palace_name": palace["name"],
                    "score": 0.99,
                },
                {
                    "room": "review-chamber/patterns",
                    "entry": high.to_dict(),
                    "palace_id": palace["id"],
                    "palace_name": palace["name"],
                    "score": 0.50,
                },
            ]

        with patch.object(
            ProjectPalaceManager,
            "_search_review_chamber_semantic",
            fake_semantic,
        ):
            results = manager.search_review_chamber(
                palace["id"],
                "test",
                semantic=True,
            )

        assert len(results) == 2
        # Similarity order preserved: low-importance first
        scores = [r["entry"]["importance_score"] for r in results]
        assert scores == [10, 99]


class TestGetReviewChamberStatsTopEntries:
    """Test that get_review_chamber_stats returns top_entries by importance."""

    def test_stats_returns_top_entries_key(self, manager):
        """Stats dict uses top_entries instead of recent_entries."""
        palace = manager.create_project_palace("owner/stats-repo")

        entry = ReviewEntry(
            source_pr="#1",
            title="Entry",
            room_type="decisions",
            content={},
            importance_score=80,
        )
        manager.add_review_entry(palace["id"], entry)

        stats = manager.get_review_chamber_stats(palace["id"])
        assert "top_entries" in stats
        assert "recent_entries" not in stats

    def test_top_entries_sorted_by_importance(self, manager):
        """top_entries are sorted by importance_score descending."""
        palace = manager.create_project_palace("owner/top-repo")

        for score in [30, 90, 50]:
            entry = ReviewEntry(
                source_pr=f"#{score}",
                title=f"Entry {score}",
                room_type="decisions",
                content={},
                importance_score=score,
            )
            manager.add_review_entry(palace["id"], entry)

        stats = manager.get_review_chamber_stats(palace["id"])
        scores = [e.get("importance_score", 40) for e in stats["top_entries"]]
        assert scores == [90, 50, 30]


class TestRoomStructure:
    """Tests for room structure constants."""

    def test_review_chamber_rooms_defined(self):
        """Test that review chamber rooms are properly defined."""
        assert "decisions" in REVIEW_CHAMBER_ROOMS
        assert "patterns" in REVIEW_CHAMBER_ROOMS
        assert "standards" in REVIEW_CHAMBER_ROOMS
        assert "lessons" in REVIEW_CHAMBER_ROOMS

        for room in REVIEW_CHAMBER_ROOMS.values():
            assert "description" in room
            assert "icon" in room
            assert "retention" in room

    def test_project_palace_rooms_include_review_chamber(self):
        """Guard the registry: ``review-chamber`` must ship with ``subrooms``."""
        assert "review-chamber" in PROJECT_PALACE_ROOMS
        assert "subrooms" in PROJECT_PALACE_ROOMS["review-chamber"]
