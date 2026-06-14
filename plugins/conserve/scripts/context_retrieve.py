#!/usr/bin/env python3
"""Retrieve a CCR-archived tool output (or a slice of it) on demand.

Companion to ``tool_output_summarizer.py``. When that PostToolUse hook
archives a large tool output, it leaves a content-addressed handle
(``ccr-<sha256[:12]>``) pointing at ``.claude/context-archive/<handle>.txt``.
This CLI fetches the original by handle so a later turn (or a fresh
continuation agent after ``/clear``) can read the full content, or just the
slice it needs, instead of re-running the expensive command.

This is the "retrieve on demand" half of reversible compression (CCR),
modelled on chopratejas/headroom's ``headroom_retrieve``.

Usage::

    python3 context_retrieve.py <handle> [--head N] [--tail N]
                                         [--lines A:B] [--grep PATTERN]
                                         [--archive-dir DIR]

With no slice flag the full original is printed. Slice flags are mutually
exclusive in effect; precedence is ``--lines`` > ``--head`` > ``--tail``.
``--grep`` filters to matching lines (applied after any slice).
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

DEFAULT_ARCHIVE_DIR = Path(".claude") / "context-archive"


def resolve_handle(handle: str, archive_dir: Path | str) -> Path:
    """Resolve a CCR handle to its archived file path.

    Accepts ``ccr-abc123``, ``ccr-abc123.txt``, or a bare path. Raises
    ``FileNotFoundError`` if the archived file does not exist.
    """
    archive_dir = Path(archive_dir)
    name = handle.strip()
    if not name.endswith(".txt"):
        name = f"{name}.txt"
    candidate = archive_dir / Path(name).name
    if not candidate.is_file():
        raise FileNotFoundError(f"No archived output for handle: {handle}")
    return candidate


def slice_content(
    text: str,
    *,
    head: int | None = None,
    tail: int | None = None,
    lines: str | None = None,
) -> str:
    """Return a slice of *text* by line.

    Precedence: ``lines`` (1-indexed inclusive ``"A:B"``) > ``head`` (first N)
    > ``tail`` (last N). With no argument the text is returned unchanged.
    """
    if lines is not None:
        start_str, _, end_str = lines.partition(":")
        # An open start ("--lines :3") reads from the first line.
        start = max(1, int(start_str)) if start_str else 1
        split = text.split("\n")
        end = int(end_str) if end_str else len(split)
        return "\n".join(split[start - 1 : end])
    if head is not None:
        if head <= 0:
            return ""
        return "\n".join(text.split("\n")[:head])
    if tail is not None:
        # Guard tail <= 0: "[-0:]" is "[0:]" (the whole text), which would
        # dump the entire archive for a request of zero trailing lines.
        if tail <= 0:
            return ""
        return "\n".join(text.split("\n")[-tail:])
    return text


def grep_content(text: str, pattern: str) -> str:
    """Return only the lines of *text* matching *pattern* (regex)."""
    compiled = re.compile(pattern)
    return "\n".join(line for line in text.split("\n") if compiled.search(line))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="context_retrieve.py",
        description="Retrieve a CCR-archived tool output by handle.",
    )
    parser.add_argument("handle", help="CCR handle, e.g. ccr-abc123def456")
    parser.add_argument("--head", type=int, help="First N lines only")
    parser.add_argument("--tail", type=int, help="Last N lines only")
    parser.add_argument("--lines", help="1-indexed inclusive range, e.g. 40:80")
    parser.add_argument("--grep", help="Keep only lines matching this regex")
    parser.add_argument(
        "--archive-dir",
        default=str(DEFAULT_ARCHIVE_DIR),
        help="Archive directory (default: .claude/context-archive)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 if the handle is missing."""
    args = _build_parser().parse_args(argv)

    try:
        path = resolve_handle(args.handle, args.archive_dir)
    except FileNotFoundError as exc:
        logger.warning("%s", exc)
        return 1

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = slice_content(text, head=args.head, tail=args.tail, lines=args.lines)
        if args.grep:
            text = grep_content(text, args.grep)
    except ValueError as exc:  # malformed --lines bound
        logger.warning("invalid --lines range %r: %s", args.lines, exc)
        return 2
    except re.error as exc:  # malformed --grep pattern
        logger.warning("invalid --grep pattern %r: %s", args.grep, exc)
        return 2
    except OSError as exc:  # unreadable archive (permission, cleanup race)
        logger.warning("could not read archive: %s", exc)
        return 2

    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
