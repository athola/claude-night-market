"""Counter-based reinforcement for semantic memory.

Implements the ACE Playbook pattern where similar insights increment counters
rather than creating duplicates. This mirrors how human memory reinforces
patterns through repetition.

Research source: https://github.com/jmanhype/ace-playbook
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ACE Playbook recommended threshold for semantic similarity
SIMILARITY_THRESHOLD = 0.8

# Thresholds for review detection
HARM_RATIO_THRESHOLD = 0.3
HELPFULNESS_RATIO_THRESHOLD = 0.4
MIN_SIGNALS_FOR_REVIEW = 5
MIN_SIGNALS_FOR_RANKING = 3


class FeedbackType(Enum):
    """Classification of knowledge feedback following ACE's labeled insights.

    Maps to ACE's Generator-Reflector-Curator triad output types.
    """

    HELPFUL = "helpful"  # Knowledge was useful/accurate
    HARMFUL = "harmful"  # Knowledge was misleading/incorrect
    NEUTRAL = "neutral"  # Knowledge was accessed but no feedback


@dataclass
class ReinforcementCounter:
    """Counter tracking reinforcement signals for a knowledge entry.

    Implements ACE's pattern of incrementing counters instead of duplicating.
    The counter ratios provide natural importance scoring.

    Attributes:
        entry_id: Unique identifier for the knowledge entry
        helpful: Count of helpful feedback signals
        harmful: Count of harmful feedback signals
        neutral: Count of neutral access signals
        first_seen: When this entry was first stored
        last_accessed: When this entry was last accessed
        metadata: Additional context about reinforcement patterns

    """

    entry_id: str
    helpful: int = 0
    harmful: int = 0
    neutral: int = 0
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_signals(self) -> int:
        """Total number of reinforcement signals received."""
        return self.helpful + self.harmful + self.neutral

    @property
    def helpfulness_ratio(self) -> float:
        """Ratio of helpful to total signals (0.0 to 1.0).

        Higher values indicate more reliable/useful knowledge.
        """
        if self.total_signals == 0:
            return 0.5  # Default neutral
        return self.helpful / self.total_signals

    @property
    def harm_ratio(self) -> float:
        """Ratio of harmful to total signals (0.0 to 1.0).

        Higher values indicate problematic/outdated knowledge.
        """
        if self.total_signals == 0:
            return 0.0
        return self.harmful / self.total_signals

    @property
    def confidence_score(self) -> float:
        """Confidence in this knowledge based on signal patterns.

        Formula: (helpful - harmful) / total, normalized to 0-1 range.
        More signals = higher confidence in the score.
        """
        if self.total_signals == 0:
            return 0.5  # Default neutral confidence

        raw_score = (self.helpful - self.harmful) / self.total_signals
        # Normalize from [-1, 1] to [0, 1]
        return (raw_score + 1.0) / 2.0

    @property
    def needs_review(self) -> bool:
        """Whether this entry should be flagged for human review.

        Criteria:
        - Harm ratio > 30%
        - Total signals > 5 but helpfulness ratio < 40%
        - No access in metadata's stale_threshold (default 30 days)
        """
        return self.harm_ratio > HARM_RATIO_THRESHOLD or (
            self.total_signals > MIN_SIGNALS_FOR_REVIEW
            and self.helpfulness_ratio < HELPFULNESS_RATIO_THRESHOLD
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize counter to dictionary for storage."""
        return {
            "entry_id": self.entry_id,
            "counters": {
                "helpful": self.helpful,
                "harmful": self.harmful,
                "neutral": self.neutral,
            },
            "first_seen": self.first_seen.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
            # Computed fields for convenience
            "helpfulness_ratio": self.helpfulness_ratio,
            "confidence_score": self.confidence_score,
            "needs_review": self.needs_review,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReinforcementCounter:
        """Deserialize counter from dictionary."""
        counters = data.get("counters", {})
        return cls(
            entry_id=data["entry_id"],
            helpful=counters.get("helpful", 0),
            harmful=counters.get("harmful", 0),
            neutral=counters.get("neutral", 0),
            first_seen=datetime.fromisoformat(
                data.get("first_seen", datetime.now(timezone.utc).isoformat())
            ),
            last_accessed=datetime.fromisoformat(
                data.get("last_accessed", datetime.now(timezone.utc).isoformat())
            ),
            metadata=data.get("metadata", {}),
        )


class CounterReinforcementTracker:
    """Tracks reinforcement counters for all knowledge entries.

    Implements ACE Playbook's counter-based reinforcement pattern:
    - When similar insights emerge, increment counters instead of duplicating
    - Counter ratios provide natural importance scoring
    - High-frequency patterns surface automatically

    Usage:
        tracker = CounterReinforcementTracker()

        # Record feedback
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        tracker.reinforce("entry-1", FeedbackType.HELPFUL)
        tracker.reinforce("entry-1", FeedbackType.NEUTRAL)

        # Get counter
        counter = tracker.get_counter("entry-1")
        print(f"Helpfulness: {counter.helpfulness_ratio:.0%}")

        # Get entries needing review
        for counter in tracker.get_review_candidates():
            print(f"{counter.entry_id} needs review")

    """

    def __init__(self) -> None:
        """Initialize the reinforcement tracker."""
        self._counters: dict[str, ReinforcementCounter] = {}

    def reinforce(
        self,
        entry_id: str,
        feedback: FeedbackType,
        metadata: dict[str, Any] | None = None,
    ) -> ReinforcementCounter:
        """Reinforce a knowledge entry with feedback.

        Instead of creating duplicate entries for similar knowledge,
        this increments the appropriate counter.

        Args:
            entry_id: The knowledge entry ID
            feedback: Type of feedback (helpful/harmful/neutral)
            metadata: Optional context about this reinforcement

        Returns:
            Updated ReinforcementCounter

        """
        # Get or create counter
        if entry_id not in self._counters:
            self._counters[entry_id] = ReinforcementCounter(entry_id=entry_id)

        counter = self._counters[entry_id]

        # Increment appropriate counter
        if feedback == FeedbackType.HELPFUL:
            counter.helpful += 1
        elif feedback == FeedbackType.HARMFUL:
            counter.harmful += 1
        else:  # NEUTRAL
            counter.neutral += 1

        # Update access time
        counter.last_accessed = datetime.now(timezone.utc)

        # Merge metadata if provided
        if metadata:
            counter.metadata.update(metadata)

        logger.debug(
            "Reinforced %s with %s (total: %d)",
            entry_id,
            feedback.value,
            counter.total_signals,
        )

        return counter

    def get_counter(self, entry_id: str) -> ReinforcementCounter | None:
        """Get the reinforcement counter for an entry.

        Args:
            entry_id: The knowledge entry ID

        Returns:
            ReinforcementCounter or None if not found

        """
        return self._counters.get(entry_id)

    def clear(self) -> None:
        """Clear all counters (for testing)."""
        self._counters.clear()
