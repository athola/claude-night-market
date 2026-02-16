#!/usr/bin/env python3
"""Skill execution observability logger for PostToolUse hook.

Captures skill invocation telemetry when Claude uses the Skill tool.
Logs execution metadata for continual learning and self-improvement.

Integrates with pre_skill_execution.py to calculate accurate duration
and enable per-iteration evaluation metrics (stability gap detection).

Issue: https://github.com/athola/claude-night-market/issues/69
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# Threshold for triggering stability gap warnings
# Based on Avalanche paper: gap > 0.3 indicates significant instability
# See: https://avalanche.continualai.org/
STABILITY_GAP_THRESHOLD = 0.3


def get_observability_dir() -> Path:
    """Get observability state directory."""
    claude_home = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
    state_dir = claude_home / "skills" / "observability"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


class ContinualEvaluator:
    """Implements continual evaluation metrics (Avalanche-style)."""

    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.skill_history: dict[str, dict[str, list]] = defaultdict(
            lambda: {"accuracies": [], "durations": []}
        )
        self._load_history()

    def _load_history(self) -> None:
        """Load historical execution data."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    self.skill_history = json.load(f)
            except (OSError, json.JSONDecodeError):
                pass  # Start fresh on error

    def _save_history(self) -> None:
        """Save historical execution data."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w") as f:
            json.dump(dict(self.skill_history), f, indent=2)

    def evaluate_iteration(
        self, skill_ref: str, success: bool, duration_ms: int
    ) -> dict[str, Any]:
        """Evaluate single iteration using continual metrics.

        Args:
            skill_ref: Skill reference (e.g., "abstract:skill-auditor")
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds

        Returns:
            Dictionary with continual evaluation metrics

        """
        history = self.skill_history[skill_ref]
        history["accuracies"].append(1 if success else 0)
        history["durations"].append(duration_ms)

        # Save history after each iteration
        self._save_history()

        accuracies = history["accuracies"]
        durations = history["durations"]

        # Avalanche continual metrics (ICLR 2023)
        worst_case = min(accuracies)
        avg_accuracy = sum(accuracies) / len(accuracies)
        stability_gap = avg_accuracy - worst_case  # Key innovation!

        # Additional metrics
        avg_duration = sum(durations) / len(durations)
        execution_count = len(accuracies)

        return {
            "worst_case_accuracy": worst_case,
            "average_accuracy": avg_accuracy,
            "stability_gap": stability_gap,
            "avg_duration_ms": avg_duration,
            "execution_count": execution_count,
        }


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
    # Truncate BEFORE regex matching to prevent ReDoS on large inputs
    if len(output) > max_length:
        output = output[:max_length] + f"\n... (truncated from {len(output)} chars)"

    # Redact potential secrets using pattern matching (safe: input is bounded above)
    sensitive_patterns = [
        # API keys
        (
            r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?",
            r"\1=<REDACTED>",
        ),
        # Bearer tokens
        (r"(?i)(bearer\s+)([A-Za-z0-9_\-\.]+)", r"\1<REDACTED>"),
        # Password fields
        (
            r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?",
            r"\1=<REDACTED>",
        ),
        # Secret fields
        (
            r"(?i)(secret|token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})['\"]?",
            r"\1=<REDACTED>",
        ),
        # AWS credentials
        (
            r"(?i)(aws[_-]?(access[_-]?key|secret)[_-]?[a-z]*)\s*[:=]\s*"
            r"['\"]?([A-Za-z0-9/+=]+)['\"]?",
            r"\1=<REDACTED>",
        ),
        # GitHub tokens
        (
            r"(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,})",
            r"<REDACTED_GITHUB_TOKEN>",
        ),
        # Generic base64-encoded secrets
        (
            r"(?i)(key|credential|auth)\s*[:=]\s*"
            r"['\"]?([A-Za-z0-9+/]{32,}={0,2})['\"]?",
            r"\1=<REDACTED>",
        ),
    ]

    for pattern, replacement in sensitive_patterns:
        output = re.sub(pattern, replacement, output)

    return output


def create_log_entry(
    tool_input: dict[str, Any],
    tool_output: str,
    pre_state: dict[str, Any] | None,
    evaluator: ContinualEvaluator | None,
) -> dict[str, Any]:
    """Create structured log entry for skill execution.

    Args:
        tool_input: Tool input parameters
        tool_output: Tool execution output
        pre_state: Pre-execution state from pre_skill_execution.py
        evaluator: Continual evaluator for metrics

    Returns:
        Structured log entry dictionary

    """
    plugin, skill = parse_skill_name(tool_input)
    skill_ref = f"{plugin}:{skill}"
    end_time = datetime.now(timezone.utc)

    # Calculate duration from pre-execution state if available
    if pre_state and "timestamp" in pre_state:
        start_time = datetime.fromisoformat(pre_state["timestamp"])
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
    else:
        # Fallback: approximate with current time
        duration_ms = 0

    # Determine outcome based on output
    # Check warning first since warnings mentioning "failed" are still partial
    outcome = "success"
    error = None

    if "warning" in tool_output.lower():
        outcome = "partial"
    elif "error" in tool_output.lower() or "failed" in tool_output.lower():
        outcome = "failure"
        error = tool_output[:500]  # Store first 500 chars of error

    # Calculate continual evaluation metrics
    continual_metrics = None
    if evaluator:
        success = outcome == "success"
        continual_metrics = evaluator.evaluate_iteration(
            skill_ref, success, duration_ms
        )

    return {
        "timestamp": end_time.isoformat(),
        "invocation_id": pre_state.get("invocation_id") if pre_state else str(uuid4()),
        "skill": skill_ref,
        "plugin": plugin,
        "skill_name": skill,
        "duration_ms": duration_ms,
        "outcome": outcome,
        "continual_metrics": continual_metrics,
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

        # Filter non-Skill tools - hooks fire for all tool invocations
        if tool_name != "Skill":
            sys.exit(0)

        # Parse tool input
        try:
            tool_input = json.loads(tool_input_str)
        except json.JSONDecodeError:
            tool_input = {"error": "malformed_input", "raw": tool_input_str[:200]}

        # Get skill reference
        plugin, skill = parse_skill_name(tool_input)
        skill_ref = f"{plugin}:{skill}"

        # Try to read pre-execution state
        pre_state = None
        state_dir = get_observability_dir()
        state_files = list(state_dir.glob(f"{skill_ref}:*.json"))

        if state_files:
            # Get most recent state file
            latest_file = max(state_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_file) as f:
                    pre_state = json.load(f)
                # Clean up state file
                latest_file.unlink()
            except (OSError, json.JSONDecodeError):
                pass

        # Initialize continual evaluator
        history_file = get_log_directory() / ".history.json"
        evaluator = ContinualEvaluator(history_file)

        # Create log entry with pre-execution state and metrics
        log_entry = create_log_entry(tool_input, tool_output, pre_state, evaluator)

        # Save log entry
        save_log_entry(log_entry)

        # Check for stability gap (automatic improvement trigger)
        if log_entry.get("continual_metrics"):
            stability_gap = log_entry["continual_metrics"].get("stability_gap", 0)
            if stability_gap > STABILITY_GAP_THRESHOLD:
                sys.stderr.write(
                    f"⚠️  Stability gap detected for {skill_ref}: {stability_gap:.2f}\n"
                )

        # Output hook data
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "skill": skill_ref,
                "outcome": log_entry["outcome"],
                "duration_ms": log_entry["duration_ms"],
                "continual_metrics": log_entry.get("continual_metrics"),
            }
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"skill_execution_logger error: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
