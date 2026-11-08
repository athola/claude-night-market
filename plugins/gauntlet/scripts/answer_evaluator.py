"""CLI for scoring a developer's answer against a challenge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# sys.path must be extended before gauntlet imports so this script works
# when invoked directly (not via the installed package).
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "hooks"))

from precommit_gate import (  # noqa: E402 - path set above
    _get_gauntlet_dir,
    _get_staged_hash,
    write_pass_token,
)

from gauntlet.models import Challenge, ChallengeResult  # noqa: E402 - path set above
from gauntlet.scoring import evaluate_answer  # noqa: E402 - path set above


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score a developer answer against a challenge.",
    )
    parser.add_argument(
        "challenge_json",
        type=Path,
        help="Path to a challenge JSON file.",
    )
    parser.add_argument(
        "answer",
        help="The developer's answer string.",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help=(
            "The challenge came from the pre-commit gate: on a pass, write "
            "the one-time token that releases the commit of the staged files."
        ),
    )
    return parser


def _challenge_from_dict(data: dict[str, Any]) -> Challenge:
    return Challenge(
        id=data["id"],
        type=data["type"],
        knowledge_entry_id=data["knowledge_entry_id"],
        difficulty=data["difficulty"],
        prompt=data["prompt"],
        context=data["context"],
        answer=data["answer"],
        hints=data.get("hints", []),
        scope_files=data.get("scope_files", []),
        options=data.get("options"),
    )


def main(argv: list[str] | None = None) -> int:
    """Score a submitted answer against a challenge file.

    Returns the process exit code: 0 when the answer was scored, non-zero
    when the challenge file is missing or unreadable, or when a ``--gate``
    pass cannot release the commit: no ``.gauntlet`` here, a challenge
    other than the pending one, or an unreadable staged set.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    challenge_path: Path = args.challenge_json
    if not challenge_path.exists():
        print(f"error: challenge file not found: {challenge_path}", file=sys.stderr)
        return 1

    data = json.loads(challenge_path.read_text())
    challenge = _challenge_from_dict(data)
    result = evaluate_answer(challenge, args.answer)
    print(result)
    if args.gate and result is ChallengeResult.PASS:
        gauntlet_dir = _get_gauntlet_dir()
        if gauntlet_dir is None:
            print("error: --gate needs a .gauntlet directory here", file=sys.stderr)
            return 1
        # Only the challenge the gate set releases the commit, so a passed
        # practice problem cannot stand in for it.
        pending_path = gauntlet_dir / "state" / "pending_challenge.json"
        try:
            pending_id = json.loads(pending_path.read_text()).get("id")
        except (OSError, json.JSONDecodeError):
            pending_id = None
        if pending_id != challenge.id:
            print(
                "error: --gate scores only the pending gate challenge", file=sys.stderr
            )
            return 1
        # A failing git call hashes to "", which the gate's own failing
        # call would match without any staged set behind it.
        staged_hash = _get_staged_hash()
        if not staged_hash:
            print("error: --gate cannot read the staged files", file=sys.stderr)
            return 1
        write_pass_token(gauntlet_dir, staged_hash)
        pending_path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
