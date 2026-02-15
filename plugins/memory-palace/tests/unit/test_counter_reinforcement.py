"""Tests for counter-based reinforcement module.

Tests the ACE Playbook-inspired pattern where similar insights
increment counters rather than creating duplicates.
"""

from datetime import UTC, datetime

import pytest

from memory_palace.corpus.counter_reinforcement import (
    SIMILARITY_THRESHOLD,
    CounterReinforcementTracker,
    FeedbackType,
    ReinforcementCounter,
)


class TestReinforcementCounter:
    """Tests for ReinforcementCounter dataclass."""

    @pytest.mark.unit
    def test_counter_initialization_defaults(self) -> None:
        """Test counter initializes with correct defaults."""
        counter = ReinforcementCounter(entry_id="test-entry")

        assert counter.entry_id == "test-entry"
        assert counter.helpful == 0
        assert counter.harmful == 0
        assert counter.neutral == 0
        assert counter.total_signals == 0

    @pytest.mark.unit
    def test_counter_total_signals(self) -> None:
        """Test total_signals property calculation."""
        counter = ReinforcementCounter(
            entry_id="test",
            helpful=5,
            harmful=2,
            neutral=3,
        )

        assert counter.total_signals == 10

    @pytest.mark.unit
    def test_helpfulness_ratio_calculation(self) -> None:
        """Test helpfulness_ratio with various signal distributions."""
        # All helpful
        counter = ReinforcementCounter(
            entry_id="test", helpful=10, harmful=0, neutral=0
        )
        assert counter.helpfulness_ratio == 1.0

        # All harmful
        counter = ReinforcementCounter(
            entry_id="test", helpful=0, harmful=10, neutral=0
        )
        assert counter.helpfulness_ratio == 0.0

        # Mixed signals
        counter = ReinforcementCounter(entry_id="test", helpful=5, harmful=2, neutral=3)
        assert counter.helpfulness_ratio == 0.5  # 5 / 10

        # No signals defaults to neutral
        counter = ReinforcementCounter(entry_id="test")
        assert counter.helpfulness_ratio == 0.5

    @pytest.mark.unit
    def test_harm_ratio_calculation(self) -> None:
        """Test harm_ratio with various signal distributions."""
        # High harm
        counter = ReinforcementCounter(entry_id="test", helpful=2, harmful=8, neutral=0)
        assert counter.harm_ratio == 0.8

        # No harm
        counter = ReinforcementCounter(
            entry_id="test", helpful=10, harmful=0, neutral=5
        )
        assert counter.harm_ratio == 0.0

        # No signals (zero division protection)
        counter = ReinforcementCounter(entry_id="test")
        assert counter.harm_ratio == 0.0

    @pytest.mark.unit
    def test_confidence_score_range(self) -> None:
        """Test confidence_score stays in 0-1 range."""
        # Maximum confidence (all helpful)
        counter = ReinforcementCounter(
            entry_id="test", helpful=100, harmful=0, neutral=0
        )
        assert counter.confidence_score == 1.0

        # Minimum confidence (all harmful)
        counter = ReinforcementCounter(
            entry_id="test", helpful=0, harmful=100, neutral=0
        )
        assert counter.confidence_score == 0.0

        # Neutral confidence
        counter = ReinforcementCounter(
            entry_id="test", helpful=50, harmful=50, neutral=0
        )
        assert counter.confidence_score == 0.5

        # No signals - defaults to neutral confidence
        counter = ReinforcementCounter(entry_id="test")
        assert counter.confidence_score == 0.5

    @pytest.mark.unit
    def test_needs_review_high_harm_ratio(self) -> None:
        """Test needs_review triggers on high harm ratio."""
        counter = ReinforcementCounter(entry_id="test", helpful=5, harmful=5, neutral=0)
        # 50% harm ratio > 30% threshold
        assert counter.needs_review is True

    @pytest.mark.unit
    def test_needs_review_low_helpfulness(self) -> None:
        """Test needs_review triggers on low helpfulness with signals."""
        counter = ReinforcementCounter(entry_id="test", helpful=1, harmful=1, neutral=8)
        # 10% helpfulness < 40% threshold, and > 5 total signals
        assert counter.needs_review is True

    @pytest.mark.unit
    def test_needs_review_healthy_entry(self) -> None:
        """Test needs_review is False for healthy entries."""
        counter = ReinforcementCounter(entry_id="test", helpful=8, harmful=1, neutral=1)
        # 80% helpfulness, 10% harm - healthy
        assert counter.needs_review is False

    @pytest.mark.unit
    def test_counter_serialization(self) -> None:
        """Test counter to_dict and from_dict roundtrip."""
        original = ReinforcementCounter(
            entry_id="test-entry",
            helpful=10,
            harmful=2,
            neutral=5,
            metadata={"source": "test"},
        )

        serialized = original.to_dict()
        restored = ReinforcementCounter.from_dict(serialized)

        assert restored.entry_id == original.entry_id
        assert restored.helpful == original.helpful
        assert restored.harmful == original.harmful
        assert restored.neutral == original.neutral
        assert restored.metadata == original.metadata


