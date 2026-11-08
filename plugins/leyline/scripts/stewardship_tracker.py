#!/usr/bin/env python3
"""Stewardship action tracker.

Records and reads stewardship actions in JSONL format.
A stewardship action is a small, voluntary improvement made
while working on a primary task.

Part of the stewardship framework. See: STEWARDSHIP.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StewardshipAction:
    """A single stewardship action: a small, voluntary improvement."""

    plugin: str
    action_type: str
    file_path: str
    description: str
    virtue: str | None = None


def record_action(base_dir: Path, action: StewardshipAction) -> None:
    """Append a stewardship action to the JSONL tracking file.

    Creates the directory and file if they don't exist.
    Append-only: never rewrites the file.

    Args:
        base_dir: Directory where actions.jsonl is stored.
        action: The stewardship action to record. Its ``virtue`` is
            omitted from the entry when None.
    """
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.stderr.write(f"stewardship_tracker: failed to create {base_dir}: {e}\n")
        return

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plugin": action.plugin,
        "action_type": action.action_type,
        "file": action.file_path,
        "description": action.description,
    }
    if action.virtue is not None:
        entry["virtue"] = action.virtue

    actions_file = base_dir / "actions.jsonl"
    try:
        with open(actions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        sys.stderr.write(
            f"stewardship_tracker: failed to write to {actions_file}: {e}\n"
        )


def read_actions(
    base_dir: Path,
    plugin: str | None = None,
    virtue: str | None = None,
) -> list[dict[str, Any]]:
    """Read stewardship actions from the JSONL tracking file.

    Returns all actions, optionally filtered by plugin name and/or virtue.
    Skips corrupt lines gracefully.

    Args:
        base_dir: Directory where actions.jsonl is stored.
        plugin: When provided, return only entries for this plugin.
        virtue: When provided, return only entries with this virtue value.
            Entries that lack a virtue field are excluded when filtering.
    """
    actions_file = base_dir / "actions.jsonl"

    if not actions_file.exists():
        return []

    actions: list[dict[str, Any]] = []
    try:
        with open(actions_file, encoding="utf-8") as f:
            for line_num, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if plugin is not None and entry.get("plugin") != plugin:
                        continue
                    if virtue is not None and entry.get("virtue") != virtue:
                        continue
                    actions.append(entry)
                except json.JSONDecodeError as exc:
                    max_preview = 80
                    truncated = len(line) > max_preview
                    preview = line[:max_preview] + "..." if truncated else line
                    sys.stderr.write(
                        f"stewardship_tracker: skipping corrupt line {line_num} "
                        f"in {actions_file}: {exc.msg} ({preview!r})\n"
                    )
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"stewardship_tracker: failed to read {actions_file}: {e}\n")

    return actions


#: The five virtues the stewardship skill names. A virtue outside them
#: would be counted as a sixth by the health report.
VIRTUES = ("care", "curiosity", "humility", "diligence", "foresight")

#: Where stewardship-health reads actions, relative to the project root.
DEFAULT_DIR = Path(".claude") / "stewardship"


def main(argv: list[str] | None = None) -> int:
    """Record a stewardship action from the command line.

    The stewardship skill asks for a small action whenever one of its
    questions triggers. This is how that action reaches the health
    report, which reads the same file.
    """
    parser = argparse.ArgumentParser(description="Record a stewardship action.")
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record", help="append one action")
    record.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    record.add_argument("--plugin", required=True)
    record.add_argument("--type", dest="action_type", required=True)
    record.add_argument("--file", dest="file_path", required=True)
    record.add_argument("--description", required=True)
    record.add_argument("--virtue", choices=VIRTUES)
    args = parser.parse_args(argv)

    record_action(
        args.dir,
        StewardshipAction(
            plugin=args.plugin,
            action_type=args.action_type,
            file_path=args.file_path,
            description=args.description,
            virtue=args.virtue,
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
