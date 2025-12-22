"""Tests for usage-based knowledge scoring with RL signals.

Tests the UsageTracker which implements usage-based scoring with
reinforcement learning signals for knowledge entries.
"""

from datetime import UTC, datetime, timedelta

import pytest
from memory_palace.corpus.usage_tracker import (
    SIGNAL_WEIGHTS,
    UsageEvent,
    UsageScore,
    UsageSignal,
    UsageTracker,
)


class TestUsageSignal:
    """Test UsageSignal enum and weights."""

    def test_all_signals_have_weights(self) -> None:
        """Every signal type should have a defined weight."""
        for signal in UsageSignal:
            assert signal in SIGNAL_WEIGHTS

    def test_signal_weight_ranges(self) -> None:
        """Weights should be in reasonable range (-1.0 to 1.0)."""
        for signal, weight in SIGNAL_WEIGHTS.items():
            assert -1.0 <= weight <= 1.0, f"{signal} weight {weight} out of range"

    def test_positive_signals(self) -> None:
        """Access, citation, positive feedback should have positive weights."""
        assert SIGNAL_WEIGHTS[UsageSignal.ACCESS] > 0
        assert SIGNAL_WEIGHTS[UsageSignal.CITATION] > 0
        assert SIGNAL_WEIGHTS[UsageSignal.POSITIVE_FEEDBACK] > 0
        assert SIGNAL_WEIGHTS[UsageSignal.CORRECTION] > 0

    def test_negative_signals(self) -> None:
        """Negative feedback and stale flag should have negative weights."""
        assert SIGNAL_WEIGHTS[UsageSignal.NEGATIVE_FEEDBACK] < 0
        assert SIGNAL_WEIGHTS[UsageSignal.STALE_FLAG] < 0


class TestUsageEvent:
    """Test UsageEvent dataclass."""

    def test_create_event(self) -> None:
        """Should create event with entry_id and signal."""
        event = UsageEvent(
            entry_id="test-entry-1",
            signal=UsageSignal.ACCESS,
        )
        assert event.entry_id == "test-entry-1"
        assert event.signal == UsageSignal.ACCESS
        assert isinstance(event.timestamp, datetime)
        assert event.context == {}

    def test_event_with_context(self) -> None:
        """Should allow context metadata."""
        event = UsageEvent(
            entry_id="test-entry-2",
            signal=UsageSignal.CITATION,
            context={"cited_by": "article-123", "section": "examples"},
        )
        assert event.context["cited_by"] == "article-123"


class TestUsageScore:
    """Test UsageScore dataclass."""

    def test_score_fields(self) -> None:
        """Should contain all required fields."""
        score = UsageScore(
            entry_id="test-1",
            raw_score=5.5,
            normalized_score=0.75,
            access_count=10,
            citation_count=3,
            feedback_balance=2,
            last_accessed=datetime.now(UTC),
            decay_factor=0.9,
        )
        assert score.entry_id == "test-1"
        assert score.raw_score == 5.5
        assert 0.0 <= score.normalized_score <= 1.0
        assert score.access_count == 10
        assert score.citation_count == 3