class TestCounterReinforcementTracker:
    """Tests for CounterReinforcementTracker."""

    @pytest.fixture
    def tracker(self) -> CounterReinforcementTracker:
        """Create a fresh tracker for each test."""
        return CounterReinforcementTracker()

    @pytest.mark.unit
    def test_reinforce_creates_counter(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test reinforce creates counter if not exists."""
        counter = tracker.reinforce("new-entry", FeedbackType.HELPFUL)

        assert counter.entry_id == "new-entry"
        assert counter.helpful == 1
        assert counter.harmful == 0
        assert counter.neutral == 0

    @pytest.mark.unit
    def test_reinforce_increments_counter(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test reinforce increments existing counter."""
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        tracker.reinforce("entry-1", FeedbackType.HARMFUL)
        counter = tracker.reinforce("entry-1", FeedbackType.NEUTRAL)

        assert counter.helpful == 2
        assert counter.harmful == 1
        assert counter.neutral == 1

    @pytest.mark.unit
    def test_reinforce_updates_last_accessed(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test reinforce updates last_accessed timestamp."""
        before = datetime.now(UTC)
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        counter = tracker.get_counter("entry-1")

        assert counter is not None
        assert counter.last_accessed >= before

    @pytest.mark.unit
    def test_get_counter_returns_none_for_missing(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test get_counter returns None for unknown entry."""
        assert tracker.get_counter("nonexistent") is None

    @pytest.mark.unit
    def test_get_or_create_counter(self, tracker: CounterReinforcementTracker) -> None:
        """Test get_or_create_counter creates if missing."""
        counter = tracker.get_or_create_counter("new-entry")

        assert counter.entry_id == "new-entry"
        assert counter.total_signals == 0

        # Second call returns same counter
        same = tracker.get_or_create_counter("new-entry")
        assert same is counter

    @pytest.mark.unit
    def test_get_review_candidates(self, tracker: CounterReinforcementTracker) -> None:
        """Test get_review_candidates returns problematic entries."""
        # Create healthy entry
        for _ in range(10):
            tracker.reinforce("healthy", FeedbackType.HELPFUL)

        # Create problematic entry
        for _ in range(5):
            tracker.reinforce("problematic", FeedbackType.HARMFUL)
        for _ in range(5):
            tracker.reinforce("problematic", FeedbackType.HELPFUL)

        candidates = tracker.get_review_candidates()

        assert len(candidates) == 1
        assert candidates[0].entry_id == "problematic"

    @pytest.mark.unit
    def test_get_top_performers(self, tracker: CounterReinforcementTracker) -> None:
        """Test get_top_performers returns high-confidence entries."""
        # Create entries with varying helpfulness
        for _ in range(10):
            tracker.reinforce("excellent", FeedbackType.HELPFUL)

        for _ in range(5):
            tracker.reinforce("good", FeedbackType.HELPFUL)
        for _ in range(5):
            tracker.reinforce("good", FeedbackType.NEUTRAL)

        for _ in range(3):
            tracker.reinforce("mediocre", FeedbackType.HELPFUL)
        for _ in range(3):
            tracker.reinforce("mediocre", FeedbackType.HARMFUL)

        top = tracker.get_top_performers(limit=2)

        assert len(top) == 2
        assert top[0].entry_id == "excellent"
        assert top[1].entry_id == "good"

    @pytest.mark.unit
    def test_get_frequently_accessed(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test get_frequently_accessed returns most active entries."""
        for _ in range(20):
            tracker.reinforce("popular", FeedbackType.NEUTRAL)

        for _ in range(5):
            tracker.reinforce("moderate", FeedbackType.NEUTRAL)

        tracker.reinforce("rare", FeedbackType.NEUTRAL)

        frequent = tracker.get_frequently_accessed(limit=2)

        assert len(frequent) == 2
        assert frequent[0].entry_id == "popular"
        assert frequent[1].entry_id == "moderate"

    @pytest.mark.unit
    def test_should_deduplicate_above_threshold(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test should_deduplicate returns True above threshold."""
        # Create a healthy existing entry
        for _ in range(5):
            tracker.reinforce("existing", FeedbackType.HELPFUL)

        result = tracker.should_deduplicate(
            new_entry_id="new",
            existing_entry_id="existing",
            similarity_score=0.85,  # Above 0.8 threshold
        )

        assert result is True

    @pytest.mark.unit
    def test_should_deduplicate_below_threshold(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test should_deduplicate returns False below threshold."""
        result = tracker.should_deduplicate(
            new_entry_id="new",
            existing_entry_id="existing",
            similarity_score=0.75,  # Below 0.8 threshold
        )

        assert result is False

    @pytest.mark.unit
    def test_should_deduplicate_skips_problematic(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test should_deduplicate skips problematic existing entries."""
        # Create a problematic existing entry
        for _ in range(5):
            tracker.reinforce("problematic", FeedbackType.HARMFUL)

        result = tracker.should_deduplicate(
            new_entry_id="new",
            existing_entry_id="problematic",
            similarity_score=0.95,  # High similarity but problematic target
        )

        assert result is False

    @pytest.mark.unit
    def test_export_import_roundtrip(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test export and import preserves all counters."""
        # Create some counters
        for _ in range(5):
            tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        for _ in range(3):
            tracker.reinforce("entry-2", FeedbackType.HARMFUL)

        # Export
        exported = tracker.export_counters()
        assert len(exported) == 2

        # Import into new tracker
        new_tracker = CounterReinforcementTracker()
        new_tracker.import_counters(exported)

        # Verify
        counter1 = new_tracker.get_counter("entry-1")
        assert counter1 is not None
        assert counter1.helpful == 5

        counter2 = new_tracker.get_counter("entry-2")
        assert counter2 is not None
        assert counter2.harmful == 3

    @pytest.mark.unit
    def test_similarity_threshold_value(self) -> None:
        """Test SIMILARITY_THRESHOLD matches ACE research."""
        # ACE Playbook uses 0.8 cosine similarity threshold
        assert SIMILARITY_THRESHOLD == 0.8

    @pytest.mark.unit
    def test_get_all_counters(self, tracker: CounterReinforcementTracker) -> None:
        """Test get_all_counters returns list of all counters."""
        # Create several entries
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        tracker.reinforce("entry-2", FeedbackType.HARMFUL)
        tracker.reinforce("entry-3", FeedbackType.NEUTRAL)

        all_counters = tracker.get_all_counters()

        assert len(all_counters) == 3
        entry_ids = {c.entry_id for c in all_counters}
        assert entry_ids == {"entry-1", "entry-2", "entry-3"}

    @pytest.mark.unit
    def test_clear_removes_all_counters(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test clear() removes all counters from tracker."""
        # Add some counters
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        tracker.reinforce("entry-2", FeedbackType.HARMFUL)

        assert len(tracker.get_all_counters()) == 2

        # Clear
        tracker.clear()

        assert len(tracker.get_all_counters()) == 0
        assert tracker.get_counter("entry-1") is None

    @pytest.mark.unit
    def test_reinforce_with_metadata(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test reinforce merges metadata correctly."""
        # First reinforcement with metadata
        tracker.reinforce(
            "entry-1",
            FeedbackType.HELPFUL,
            metadata={"source": "test", "version": 1},
        )

        # Second reinforcement with different metadata
        tracker.reinforce(
            "entry-1",
            FeedbackType.HELPFUL,
            metadata={"version": 2, "extra": "data"},
        )

        counter = tracker.get_counter("entry-1")

        assert counter is not None
        assert counter.metadata == {"source": "test", "version": 2, "extra": "data"}

    @pytest.mark.unit
    def test_import_counters_skips_invalid_data(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test import_counters gracefully skips invalid data."""
        valid_data = {
            "entry_id": "valid-entry",
            "counters": {"helpful": 5, "harmful": 0, "neutral": 0},
        }
        invalid_data = {"missing_entry_id": True}

        tracker.import_counters([valid_data, invalid_data])

        # Should have imported only the valid entry
        assert len(tracker.get_all_counters()) == 1
        assert tracker.get_counter("valid-entry") is not None
