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

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Threshold constants for three-tier MECW warnings
WARNING_THRESHOLD = 0.40
CRITICAL_THRESHOLD = 0.50
# Emergency threshold is configurable via environment variable
EMERGENCY_THRESHOLD = float(os.environ.get("CONSERVE_EMERGENCY_THRESHOLD", "0.80"))

# Staleness threshold: ignore session files older than this (seconds)
STALE_SESSION_SECONDS = 60


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
                f"Context usage high: {usage * 100:.1f}%. "
                "Consider wrapping up current work soon."
            ),
            recommendations=[
                "Complete current in-progress work",
                "Commit any pending changes",
                "Summarize remaining tasks for the user",
                "Session will auto-compact if needed, work is not lost",
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

        # Convert cwd to Claude's project directory naming convention
        # e.g., /home/user/my-project -> -home-user-my-project
        project_dir_name = str(cwd).replace("/", "-")
        if project_dir_name.startswith("-"):
            project_dir_name = project_dir_name[1:]
        project_dir_name = "-" + project_dir_name

        project_dir = claude_projects / project_dir_name

        # Guard: need existing projects dir, project dir, and JSONL files
        if not claude_projects.exists() or not project_dir.exists():
            return None

        jsonl_files = list(project_dir.glob("*.jsonl"))
        if not jsonl_files:
            return None

        # Use CLAUDE_SESSION_ID to find the correct session file if available
        session_id = os.environ.get("CLAUDE_SESSION_ID", "")
        current_session = None
        if session_id:
            # Match session ID to filename (files are named {uuid}.jsonl)
            for f in jsonl_files:
                if f.stem == session_id:
                    current_session = f
                    break

        if current_session is None:
            # Fallback: use most recently modified file, but only if it was
            # modified in the last 60 seconds (likely the active session).
            # Without this guard, old multi-MB session files trigger false
            # EMERGENCY alerts on every tool call.

            candidates = sorted(
                jsonl_files, key=lambda f: f.stat().st_mtime, reverse=True
            )
            newest = candidates[0]
            age_seconds = time.time() - newest.stat().st_mtime
            if age_seconds > STALE_SESSION_SECONDS:
                # Most recent file is stale — not the current session
                return None
            current_session = newest

        file_size = current_session.stat().st_size

        # Primary estimate: file size relative to context window bytes
        size_usage = min(file_size / context_window_bytes, 0.95)

        # Secondary estimate: parse message/tool counts for cross-check
        heuristic_usage = _estimate_from_heuristics(current_session)

        # Use the higher of the two to be conservative (fail safe)
        usage = (
            max(size_usage, heuristic_usage)
            if heuristic_usage is not None
            else size_usage
        )

        logger.debug(
            "Estimated context from %s: %d bytes, size=%.1f%%, heuristic=%.1f%%",
            current_session.name,
            file_size,
            size_usage * 100,
            (heuristic_usage or 0) * 100,
        )
        return usage

    except (OSError, PermissionError) as e:
        logger.debug("Could not estimate context from session files: %s", e)
        return None


def _estimate_from_heuristics(session_file: Path) -> float | None:
    """Estimate context usage by counting messages and tool calls in a session file.

    Uses per-turn and per-tool-result token heuristics as a cross-check
    against the file-size estimate. Returns the higher of turn-based and
    character-based approximations, capped at 0.95.
    """
    context_window_tokens = 200_000
    tokens_per_turn = 800
    tokens_per_tool_result = 200

    try:
        content = session_file.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return None

    turn_count = 0
    tool_result_count = 0
    total_chars = len(content)

    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            entry = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        role = entry.get("role", "")
        if role in ("user", "assistant"):
            turn_count += 1

        message_content = entry.get("content", [])
        if isinstance(message_content, list):
            for block in message_content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_result_count += 1

    turn_tokens = (
        turn_count * tokens_per_turn + tool_result_count * tokens_per_tool_result
    )
    char_tokens = total_chars // 4
    estimated_tokens = max(turn_tokens, char_tokens)

    return min(estimated_tokens / context_window_tokens, 0.95)


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

    # Add additionalContext for non-OK levels (overwritten for EMERGENCY in main())
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
        # For EMERGENCY level, provide clear guidance (not imperative commands)
        if alert.severity == ContextSeverity.EMERGENCY:
            output["hookSpecificOutput"]["additionalContext"] = (
                f"Context usage high ({alert.usage_percent * 100:.1f}%). "
                "Consider wrapping up current work:\n"
                "- Complete in-progress tasks\n"
                "- Commit pending changes\n"
                "- Summarize remaining work for the user\n"
                "- The session will auto-compact if needed"
            )
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
