"""CLI for knowledge extraction from a target directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# sys.path must be extended before gauntlet imports so this script works
# when invoked directly (not via the installed package).
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from gauntlet.extraction import extract_from_directory  # noqa: E402 - path set above
from gauntlet.knowledge_store import KnowledgeStore  # noqa: E402 - path set above


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract knowledge entries from a Python codebase.",
    )
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory to extract from.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Gauntlet directory to save knowledge.json into. "
            "When omitted, prints to stdout."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    target_dir: Path = args.target_dir
    if not target_dir.exists():
        print(f"error: target directory does not exist: {target_dir}", file=sys.stderr)
        return 1

    entries = extract_from_directory(target_dir)

    if args.output is not None:
        store = KnowledgeStore(args.output)
        store.save(entries)
        if args.format == "text":
            print(f"Saved {len(entries)} entries to {args.output / 'knowledge.json'}")
        else:
            print(json.dumps({"saved": len(entries), "path": str(args.output)}))
        return 0

    if args.format == "text":
        for entry in entries:
            print(
                f"[{entry.category}] {entry.module}.{entry.concept} (d={entry.difficulty})"
            )
    else:
        print(json.dumps([e.to_dict() for e in entries], indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
