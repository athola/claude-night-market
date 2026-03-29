#!/usr/bin/env python3
"""Gemini CLI Quota Tracker.

Track Gemini CLI usage to provide warnings and prevent rate limit
exhaustion. Extends leyline's universal QuotaTracker with Gemini-specific
token estimation and CLI command parsing.
"""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
sys.path.insert(0, str(_LEYLINE_SRC))

try:
    from leyline.fs import (
        FILE_OVERHEAD_TOKENS,
        SKIP_DIRS,
        SOURCE_EXTENSIONS,
        iter_source_files,
    )

    _HAS_LEYLINE_FS = True
except ImportError:  # pragma: no cover
    _HAS_LEYLINE_FS = False
    FILE_OVERHEAD_TOKENS = 6
    SKIP_DIRS = frozenset(
        {
            "__pycache__",
            "node_modules",
            ".git",
            "venv",
            ".venv",
            "dist",
            "build",
            ".pytest_cache",
        }
    )
    SOURCE_EXTENSIONS = frozenset(
        {
            ".py",
            ".js",
            ".ts",
            ".rs",
            ".md",
            ".txt",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
        }
    )

    def iter_source_files(
        root_dir: Any,
        extensions: Any = None,
        skip_dirs: Any = None,
    ) -> Any:
        """Fallback directory walker when leyline.fs is unavailable."""
        effective_ext = extensions if extensions is not None else SOURCE_EXTENSIONS
        effective_skip = skip_dirs if skip_dirs is not None else SKIP_DIRS
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in effective_skip]
            for file in files:
                candidate = Path(root) / file
                if candidate.suffix.lower() in effective_ext:
                    yield candidate


try:
    from leyline import (
        QuotaConfig,
        QuotaTracker,
    )
except ImportError:  # pragma: no cover
    # Define fallback classes when leyline is not available
    @dataclass(frozen=True)
    class QuotaConfig:
        """Quota configuration (stub when leyline not available)."""

        requests_per_minute: int
        requests_per_day: int
        tokens_per_minute: int
        tokens_per_day: int

    class QuotaTracker:
        def __init__(
            self,
            service: str,
            config: QuotaConfig,
            storage_dir: Path | None = None,
        ) -> None:
            """Initialize quota tracker (stub when leyline not available)."""
            self.service = service
            self.config = config
            self.storage_dir = storage_dir

        def estimate_file_tokens(self, path: Path) -> int:
            """Estimate token count for a file."""
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return 0
            return (len(text) // 4) + 6

        def get_quota_status(self) -> tuple[str, list[str]]:
            """Get quota status (stub when leyline not available)."""
            return "[OK] Healthy", ["(leyline not installed; quota tracking disabled)"]


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

try:
    import tiktoken
except ImportError:
    tiktoken = None

# Configure logging
logger = logging.getLogger(__name__)

# Gemini Free Tier Limits (adjustable based on your plan)
GEMINI_QUOTA_CONFIG = QuotaConfig(
    requests_per_minute=60,
    requests_per_day=1000,
    tokens_per_minute=32000,
    tokens_per_day=1000000,
)

# Default limits dict for backward compatibility with tests
DEFAULT_LIMITS = {
    "requests_per_minute": 60,
    "requests_per_day": 1000,
    "tokens_per_minute": 32000,
    "tokens_per_day": 1000000,
}

# Named per-service quota limit dicts for use by delegation_executor
DEFAULT_GEMINI_LIMITS: dict[str, int] = {
    "requests_per_minute": 60,
    "requests_per_day": 1000,
    "tokens_per_day": 1000000,
}

DEFAULT_QWEN_LIMITS: dict[str, int] = {
    "requests_per_minute": 120,
    "requests_per_day": 2000,
    "tokens_per_day": 2000000,
}


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
        file_paths: Sequence[str | Path],
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
        file_paths: Sequence[str | Path],
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
        file_paths: Sequence[str | Path],
        prompt_length: int,
    ) -> int:
        """Estimate tokens using heuristic ratios."""
        tokens = int(prompt_length / 4.0)  # Default ratio

        for path in self._iter_source_paths(file_paths):
            tokens += self.estimate_file_tokens(Path(path)) + FILE_OVERHEAD_TOKENS

        return int(tokens)

    def _iter_source_paths(self, file_paths: Sequence[str | Path]) -> Iterable[str]:
        """Iterate over source file paths, walking directories.

        Delegates to leyline.fs.iter_source_files (with fallback) so that
        skip-dir and extension logic stays in one place.

        Yields string paths for backward compatibility with callers.
        """
        for file_path in file_paths:
            path = Path(file_path)
            try:
                if path.is_file():
                    yield str(path)
                elif path.is_dir():
                    for p in iter_source_files(path):
                        yield str(p)
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
    """Run CLI entry point for quota tracker."""
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
        print(status)
        for warning in warnings:
            print(f"  WARNING: {warning}")

    elif args.estimate:
        tokens = tracker.estimate_task_tokens(args.estimate)
        print(f"Estimated tokens: {tokens}")

    elif args.validate_config:
        for key, value in tracker.limits.items():
            print(f"  {key}: {value}")

    else:
        status, warnings = tracker.get_quota_status()
        print(status)
        for warning in warnings:
            print(f"  WARNING: {warning}")


if __name__ == "__main__":
    main()
