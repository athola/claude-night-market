#!/usr/bin/env python3
"""
Session-aware usage logging for audit trails and analytics.

This is a generalized usage logger that can be used by any plugin
for tracking operations, costs, and building analytics.

Usage:
    from leyline.usage_logger import UsageLogger

    logger = UsageLogger(service="my-service")
    logger.log_usage("operation", tokens=1000, success=True, duration=2.5)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass
class LogEntry:
    """A single usage log entry."""

    timestamp: str
    session_id: str
    service: str
    operation: str
    tokens: int
    success: bool
    duration_seconds: float
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class UsageLogger:
    """Session-aware usage logger with JSONL storage."""

    SESSION_TIMEOUT = 3600  # 1 hour

    def __init__(
        self,
        service: str,
        storage_dir: Path | None = None,
        session_id: str | None = None,
    ):
        self.service = service

        # Storage location
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            self.storage_dir = Path.home() / ".claude" / "leyline" / "usage"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.storage_dir / f"{service}.jsonl"
        self.session_file = self.storage_dir / f"{service}_session.json"

        # Session management
        if session_id:
            self.session_id = session_id
        else:
            self.session_id = self._get_or_create_session()

    def _get_or_create_session(self) -> str:
        """Get existing session or create new one."""
        if self.session_file.exists():
            try:
                session = json.loads(self.session_file.read_text())
                # Check if session is still active
                if time.time() - session.get("last_activity", 0) < self.SESSION_TIMEOUT:
                    return session["session_id"]
            except (json.JSONDecodeError, KeyError):
                pass

        # Create new session
        session_id = f"session_{int(time.time())}"
        self._save_session(session_id)
        return session_id

    def _save_session(self, session_id: str) -> None:
        """Save session state."""
        session = {
            "session_id": session_id,
            "created_at": time.time(),
            "last_activity": time.time(),
        }
        self.session_file.write_text(json.dumps(session))

    def _update_session_activity(self) -> None:
        """Update session last activity timestamp."""
        if self.session_file.exists():
            try:
                session = json.loads(self.session_file.read_text())
                session["last_activity"] = time.time()
                self.session_file.write_text(json.dumps(session))
            except (json.JSONDecodeError, KeyError):
                pass

    def log_usage(
        self,
        operation: str,
        tokens: int = 0,
        success: bool = True,
        duration: float = 0.0,
        error_type: str | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log a usage entry."""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            session_id=self.session_id,
            service=self.service,
            operation=operation,
            tokens=tokens,
            success=success,
            duration_seconds=duration,
            error_type=error_type,
            error_message=error_message,
            metadata=metadata or {},
        )

        # Append to JSONL file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry.__dict__) + "\n")

        self._update_session_activity()

    def get_recent_operations(self, hours: int = 24) -> list[dict]:
        """Get operations from the last N hours."""
        if not self.log_file.exists():
            return []

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        operations = []

        for line in self.log_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry["timestamp"].rstrip("Z"))
                if entry_time >= cutoff:
                    operations.append(entry)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return operations

    def get_usage_summary(self, days: int = 7) -> dict:
        """Get usage summary for the last N days."""
        operations = self.get_recent_operations(hours=days * 24)

        if not operations:
            return {
                "total_operations": 0,
                "total_tokens": 0,
                "success_rate": 0.0,
                "total_duration": 0.0,
                "estimated_cost": 0.0,
            }

        total_tokens = sum(op.get("tokens", 0) for op in operations)
        successful = sum(1 for op in operations if op.get("success", False))
        total_duration = sum(op.get("duration_seconds", 0) for op in operations)

        return {
            "total_operations": len(operations),
            "total_tokens": total_tokens,
            "success_rate": successful / len(operations) if operations else 0.0,
            "total_duration": total_duration,
            "estimated_cost": total_tokens / 1_000_000 * 0.5,  # Rough estimate
        }

    def get_recent_errors(self, count: int = 10) -> list[dict]:
        """Get recent error entries."""
        if not self.log_file.exists():
            return []

        errors = []
        for line in reversed(self.log_file.read_text().splitlines()):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if not entry.get("success", True):
                    errors.append(entry)
                    if len(errors) >= count:
                        break
            except json.JSONDecodeError:
                continue

        return errors

    def get_session_operations(self, session_id: str | None = None) -> list[dict]:
        """Get all operations for a session."""
        target_session = session_id or self.session_id

        if not self.log_file.exists():
            return []

        operations = []
        for line in self.log_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("session_id") == target_session:
                    operations.append(entry)
            except json.JSONDecodeError:
                continue

        return operations


def main():
    """CLI interface for usage logger."""
    import argparse

    parser = argparse.ArgumentParser(description="Query usage logs")
    parser.add_argument("service", help="Service name")
    parser.add_argument("--summary", action="store_true", help="Show usage summary")
    parser.add_argument("--recent", type=int, default=24, help="Hours of recent data")
    parser.add_argument("--errors", type=int, help="Show N recent errors")
    parser.add_argument(
        "--log", nargs=4, metavar=("OPERATION", "TOKENS", "SUCCESS", "DURATION"),
        help="Log an operation"
    )

    args = parser.parse_args()

    logger = UsageLogger(service=args.service)

    if args.summary:
        summary = logger.get_usage_summary()
        print(f"Usage Summary ({args.service}):")
        print(f"  Operations: {summary['total_operations']}")
        print(f"  Total tokens: {summary['total_tokens']:,}")
        print(f"  Success rate: {summary['success_rate']:.1%}")
        print(f"  Total duration: {summary['total_duration']:.1f}s")
        print(f"  Estimated cost: ${summary['estimated_cost']:.4f}")
    elif args.errors:
        errors = logger.get_recent_errors(args.errors)
        print(f"Recent Errors ({len(errors)}):")
        for err in errors:
            print(f"  [{err['timestamp']}] {err.get('error_type', 'Unknown')}: {err.get('error_message', 'No message')}")
    elif args.log:
        operation, tokens, success, duration = args.log
        logger.log_usage(
            operation=operation,
            tokens=int(tokens),
            success=success.lower() == "true",
            duration=float(duration)
        )
        print(f"Logged: {operation}")
    else:
        operations = logger.get_recent_operations(hours=args.recent)
        print(f"Recent Operations ({len(operations)} in last {args.recent}h):")
        for op in operations[-10:]:
            status = "✓" if op.get("success") else "✗"
            print(f"  {status} [{op['timestamp'][:19]}] {op['operation']} ({op.get('tokens', 0)} tokens)")


if __name__ == "__main__":
    main()
