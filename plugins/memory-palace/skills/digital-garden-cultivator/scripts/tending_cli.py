#!/usr/bin/env python3
"""Surface actionable tending queues from vitality scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

DEFAULT_VITALITY = Path("data/indexes/vitality-scores.yaml")


def load_vitality(path: Path) -> dict[str, Any]:
    """Load vitality scores YAML."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_queue(data: dict[str, Any]) -> dict[str, list[str]]:
    """Build tending queues grouped by state."""
    entries = data.get("entries", {})
    stale_threshold = data.get("metadata", {}).get("stale_threshold", 10)
    queue = {"stale": [], "probation": [], "evergreen": []}
    for entry_id, payload in entries.items():
        vitality = int(payload.get("vitality", 0))
        state = payload.get("state", "")
        if vitality < stale_threshold:
            queue["stale"].append(entry_id)
        if state == "probation":
            queue["probation"].append(entry_id)
        if state == "evergreen":
            queue["evergreen"].append(entry_id)
    for _key, values in queue.items():
        values.sort()
    return queue


def main() -> None:
    """Generate tending queue markdown from vitality file."""
    parser = argparse.ArgumentParser(description="Garden tending queue generator")
    parser.add_argument("--vitality-file", type=Path, default=DEFAULT_VITALITY)
    parser.add_argument("--export", type=Path, help="Optional path to export JSON queue")
    args = parser.parse_args()

    data = load_vitality(args.vitality_file)
    queue = build_queue(data)
    print(json.dumps(queue, indent=2))
    if args.export:
        args.export.write_text(json.dumps(queue, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
