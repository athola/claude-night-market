"""CLI for generating a challenge from the knowledge base."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

# sys.path must be extended before gauntlet imports so this script works
# when invoked directly (not via the installed package).
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from gauntlet.challenges import (  # noqa: E402 - path set above
    generate_bank_challenge,
    generate_challenge,
    select_challenge_type,
)
from gauntlet.graph import GraphStore  # noqa: E402 - path set above
from gauntlet.graph_challenges import generate_graph_challenges  # noqa: E402 - path set above
from gauntlet.knowledge_store import KnowledgeStore  # noqa: E402 - path set above
from gauntlet.models import Challenge, DeveloperProgress, Difficulty  # noqa: E402 - path set above
from gauntlet.problem_bank import filter_problems, load_bank  # noqa: E402 - path set above
from gauntlet.progress import ProgressTracker  # noqa: E402 - path set above
from gauntlet.providers.in_loop import (  # noqa: E402 - path set above
    register_in_loop_provider_if_inside_claude_code,
)


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
        "--source",
        choices=["knowledge", "bank", "graph"],
        default="knowledge",
        help=(
            "Where the challenge comes from: the knowledge base (default), the "
            "shipped problem bank, or the code graph in .gauntlet/graph.db."
        ),
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Bank source only: draw from this problem category.",
    )
    parser.add_argument(
        "--difficulty",
        choices=[d.value for d in Difficulty],
        default=None,
        help="Bank source only: draw at this difficulty.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json).",
    )
    return parser


def _knowledge_challenge(
    gauntlet_dir: Path, args: argparse.Namespace
) -> tuple[Challenge | None, str]:
    store = KnowledgeStore(gauntlet_dir)
    entries = store.query(files=args.files)
    if not entries:
        return None, "No knowledge entries found. Run /gauntlet-extract first."
    tracker = ProgressTracker(gauntlet_dir)
    progress: DeveloperProgress = tracker.get_or_create(args.developer)
    entry = tracker.select_entry(progress, entries)
    challenge_type = args.challenge_type or select_challenge_type(progress)
    return generate_challenge(entry, challenge_type), ""


def _bank_challenge(args: argparse.Namespace) -> tuple[Challenge | None, str]:
    """Draw one bank problem and vary it so its answer cannot be memorised.

    The variation runs through the in-loop provider inside Claude Code and
    the Anthropic API outside it; this process makes that switch itself,
    because a registration in the skill's process does not reach it.
    """
    problems = filter_problems(
        load_bank(),
        category=args.category,
        difficulty=Difficulty(args.difficulty) if args.difficulty else None,
    )
    if not problems:
        return None, "No bank problems match that category and difficulty."
    register_in_loop_provider_if_inside_claude_code()
    return generate_bank_challenge(random.choice(problems)), ""  # noqa: S311 - choosing a practice problem, not a secret


def _graph_challenge(gauntlet_dir: Path) -> tuple[Challenge | None, str]:
    graph_path = gauntlet_dir / "graph.db"
    if not graph_path.exists():
        return None, f"No code graph at {graph_path}. Run /gauntlet-graph build first."
    graph = GraphStore(graph_path)
    try:
        challenges = generate_graph_challenges(graph, count=1)
    finally:
        graph.close()
    if not challenges:
        return None, "The code graph has no call edges to ask about yet."
    return challenges[0], ""


def main(argv: list[str] | None = None) -> int:
    """Emit a challenge set drawn from the gauntlet knowledge base.

    Returns the process exit code: 0 on a generated set, non-zero when the
    knowledge base is absent or holds too few entries to draw from.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    gauntlet_dir: Path = args.gauntlet_dir

    if args.source == "bank":
        challenge, error = _bank_challenge(args)
    elif args.source == "graph":
        challenge, error = _graph_challenge(gauntlet_dir)
    else:
        challenge, error = _knowledge_challenge(gauntlet_dir, args)

    if challenge is None:
        if args.format == "json":
            print(json.dumps({"error": error}))
        else:
            print(error)
        return 1

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
