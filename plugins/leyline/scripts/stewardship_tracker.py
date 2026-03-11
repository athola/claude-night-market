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
from typing import Any, Optional


def record_action(
    base_dir: Path,
    plugin: str,
    action_type: str,
    file_path: str,
    description: str,
    virtue: Optional[str] = None,  # noqa: UP045
) -> None:
    """Append a stewardship action to the JSONL tracking file.

    Creates the directory and file if they don't exist.
    Append-only: never rewrites the file.

    Args:
        base_dir: Directory where actions.jsonl is stored.
        plugin: Plugin name originating the action.
        action_type: Category of stewardship action.
        file_path: File path the action relates to.
        description: Human-readable description of the action.
        virtue: Optional virtue associated with this action.
            Omitted from the entry when None.
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    entry: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "plugin": plugin,
        "action_type": action_type,
        "file": file_path,
        "description": description,
    }
    if virtue is not None:
        entry["virtue"] = virtue

    actions_file = base_dir / "actions.jsonl"
    with open(actions_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_actions(
    base_dir: Path,
    plugin: Optional[str] = None,  # noqa: UP045
    virtue: Optional[str] = None,  # noqa: UP045
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
            for raw_line in f:
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
                except json.JSONDecodeError:
                    sys.stderr.write("stewardship_tracker: skipping corrupt line\n")
    except OSError as e:
        sys.stderr.write(f"stewardship_tracker: failed to read {actions_file}: {e}\n")

    return actions
