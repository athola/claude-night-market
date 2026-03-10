#!/usr/bin/env python3
"""Stewardship action tracker.

Records and reads stewardship actions in JSONL format.
A stewardship action is a small, voluntary improvement made
while working on a primary task.

Part of the stewardship framework. See: STEWARDSHIP.md
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def record_action(
    base_dir: Path,
    plugin: str,
    action_type: str,
    file_path: str,
    description: str,
) -> None:
    """Append a stewardship action to the JSONL tracking file.

    Creates the directory and file if they don't exist.
    Append-only: never rewrites the file.
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "plugin": plugin,
        "action_type": action_type,
        "file": file_path,
        "description": description,
    }

    actions_file = base_dir / "actions.jsonl"
    with open(actions_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_actions(
    base_dir: Path,
    plugin: str | None = None,
) -> list[dict[str, Any]]:
    """Read stewardship actions from the JSONL tracking file.

    Returns all actions, optionally filtered by plugin name.
    Skips corrupt lines gracefully.
    """
    actions_file = base_dir / "actions.jsonl"

    if not actions_file.exists():
        return []

    actions: list[dict] = []
    try:
        with open(actions_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if plugin is None or entry.get("plugin") == plugin:
                        actions.append(entry)
                except json.JSONDecodeError:
                    sys.stderr.write("stewardship_tracker: skipping corrupt line\n")
    except OSError as e:
        sys.stderr.write(f"stewardship_tracker: failed to read {actions_file}: {e}\n")

    return actions
