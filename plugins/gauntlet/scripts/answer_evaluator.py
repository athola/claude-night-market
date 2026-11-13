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
        help="Path to a challenge JSON file (ignored under --gate).",
    )
    parser.add_argument(
        "answer",
        help="The developer's answer string.",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help=(
            "Score the pending pre-commit gate challenge: on a pass, write "
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
    run cannot release the commit: no ``.gauntlet`` here, no readable
    pending gate challenge, or an unreadable staged set.

    Under ``--gate`` the challenge comes from the pending file the gate
    wrote, and the positional file is ignored. The caller's file carries
    its own answer, so scoring it would let anyone write the pass token.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    pending_path: Path | None = None
    gauntlet_dir: Path | None = None
    if args.gate:
        gauntlet_dir = _get_gauntlet_dir()
        if gauntlet_dir is None:
            print("error: --gate needs a .gauntlet directory here", file=sys.stderr)
            return 1
        pending_path = gauntlet_dir / "state" / "pending_challenge.json"
        try:
            challenge = _challenge_from_dict(json.loads(pending_path.read_text()))
        except (OSError, json.JSONDecodeError, KeyError, TypeError):
            print(
                f"error: --gate needs the pending gate challenge: {pending_path}",
                file=sys.stderr,
            )
            return 1
    else:
        challenge_path: Path = args.challenge_json
        if not challenge_path.exists():
            print(f"error: challenge file not found: {challenge_path}", file=sys.stderr)
            return 1
        challenge = _challenge_from_dict(json.loads(challenge_path.read_text()))

    result = evaluate_answer(challenge, args.answer)
    print(result)
    if gauntlet_dir is not None and pending_path is not None:
        if result is not ChallengeResult.PASS:
            return 0
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
