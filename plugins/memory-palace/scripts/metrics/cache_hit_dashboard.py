#!/usr/bin/env python3
"""Summarize cache hit metrics from telemetry csv."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

TELEMETRY_FILE = Path("data/telemetry/memory-palace.csv")
OUTPUT_DOC = Path("docs/metrics/cache-hit-dashboard.md")


def load_rows(path: Path) -> list[dict[str, str]]:
    """Load rows from a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        A list of dictionaries representing rows in the CSV file.
        Returns an empty list if the file doesn't exist.

    """
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize(rows: list[dict[str, str]]) -> dict[str, Counter]:
    """Summarize telemetry data by counting modes and decisions.

    Args:
        rows: List of dictionaries containing telemetry data.

    Returns:
        A dictionary with two Counters - one for modes and one for decisions.

    """
    mode_counter = Counter()
    decision_counter = Counter()
    for row in rows:
        mode_counter[row.get("mode", "unknown")] += 1
        decision_counter[row.get("decision", "unknown")] += 1
    return {"mode": mode_counter, "decision": decision_counter}


def render_markdown(summary: dict[str, Counter]) -> str:
    lines = ["# Cache Hit Dashboard", ""]
    lines.append("## Decisions")
    lines.append("| Decision | Count |")
    lines.append("|----------|-------|")
    for decision, count in summary["decision"].most_common():
        lines.append(f"| {decision} | {count} |")
    lines.append("")
    lines.append("## Modes")
    lines.append("| Mode | Count |")
    lines.append("|------|-------|")
    for mode, count in summary["mode"].most_common():
        lines.append(f"| {mode} | {count} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Main entry point for the cache hit dashboard generator."""
    parser = argparse.ArgumentParser(description="Generate cache hit dashboard markdown")
    parser.add_argument("--telemetry", type=Path, default=TELEMETRY_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_DOC)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    rows = load_rows(args.telemetry)
    summary = summarize(rows)
    markdown = render_markdown(summary)
    if args.preview:
        print(markdown)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Wrote dashboard to {args.output}")


if __name__ == "__main__":
    main()
