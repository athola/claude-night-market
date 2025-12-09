#!/usr/bin/env python3
"""Estimate token/context savings from cache interceptions."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

TELEMETRY_FILE = Path("data/telemetry/memory-palace.csv")


def estimate_savings(rows: list[dict[str, str]]) -> int:
    """Estimate total token savings from cache interceptions.

    Args:
        rows: List of dictionaries containing telemetry data.

    Returns:
        Total estimated number of tokens saved.

    """
    total = 0
    for row in rows:
        if row.get("decision") in {"augment", "block"}:
            total += int(row.get("estimated_token_savings", "800"))
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate context/token savings")
    parser.add_argument("--telemetry", type=Path, default=TELEMETRY_FILE)
    args = parser.parse_args()

    with args.telemetry.open("r", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    savings = estimate_savings(rows)
    print(f"Estimated tokens saved: {savings}")


if __name__ == "__main__":
    main()
