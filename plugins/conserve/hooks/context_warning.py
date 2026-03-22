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

# Maximum bytes to read from the tail of a JSONL session file.
# 4MB ≈ one full 1M-token context window at ~4 chars/token.
# Reading beyond this risks counting auto-compressed history.
_TAIL_BYTES = 4_000_000


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
                f"EMERGENCY: Context at {usage * 100:.1f}%. "
                "Invoke Skill(conserve:clear-context) to delegate to "
                "a continuation agent."
            ),
            recommendations=[
                "Invoke Skill(conserve:clear-context) immediately",
                "Save session state and spawn continuation agent",
                "Do NOT stop working - delegate remaining tasks",
                "Continuation agent will resume with fresh context",
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


def _resolve_project_dir(cwd: Path, claude_projects: Path) -> Path | None:
    """Resolve the Claude Code project directory for the given working directory.

    Claude Code names project directories by replacing path separators with
    dashes.  For example, ``/home/user/project`` becomes
    ``-home-user-project``.

    Returns:
        The resolved project directory Path, or None if not found.

    """
    # Claude Code convention: replace path separators with dashes
    project_dir_name = str(cwd).replace(os.sep, "-")
    if not project_dir_name.startswith("-"):
        project_dir_name = "-" + project_dir_name

    project_dir = claude_projects / project_dir_name
    if project_dir.exists():
        return project_dir

    return None


def _find_current_session(jsonl_files: list[Path]) -> Path | None:
    """Find the active session file from a list of JSONL candidates.

    Returns:
        The session file Path, or None if no active session found.

    """
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if session_id:
        for f in jsonl_files:
            if f.stem == session_id:
                return f

    # Fallback: most recently modified file, but only if modified
    # within STALE_SESSION_SECONDS (likely the active session).
    candidates = sorted(jsonl_files, key=lambda f: f.stat().st_mtime, reverse=True)
    newest = candidates[0]
    age_seconds = time.time() - newest.stat().st_mtime
    if age_seconds > STALE_SESSION_SECONDS:
        return None
    return newest


def _resolve_session_file() -> Path | None:
    """Find the active JSONL session file for the current working directory.

    Returns:
        Path to the session file, or None if not found.

    """
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    claude_projects = claude_dir / "projects"
    if not claude_projects.exists():
        return None

    project_dir = _resolve_project_dir(Path.cwd(), claude_projects)
    if project_dir is None:
        return None

    jsonl_files = list(project_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None

    return _find_current_session(jsonl_files)


def estimate_context_from_session() -> float | None:
    """Estimate context usage from current session's JSONL conversation data.

    This is a FAST fallback for real-time hooks when CLAUDE_CONTEXT_USAGE
    is not available. Estimates based on **recent** conversation entries,
    not total file size — JSONL files contain the full conversation history
    including auto-compressed messages that are no longer in the context
    window.

    Note: For more precise context reading in batch/headless scenarios,
    use the CLI method instead:
        claude -p "/context" --verbose --output-format json
    See: plugins/conserve/commands/optimize-context.md

    Returns:
        Estimated context usage as float 0-1, or None if cannot estimate.

    """
    if os.environ.get("CONSERVE_CONTEXT_ESTIMATION", "1") == "0":
        return None

    try:
        current_session = _resolve_session_file()
        if current_session is None:
            return None

        usage = _estimate_from_recent_turns(current_session)
        logger.debug(
            "Estimated context from %s: %.1f%%",
            current_session.name,
            (usage or 0) * 100,
        )
        return usage

    except (OSError, PermissionError) as e:
        logger.debug("Could not estimate context from session files: %s", e)
        return None


def _count_content(message_content: object) -> tuple[int, int]:
    """Count chars and tool results from a message content field.

    Returns:
        (content_chars, tool_result_count)

    """
    chars = 0
    tool_results = 0
    if isinstance(message_content, list):
        for block in message_content:
            if isinstance(block, dict):
                if block.get("type") == "tool_result":
                    tool_results += 1
                text = block.get("text", "") or block.get("content", "")
                if text:
                    chars += len(text)
            elif isinstance(block, str):
                chars += len(block)
    elif isinstance(message_content, str):
        chars += len(message_content)
    return chars, tool_results


def _estimate_from_recent_turns(session_file: Path) -> float | None:
    """Estimate context usage from recent conversation turns only.

    JSONL files contain the FULL conversation history, including messages
    that Claude Code has auto-compressed out of the active context window.
    Reading the entire file vastly over-estimates actual context usage.

    This function reads only the tail of the file (last ``_TAIL_BYTES``)
    and counts turns + content size within that window.  The result is a
    conservative estimate that avoids false EMERGENCY alerts from large
    history files.

    Returns:
        Estimated context usage as float 0-1, or None on read failure.

    """
    context_window_tokens = 1_000_000
    tokens_per_turn = 600
    tokens_per_tool_result = 150

    try:
        file_size = session_file.stat().st_size

        # Read only the tail of the file — recent conversation is at the end.
        # 4MB ≈ 1M tokens at ~4 chars/token, which is one full context
        # window.  Reading more than this means we're counting compressed
        # history that is no longer in the context.
        tail_bytes = _TAIL_BYTES
        with open(session_file, encoding="utf-8", errors="replace") as fh:
            if file_size > tail_bytes:
                fh.seek(file_size - tail_bytes)
                # Skip partial first line after seeking
                fh.readline()
            content = fh.read()
    except (OSError, PermissionError):
        return None

    turn_count = 0
    tool_result_count = 0
    content_chars = 0

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
        chars, tool_results = _count_content(message_content)
        content_chars += chars
        tool_result_count += tool_results

    # Estimate tokens from turn structure
    turn_tokens = (
        turn_count * tokens_per_turn + tool_result_count * tokens_per_tool_result
    )
    # Estimate tokens from actual content (text only, not JSON keys)
    content_tokens = content_chars // 4
    # Use the higher of structural vs content estimates
    estimated_tokens = max(turn_tokens, content_tokens)

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
                f"EMERGENCY: Context at {alert.usage_percent * 100:.1f}%. "
                "Invoke Skill(conserve:clear-context) to hand off to a "
                "continuation agent:\n"
                "- Save session state to .claude/session-state.md\n"
                "- Spawn a continuation agent with fresh context\n"
                "- The continuation agent will resume all remaining work\n"
                "- Do NOT simply stop or wrap up - DELEGATE via continuation"
            )
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
