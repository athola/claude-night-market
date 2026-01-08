#!/usr/bin/env python3
"""Skill execution observability logger for PostToolUse hook.

Captures skill invocation telemetry when Claude uses the Skill tool.
Logs execution metadata for later analysis and self-improvement.

Issue: https://github.com/athola/claude-night-market/issues/69
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def get_log_directory() -> Path:
    """Get or create the skill execution log directory.

    Returns:
        Path to .claude/skills/logs/<plugin>/<skill-name>/

    """
    # Try to get Claude home directory
    claude_home = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
    log_base = claude_home / "skills" / "logs"

    # Create base directory if it doesn't exist
    log_base.mkdir(parents=True, exist_ok=True)

    return log_base


def parse_skill_name(tool_input: dict[str, Any]) -> tuple[str, str]:
    """Parse plugin and skill name from Skill tool input.

    Args:
        tool_input: Skill tool input dictionary

    Returns:
        Tuple of (plugin_name, skill_name)

    """
    # Skill tool uses "skill" parameter with format "plugin:skill-name"
    skill_ref = tool_input.get("skill", "unknown:unknown")

    if ":" in skill_ref:
        plugin, skill = skill_ref.split(":", 1)
        return plugin.strip(), skill.strip()

    return "unknown", skill_ref.strip()


def sanitize_output(output: str, max_length: int = 5000) -> str:
    """Sanitize and truncate tool output for logging.

    Args:
        output: Raw tool output
        max_length: Maximum output length to store

    Returns:
        Sanitized and truncated output

    """
    # Truncate if too long
    if len(output) > max_length:
        output = output[:max_length] + f"\n... (truncated from {len(output)} chars)"

    # Basic sanitization - remove potential secrets
    # (In production, use more sophisticated secret detection)
    # TODO: Implement pattern matching for sensitive data
    # sensitive_patterns = ["password", "api_key", "secret", "token"]

    return output


def create_log_entry(
    tool_input: dict[str, Any], tool_output: str, start_time: datetime
) -> dict[str, Any]:
    """Create structured log entry for skill execution.

    Args:
        tool_input: Tool input parameters
        tool_output: Tool execution output
        start_time: When the skill started executing

    Returns:
        Structured log entry dictionary

    """
    plugin, skill = parse_skill_name(tool_input)
    end_time = datetime.now(UTC)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Determine outcome based on output
    outcome = "success"
    error = None

    if "error" in tool_output.lower() or "failed" in tool_output.lower():
        outcome = "failure"
        error = tool_output[:500]  # Store first 500 chars of error
    elif "warning" in tool_output.lower():
        outcome = "partial"

    return {
        "timestamp": start_time.isoformat(),
        "invocation_id": str(uuid4()),
        "skill": f"{plugin}:{skill}",
        "plugin": plugin,
        "skill_name": skill,
        "duration_ms": duration_ms,
        "outcome": outcome,
        "context": {
            "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
            "tool_input": tool_input,
            "output_preview": sanitize_output(tool_output, max_length=1000),
        },
        "error": error,
        "qualitative_evaluation": None,  # Populated later by human-in-loop
    }


def save_log_entry(log_entry: dict[str, Any]) -> None:
    """Save log entry to disk.

    Args:
        log_entry: Structured log entry to save

    """
    log_base = get_log_directory()
    plugin = log_entry["plugin"]
    skill = log_entry["skill_name"]

    # Create plugin/skill-specific directory
    skill_log_dir = log_base / plugin / skill
    skill_log_dir.mkdir(parents=True, exist_ok=True)

    # Use date-based log file (one file per day)
    log_date = datetime.fromisoformat(log_entry["timestamp"]).strftime("%Y-%m-%d")
    log_file = skill_log_dir / f"{log_date}.jsonl"

    # Append to JSONL file (one JSON object per line)
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def main() -> None:
    """PostToolUse hook entry point."""
    try:
        # Read environment variables from Claude Code
        tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
        tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
        tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

        # Only log if this is a Skill tool invocation
        if tool_name != "Skill":
            # Not a skill invocation, exit silently
            sys.exit(0)

        # Parse tool input
        try:
            tool_input = json.loads(tool_input_str)
        except json.JSONDecodeError:
            # If input is malformed, log with minimal info
            tool_input = {"error": "malformed_input", "raw": tool_input_str[:200]}

        # Create log entry (use current time as start approximation)
        start_time = datetime.now(UTC)
        log_entry = create_log_entry(tool_input, tool_output, start_time)

        # Save log entry
        save_log_entry(log_entry)

        # PostToolUse hooks don't modify output (return None implicitly)
        # Just exit successfully
        sys.exit(0)

    except Exception as e:
        # Hook failures should not break Claude Code
        # Log error to stderr and exit gracefully
        sys.stderr.write(f"skill_execution_logger error: {e}\n")
        sys.exit(0)  # Exit 0 to not block Claude Code


if __name__ == "__main__":
    main()
