"""Maximum Effective Context Window (MECW) utilities.

This module provides utilities for managing context window usage according to
MECW principles, which prevent hallucinations by maintaining context usage
below critical thresholds.

The core principle: Never use more than 50% of total context window for input.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Constants for context management
MAX_HISTORY_LENGTH = 10
GROWTH_CHECK_MINIMUM = 3
GROWTH_WARNING_PERCENTAGE = 0.1

# MECW threshold levels
MECW_THRESHOLDS = {
    "LOW": 0.30,  # < 30%: Optimal performance, high accuracy
    "MODERATE": 0.50,  # 30-50%: Good performance, within MECW limits
    "HIGH": 0.70,  # 50-70%: Degraded performance, risk zone
    "CRITICAL": 0.95,  # > 70%: Severe degradation, high hallucination risk
}


def calculate_context_pressure(current_tokens: int, max_tokens: int) -> str:
    """Calculate context pressure level based on usage ratio.

    Context pressure increases non-linearly as usage approaches limits.
    This function categorizes the current usage into four levels.

    Args:
        current_tokens: Current token count in context
        max_tokens: Maximum available tokens in context window

    Returns:
        Pressure level: "LOW", "MODERATE", "HIGH", or "CRITICAL"

    Examples:
        >>> calculate_context_pressure(30000, 200000)
        'LOW'
        >>> calculate_context_pressure(100000, 200000)
        'MODERATE'
        >>> calculate_context_pressure(150000, 200000)
        'HIGH'
        >>> calculate_context_pressure(180000, 200000)
        'CRITICAL'

    """
    if max_tokens <= 0:
        return "CRITICAL"

    usage_ratio = current_tokens / max_tokens

    if usage_ratio < MECW_THRESHOLDS["LOW"]:
        return "LOW"  # Plenty of headroom
    if usage_ratio < MECW_THRESHOLDS["MODERATE"]:
        return "MODERATE"  # Within MECW limits
    if usage_ratio < MECW_THRESHOLDS["HIGH"]:
        return "HIGH"  # Exceeding MECW, risk zone
    return "CRITICAL"  # Severe hallucination risk


def check_mecw_compliance(
    current_tokens: int,
    max_tokens: int = 200000,
) -> dict[str, Any]:
    """Check if current token usage complies with MECW principles.

    The Maximum Effective Context Window (MECW) threshold is 50% of the
    total context window. Exceeding this increases hallucination risk.

    Args:
        current_tokens: Current token count in context
        max_tokens: Maximum available tokens (default: 200000 for Sonnet)

    Returns:
        Dictionary containing:
            - compliant: bool - Whether usage is within MECW limits
            - usage_ratio: float - Current usage as percentage (0-100)
            - pressure_level: str - Current pressure level
            - mecw_threshold: int - The 50% MECW threshold in tokens
            - overage: int - Tokens over MECW threshold (0 if compliant)
            - action: str - Recommended action based on status
            - headroom: int - Tokens remaining before MECW threshold

    Examples:
        >>> result = check_mecw_compliance(80000, 200000)
        >>> result['compliant']
        True
        >>> result['pressure_level']
        'MODERATE'

        >>> result = check_mecw_compliance(120000, 200000)
        >>> result['compliant']
        False
        >>> result['action']
        'immediate_optimization_required'

    """
    mecw_threshold = int(max_tokens * MECW_THRESHOLDS["MODERATE"])
    pressure_level = calculate_context_pressure(current_tokens, max_tokens)
    compliant = current_tokens <= mecw_threshold
    usage_ratio = (current_tokens / max_tokens * 100) if max_tokens > 0 else 100.0
    overage = max(0, current_tokens - mecw_threshold)
    headroom = max(0, mecw_threshold - current_tokens)

    # Determine recommended action
    if pressure_level == "CRITICAL":
        action = "immediate_context_reset_required"
    elif pressure_level == "HIGH":
        action = "immediate_optimization_required"
    elif pressure_level == "MODERATE" and not compliant:
        action = "optimize_before_next_operation"
    elif pressure_level == "MODERATE":
        action = "monitor_closely"
    else:
        action = "continue_normally"

    return {
        "compliant": compliant,
        "usage_ratio": round(usage_ratio, 2),
        "pressure_level": pressure_level,
        "mecw_threshold": mecw_threshold,
        "overage": overage,
        "action": action,
        "headroom": headroom,
        "current_tokens": current_tokens,
        "max_tokens": max_tokens,
    }


@dataclass
class MECWStatus:
    """Status result from MECW monitoring."""

    compliant: bool
    pressure_level: str
    usage_ratio: float
    headroom: int
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class MECWMonitor:
    """Monitor context window usage according to MECW principles.

    This class provides continuous monitoring of context usage with
    configurable thresholds and automatic recommendation generation.

    Attributes:
        max_context: Maximum context window size in tokens
        mecw_threshold: The 50% MECW threshold in tokens
        current_tokens: Current token count (updated via track_usage)

    Examples:
        >>> monitor = MECWMonitor(max_context=200000)
        >>> monitor.track_usage(80000)
        >>> status = monitor.get_status()
        >>> status.compliant
        True
        >>> status.pressure_level
        'MODERATE'

    """

    def __init__(self, max_context: int = 200000) -> None:
        """Initialize MECW monitor.

        Args:
            max_context: Maximum context window size (default: 200000)

        """
        self.max_context = max_context
        self.mecw_threshold = int(max_context * MECW_THRESHOLDS["MODERATE"])
        self.current_tokens = 0
        self._usage_history: list[int] = []

    def track_usage(self, tokens: int) -> None:
        """Track current token usage.

        Args:
            tokens: Current token count in context

        """
        self.current_tokens = tokens
        self._usage_history.append(tokens)

        # Keep only recent history (last 10 measurements)
        if len(self._usage_history) > MAX_HISTORY_LENGTH:
            self._usage_history = self._usage_history[-MAX_HISTORY_LENGTH:]

    def get_status(self) -> MECWStatus:
        """Get current MECW compliance status.

        Returns:
            MECWStatus object with compliance info and recommendations

        """
        compliance = check_mecw_compliance(self.current_tokens, self.max_context)

        warnings = []
        recommendations = []

        # Generate warnings based on pressure level
        if compliance["pressure_level"] == "CRITICAL":
            warnings.append(
                f"CRITICAL: Context at {compliance['usage_ratio']:.1f}% - "
                f"high hallucination risk",
            )
            recommendations.append("Execute context reset immediately")
            recommendations.append("Use /clear command or restart session")
        elif compliance["pressure_level"] == "HIGH":
            warnings.append(
                f"HIGH: Context at {compliance['usage_ratio']:.1f}% - "
                f"exceeding MECW limits",
            )
            recommendations.append("Optimize context before next operation")
            recommendations.append("Consider using subagents for complex tasks")
        elif compliance["pressure_level"] == "MODERATE" and not compliance["compliant"]:
            warnings.append(
                f"Approaching MECW limit: "
                f"{compliance['overage']:,} tokens over threshold",
            )
            recommendations.append("Monitor context usage closely")
            recommendations.append("Plan context optimization strategy")

        # Check for rapid growth
        if len(self._usage_history) >= GROWTH_CHECK_MINIMUM:
            idx = -GROWTH_CHECK_MINIMUM
            recent_growth = self._usage_history[-1] - self._usage_history[idx]
            growth_threshold = self.max_context * GROWTH_WARNING_PERCENTAGE
            if recent_growth > growth_threshold:  # >10% growth in 3 checks
                warnings.append(
                    f"Rapid context growth detected: +{recent_growth:,} tokens",
                )
                recommendations.append("Review context consumption patterns")

        return MECWStatus(
            compliant=compliance["compliant"],
            pressure_level=compliance["pressure_level"],
            usage_ratio=compliance["usage_ratio"],
            headroom=compliance["headroom"],
            warnings=warnings,
            recommendations=recommendations,
        )

    def can_handle_additional(self, additional_tokens: int) -> tuple[bool, list[str]]:
        """Check if additional tokens can be added while staying MECW-compliant.

        Args:
            additional_tokens: Number of tokens to potentially add

        Returns:
            Tuple of (can_proceed, list of issues)

        """
        projected_tokens = self.current_tokens + additional_tokens
        compliance = check_mecw_compliance(projected_tokens, self.max_context)

        issues = []

        if not compliance["compliant"]:
            issues.append(
                f"Would exceed MECW threshold by {compliance['overage']:,} tokens",
            )

        if compliance["pressure_level"] == "CRITICAL":
            issues.append("Would push context into CRITICAL zone")

        if compliance["pressure_level"] == "HIGH":
            issues.append("Would push context into HIGH pressure zone")

        return len(issues) == 0, issues

    def get_safe_budget(self) -> int:
        """Get the safe token budget remaining before MECW threshold.

        Returns:
            Number of tokens that can be safely added

        """
        return max(0, self.mecw_threshold - self.current_tokens)

    def reset(self) -> None:
        """Reset the monitor (typically after context clear)."""
        self.current_tokens = 0
        self._usage_history.clear()
