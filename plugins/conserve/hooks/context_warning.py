#!/usr/bin/env python3
"""Context warning hook for three-tier MECW alerts with auto-clear support.

This hook implements the three-tier context warning system:
- WARNING at 40% context usage
- CRITICAL at 50% context usage
- EMERGENCY at 80% context usage (triggers auto-clear workflow)

The hook is triggered on PreToolUse events to monitor context pressure
and provide proactive optimization guidance. At EMERGENCY level, it
recommends invoking the clear-context skill for automatic continuation.

Environment variables:
- CLAUDE_CONTEXT_USAGE: Context usage as float 0-1 (set by Claude Code)
- CONSERVE_EMERGENCY_THRESHOLD: Override default 80% emergency threshold
- CONSERVE_SESSION_STATE_PATH: Override default .claude/session-state.md
- CONSERVE_CONTEXT_ESTIMATION: Enable fallback estimation (default: 1)
- CONSERVE_CONTEXT_WINDOW_BYTES: Estimated context window in bytes (default: 800000)
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging for hook diagnostics
logging.basicConfig(level=logging.WARNING, format="%(name)s: %(message)s")
logger = logging.getLogger("context_warning")

# Threshold constants for three-tier MECW warnings
WARNING_THRESHOLD = 0.40
CRITICAL_THRESHOLD = 0.50
# Emergency threshold is configurable via environment variable
EMERGENCY_THRESHOLD = float(os.environ.get("CONSERVE_EMERGENCY_THRESHOLD", "0.80"))


class ContextSeverity(Enum):
    """Severity levels for context usage alerts."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


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

    Raises:
        ValueError: If usage is not in the valid 0-1 range.

    """
    if not 0.0 <= usage <= 1.0:
        raise ValueError(f"context_usage must be between 0 and 1, got {usage}")

    # EMERGENCY level - auto-clear workflow required
    if usage >= EMERGENCY_THRESHOLD:
        return ContextAlert(
            severity=ContextSeverity.EMERGENCY,
            usage_percent=usage,
            message=(
                f"EMERGENCY: Context at {usage * 100:.1f}% - "
                "AUTO-CLEAR REQUIRED! Execute clear-context workflow NOW."
            ),
            recommendations=[
                "Complete current in-progress work",
                "Commit any pending changes",
                "Summarize remaining tasks in your response",
                "Session will auto-compact if needed - work is not lost",
            ],
        )
    # CRITICAL level - immediate optimization needed
    elif usage >= CRITICAL_THRESHOLD:
        return ContextAlert(
            severity=ContextSeverity.CRITICAL,
            usage_percent=usage,
            message=(
                f"CRITICAL: Context at {usage * 100:.1f}% - "
                "Immediate optimization required!"
            ),
            recommendations=[
                "Summarize completed work immediately",
                "Delegate remaining tasks to subagents",
                "Prepare for clear-context workflow if usage continues to grow",
            ],
        )
    # WARNING level - plan optimization
    elif usage >= WARNING_THRESHOLD:
        return ContextAlert(
            severity=ContextSeverity.WARNING,
            usage_percent=usage,
            message=f"WARNING: Context at {usage * 100:.1f}% - Plan optimization soon",
            recommendations=[
                "Monitor context growth rate",
                "Prepare optimization strategy",
                "Invoke Skill(conserve:context-optimization) if needed",
            ],
        )
    # OK level - no action needed
    return ContextAlert(
        severity=ContextSeverity.OK,
        usage_percent=usage,
        message=f"OK: Context at {usage * 100:.1f}%",
        recommendations=[],
    )


def estimate_context_from_session() -> float | None:
    """Estimate context usage from current session's JSONL file size.

    This is a FAST fallback for real-time hooks when CLAUDE_CONTEXT_USAGE
    is not available. Estimates based on conversation history file size.

    Note: For more precise context reading in batch/headless scenarios,
    use the CLI method instead:
        claude -p "/context" --verbose --output-format json
    See: plugins/conserve/commands/optimize-context.md

    Returns:
        Estimated context usage as float 0-1, or None if cannot estimate.
    """
    # Check if estimation is disabled
    if os.environ.get("CONSERVE_CONTEXT_ESTIMATION", "1") == "0":
        return None

    # Claude's context window is ~200K tokens, ~4 chars/token = ~800KB
    # Use conservative estimate to trigger earlier rather than later
    context_window_bytes = int(
        os.environ.get("CONSERVE_CONTEXT_WINDOW_BYTES", "800000")
    )

    try:
        # Find Claude's project directory for current working directory
        cwd = Path.cwd()
        home = Path.home()
        claude_projects = home / ".claude" / "projects"

        if not claude_projects.exists():
            return None

        # Convert cwd to Claude's project directory naming convention
        # e.g., /home/user/my-project -> -home-user-my-project
        project_dir_name = str(cwd).replace("/", "-")
        if project_dir_name.startswith("-"):
            project_dir_name = project_dir_name[1:]
        project_dir_name = "-" + project_dir_name

        project_dir = claude_projects / project_dir_name
        if not project_dir.exists():
            return None

        # Find most recently modified JSONL file (current session)
        jsonl_files = list(project_dir.glob("*.jsonl"))
        if not jsonl_files:
            return None

        # Get the most recent file by modification time
        current_session = max(jsonl_files, key=lambda f: f.stat().st_mtime)
        file_size = current_session.stat().st_size

        # Estimate usage as percentage of context window
        # Cap at 0.95 to leave room for estimation error
        usage = min(file_size / context_window_bytes, 0.95)

        logger.debug(
            "Estimated context from %s: %d bytes = %.1f%%",
            current_session.name,
            file_size,
            usage * 100,
        )
        return usage

    except (OSError, PermissionError) as e:
        logger.debug("Could not estimate context from session files: %s", e)
        return None


def get_context_usage_from_env() -> float | None:
    """Attempt to get current context usage from environment.

    Returns:
        Context usage as float 0-1, or None if unavailable.

    """
    # Try to get from environment variable (set by Claude Code)
    usage_str = os.environ.get("CLAUDE_CONTEXT_USAGE")
    if usage_str:
        try:
            return float(usage_str)
        except ValueError:
            logger.warning(
                "Invalid CLAUDE_CONTEXT_USAGE value: %r (expected float)", usage_str
            )

    # Fallback: estimate from session file size
    return estimate_context_from_session()


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
    """Execute hook entry point.

    Returns:
        Exit code (0 for success).

    """
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse hook input as JSON: %s", e)
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
    try:
        alert = assess_context_usage(usage)
    except ValueError as e:
        logger.warning("Invalid context usage value: %s", e)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse"}}))
        return 0

    # Only output for WARNING, CRITICAL, or EMERGENCY
    if alert.severity == ContextSeverity.OK:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse"}}))
    else:
        output = format_hook_output(alert)
        # For EMERGENCY level, trigger mandatory auto-continuation
        if alert.severity == ContextSeverity.EMERGENCY:
            output["hookSpecificOutput"]["additionalContext"] = (
                "**MANDATORY AUTO-CONTINUATION TRIGGERED**\n\n"
                f"{alert.message}\n\n"
                "**YOU MUST EXECUTE THIS NOW** (not optional):\n\n"
                "```\n"
                "1. Write session state to .claude/session-state.md with:\n"
                "   - Current task objective\n"
                "   - Progress summary\n"
                "   - Remaining work\n"
                "   - execution_mode: unattended, auto_continue: true\n\n"
                "2. Spawn continuation agent with Task tool:\n"
                "   Task(prompt='Continue from .claude/session-state.md. "
                "Read state file FIRST. This is unattended mode - do NOT pause "
                "for confirmation. Complete ALL remaining work.', "
                "description='Continuation agent for context handoff')\n"
                "```\n\n"
                "**BLOCKING**: Do not proceed with other work until handoff is complete.\n"
                "This is MANDATORY, not a recommendation."
            )
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