class TestUsageTracker:
    """Test UsageTracker functionality."""

    @pytest.fixture
    def tracker(self) -> UsageTracker:
        """Create a fresh UsageTracker instance."""
        return UsageTracker()

    def test_record_event(self, tracker: UsageTracker) -> None:
        """Should record usage events."""
        event = tracker.record_event("entry-1", UsageSignal.ACCESS)
        assert event.entry_id == "entry-1"
        assert event.signal == UsageSignal.ACCESS

    def test_record_event_with_context(self, tracker: UsageTracker) -> None:
        """Should record events with context."""
        event = tracker.record_event(
            "entry-1",
            UsageSignal.CITATION,
            context={"cited_by": "article-456"},
        )
        assert event.context["cited_by"] == "article-456"

    def test_get_score_no_events(self, tracker: UsageTracker) -> None:
        """Should return zero score for entries with no events."""
        score = tracker.get_score("nonexistent-entry")
        assert score.raw_score == 0.0
        assert score.normalized_score == 0.0
        assert score.access_count == 0
        assert score.citation_count == 0

    def test_get_score_with_events(self, tracker: UsageTracker) -> None:
        """Should calculate score from events."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-1", UsageSignal.CITATION)

        score = tracker.get_score("entry-1")
        expected_raw = (
            2 * SIGNAL_WEIGHTS[UsageSignal.ACCESS]
            + SIGNAL_WEIGHTS[UsageSignal.CITATION]
        )
        assert score.raw_score == pytest.approx(expected_raw)
        assert score.access_count == 2
        assert score.citation_count == 1

    def test_get_score_mixed_signals(self, tracker: UsageTracker) -> None:
        """Should handle positive and negative signals."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-1", UsageSignal.POSITIVE_FEEDBACK)
        tracker.record_event("entry-1", UsageSignal.NEGATIVE_FEEDBACK)

        score = tracker.get_score("entry-1")
        expected_raw = (
            SIGNAL_WEIGHTS[UsageSignal.ACCESS]
            + SIGNAL_WEIGHTS[UsageSignal.POSITIVE_FEEDBACK]
            + SIGNAL_WEIGHTS[UsageSignal.NEGATIVE_FEEDBACK]
        )
        assert score.raw_score == pytest.approx(expected_raw)

    def test_normalized_score_range(self, tracker: UsageTracker) -> None:
        """Normalized score should be between 0.0 and 1.0."""
        # Add many positive events
        for _ in range(100):
            tracker.record_event("entry-1", UsageSignal.POSITIVE_FEEDBACK)

        score = tracker.get_score("entry-1")
        assert 0.0 <= score.normalized_score <= 1.0

        # Add many negative events
        for _ in range(200):
            tracker.record_event("entry-2", UsageSignal.NEGATIVE_FEEDBACK)

        score2 = tracker.get_score("entry-2")
        assert 0.0 <= score2.normalized_score <= 1.0

    def test_feedback_balance(self, tracker: UsageTracker) -> None:
        """Should track positive vs negative feedback balance."""
        tracker.record_event("entry-1", UsageSignal.POSITIVE_FEEDBACK)
        tracker.record_event("entry-1", UsageSignal.POSITIVE_FEEDBACK)
        tracker.record_event("entry-1", UsageSignal.NEGATIVE_FEEDBACK)

        score = tracker.get_score("entry-1")
        assert score.feedback_balance == 1  # 2 positive - 1 negative

    def test_last_accessed_tracking(self, tracker: UsageTracker) -> None:
        """Should track last access time."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        score = tracker.get_score("entry-1")
        assert score.last_accessed is not None

    def test_get_all_scores(self, tracker: UsageTracker) -> None:
        """Should return scores for all tracked entries."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-2", UsageSignal.CITATION)
        tracker.record_event("entry-3", UsageSignal.POSITIVE_FEEDBACK)

        all_scores = tracker.get_all_scores()
        assert len(all_scores) == 3
        assert any(s.entry_id == "entry-1" for s in all_scores)
        assert any(s.entry_id == "entry-2" for s in all_scores)
        assert any(s.entry_id == "entry-3" for s in all_scores)

    def test_get_events_for_entry(self, tracker: UsageTracker) -> None:
        """Should retrieve all events for a specific entry."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-1", UsageSignal.CITATION)
        tracker.record_event("entry-2", UsageSignal.ACCESS)

        events = tracker.get_events("entry-1")
        assert len(events) == 2
        assert all(e.entry_id == "entry-1" for e in events)

    def test_get_events_time_range(self, tracker: UsageTracker) -> None:
        """Should filter events by time range."""
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)

        # Record events manually with different timestamps
        tracker._events.append(
            UsageEvent(
                entry_id="entry-1", signal=UsageSignal.ACCESS, timestamp=yesterday
            )
        )
        tracker._events.append(
            UsageEvent(entry_id="entry-1", signal=UsageSignal.CITATION, timestamp=now)
        )

        recent_events = tracker.get_events(
            "entry-1",
            since=now - timedelta(hours=1),
        )
        assert len(recent_events) == 1
        assert recent_events[0].signal == UsageSignal.CITATION

    def test_clear_events(self, tracker: UsageTracker) -> None:
        """Should allow clearing events for an entry."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-1", UsageSignal.CITATION)

        tracker.clear_events("entry-1")
        score = tracker.get_score("entry-1")
        assert score.raw_score == 0.0

    def test_decay_factor_integration(self, tracker: UsageTracker) -> None:
        """Should integrate external decay factor into score."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)

        score_with_decay = tracker.get_score("entry-1", decay_factor=0.5)
        assert score_with_decay.decay_factor == 0.5

    def test_export_events(self, tracker: UsageTracker) -> None:
        """Should export events as serializable data."""
        tracker.record_event("entry-1", UsageSignal.ACCESS)
        tracker.record_event("entry-1", UsageSignal.CITATION)

        exported = tracker.export_events()
        assert isinstance(exported, list)
        assert len(exported) == 2
        assert all("entry_id" in e for e in exported)
        assert all("signal" in e for e in exported)
        assert all("timestamp" in e for e in exported)

    def test_import_events(self, tracker: UsageTracker) -> None:
        """Should import events from serializable data."""
        events_data = [
            {
                "entry_id": "entry-1",
                "signal": "access",
                "timestamp": datetime.now(UTC).isoformat(),
                "context": {},
            },
            {
                "entry_id": "entry-2",
                "signal": "citation",
                "timestamp": datetime.now(UTC).isoformat(),
                "context": {"cited_by": "test"},
            },
        ]

        tracker.import_events(events_data)
        assert len(tracker.get_events("entry-1")) == 1
        assert len(tracker.get_events("entry-2")) == 1
