"""Quality decay model for knowledge entries.

Implements time-based quality decay with different decay curves
based on entry maturity. Knowledge that isn't validated decays
over time, encouraging regular maintenance.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Status thresholds
STATUS_FRESH_THRESHOLD = 0.7
STATUS_STALE_THRESHOLD = 0.4
STATUS_CRITICAL_THRESHOLD = 0.2


class DecayCurve(Enum):
    """Types of decay curves."""

    LINEAR = "linear"  # Uniform decay over time
    EXPONENTIAL = "exponential"  # Classic half-life decay
    LOGARITHMIC = "logarithmic"  # Fast initial decay, decelerates over time


DECAY_CONFIG: dict[str, dict] = {
    "seedling": {
        "half_life_days": 14,
        "curve": DecayCurve.EXPONENTIAL,
    },
    "growing": {
        "half_life_days": 30,
        "curve": DecayCurve.EXPONENTIAL,
    },
    "evergreen": {
        "half_life_days": 90,
        "curve": DecayCurve.LOGARITHMIC,
    },
}

# Importance classification (0-100 scale)
IMPORTANCE_CLASSES: dict[str, dict[str, Any]] = {
    "constitutional": {"min_score": 90, "decay_floor": 0.5},
    "architectural": {"min_score": 70, "decay_floor": 0.4},
    "significant": {"min_score": 50, "decay_floor": 0.3},
    "standard": {"min_score": 30, "decay_floor": 0.1},
    "ephemeral": {"min_score": 0, "decay_floor": 0.0},
}

DEFAULT_IMPORTANCE_SCORE = 40
MAX_IMPORTANCE_SCORE = 100
CONSTITUTIONAL_MIN_SCORE: int = IMPORTANCE_CLASSES["constitutional"]["min_score"]


def get_importance_class(score: int) -> str:
    """Classify an importance score into a named class.

    Args:
        score: Importance score, must be 0-100 inclusive.

    Raises:
        ValueError: If score is outside 0-100 range.

    """
    if not (0 <= score <= MAX_IMPORTANCE_SCORE):
        msg = f"importance_score must be 0-100, got {score}"
        raise ValueError(msg)
    for name, config in IMPORTANCE_CLASSES.items():
        if score >= config["min_score"]:
            return name
    return "ephemeral"


def get_decay_floor(score: int) -> float:
    """Get the decay floor for a given importance score."""
    cls = get_importance_class(score)
    floor: float = IMPORTANCE_CLASSES[cls]["decay_floor"]
    return floor


@dataclass
class DecayState:
    """Current decay state for a knowledge entry."""

    entry_id: str
    maturity: str
    decay_factor: float  # 0.0 to 1.0
    days_since_validation: int
    status: str  # "fresh", "stale", "critical", "archived"


class DecayModel:
    """Models quality decay for knowledge entries.

    Uses configurable decay curves based on entry maturity.
    Seedlings decay faster than evergreen entries.
    """

    def __init__(self) -> None:
        """Initialize the decay model."""
        self._validation_dates: dict[str, datetime] = {}

    def calculate_decay(
        self,
        entry_id: str,
        maturity: str,
        last_validated: datetime,
        importance_score: int | None = None,
    ) -> DecayState:
        """Calculate current decay state for an entry.

        Args:
            entry_id: The ID of the knowledge entry
            maturity: The maturity level (seedling, growing, evergreen)
            last_validated: When the entry was last validated
            importance_score: Importance score (0-100) for decay floor

        Returns:
            DecayState with current decay metrics

        """
        now = datetime.now(timezone.utc)

        # validate last_validated is timezone-aware
        if last_validated.tzinfo is None:
            last_validated = last_validated.replace(tzinfo=timezone.utc)

        delta = now - last_validated
        days_since = max(0, delta.days)

        # Get decay config for maturity level
        config = DECAY_CONFIG.get(maturity, DECAY_CONFIG["growing"])
        half_life = config["half_life_days"]
        curve = config["curve"]

        # Calculate decay factor
        decay_factor = self._apply_decay_curve(days_since, half_life, curve)

        # Clamp to valid range
        decay_factor = max(0.0, min(1.0, decay_factor))

        # Enforce importance-based decay floor
        if importance_score is None:
            importance_score = DEFAULT_IMPORTANCE_SCORE
        floor = get_decay_floor(importance_score)
        decay_factor = max(decay_factor, floor)

        # Determine status
        status = self._determine_status(decay_factor)

        return DecayState(
            entry_id=entry_id,
            maturity=maturity,
            decay_factor=decay_factor,
            days_since_validation=days_since,
            status=status,
        )

    def _apply_decay_curve(
        self,
        days: int,
        half_life: int,
        curve: DecayCurve,
    ) -> float:
        """Apply decay curve to calculate decay factor.

        Args:
            days: Days since last validation
            half_life: Half-life in days
            curve: Type of decay curve

        Returns:
            Decay factor between 0.0 and 1.0

        """
        if days <= 0:
            return 1.0

        if curve == DecayCurve.LINEAR:
            # Linear: reaches 0 at 2 * half_life
            max_days = half_life * 2
            return max(0.0, 1.0 - (days / max_days))

        if curve == DecayCurve.EXPONENTIAL:
            # Exponential: classic half-life formula
            # decay_factor = 0.5 ^ (days / half_life)
            return math.pow(0.5, days / half_life)

        if curve == DecayCurve.LOGARITHMIC:
            # Logarithmic: slower initial decay
            # Uses modified formula for slower decay
            if days >= half_life * 4:
                return 0.1  # Floor for very old entries
            # Slower decay using log curve
            ratio = days / half_life
            return 1.0 / (1.0 + math.log1p(ratio))

        # Default to exponential
        return math.pow(0.5, days / half_life)

    def _determine_status(self, decay_factor: float) -> str:
        """Determine status based on decay factor.

        Args:
            decay_factor: Current decay factor

        Returns:
            Status string

        """
        if decay_factor >= STATUS_FRESH_THRESHOLD:
            return "fresh"
        if decay_factor >= STATUS_STALE_THRESHOLD:
            return "stale"
        if decay_factor >= STATUS_CRITICAL_THRESHOLD:
            return "critical"
        return "archived"

    def validate_entry(
        self, entry_id: str, validation_date: datetime | None = None
    ) -> None:
        """Record that an entry has been validated.

        Args:
            entry_id: The ID of the knowledge entry
            validation_date: When validation occurred (defaults to now)

        """
        if validation_date is None:
            validation_date = datetime.now(timezone.utc)
        elif validation_date.tzinfo is None:
            validation_date = validation_date.replace(tzinfo=timezone.utc)

        self._validation_dates[entry_id] = validation_date

    def get_validation_date(self, entry_id: str) -> datetime | None:
        """Get the last validation date for an entry.

        Args:
            entry_id: The ID of the knowledge entry

        Returns:
            Last validation datetime or None if never validated

        """
        return self._validation_dates.get(entry_id)

    def get_stale_entries(
        self,
        entries: list[dict[str, Any]],
        threshold: float = STATUS_STALE_THRESHOLD,
    ) -> list[DecayState]:
        """Get entries with decay below threshold.

        Args:
            entries: List of entry dicts with 'id' and 'maturity' keys
            threshold: Decay threshold below which entries are returned

        Returns:
            List of DecayState for stale entries, sorted by decay (worst first)

        """
        stale: list[DecayState] = []

        for entry in entries:
            entry_id = entry.get("id", "")
            maturity = entry.get("maturity", "growing")
            importance_score = entry.get("importance_score", DEFAULT_IMPORTANCE_SCORE)

            # Constitutional entries never appear as stale
            if importance_score >= CONSTITUTIONAL_MIN_SCORE:
                continue

            # Get validation date
            last_validated = self._validation_dates.get(entry_id)
            if last_validated is None:
                last_validated = datetime.now(timezone.utc)

            state = self.calculate_decay(
                entry_id,
                maturity,
                last_validated,
                importance_score=importance_score,
            )

            if state.decay_factor < threshold:
                stale.append(state)

        # Sort by decay factor (worst first)
        stale.sort(key=lambda s: s.decay_factor)

        return stale

    def export_state(self) -> dict[str, str]:
        """Export validation state as serializable data.

        Returns:
            Dict of entry_id -> validation_date ISO string

        """
        return {
            entry_id: date.isoformat()
            for entry_id, date in self._validation_dates.items()
        }

    def import_state(self, state_data: dict[str, str]) -> None:
        """Import validation state from serializable data.

        Args:
            state_data: Dict of entry_id -> validation_date ISO string

        """
        for entry_id, date_str in state_data.items():
            try:
                self._validation_dates[entry_id] = datetime.fromisoformat(date_str)
            except ValueError:
                logger.warning(
                    "Skipping entry %s with invalid date format: %r",
                    entry_id,
                    date_str,
                )
