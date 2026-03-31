"""CLI for generating a challenge from the knowledge base."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# sys.path must be extended before gauntlet imports so this script works
# when invoked directly (not via the installed package).
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from gauntlet.challenges import (  # noqa: E402 - path set above
    generate_challenge,
    select_challenge_type,
)
from gauntlet.knowledge_store import KnowledgeStore  # noqa: E402 - path set above
from gauntlet.models import DeveloperProgress  # noqa: E402 - path set above
from gauntlet.progress import ProgressTracker  # noqa: E402 - path set above


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a gauntlet challenge from the knowledge base.",
    )
    parser.add_argument(
        "gauntlet_dir",
        type=Path,
        help="Path to the .gauntlet directory.",
    )
    parser.add_argument(
        "--developer",
        default="anonymous",
        help="Developer ID (e.g. git email) used for adaptive weighting.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Limit to knowledge entries related to these files.",
    )
    parser.add_argument(
        "--type",
        dest="challenge_type",
        default=None,
        help="Force a specific challenge type.",
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

    gauntlet_dir: Path = args.gauntlet_dir

    store = KnowledgeStore(gauntlet_dir)
    entries = store.query(files=args.files)

    if not entries:
        msg = {"error": "No knowledge entries found. Run /gauntlet-extract first."}
        if args.format == "json":
            print(json.dumps(msg))
        else:
            print(msg["error"])
        return 1

    tracker = ProgressTracker(gauntlet_dir)
    progress: DeveloperProgress = tracker.get_or_create(args.developer)

    entry = tracker.select_entry(progress, entries)
    challenge_type = args.challenge_type or select_challenge_type(progress)
    challenge = generate_challenge(entry, challenge_type)

    if args.format == "json":
        print(json.dumps(challenge.to_dict(), indent=2))
    else:
        print(f"[{challenge.type}] {challenge.prompt}")
        if challenge.options:
            for i, opt in enumerate(challenge.options):
                print(f"  {chr(ord('A') + i)}) {opt}")
        if challenge.hints:
            print(f"\nHint: {challenge.hints[0]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
