"""Usage-based knowledge scoring with RL signals.

Implements usage tracking and scoring for knowledge entries using
reinforcement learning signals. Each usage event contributes to
an entry's overall quality score.
"""

from __future__ import annotations

import logging
import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Score normalization constants
SCORE_SCALE_FACTOR = 10.0  # Scale for normalizing raw scores
SCORE_MIN = 0.0
SCORE_MAX = 1.0

# Event storage limit to prevent unbounded memory growth
MAX_EVENTS = 10000


class UsageSignal(Enum):
    """Types of usage signals that affect knowledge quality scores."""

    ACCESS = "access"  # Entry was accessed/read
    CITATION = "citation"  # Entry was cited in another context
    POSITIVE_FEEDBACK = "positive_feedback"  # User marked as helpful
    NEGATIVE_FEEDBACK = "negative_feedback"  # User marked as unhelpful
    CORRECTION = "correction"  # Entry was corrected/updated
    STALE_FLAG = "stale_flag"  # Entry marked as potentially outdated


SIGNAL_WEIGHTS: dict[UsageSignal, float] = {
    UsageSignal.ACCESS: 0.1,
    UsageSignal.CITATION: 0.3,
    UsageSignal.POSITIVE_FEEDBACK: 0.5,
    UsageSignal.NEGATIVE_FEEDBACK: -0.3,
    UsageSignal.CORRECTION: 0.2,
    UsageSignal.STALE_FLAG: -0.4,
}


@dataclass
class UsageEvent:
    """A single usage event for a knowledge entry."""

    entry_id: str
    signal: UsageSignal
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageScore:
    """Aggregated usage score for a knowledge entry."""

    entry_id: str
    raw_score: float
    normalized_score: float  # 0.0 to 1.0
    access_count: int
    citation_count: int
    feedback_balance: int  # positive - negative feedback count
    last_accessed: datetime | None
    decay_factor: float  # External decay factor (from DecayModel)


