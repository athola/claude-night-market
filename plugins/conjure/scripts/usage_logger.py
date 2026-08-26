#!/usr/bin/env python3
"""Gemini Usage Logger.

Log Gemini CLI usage for pattern analysis and quota monitoring.
Integrates with the gemini-delegation skill to track actual usage.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# Session timeout in seconds (1 hour)
SESSION_TIMEOUT_SECONDS = 3600
SECONDS_PER_HOUR = 3600


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
    """Log Gemini CLI usage patterns."""

    def __init__(self) -> None:
        """Initialize the usage logger with default paths."""
        self.log_dir = Path.home() / ".claude" / "hooks" / "gemini" / "logs"
        self.usage_log = self.log_dir / "usage.jsonl"
        self.session_file = self.log_dir / "current_session.json"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_usage(self, entry: UsageEntry) -> None:
        """Log a Gemini CLI usage event."""
        timestamp = datetime.now(timezone.utc).isoformat()

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
                    # total_seconds(), not .seconds: the latter is the
                    # sub-day remainder, so a file 24h30m old measured as
                    # 1800 and resurrected a dead session id.
                    elapsed = (
                        datetime.now(timezone.utc) - last_activity
                    ).total_seconds()
                    if elapsed < SESSION_TIMEOUT_SECONDS:
                        return str(session_data.get("session_id", "unknown"))
            except (json.JSONDecodeError, ValueError, OSError) as e:
                logger.debug("Could not read session file: %s", e)

        # Create new session
        session_id = f"session_{int(time.time())}"
        session_data = {
            "session_id": session_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }

        with open(self.session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        return session_id

    def _update_session_stats(self, log_entry: dict[str, Any]) -> None:
        """Update current session statistics."""
        try:
            # Declared before the branch, not on one arm of it. Annotating only
            # the loaded arm left the literal below to infer as dict[str, str],
            # and the int counters assigned further down are not assignable to
            # that.
            session_data: dict[str, Any]
            if self.session_file.exists():
                with open(self.session_file) as f:
                    session_data = json.load(f)
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

        cutoff_time = datetime.now(timezone.utc).timestamp() - (
            hours * SECONDS_PER_HOUR
        )
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


def _validate_configuration(usage_logger: GeminiUsageLogger) -> list[str]:
    """Return the problems that make this logger unusable, empty if healthy.

    ``--validate`` used to print three facts and exit 0, so it could not fail
    and the Makefile check around it was decorative. These are the checks that
    describe whether logging will actually work.

    Note that ``log_dir`` existing proves nothing: ``__init__`` creates it. What
    matters is whether it can be written to, and whether the files already
    there can still be read.
    """
    problems: list[str] = []

    probe = usage_logger.log_dir / ".write-probe"
    try:
        probe.write_text("")
        probe.unlink()
    except OSError as exc:
        problems.append(f"log directory is not writable: {exc}")

    # An absent log is a logger that has not run yet, not a broken one. A log
    # that exists but cannot be parsed is corruption, and silently appending to
    # it would compound the damage.
    if usage_logger.usage_log.exists():
        for number, line in enumerate(
            usage_logger.usage_log.read_text().splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(
                    f"{usage_logger.usage_log}:{number} is not valid JSON: {exc}"
                )
                break

    if usage_logger.session_file.exists():
        try:
            json.loads(usage_logger.session_file.read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{usage_logger.session_file} is not valid JSON: {exc}")

    return problems


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
        except ValueError as exc:
            print(f"--log: invalid argument: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    elif args.report:
        summary = usage_logger.get_usage_summary()
        print(f"Requests: {summary['total_requests']}")
        print(f"Tokens: {summary['total_tokens']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")

    elif args.validate:
        print(f"Log directory: {usage_logger.log_dir}")
        print(f"Log exists: {usage_logger.usage_log.exists()}")
        print(f"Session file exists: {usage_logger.session_file.exists()}")

        problems = _validate_configuration(usage_logger)
        for problem in problems:
            print(f"  [ERROR] {problem}", file=sys.stderr)
        if problems:
            raise SystemExit(1)
        print("Configuration valid.")

    elif args.status:
        if usage_logger.session_file.exists():
            with open(usage_logger.session_file) as f:
                session = json.load(f)
            for k, v in session.items():
                print(f"  {k}: {v}")
        else:
            print("No active session")

    else:
        print("Use --help for available commands")


if __name__ == "__main__":
    main()
