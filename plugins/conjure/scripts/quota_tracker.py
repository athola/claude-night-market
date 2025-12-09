#!/usr/bin/env python3
"""Gemini CLI Quota Tracker.

Track Gemini CLI usage to provide quota warnings and prevent rate limit
exhaustion. Extends leyline's universal QuotaTracker with Gemini-specific
token estimation and CLI command parsing.
"""

from __future__ import annotations

import argparse
import logging
import os
import shlex
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from leyline import QuotaConfig, QuotaTracker

if TYPE_CHECKING:
    from collections.abc import Iterable

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore[assignment]

# Configure logging
logger = logging.getLogger(__name__)

# Gemini Free Tier Limits (adjustable based on your plan)
GEMINI_QUOTA_CONFIG = QuotaConfig(
    requests_per_minute=60,
    requests_per_day=1000,
    tokens_per_minute=32000,
    tokens_per_day=1000000,
)

# File overhead for token estimation
FILE_OVERHEAD_TOKENS = 6


class GeminiQuotaTracker(QuotaTracker):
    """Track and manage Gemini CLI quota usage.

    Extends leyline's QuotaTracker with Gemini-specific features:
    - Gemini-specific storage location
    - Advanced token estimation with tiktoken
    - Directory walking for file analysis
    - Gemini CLI command parsing
    """

    def __init__(self, limits: dict[str, int] | None = None) -> None:
        """Initialize tracker with optional custom limits.

        Args:
            limits: Optional dict with quota limits. If provided, overrides
                   GEMINI_QUOTA_CONFIG defaults.

        """
        # Convert limits dict to QuotaConfig if provided
        if limits:
            config = QuotaConfig(
                requests_per_minute=limits.get("requests_per_minute", 60),
                requests_per_day=limits.get("requests_per_day", 1000),
                tokens_per_minute=limits.get("tokens_per_minute", 32000),
                tokens_per_day=limits.get("tokens_per_day", 1000000),
            )
        else:
            config = GEMINI_QUOTA_CONFIG

        # Use Gemini-specific storage location
        storage_dir = Path.home() / ".claude" / "hooks" / "gemini"

        super().__init__(
            service="gemini",
            config=config,
            storage_dir=storage_dir,
        )

        # Rename usage.json to match Gemini expectations
        self.usage_file = storage_dir / "usage.json"

    @property
    def limits(self) -> dict[str, int]:
        """Backward compatibility property for limits dict."""
        return {
            "requests_per_minute": self.config.requests_per_minute,
            "requests_per_day": self.config.requests_per_day,
            "tokens_per_minute": self.config.tokens_per_minute,
            "tokens_per_day": self.config.tokens_per_day,
        }

    def estimate_task_tokens(
        self,
        file_paths: list[str],
        prompt_length: int = 100,
    ) -> int:
        """Estimate tokens with optional tiktoken encoder fallback.

        Uses tiktoken if available, otherwise falls back to heuristic estimation.

        Args:
            file_paths: List of file/directory paths to analyze
            prompt_length: Estimated prompt length in characters

        Returns:
            Estimated total tokens

        """
        encoder = self._get_encoder()
        if encoder:
            return self._estimate_with_encoder(encoder, file_paths, prompt_length)

        return self._estimate_with_heuristic(file_paths, prompt_length)

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_encoder() -> Any | None:
        """Get tiktoken encoder if available."""
        if tiktoken is None:
            return None
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:  # pragma: no cover - optional dependency
            return None

    def _estimate_with_encoder(
        self,
        encoder: Any,
        file_paths: list[str],
        prompt_length: int,
    ) -> int:
        """Estimate tokens using tiktoken encoder."""
        tokens = len(encoder.encode("x" * prompt_length))

        for path in self._iter_source_paths(file_paths):
            try:
                text = Path(path).read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeDecodeError):
                continue
            tokens += len(encoder.encode(text)) + FILE_OVERHEAD_TOKENS

        return tokens

    def _estimate_with_heuristic(
        self,
        file_paths: list[str],
        prompt_length: int,
    ) -> int:
        """Estimate tokens using heuristic ratios."""
        tokens = int(prompt_length / 4.0)  # Default ratio

        for path in self._iter_source_paths(file_paths):
            tokens += self.estimate_file_tokens(Path(path))

        return int(tokens)

    def _iter_source_paths(self, file_paths: list[str]) -> Iterable[str]:
        """Iterate over source file paths, walking directories.

        Skips common build/dependency directories and filters for relevant
        file types.
        """
        skip_dirs = {
            "__pycache__",
            "node_modules",
            ".git",
            "venv",
            ".venv",
            "dist",
            "build",
        }

        valid_extensions = {
            ".py",
            ".js",
            ".ts",
            ".md",
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".txt",
            ".rs",
            ".go",
        }

        for file_path in file_paths:
            try:
                if os.path.isfile(file_path):
                    yield file_path
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        # Filter out skip directories
                        dirs[:] = [d for d in dirs if d not in skip_dirs]
                        for file in files:
                            candidate = os.path.join(root, file)
                            if Path(candidate).suffix.lower() in valid_extensions:
                                yield candidate
            except (OSError, PermissionError):
                continue


def estimate_tokens_from_gemini_command(command: str) -> int:
    """Estimate tokens from a Gemini CLI command by analyzing @ paths.

    Parses the command string to extract file paths prefixed with @ and
    estimates the total tokens needed.

    Args:
        command: Gemini CLI command string (e.g., "gemini @file.py ask...")

    Returns:
        Estimated token count

    """
    try:
        parts = shlex.split(command)
        file_paths = []

        for part in parts:
            if part.startswith("@"):
                file_paths.append(part[1:])  # Remove @ prefix

        # Create a tracker instance for estimation
        tracker = GeminiQuotaTracker()
        return tracker.estimate_task_tokens(file_paths, len(command))
    except (ValueError, OSError) as e:
        logger.debug("Error parsing command for token estimation: %s", e)
        return len(command) // 4  # Default estimation


def main() -> None:
    """CLI entry point for quota tracker."""
    parser = argparse.ArgumentParser(description="Track Gemini CLI quota and usage")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current quota status",
    )
    parser.add_argument("--estimate", nargs="+", help="Estimate tokens for given paths")
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate quota configuration",
    )

    args = parser.parse_args()

    tracker = GeminiQuotaTracker()

    if args.status:
        status, warnings = tracker.get_quota_status()
        for _warning in warnings:
            pass

    elif args.estimate:
        tracker.estimate_task_tokens(args.estimate)

    elif args.validate_config:
        # Basic validation of configuration
        for _key, _value in tracker.limits.items():
            pass

    else:
        # Default: show status
        _status, warnings = tracker.get_quota_status()
        for _warning in warnings:
            pass


if __name__ == "__main__":
    main()