class UsageTracker:
    """Tracks usage events and calculates scores for knowledge entries.

    Implements reinforcement learning-style scoring where positive
    interactions increase quality scores and negative interactions
    decrease them.
    """

    def __init__(self, max_events: int = MAX_EVENTS) -> None:
        """Initialize the usage tracker.

        Args:
            max_events: Maximum number of events to retain (oldest discarded).

        """
        self._events: deque[UsageEvent] = deque(maxlen=max_events)
        self._event_handlers: list[Callable[[UsageEvent], None]] = []

    def record_event(
        self,
        entry_id: str,
        signal: UsageSignal,
        context: dict[str, Any] | None = None,
    ) -> UsageEvent:
        """Record a usage event for an entry.

        Args:
            entry_id: The ID of the knowledge entry
            signal: The type of usage signal
            context: Optional context metadata for the event

        Returns:
            The created UsageEvent

        """
        event = UsageEvent(
            entry_id=entry_id,
            signal=signal,
            timestamp=datetime.now(UTC),
            context=context or {},
        )
        self._events.append(event)

        # Notify handlers
        for handler in self._event_handlers:
            handler(event)

        return event

    def get_score(
        self,
        entry_id: str,
        decay_factor: float = 1.0,
    ) -> UsageScore:
        """Calculate the usage score for an entry.

        Args:
            entry_id: The ID of the knowledge entry
            decay_factor: External decay factor to incorporate

        Returns:
            UsageScore with aggregated metrics

        """
        events = [e for e in self._events if e.entry_id == entry_id]

        if not events:
            return UsageScore(
                entry_id=entry_id,
                raw_score=0.0,
                normalized_score=0.0,
                access_count=0,
                citation_count=0,
                feedback_balance=0,
                last_accessed=None,
                decay_factor=decay_factor,
            )

        # Calculate metrics
        raw_score = sum(SIGNAL_WEIGHTS[e.signal] for e in events)
        access_count = sum(1 for e in events if e.signal == UsageSignal.ACCESS)
        citation_count = sum(1 for e in events if e.signal == UsageSignal.CITATION)

        positive_feedback = sum(
            1 for e in events if e.signal == UsageSignal.POSITIVE_FEEDBACK
        )
        negative_feedback = sum(
            1 for e in events if e.signal == UsageSignal.NEGATIVE_FEEDBACK
        )
        feedback_balance = positive_feedback - negative_feedback

        # Find last access
        access_events = [e for e in events if e.signal == UsageSignal.ACCESS]
        last_accessed = max((e.timestamp for e in access_events), default=None)

        # Normalize score using sigmoid-like function
        normalized_score = self._normalize_score(raw_score)

        return UsageScore(
            entry_id=entry_id,
            raw_score=raw_score,
            normalized_score=normalized_score,
            access_count=access_count,
            citation_count=citation_count,
            feedback_balance=feedback_balance,
            last_accessed=last_accessed,
            decay_factor=decay_factor,
        )

    def _normalize_score(self, raw_score: float) -> float:
        """Normalize raw score to 0.0-1.0 range using sigmoid.

        Args:
            raw_score: The raw score to normalize

        Returns:
            Normalized score between 0.0 and 1.0

        """
        # Sigmoid normalization
        normalized = 1.0 / (1.0 + math.exp(-raw_score / SCORE_SCALE_FACTOR))

        # Clamp to range
        return max(SCORE_MIN, min(SCORE_MAX, normalized))

    def get_all_scores(
        self, decay_factors: dict[str, float] | None = None
    ) -> list[UsageScore]:
        """Get scores for all tracked entries.

        Args:
            decay_factors: Optional dict of entry_id -> decay_factor

        Returns:
            List of UsageScores for all entries

        """
        decay_factors = decay_factors or {}
        entry_ids = {e.entry_id for e in self._events}
        return [
            self.get_score(entry_id, decay_factors.get(entry_id, 1.0))
            for entry_id in entry_ids
        ]

    def get_events(
        self,
        entry_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[UsageEvent]:
        """Get events for a specific entry.

        Args:
            entry_id: The ID of the knowledge entry
            since: Optional start time filter
            until: Optional end time filter

        Returns:
            List of matching UsageEvents

        """
        events = [e for e in self._events if e.entry_id == entry_id]

        if since:
            events = [e for e in events if e.timestamp >= since]
        if until:
            events = [e for e in events if e.timestamp <= until]

        return events

    def clear_events(self, entry_id: str) -> None:
        """Clear all events for an entry.

        Args:
            entry_id: The ID of the knowledge entry

        """
        max_events = self._events.maxlen
        self._events = deque(
            (e for e in self._events if e.entry_id != entry_id),
            maxlen=max_events,
        )

    def add_event_handler(self, handler: Callable[[UsageEvent], None]) -> None:
        """Add a handler to be called on new events.

        Args:
            handler: Callback function for events

        """
        self._event_handlers.append(handler)

    def export_events(self) -> list[dict[str, Any]]:
        """Export all events as serializable data.

        Returns:
            List of event dictionaries

        """
        return [
            {
                "entry_id": e.entry_id,
                "signal": e.signal.value,
                "timestamp": e.timestamp.isoformat(),
                "context": e.context,
            }
            for e in self._events
        ]

    def import_events(self, events_data: list[dict[str, Any]]) -> None:
        """Import events from serializable data.

        Args:
            events_data: List of event dictionaries

        """
        for data in events_data:
            try:
                event = UsageEvent(
                    entry_id=data["entry_id"],
                    signal=UsageSignal(data["signal"]),
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    context=data.get("context", {}),
                )
                self._events.append(event)
            except (ValueError, KeyError) as e:
                logger.warning(
                    "Skipping event with invalid data: %r (error: %s)",
                    data,
                    e,
                )
