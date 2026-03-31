"""CLI for displaying developer challenge progress statistics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# sys.path must be extended before gauntlet imports so this script works
# when invoked directly (not via the installed package).
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from gauntlet.progress import ProgressTracker  # noqa: E402 - path set above

_ALL_CATEGORIES = [
    "business_logic",
    "architecture",
    "data_flow",
    "api_contract",
    "pattern",
    "dependency",
    "error_handling",
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Show developer challenge progress statistics.",
    )
    parser.add_argument(
        "gauntlet_dir",
        type=Path,
        help="Path to the .gauntlet directory.",
    )
    parser.add_argument(
        "--developer",
        default="anonymous",
        help="Developer ID (e.g. git email).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    tracker = ProgressTracker(args.gauntlet_dir)
    progress = tracker.get_or_create(args.developer)

    overall = progress.overall_accuracy()
    total = len(progress.history)
    streak = progress.streak
    last_seen = max(progress.last_seen.values()) if progress.last_seen else "never"
    category_stats = {
        cat: round(progress.category_accuracy(cat), 3) for cat in _ALL_CATEGORIES
    }

    if args.format == "json":
        print(
            json.dumps(
                {
                    "developer_id": progress.developer_id,
                    "accuracy": round(overall, 3),
                    "streak": streak,
                    "total_challenges": total,
                    "last_session": last_seen,
                    "by_category": category_stats,
                },
                indent=2,
            )
        )
    else:
        print(f"Developer : {progress.developer_id}")
        print(f"Accuracy  : {overall:.1%}")
        print(f"Streak    : {streak}")
        print(f"Total     : {total}")
        print(f"Last seen : {last_seen}")
        print()
        print("By category:")
        for cat, acc in category_stats.items():
            print(f"  {cat:<20} {acc:.1%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
