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

from gauntlet.models import Challenge  # noqa: E402 - path set above
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
