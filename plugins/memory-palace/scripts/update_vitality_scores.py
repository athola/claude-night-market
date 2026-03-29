#!/usr/bin/env python3
"""Decay vitality scores and surface tending queues."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
DEFAULT_FILE = PLUGIN_ROOT / "data" / "indexes" / "vitality-scores.yaml"
DEFAULT_QUEUE_FILE = PLUGIN_ROOT / "data" / "indexes" / "vitality-tending-queue.json"


def load_vitality(path: Path) -> dict[str, Any]:
    """Load vitality scores YAML into a dictionary."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _is_evergreen(payload: dict[str, Any]) -> bool:
    maturity = payload.get("maturity") or payload.get("state")
    return isinstance(maturity, str) and maturity.lower() == "evergreen"


def _persist_queue(queue: dict[str, Any], queue_path: Path) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")


def decay_entries(data: dict[str, Any], decay: int) -> dict[str, Any]:
    """Apply decay to vitality entries and build tending queue."""
    entries = data.get("entries", {})
    stale_threshold = data.get("metadata", {}).get("stale_threshold", 10)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    queue: dict[str, list[str]] = {"stale": [], "probation_overdue": []}

    for entry_id, payload in entries.items():
        if _is_evergreen(payload):
            continue
        vitality = int(payload.get("vitality", 0)) - decay
        vitality = max(vitality, 0)
        payload["vitality"] = vitality
        payload["history"] = payload.get("history", [])
        payload["history"].append({"event": "decay", "delta": -decay, "at": now})
        if vitality < stale_threshold:
            queue["stale"].append(entry_id)

        state = payload.get("state", "")
        last_accessed = payload.get("last_accessed")
        if state == "probation" and last_accessed:
            last_dt = dt.datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
            overdue_days = 14
            if (dt.datetime.now(dt.timezone.utc) - last_dt).days >= overdue_days:
                queue["probation_overdue"].append(entry_id)

    metadata = data.setdefault("metadata", {})
    metadata["last_recomputed"] = now
    return queue


def main() -> None:
    """Update vitality scores and emit queue summaries."""
    parser = argparse.ArgumentParser(
        description="Update vitality scores and emit tending queues"
    )
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--decay", type=int, default=None, help="Override decay amount")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--queue-file",
        type=Path,
        default=DEFAULT_QUEUE_FILE,
        help="Optional path to write tending queue JSON output.",
    )
    args = parser.parse_args()

    data = load_vitality(args.file)
    decay = args.decay or data.get("metadata", {}).get("decay_per_day", 1)
    queue = decay_entries(data, decay)

    if not args.dry_run:
        args.file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    if args.queue_file:
        _persist_queue(queue, Path(args.queue_file))
    print(json.dumps({"decay": decay, "queue": queue}, indent=2))


if __name__ == "__main__":
    main()
