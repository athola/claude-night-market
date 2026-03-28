#!/usr/bin/env python3
"""Stop hook: final sweep for unfiled deferred items.

Reads the session ledger, retries any entries where
filed=false, prints summary, cleans up.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _ledger_utils import get_ledger_path as _get_ledger_path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def get_ledger_path() -> Path:
    """Return the session-scoped ledger path."""
    return _get_ledger_path()


def call_capture_script(title: str, source: str) -> dict:
    """Call deferred_capture.py for a single unfiled item.

    Returns parsed JSON output or an error dict.
    """
    script = SCRIPT_DIR / "deferred_capture.py"
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--title",
                title,
                "--source",
                source,
                "--context",
                "Captured by Stop hook sweep",
                "--captured-by",
                "safety-net",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"status": "error", "message": result.stderr.strip()}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
        return {"status": "error", "message": str(exc)}


def process_ledger(ledger_path: Path) -> dict:
    """Read ledger, retry unfiled entries, clean up.

    Returns stats dict with keys: filed, already_filed, failed, duplicates.
    """
    stats: dict[str, int] = {
        "filed": 0,
        "already_filed": 0,
        "failed": 0,
        "duplicates": 0,
    }

    if not ledger_path.exists():
        return stats

    try:
        with open(ledger_path) as f:
            entries = json.load(f)
    except (OSError, json.JSONDecodeError):
        return stats

    if not entries:
        ledger_path.unlink(missing_ok=True)
        return stats

    all_filed = True
    for entry in entries:
        if entry.get("filed"):
            stats["already_filed"] += 1
            continue

        result = call_capture_script(
            entry.get("title", "Untitled deferred item"),
            entry.get("source", "unknown"),
        )
        status = result.get("status", "error")
        if status == "created":
            entry["filed"] = True
            entry["issue_number"] = result.get("number")
            stats["filed"] += 1
        elif status == "duplicate":
            entry["filed"] = True
            entry["issue_number"] = result.get("number")
            stats["duplicates"] += 1
        else:
            stats["failed"] += 1
            all_filed = False

    if all_filed:
        ledger_path.unlink(missing_ok=True)
    else:
        with open(ledger_path, "w") as f:
            json.dump(entries, f, indent=2)
        sys.stderr.write(
            f"deferred_item_sweep: {stats['failed']} items remain unfiled. "
            f"Ledger preserved at {ledger_path}\n"
        )

    return stats


def main() -> None:
    """Stop hook entry point."""
    ledger_path = get_ledger_path()
    stats = process_ledger(ledger_path)

    total = stats["filed"] + stats["duplicates"]
    if total > 0 or stats["failed"] > 0:
        sys.stderr.write(
            f"Deferred items: {total} filed, "
            f"{stats['duplicates']} duplicate, "
            f"{stats['failed']} failed\n"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        sys.stderr.write(f"deferred_item_sweep: {traceback.format_exc()}")
