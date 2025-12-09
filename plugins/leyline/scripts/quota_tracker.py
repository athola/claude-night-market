#!/usr/bin/env python3
"""Universal quota tracking for rate-limited services.

This is a generalized quota tracker that can be used by any plugin
integrating with rate-limited external services.

Usage:
    from leyline.quota_tracker import QuotaTracker

    tracker = QuotaTracker(service="my-service")
    status, warnings = tracker.get_quota_status()
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class QuotaConfig:
    """Configuration for service quotas."""

    requests_per_minute: int = 60
    requests_per_day: int = 1000
    tokens_per_minute: int = 100000
    tokens_per_day: int = 1000000


@dataclass
class UsageStats:
    """Current usage statistics."""

    requests_this_minute: int = 0
    requests_today: int = 0
    tokens_this_minute: int = 0
    tokens_today: int = 0
    last_request_time: float = 0.0


@dataclass
class QuotaStatus:
    """Quota status result."""

    level: str  # "healthy", "warning", "critical"
    warnings: list[str] = field(default_factory=list)
    usage_percent: dict[str, float] = field(default_factory=dict)


# Token estimation ratios by file type
TOKEN_RATIOS = {
    ".py": 3.2,
    ".js": 3.2,
    ".ts": 3.2,
    ".go": 3.2,
    ".rs": 3.2,
    ".json": 3.6,
    ".yaml": 3.6,
    ".yml": 3.6,
    ".toml": 3.6,
    ".md": 4.2,
    ".txt": 4.2,
    ".rst": 4.2,
}
DEFAULT_TOKEN_RATIO = 4.0


class QuotaTracker:
    """Universal quota tracker for rate-limited services."""

    def __init__(
        self,
        service: str,
        config: QuotaConfig | None = None,
        storage_dir: Path | None = None,
    ) -> None:
        self.service = service
        self.config = config or QuotaConfig()

        # Storage location
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            self.storage_dir = Path.home() / ".claude" / "leyline" / "quota"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.storage_dir / f"{service}_usage.json"

        self._load_usage()

    def _load_usage(self) -> None:
        """Load usage data from storage."""
        if self.usage_file.exists():
            try:
                data = json.loads(self.usage_file.read_text())
                self.usage = UsageStats(**data)
            except (json.JSONDecodeError, TypeError):
                self.usage = UsageStats()
        else:
            self.usage = UsageStats()

        self._cleanup_old_data()

    def _save_usage(self) -> None:
        """Save usage data to storage."""
        data = {
            "requests_this_minute": self.usage.requests_this_minute,
            "requests_today": self.usage.requests_today,
            "tokens_this_minute": self.usage.tokens_this_minute,
            "tokens_today": self.usage.tokens_today,
            "last_request_time": self.usage.last_request_time,
        }
        self.usage_file.write_text(json.dumps(data, indent=2))

    def _cleanup_old_data(self) -> None:
        """Reset counters if time periods have passed."""
        now = time.time()

        # Reset minute counters if more than 60 seconds
        if now - self.usage.last_request_time > 60:
            self.usage.requests_this_minute = 0
            self.usage.tokens_this_minute = 0

        # Reset daily counters if new day
        last_date = datetime.fromtimestamp(self.usage.last_request_time).date()
        current_date = datetime.now().date()
        if current_date > last_date:
            self.usage.requests_today = 0
            self.usage.tokens_today = 0

    def record_request(
        self,
        tokens: int = 0,
        success: bool = True,
        duration: float = 0.0,
    ) -> None:
        """Record a request to the service."""
        self._cleanup_old_data()

        self.usage.requests_this_minute += 1
        self.usage.requests_today += 1
        self.usage.tokens_this_minute += tokens
        self.usage.tokens_today += tokens
        self.usage.last_request_time = time.time()

        self._save_usage()

    def get_current_usage(self) -> UsageStats:
        """Get current usage statistics."""
        self._cleanup_old_data()
        return self.usage

    def get_quota_status(self) -> tuple[str, list[str]]:
        """Get current quota status.

        Returns:
            Tuple of (status_level, list of warnings)
            Status levels: "healthy", "warning", "critical"

        """
        self._cleanup_old_data()
        warnings = []

        # Calculate usage percentages
        rpm_percent = (
            self.usage.requests_this_minute / self.config.requests_per_minute
        ) * 100
        daily_percent = (self.usage.requests_today / self.config.requests_per_day) * 100
        tpm_percent = (
            self.usage.tokens_this_minute / self.config.tokens_per_minute
        ) * 100

        # Determine status level
        max_usage = max(rpm_percent, daily_percent, tpm_percent)

        if max_usage >= 95:
            level = "critical"
        elif max_usage >= 80:
            level = "warning"
        else:
            level = "healthy"

        # Generate warnings
        if rpm_percent >= 80:
            warnings.append(
                f"RPM at {rpm_percent:.1f}% ({self.usage.requests_this_minute}/{self.config.requests_per_minute})",
            )
        if daily_percent >= 80:
            warnings.append(
                f"Daily requests at {daily_percent:.1f}% ({self.usage.requests_today}/{self.config.requests_per_day})",
            )
        if tpm_percent >= 80:
            warnings.append(
                f"TPM at {tpm_percent:.1f}% ({self.usage.tokens_this_minute}/{self.config.tokens_per_minute})",
            )

        return level, warnings

    def can_handle_task(self, estimated_tokens: int) -> tuple[bool, list[str]]:
        """Check if quota can handle a task.

        Returns:
            Tuple of (can_proceed, list of issues)

        """
        self._cleanup_old_data()
        issues = []

        # Check if tokens would exceed limits
        if (
            self.usage.tokens_this_minute + estimated_tokens
            > self.config.tokens_per_minute
        ):
            issues.append(
                f"Would exceed TPM limit ({self.usage.tokens_this_minute + estimated_tokens} > {self.config.tokens_per_minute})",
            )

        if self.usage.tokens_today + estimated_tokens > self.config.tokens_per_day:
            issues.append(
                f"Would exceed daily token limit ({self.usage.tokens_today + estimated_tokens} > {self.config.tokens_per_day})",
            )

        # Check request counts
        if self.usage.requests_this_minute >= self.config.requests_per_minute:
            issues.append("RPM limit reached")

        if self.usage.requests_today >= self.config.requests_per_day:
            issues.append("Daily request limit reached")

        return len(issues) == 0, issues

    def estimate_file_tokens(self, path: Path) -> int:
        """Estimate tokens for a file based on size and type."""
        if not path.exists() or not path.is_file():
            return 0

        size = path.stat().st_size
        ratio = TOKEN_RATIOS.get(path.suffix.lower(), DEFAULT_TOKEN_RATIO)
        return int(size / ratio)

    def estimate_task_tokens(
        self,
        file_paths: list[str | Path],
        prompt_length: int = 100,
    ) -> int:
        """Estimate total tokens for a task."""
        total = prompt_length // 4  # Rough prompt token estimate

        for path_input in file_paths:
            path = Path(path_input) if isinstance(path_input, str) else path_input
            total += self.estimate_file_tokens(path)

        return total


def main() -> None:
    """CLI interface for quota tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="Check service quota status")
    parser.add_argument("service", help="Service name")
    parser.add_argument("--check", action="store_true", help="Check quota status")
    parser.add_argument("--estimate", nargs="+", help="Estimate tokens for files")

    args = parser.parse_args()

    tracker = QuotaTracker(service=args.service)

    if args.check:
        _level, warnings = tracker.get_quota_status()
        if warnings:
            for _w in warnings:
                pass
    elif args.estimate:
        total = tracker.estimate_task_tokens(args.estimate)
        can_proceed, issues = tracker.can_handle_task(total)
        if can_proceed:
            pass
        else:
            for _issue in issues:
                pass


if __name__ == "__main__":
    main()
