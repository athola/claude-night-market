"""Tests for gauntlet progress tracking."""

from __future__ import annotations

from pathlib import Path

import pytest
from gauntlet.models import AnswerRecord, KnowledgeEntry
from gauntlet.progress import ProgressTracker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(
    entry_id: str = "ke-001",
    category: str = "business_logic",
    module: str = "billing",
) -> KnowledgeEntry:
    return KnowledgeEntry(
        id=entry_id,
        category=category,
        module=module,
        concept="Pro-rata calculation",
        detail="Charge based on remaining days.",
        difficulty=2,
        extracted_at="2026-01-01T00:00:00",
        source="code",
        related_files=["src/billing/proration.py"],
    )


# ---------------------------------------------------------------------------
# Feature: get_or_create
# ---------------------------------------------------------------------------


class TestGetOrCreate:
    """
    Feature: Developer progress initialisation

    As a gauntlet engine
    I want to retrieve or create a DeveloperProgress record
    So that new developers start with a clean slate automatically
    """

    @pytest.mark.unit
    def test_creates_new_progress_for_unknown_developer(self, tmp_gauntlet_dir: Path):
        """
        Scenario: First time a developer is seen
        Given no existing progress file for 'dev@example.com'
        When get_or_create is called
        Then a DeveloperProgress with empty history is returned
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")

        assert progress.developer_id == "dev@example.com"
        assert progress.history == []
        assert progress.streak == 0


# ---------------------------------------------------------------------------
# Feature: record_answer
# ---------------------------------------------------------------------------


class TestRecordAnswer:
    """
    Feature: Recording challenge answers

    As a gauntlet engine
    I want to record every answer and update the streak
    So that difficulty and type weights adapt over time
    """

    @pytest.mark.unit
    def test_pass_increments_streak(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Developer answers correctly
        Given a developer with streak=0
        When record_answer is called with result='pass'
        Then streak becomes 1 and history has one record
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        tracker.record_answer(
            progress,
            challenge_id="ch-001",
            knowledge_entry_id="ke-001",
            challenge_type="explain_why",
            category="business_logic",
            difficulty=2,
            result="pass",
        )

        assert progress.streak == 1
        assert len(progress.history) == 1
        assert progress.history[0].result == "pass"

    @pytest.mark.unit
    def test_fail_resets_streak(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Developer answers incorrectly after a streak
        Given a developer with streak=5
        When record_answer is called with result='fail'
        Then streak resets to 0
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        progress.streak = 5
        tracker.record_answer(
            progress,
            challenge_id="ch-002",
            knowledge_entry_id="ke-001",
            challenge_type="trace",
            category="data_flow",
            difficulty=3,
            result="fail",
        )

        assert progress.streak == 0

    @pytest.mark.unit
    def test_partial_resets_streak(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Developer gives a partial answer
        Given a developer with streak=3
        When record_answer is called with result='partial'
        Then streak resets to 0 (only 'pass' extends streak)
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        progress.streak = 3
        tracker.record_answer(
            progress,
            challenge_id="ch-003",
            knowledge_entry_id="ke-001",
            challenge_type="spot_bug",
            category="business_logic",
            difficulty=2,
            result="partial",
        )

        assert progress.streak == 0


# ---------------------------------------------------------------------------
# Feature: save and load roundtrip
# ---------------------------------------------------------------------------


class TestSaveLoadRoundtrip:
    """
    Feature: Persistence roundtrip

    As a gauntlet engine
    I want to save and reload DeveloperProgress from disk
    So that state persists across sessions
    """

    @pytest.mark.unit
    def test_save_and_reload_preserves_history(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Progress is saved then reloaded
        Given a developer with one recorded answer
        When save is called and then get_or_create is called again
        Then the reloaded progress has the same history record
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        tracker.record_answer(
            progress,
            challenge_id="ch-001",
            knowledge_entry_id="ke-001",
            challenge_type="explain_why",
            category="business_logic",
            difficulty=2,
            result="pass",
        )
        # record_answer auto-saves, but call save explicitly too
        tracker.save(progress)

        reloaded = tracker.get_or_create("dev@example.com")
        assert len(reloaded.history) == 1
        assert reloaded.history[0].challenge_id == "ch-001"
        assert reloaded.history[0].result == "pass"
        assert reloaded.streak == 1


# ---------------------------------------------------------------------------
# Feature: select_entry
# ---------------------------------------------------------------------------


class TestSelectEntry:
    """
    Feature: Knowledge entry selection

    As a gauntlet engine
    I want to pick the next entry to quiz on
    So that developers see unseen and weak-category entries more often
    """

    @pytest.mark.unit
    def test_prefers_unseen_entries(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Unseen entries are preferred over well-known ones
        Given two entries where only one has been seen (and passed)
        When select_entry is called 50 times
        Then the unseen entry is selected at least once
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")

        # ke-001 has been seen and passed
        progress.history.append(
            AnswerRecord(
                challenge_id="ch-x",
                knowledge_entry_id="ke-001",
                challenge_type="explain_why",
                category="business_logic",
                difficulty=2,
                result="pass",
                answered_at="2026-01-01T00:00:00",
            )
        )
        progress.last_seen["ke-001"] = "2026-01-01T00:00:00"

        entries = [
            _entry(entry_id="ke-001"),
            _entry(entry_id="ke-002"),  # unseen
        ]

        seen_ids = {tracker.select_entry(progress, entries).id for _ in range(50)}
        assert "ke-002" in seen_ids

    @pytest.mark.unit
    def test_prefers_weak_categories(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Entries from weak categories are selected more often
        Given two entries in different categories where one has 0% accuracy
        When select_entry is called 100 times
        Then both categories appear (weak category is not ignored)
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")

        # business_logic: 100% accuracy
        for i in range(5):
            progress.history.append(
                AnswerRecord(
                    challenge_id=f"ch-{i}",
                    knowledge_entry_id="ke-001",
                    challenge_type="explain_why",
                    category="business_logic",
                    difficulty=2,
                    result="pass",
                    answered_at="2026-01-01T00:00:00",
                )
            )

        # architecture: 0% accuracy
        for i in range(5, 10):
            progress.history.append(
                AnswerRecord(
                    challenge_id=f"ch-{i}",
                    knowledge_entry_id="ke-002",
                    challenge_type="trace",
                    category="architecture",
                    difficulty=3,
                    result="fail",
                    answered_at="2026-01-01T00:00:00",
                )
            )

        entries = [
            _entry(entry_id="ke-001", category="business_logic"),
            _entry(entry_id="ke-002", category="architecture"),
        ]

        seen_categories = {
            tracker.select_entry(progress, entries).category for _ in range(100)
        }
        assert "architecture" in seen_categories
        assert "business_logic" in seen_categories


# ---------------------------------------------------------------------------
# Feature: current_difficulty
# ---------------------------------------------------------------------------


class TestCurrentDifficulty:
    """
    Feature: Adaptive difficulty calculation

    As a gauntlet engine
    I want to increase difficulty as developers answer correctly
    So that challenges remain appropriately challenging
    """

    @pytest.mark.unit
    def test_default_difficulty_is_three(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Developer with no history
        Given a developer with streak=0
        When current_difficulty is called
        Then it returns 3
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        assert tracker.current_difficulty(progress) == 3

    @pytest.mark.unit
    def test_difficulty_increases_with_streak(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Developer on a 3-answer winning streak
        Given a developer with streak=3
        When current_difficulty is called
        Then it returns 4 (base 3 + 1 for every 3 correct)
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        progress.streak = 3
        assert tracker.current_difficulty(progress) == 4

    @pytest.mark.unit
    def test_difficulty_caps_at_five(self, tmp_gauntlet_dir: Path):
        """
        Scenario: Developer on a very long streak
        Given a developer with streak=30
        When current_difficulty is called
        Then it returns 5 (max difficulty)
        """
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("dev@example.com")
        progress.streak = 30
        assert tracker.current_difficulty(progress) == 5
