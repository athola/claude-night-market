#!/usr/bin/env python3
"""Gemini Usage Logger.

Logs Gemini CLI usage for pattern analysis and quota monitoring.
Integrates with the gemini-delegation skill to track actual usage.
"""

import argparse
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# Session timeout in seconds (1 hour)
SESSION_TIMEOUT_SECONDS = 3600


@dataclass
class UsageEntry:
    """Data for a single usage log entry."""

    command: str
    estimated_tokens: int
    actual_tokens: int | None = None
    success: bool = True
    duration: float | None = None
    error: str | None = None


class GeminiUsageLogger:
    """Logger for tracking Gemini CLI usage patterns."""

    def __init__(self) -> None:
        """Initialize the usage logger with default paths."""
        self.log_dir = Path.home() / ".claude" / "hooks" / "gemini" / "logs"
        self.usage_log = self.log_dir / "usage.jsonl"
        self.session_file = self.log_dir / "current_session.json"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_usage(self, entry: UsageEntry) -> None:
        """Log a Gemini CLI usage event."""
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "command": entry.command,
            "estimated_tokens": entry.estimated_tokens,
            "actual_tokens": entry.actual_tokens or entry.estimated_tokens,
            "success": entry.success,
            "duration_seconds": entry.duration,
            "error": entry.error,
            "session_id": self._get_session_id(),
        }

        # Write to usage log
        with open(self.usage_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        # Update session stats
        self._update_session_stats(log_entry)

    def _get_session_id(self) -> str:
        """Get or create a session identifier."""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    session_data = json.load(f)
                    # Check if session is still recent (within 1 hour)
                    last_activity = datetime.fromisoformat(
                        session_data.get("last_activity", ""),
                    )
                    elapsed = (datetime.now() - last_activity).seconds
                    if elapsed < SESSION_TIMEOUT_SECONDS:
                        return str(session_data.get("session_id", "unknown"))
            except (json.JSONDecodeError, ValueError, OSError) as e:
                logger.debug("Could not read session file: %s", e)

        # Create new session
        session_id = f"session_{int(time.time())}"
        session_data = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }

        with open(self.session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        return session_id

    def _update_session_stats(self, log_entry: dict[str, Any]) -> None:
        """Update current session statistics."""
        try:
            if self.session_file.exists():
                with open(self.session_file) as f:
                    session_data: dict[str, Any] = json.load(f)
            else:
                session_data = {"session_id": self._get_session_id()}

            # Update stats
            session_data["last_activity"] = log_entry["timestamp"]

            # validate numeric fields exist with correct type
            total_requests: int = int(session_data.get("total_requests", 0))
            total_tokens: int = int(session_data.get("total_tokens", 0))
            successful_requests: int = int(session_data.get("successful_requests", 0))

            session_data["total_requests"] = total_requests + 1
            actual = int(log_entry["actual_tokens"])
            session_data["total_tokens"] = total_tokens + actual
            if log_entry["success"]:
                session_data["successful_requests"] = successful_requests + 1

            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)

        except (json.JSONDecodeError, OSError, KeyError, TypeError) as e:
            # Don't let logging errors break the main flow
            logger.debug("Failed to update session stats: %s", e)

    def get_usage_summary(self, hours: int = 24) -> dict:
        """Get usage summary for the last N hours."""
        if not self.usage_log.exists():
            return {"total_requests": 0, "total_tokens": 0, "success_rate": 0.0}

        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        total_requests = 0
        total_tokens = 0
        successful_requests = 0

        try:
            with open(self.usage_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(
                            entry["timestamp"],
                        ).timestamp()

                        if entry_time >= cutoff_time:
                            total_requests += 1
                            total_tokens += entry.get("actual_tokens", 0)
                            if entry.get("success", False):
                                successful_requests += 1
                    except (json.JSONDecodeError, KeyError):
                        continue
        except FileNotFoundError:
            pass

        success_rate = (
            (successful_requests / total_requests * 100) if total_requests > 0 else 0.0
        )

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "hours_analyzed": hours,
        }

    def get_recent_errors(self, count: int = 5) -> list:
        """Get recent error entries."""
        if not self.usage_log.exists():
            return []

        errors = []
        try:
            with open(self.usage_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if not entry.get("success", True) and entry.get("error"):
                            errors.append(entry)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except FileNotFoundError:
            pass

        return errors[-count:]  # Return last N errors


def main() -> None:
    """CLI entry point for usage logger."""
    parser = argparse.ArgumentParser(description="Log and analyze Gemini CLI usage")
    parser.add_argument(
        "--log",
        nargs=4,
        metavar=("COMMAND", "TOKENS", "SUCCESS", "DURATION"),
        help="Log usage: command tokens success duration",
    )
    parser.add_argument("--report", action="store_true", help="Generate usage report")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate logging configuration",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current session status",
    )

    args = parser.parse_args()

    usage_logger = GeminiUsageLogger()

    if args.log:
        command, tokens, success, duration = args.log
        try:
            estimated_tokens = int(tokens)
            success_bool = success.lower() == "true"
            duration_float = float(duration) if duration != "None" else None

            entry = UsageEntry(
                command=command,
                estimated_tokens=estimated_tokens,
                success=success_bool,
                duration=duration_float,
            )
            usage_logger.log_usage(entry)
        except ValueError:
            pass

    elif args.report:
        usage_logger.get_usage_summary()

    elif args.validate or args.status:
        pass

    else:
        pass


if __name__ == "__main__":
    main()
