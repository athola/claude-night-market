#!/usr/bin/env python3
"""Context warning hook for two-tier MECW alerts.

This hook implements the two-tier context warning system:
- WARNING at 40% context usage
- CRITICAL at 50% context usage

The hook is triggered on PreToolUse events to monitor context pressure
and provide proactive optimization guidance.
"""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Threshold constants for two-tier MECW warnings
WARNING_THRESHOLD = 0.40
CRITICAL_THRESHOLD = 0.50


class ContextSeverity(Enum):
    """Severity levels for context usage alerts."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ContextAlert:
    """Represents a context usage alert with severity and recommendations."""

    severity: ContextSeverity
    usage_percent: float
    message: str
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert alert to dictionary for JSON serialization."""
        return {
            "severity": self.severity.value,
            "usage_percent": round(self.usage_percent * 100, 1),
            "message": self.message,
            "recommendations": self.recommendations,
        }


def assess_context_usage(usage: float) -> ContextAlert:
    """Assess context usage and return appropriate alert.

    Args:
        usage: Current context usage as a float between 0 and 1.

    Returns:
        ContextAlert with severity, message, and recommendations.
    """
    if usage >= CRITICAL_THRESHOLD:
        return ContextAlert(
            severity=ContextSeverity.CRITICAL,
            usage_percent=usage,
            message=f"CRITICAL: Context at {usage*100:.1f}% - Immediate optimization required!",
            recommendations=[
                "Summarize completed work immediately",
                "Delegate remaining tasks to subagents",
                "Consider /clear + /catchup workflow",
            ],
        )
    elif usage >= WARNING_THRESHOLD:
        return ContextAlert(
            severity=ContextSeverity.WARNING,
            usage_percent=usage,
            message=f"WARNING: Context at {usage*100:.1f}% - Plan optimization soon",
            recommendations=[
                "Monitor context growth rate",
                "Prepare optimization strategy",
                "Invoke Skill(conservation:optimize-context)",
            ],
        )
    return ContextAlert(
        severity=ContextSeverity.OK,
        usage_percent=usage,
        message=f"OK: Context at {usage*100:.1f}%",
        recommendations=[],
    )


def get_context_usage_from_env() -> float | None:
    """Attempt to get current context usage from environment.

    Returns:
        Context usage as float 0-1, or None if unavailable.
    """
    import os

    # Try to get from environment variable (set by Claude Code)
    usage_str = os.environ.get("CLAUDE_CONTEXT_USAGE")
    if usage_str:
        try:
            return float(usage_str)
        except ValueError:
            pass

    # Try to parse from stdin hook input
    return None


def format_hook_output(alert: ContextAlert) -> dict[str, Any]:
    """Format alert as hook-compatible output.

    Args:
        alert: The ContextAlert to format.

    Returns:
        Dictionary suitable for hook JSON output.
    """
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "contextWarning": alert.to_dict(),
        }
    }

    # Add additionalContext for WARNING and CRITICAL levels
    if alert.severity != ContextSeverity.OK:
        output["hookSpecificOutput"]["additionalContext"] = (
            f"{alert.message}\n\nRecommendations:\n"
            + "\n".join(f"- {rec}" for rec in alert.recommendations)
        )

    return output


def main() -> int:
    """Main entry point for hook execution.

    Returns:
        Exit code (0 for success).
    """
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    # Get context usage - try environment first, then hook input
    usage = get_context_usage_from_env()

    if usage is None:
        # Try to extract from hook input if provided
        usage = hook_input.get("context_usage")

    if usage is None:
        # No context usage available, output empty response
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse"}}))
        return 0

    # Assess context and generate alert
    alert = assess_context_usage(usage)

    # Only output for WARNING or CRITICAL
    if alert.severity == ContextSeverity.OK:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse"}}))
    else:
        print(json.dumps(format_hook_output(alert)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
