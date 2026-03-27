"""Estimate tokens for LLM context management.

This module provides utilities for estimating token counts for files and prompts,
with optional tiktoken integration for accurate tokenization and a secondary
heuristic-based estimation.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from leyline.fs import (
    FILE_OVERHEAD_TOKENS,
    SKIP_DIRS,
    SOURCE_EXTENSIONS,
    iter_source_files,
)

logger = logging.getLogger(__name__)

# Import tiktoken if available
try:
    import tiktoken
except ImportError:  # pragma: no cover - optional dependency
    tiktoken = None
    logger.debug("tiktoken not available, using heuristic estimation")
except Exception as e:  # pragma: no cover - edge case
    tiktoken = None
    logger.debug("Failed to import tiktoken: %s", e)

# Token estimation ratios: characters per token for different file types
FILE_TOKEN_RATIOS = {
    "code": 3.2,  # .py, .js, .ts, .rs
    "json": 3.6,  # .json, .yaml, .yml, .toml
    "text": 4.2,  # .md, .txt
    "default": 4.0,
}

# Extension-level token ratios (granular form of FILE_TOKEN_RATIOS)
EXTENSION_TOKEN_RATIOS = {
    ".py": FILE_TOKEN_RATIOS["code"],
    ".js": FILE_TOKEN_RATIOS["code"],
    ".ts": FILE_TOKEN_RATIOS["code"],
    ".go": FILE_TOKEN_RATIOS["code"],
    ".rs": FILE_TOKEN_RATIOS["code"],
    ".json": FILE_TOKEN_RATIOS["json"],
    ".yaml": FILE_TOKEN_RATIOS["json"],
    ".yml": FILE_TOKEN_RATIOS["json"],
    ".toml": FILE_TOKEN_RATIOS["json"],
    ".md": FILE_TOKEN_RATIOS["text"],
    ".txt": FILE_TOKEN_RATIOS["text"],
    ".rst": FILE_TOKEN_RATIOS["text"],
}
DEFAULT_EXTENSION_TOKEN_RATIO = FILE_TOKEN_RATIOS["default"]

# Re-export fs constants so existing importers of tokens.py keep working
__all__ = [
    "DEFAULT_EXTENSION_TOKEN_RATIO",
    "EXTENSION_TOKEN_RATIOS",
    "FILE_OVERHEAD_TOKENS",
    "FILE_TOKEN_RATIOS",
    "SKIP_DIRS",
    "SOURCE_EXTENSIONS",
    "estimate_file_tokens",
    "estimate_tokens",
]


@lru_cache(maxsize=1)
def _get_encoder() -> Any | None:
    """Get tiktoken encoder if available.

    Returns:
        tiktoken encoder instance or None if tiktoken is not installed

    """
    if tiktoken is None:
        logger.debug("tiktoken not available, using heuristic estimation")
        return None

    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception as e:  # pragma: no cover - edge case
        logger.debug("Failed to load tiktoken encoder: %s", e)
        return None


def estimate_file_tokens(path: Path) -> int:
    """Estimate token count for a single file using heuristics.

    Args:
        path: Path to the file

    Returns:
        Estimated token count including overhead

    """
    try:
        size = path.stat().st_size
    except OSError:
        return 0

    suffix = path.suffix.lower()

    if suffix in {".py", ".js", ".ts", ".rs"}:
        ratio = FILE_TOKEN_RATIOS["code"]
    elif suffix in {".json", ".yaml", ".yml", ".toml"}:
        ratio = FILE_TOKEN_RATIOS["json"]
    elif suffix in {".md", ".txt"}:
        ratio = FILE_TOKEN_RATIOS["text"]
    else:
        ratio = FILE_TOKEN_RATIOS["default"]

    return int(size / ratio) + FILE_OVERHEAD_TOKENS


def _encode_file_with_tiktoken(encoder: Any, path: Path) -> int:
    """Encode a file using tiktoken for accurate token count.

    Args:
        encoder: tiktoken encoder instance
        path: Path to the file

    Returns:
        Actual token count including overhead

    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return 0
    return len(encoder.encode(text)) + FILE_OVERHEAD_TOKENS


def _estimate_with_encoder(encoder: Any, files: list[str], prompt: str) -> int:
    """Estimate tokens using tiktoken encoder.

    Args:
        encoder: tiktoken encoder instance
        files: List of file paths (files or directories)
        prompt: Prompt text

    Returns:
        Estimated token count

    """
    # Start with prompt tokens
    total_tokens = len(encoder.encode(prompt))

    # Process each file or directory
    for file_path in files:
        try:
            path = Path(file_path)
            if path.is_file():
                total_tokens += _encode_file_with_tiktoken(encoder, path)
            elif path.is_dir():
                for file in iter_source_files(path):
                    total_tokens += _encode_file_with_tiktoken(encoder, file)
        except OSError as exc:  # pragma: no cover - filesystem edge case
            logger.debug("Could not access file %s: %s", file_path, exc)
            continue

    return total_tokens


def _estimate_with_heuristic(files: list[str], prompt: str) -> int:
    """Estimate tokens using character-based heuristics.

    Args:
        files: List of file paths (files or directories)
        prompt: Prompt text

    Returns:
        Estimated token count

    """
    # Start with prompt tokens (using default ratio)
    tokens = int(len(prompt) / FILE_TOKEN_RATIOS["default"])

    # Process each file or directory
    for file_path in files:
        try:
            path = Path(file_path)
            if path.is_file():
                tokens += estimate_file_tokens(path)
            elif path.is_dir():
                for file in iter_source_files(path):
                    tokens += estimate_file_tokens(file)
        except OSError as exc:
            logger.debug("Could not access file %s: %s", file_path, exc)
            continue

    return int(tokens)


def estimate_tokens(files: list[str], prompt: str = "") -> int:
    """Estimate total tokens for a list of files and prompt.

    This function provides token estimation with two strategies:
    1. If tiktoken is available, uses accurate tokenization (cl100k_base encoding)
    2. Otherwise, uses a default heuristic estimation based on file size and type

    Args:
        files: List of file or directory paths to estimate
        prompt: Optional prompt text to include in estimation

    Returns:
        Estimated total token count

    Examples:
        >>> estimate_tokens(["main.py", "utils.py"], "Review this code")
        1234

        >>> estimate_tokens(["src/"], "Analyze this project")
        5678

    """
    encoder = _get_encoder()

    if encoder:
        return _estimate_with_encoder(encoder, files, prompt)

    return _estimate_with_heuristic(files, prompt)
