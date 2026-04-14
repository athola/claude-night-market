"""CLI interface for context_scanner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cache import load_cache, save_cache
from .ecosystems import scan_directory
from .import_graph import blast_radius, build_import_graph
from .renderers import (
    _VALID_SECTIONS,
    generate_wiki,
    render_blast_radius,
    render_json,
    render_markdown,
    render_section,
)


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0912, PLR0915 - CLI dispatch with subcommands requires many branches
    """CLI entry point."""
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

    args = parser.parse_args(argv)
    root = Path(args.path).resolve()

    if not root.is_dir():
        print(f"Error: '{args.path}' is not a valid directory", file=sys.stderr)
        return 1

    if args.blast:
        graph = build_import_graph(root)
        blast_file = args.blast
        br = blast_radius(graph, blast_file)
        output = render_blast_radius(br)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
        return 0

    # Try cache first
    result = None
    if not args.no_cache:
        result = load_cache(root)

    if result is None:
        result = scan_directory(root)
        try:
            save_cache(root, result)
        except OSError:
            pass  # read-only filesystem (CI, Docker) -- scan result is still valid

    if args.section:
        section_out = render_section(result, args.section)
        if section_out is None:
            print(
                f"Error: unknown section '{args.section}'. "
                f"Valid: {', '.join(sorted(_VALID_SECTIONS))}",
                file=sys.stderr,
            )
            return 1
        if args.output:
            Path(args.output).write_text(section_out)
        else:
            print(section_out)
        return 0

    # Wiki generation
    if not args.no_wiki or args.wiki_only:
        try:
            generate_wiki(root, result)
        except OSError as e:
            print(f"Warning: wiki generation failed: {e}", file=sys.stderr)

    if args.wiki_only:
        return 0

    # Adjust limits based on max-tokens target
    max_deps = max(4, min(12, args.max_tokens // 500))
    max_dirs = max(4, min(12, args.max_tokens // 400))

    if args.format == "json":
        output = render_json(result)
    else:
        output = render_markdown(result, max_dirs=max_dirs, max_deps=max_deps)

    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)

    return 0
