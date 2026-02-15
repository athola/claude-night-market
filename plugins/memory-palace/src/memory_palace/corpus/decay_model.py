"""Quality decay model for knowledge entries.

Implements time-based quality decay with different decay curves
based on entry maturity. Knowledge that isn't validated decays
over time, encouraging regular maintenance.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Status thresholds
STATUS_FRESH_THRESHOLD = 0.7
STATUS_STALE_THRESHOLD = 0.4
STATUS_CRITICAL_THRESHOLD = 0.2


class DecayCurve(Enum):
    """Types of decay curves."""

    LINEAR = "linear"  # Uniform decay over time
    EXPONENTIAL = "exponential"  # Classic half-life decay
    LOGARITHMIC = "logarithmic"  # Slow initial decay, accelerates later


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
    ) -> DecayState:
        """Calculate current decay state for an entry.

        Args:
            entry_id: The ID of the knowledge entry
            maturity: The maturity level (seedling, growing, evergreen)
            last_validated: When the entry was last validated

        Returns:
            DecayState with current decay metrics

        """
        now = datetime.now(UTC)

        # validate last_validated is timezone-aware
        if last_validated.tzinfo is None:
            last_validated = last_validated.replace(tzinfo=UTC)

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
            validation_date = datetime.now(UTC)
        elif validation_date.tzinfo is None:
            validation_date = validation_date.replace(tzinfo=UTC)

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
        entries: list[dict],
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
            entry_id = entry["id"]
            maturity = entry.get("maturity", "growing")

            # Get validation date
            validation_date = self._validation_dates.get(entry_id)
            if validation_date is None:
                # Use entry creation time or default to old date
                validation_date = datetime.now(UTC)

            state = self.calculate_decay(entry_id, maturity, validation_date)

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
