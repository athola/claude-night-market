#!/usr/bin/env python3
"""Shared CLI scaffolding for abstract wrapper scripts.

Extracts common boilerplate: src path setup, argument parsing,
and output handling shared across CLI wrappers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def setup_src_path() -> None:
    """Add the plugin src directory to sys.path for imports."""
    src_path = str((Path(__file__).parent.parent / "src").resolve())
    if src_path not in [str(Path(p).resolve()) for p in sys.path]:
        sys.path.insert(0, src_path)


def create_parser(
    description: str,
    *,
    add_format: bool = False,
) -> argparse.ArgumentParser:
    """Create an argument parser with common flags.

    Args:
        description: Parser description.
        add_format: Add --format text/json choice.

    Returns:
        Configured ArgumentParser.

    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--output", type=Path, help="Output file path")
    if add_format:
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format",
        )
    return parser


def write_output(text: str, output_path: Path | None) -> None:
    """Write text to file or stdout.

    Args:
        text: Content to write.
        output_path: File path, or None for stdout.

    """
    if output_path:
        with open(output_path, "w") as f:
            f.write(text)
    else:
        print(text)


def format_result(
    data: Any,
    fmt: str = "text",
    text_fn: Any = None,
) -> str:
    """Format a result as JSON or text.

    Args:
        data: Raw data (dict or object).
        fmt: "json" or "text".
        text_fn: Callable that produces text from data.
            Required when fmt is "text".

    Returns:
        Formatted string.

    """
    if fmt == "json":
        return json.dumps(data, indent=2, default=str)
    if text_fn is not None:
        return str(text_fn(data))
    return str(data)
