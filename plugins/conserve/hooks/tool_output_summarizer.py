#!/usr/bin/env python3
"""PostToolUse hook to monitor and warn about tool output bloat.

This hook tracks cumulative tool output size and warns when approaching
context pressure thresholds. It helps users proactively manage context
before hitting Anthropic's limits.

Environment variables:
- CLAUDE_HOME: Claude configuration directory
- CLAUDE_SESSION_ID: Current session identifier
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Threshold for warning about accumulated output (bytes)
# ~100KB of text is roughly 25K tokens, which is 2.5% of 1M context
BLOAT_WARNING_THRESHOLD = 100_000


def resolve_session_file() -> Path | None:
    """Find the current session's JSONL file."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")))
    claude_projects = claude_dir / "projects"

    if not claude_projects.exists():
        return None

    # Try to find project directory from CWD
    cwd = Path.cwd()
    project_dir_name = str(cwd).replace(os.sep, "-")
    if not project_dir_name.startswith("-"):
        project_dir_name = "-" + project_dir_name

    project_dir = claude_projects / project_dir_name
    if not project_dir.exists():
        # Fallback: list all project dirs and use most recent
        project_dirs = sorted(
            claude_projects.iterdir(),
            key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
            reverse=True,
        )
        if project_dirs:
            project_dir = project_dirs[0]
        else:
            return None

    # Find the current session file
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    jsonl_files = list(project_dir.glob("*.jsonl"))

    if not jsonl_files:
        return None

    if session_id:
        for f in jsonl_files:
            if f.stem == session_id:
                return f

    # Fallback to most recent
    return max(jsonl_files, key=lambda f: f.stat().st_mtime)


def get_session_output_size(session_file: Path, max_bytes: int = 512_000) -> int:
    """Calculate total size of tool outputs in session.

    Reads at most *max_bytes* of the file to stay within the hook
    timeout budget.  The result is an approximation for large sessions.

    Args:
        session_file: Path to the JSONL session file.
        max_bytes: Maximum bytes to read (default 512 KB).

    Returns:
        Total bytes of tool result content (may be approximate).

    """
    total_size = 0
    bytes_read = 0

    try:
        with open(session_file, encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                bytes_read += len(raw_line)
                if bytes_read > max_bytes:
                    break
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError:
                    continue

                content = entry.get("content", "")
                if isinstance(content, list):
                    for block in content:
                        is_tool_result = (
                            isinstance(block, dict)
                            and block.get("type") == "tool_result"
                        )
                        if is_tool_result:
                            result_content = block.get("content", "")
                            if isinstance(result_content, str):
                                total_size += len(result_content)
                            elif isinstance(result_content, list):
                                for item in result_content:
                                    if isinstance(item, dict):
                                        text = item.get("text", "")
                                        total_size += len(text)
                                    elif isinstance(item, str):
                                        total_size += len(item)
    except (OSError, PermissionError) as e:
        logger.debug("Could not read session file: %s", e)

    return total_size


def assess_output_bloat(
    session_file: Path, threshold: int = BLOAT_WARNING_THRESHOLD
) -> dict[str, Any]:
    """Assess tool output bloat and return severity level.

    Args:
        session_file: Path to the session file.
        threshold: Critical threshold in bytes (warning at 80%).

    Returns:
        Dictionary with severity, bytes_accumulated, and recommendations.

    """
    output_size = get_session_output_size(session_file)
    warning_threshold = int(threshold * 0.8)

    if output_size >= threshold:
        return {
            "severity": "critical",
            "bytes_accumulated": output_size,
            "threshold": threshold,
            "recommendations": [
                "Run /clear to reset context immediately",
                "Consider spawning a subagent for remaining work",
                "Archive recent outputs to external files",
            ],
        }
    elif output_size >= warning_threshold:
        return {
            "severity": "warning",
            "bytes_accumulated": output_size,
            "threshold": threshold,
            "recommendations": [
                "Monitor context growth",
                "Consider summarizing recent tool outputs",
                "Use /clear before starting new major task phase",
            ],
        }

    return {
        "severity": "ok",
        "bytes_accumulated": output_size,
        "threshold": threshold,
        "recommendations": [],
    }


def format_hook_output(assessment: dict[str, Any]) -> dict[str, Any]:
    """Format assessment as hook-compatible output.

    Args:
        assessment: The bloat assessment result.

    Returns:
        Dictionary suitable for hook JSON output.

    """
    kb_accumulated = assessment["bytes_accumulated"] / 1024
    kb_threshold = assessment["threshold"] / 1024
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"Tool output bloat: {kb_accumulated:.1f}KB accumulated "
                f"(threshold: {kb_threshold:.1f}KB)\n"
                f"Severity: {assessment['severity'].upper()}\n"
                + "\n".join(f"- {rec}" for rec in assessment["recommendations"])
            ),
        }
    }


def main() -> int:
    """Execute PostToolUse hook entry point."""
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    # Only process Bash, Read, Grep tools (verbose output tools)
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Bash", "Read", "Grep"):
        return 0

    # Find and assess session
    session_file = resolve_session_file()
    if not session_file:
        logger.debug("No session file found")
        return 0

    assessment = assess_output_bloat(session_file)

    # Only output if warning or critical
    if assessment["severity"] != "ok":
        output = format_hook_output(assessment)
        print(json.dumps(output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
