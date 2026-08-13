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

from gauntlet.models import AnswerRecord  # noqa: E402 - path set above
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
        "--record",
        metavar="JSON",
        help=(
            "Persist an answer record instead of printing stats. Accepts a JSON "
            "object with the AnswerRecord fields. Used by reviewing agents "
            "outside the challenge loop, such as /pr-review --interactive."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _record_answer(tracker: ProgressTracker, developer: str, raw: str) -> int:
    """Persist one answer record supplied as JSON on the command line.

    This is a trust boundary: the payload arrives from another process, so
    both the JSON and the record fields are validated before anything is
    written. A rejected payload persists nothing.
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: --record is not valid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("error: --record must be a JSON object", file=sys.stderr)
        return 1

    # record_answer() stamps answered_at with the current time, so callers
    # do not supply it. from_dict still requires the key to be present.
    payload.setdefault("answered_at", "")

    try:
        record = AnswerRecord.from_dict(payload)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"error: invalid answer record: {exc}", file=sys.stderr)
        return 1

    progress = tracker.get_or_create(developer)
    tracker.record_answer(progress, record)
    print(
        f"recorded {record.result} on {record.category} "
        f"(streak {progress.streak}, {len(progress.history)} total)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Record an answer with ``--record``, or print progress stats."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    tracker = ProgressTracker(args.gauntlet_dir)

    if args.record is not None:
        return _record_answer(tracker, args.developer, args.record)

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
