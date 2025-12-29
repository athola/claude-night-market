#!/usr/bin/env python3
"""Compute regret rate from autonomy history."""

from __future__ import annotations

import argparse
import json
import textwrap
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

HISTORY_PATH = Path("telemetry/autonomy_history.json")


def main() -> None:
    """Calculate regret rate metrics from autonomy history JSON."""
    parser = argparse.ArgumentParser(description="Regret rate calculator")
    parser.add_argument("--history", type=Path, default=HISTORY_PATH)
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path to persist the JSON payload.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        help="Optional path to persist the Markdown summary.",
    )
    args = parser.parse_args()
    events = json.loads(args.history.read_text(encoding="utf-8"))
    counter = Counter(event.get("result", "correct") for event in events)
    total = sum(counter.values()) or 1
    regret_rate = counter.get("regret", 0) / total
    generated_at = datetime.now(UTC).isoformat()
    payload: dict[str, float | int | str] = {
        "total": total,
        "regret_rate": regret_rate,
        "generated_at": generated_at,
    }
    markdown = _render_markdown(payload)
    encoded = json.dumps(payload, indent=2)
    print(encoded)
    print()
    print(markdown)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(encoded + "\n", encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown + "\n", encoding="utf-8")


def _render_markdown(payload: dict[str, float | int | str]) -> str:
    percent = float(payload["regret_rate"]) * 100
    return textwrap.dedent(
        f"""\
        # Regret Rate Snapshot

        | Total Decisions | Regret Rate |
        |-----------------|-------------|
        | {payload["total"]} | {percent:.2f}% |

        _Generated at {payload["generated_at"]}._
        """
    ).strip()


if __name__ == "__main__":
    main()
