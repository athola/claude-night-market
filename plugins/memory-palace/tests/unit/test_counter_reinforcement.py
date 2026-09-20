"""Tests for counter-based reinforcement module.

Tests the ACE Playbook-inspired pattern where similar insights
increment counters rather than creating duplicates.
"""

from datetime import datetime, timezone

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
        before = datetime.now(timezone.utc)
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        counter = tracker.get_counter("entry-1")

        assert isinstance(counter, ReinforcementCounter)
        assert counter.last_accessed >= before

    @pytest.mark.unit
    def test_get_counter_returns_none_for_missing(
        self, tracker: CounterReinforcementTracker
    ) -> None:
        """Test get_counter returns None for unknown entry."""
        assert tracker.get_counter("nonexistent") is None

    @pytest.mark.unit
    def test_similarity_threshold_value(self) -> None:
        """Test SIMILARITY_THRESHOLD matches ACE research."""
        # ACE Playbook uses 0.8 cosine similarity threshold
        assert SIMILARITY_THRESHOLD == 0.8

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

        assert isinstance(counter, ReinforcementCounter)
        assert counter.metadata == {"source": "test", "version": 2, "extra": "data"}
