#!/usr/bin/env python3
r"""CLI wrapper for the leyline decision-journal contract.

Appends an entry to ``docs/tradeoffs.md`` or ``docs/lessons-learned.md`` with a
deterministic stable id, updating the active index and handling supersession.

Usage:
    python journal_append.py tradeoffs --title "Pick Postgres" \\
        --field context="Need durable storage" --phase plan

    python journal_append.py lessons --json '{"title": "...", ...}'

    python journal_append.py tradeoffs --title "Switch to gRPC" \\
        --supersedes TR-001 --dry-run

The structured fields differ by kind (see leyline:decision-journal SKILL.md).
``--json`` takes a full field object; ``--field k=v`` sets individual fields;
``--title``/``--phase``/``--status`` are convenience flags. ``--dry-run``
prints the resulting file without writing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_LEYLINE_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_LEYLINE_SRC) not in sys.path:
    sys.path.insert(0, str(_LEYLINE_SRC))

from leyline.decision_journal import apply_append  # noqa: E402 - after path setup

_FILENAME = {"tradeoffs": "tradeoffs.md", "lessons": "lessons-learned.md"}


def _parse_fields(args: argparse.Namespace) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if args.json:
        try:
            fields.update(json.loads(args.json))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"error: --json is not valid JSON: {exc}") from exc
    for pair in args.field or []:
        if "=" not in pair:
            raise SystemExit(f"--field expects key=value, got {pair!r}")
        key, value = pair.split("=", 1)
        fields[key.strip()] = value
    for flag in ("title", "phase", "status"):
        val = getattr(args, flag)
        if val:
            fields[flag] = val
    return fields


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append a decision-journal entry.")
    parser.add_argument("kind", choices=["tradeoffs", "lessons"])
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", help="Full field object as JSON")
    parser.add_argument(
        "--field", action="append", metavar="KEY=VALUE", help="Set one field"
    )
    parser.add_argument("--title")
    parser.add_argument("--phase")
    parser.add_argument("--status")
    parser.add_argument("--supersedes", help="ID this entry supersedes, e.g. TR-001")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the journal-append CLI."""
    args = _build_parser().parse_args(argv)
    fields = _parse_fields(args)
    if not fields.get("title"):
        msg = "error: an entry requires a --title (or title in --json)"
        print(msg, file=sys.stderr)
        return 2

    target = args.project_root / "docs" / _FILENAME[args.kind]
    try:
        content = apply_append(
            target, args.kind, fields, supersedes=args.supersedes, dry_run=args.dry_run
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(content)
    else:
        print(f"OK: appended to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
