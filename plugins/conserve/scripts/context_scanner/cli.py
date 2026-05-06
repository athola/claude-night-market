"""CLI interface for context_scanner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cache import load_cache, save_cache
from .ecosystems import scan_directory
from .import_graph import blast_radius, build_import_graph
from .models import ScanResult
from .renderers import (
    _VALID_SECTIONS,
    generate_wiki,
    render_blast_radius,
    render_json,
    render_markdown,
    render_section,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for context_scanner."""
    parser = argparse.ArgumentParser(
        description="Generate a compressed context map for a project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Project directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=5000,
        help="Target maximum token count (default: 5000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--blast",
        type=str,
        default=None,
        metavar="FILE",
        help="Show blast radius for a specific file",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Force fresh scan, ignore cached results",
    )
    parser.add_argument(
        "--no-wiki",
        action="store_true",
        default=False,
        help="Skip wiki article generation",
    )
    parser.add_argument(
        "--wiki-only",
        action="store_true",
        default=False,
        help="Generate wiki articles only, no stdout output",
    )
    parser.add_argument(
        "--section",
        type=str,
        default=None,
        metavar="NAME",
        help=("Output a single section: " + ", ".join(sorted(_VALID_SECTIONS))),
    )
    return parser


def _emit(text: str, output_path: str | None) -> None:
    """Write text to file when output_path is set, otherwise to stdout."""
    if output_path:
        Path(output_path).write_text(text)
    else:
        print(text)


def _run_blast(root: Path, blast_target: str, output_path: str | None) -> int:
    """Render blast radius for one file."""
    graph = build_import_graph(root)
    br = blast_radius(graph, blast_target)
    _emit(render_blast_radius(br), output_path)
    return 0


def _load_or_scan(root: Path, *, no_cache: bool) -> ScanResult:
    """Return a scan result, using the cache unless suppressed."""
    result = None if no_cache else load_cache(root)
    if result is None:
        result = scan_directory(root)
        try:
            save_cache(root, result)
        except OSError:
            pass  # read-only filesystem (CI, Docker) -- scan result is still valid
    return result


def _run_section(result: ScanResult, section: str, output_path: str | None) -> int:
    """Render a single named section, returning 1 if the name is unknown."""
    section_out = render_section(result, section)
    if section_out is None:
        print(
            f"Error: unknown section '{section}'. "
            f"Valid: {', '.join(sorted(_VALID_SECTIONS))}",
            file=sys.stderr,
        )
        return 1
    _emit(section_out, output_path)
    return 0


def _maybe_generate_wiki(
    root: Path, result: ScanResult, *, no_wiki: bool, wiki_only: bool
) -> None:
    """Generate wiki articles unless explicitly suppressed."""
    if no_wiki and not wiki_only:
        return
    try:
        generate_wiki(root, result)
    except OSError as e:
        print(f"Warning: wiki generation failed: {e}", file=sys.stderr)


def _render_full(result: ScanResult, fmt: str, max_tokens: int) -> str:
    """Render the full project map in the requested format."""
    if fmt == "json":
        return render_json(result)
    max_deps = max(4, min(12, max_tokens // 500))
    max_dirs = max(4, min(12, max_tokens // 400))
    return render_markdown(result, max_dirs=max_dirs, max_deps=max_deps)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = _build_parser().parse_args(argv)
    root = Path(args.path).resolve()

    if not root.is_dir():
        print(f"Error: '{args.path}' is not a valid directory", file=sys.stderr)
        return 1

    if args.blast:
        return _run_blast(root, args.blast, args.output)

    result = _load_or_scan(root, no_cache=args.no_cache)

    if args.section:
        return _run_section(result, args.section, args.output)

    _maybe_generate_wiki(root, result, no_wiki=args.no_wiki, wiki_only=args.wiki_only)
    if args.wiki_only:
        return 0

    _emit(_render_full(result, args.format, args.max_tokens), args.output)
    return 0
