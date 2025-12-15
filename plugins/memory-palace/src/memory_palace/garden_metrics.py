#!/usr/bin/env python3
"""Calculate and report key metrics for a digital garden.

Process a JSON file representing a digital garden to derive actionable insights
into its health and maintenance. Quantify 'link density' to reflect
interconnectedness and 'recency of maintenance' to highlight areas potentially
needing attention. Output can be formatted for human readability, brief
summaries, or Prometheus ingestion, aiding continuous tending of a digital
knowledge base.

Expected JSON schema for garden files:

{
  "garden": {
    "plots": [
      {
        "name": "plot-name",
        "inbound_links": ["a", "b"],
        "outbound_links": ["c"],
        "last_tended": "2025-11-20T12:00:00"
      }
    ]
  }
}
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate link density and tending recency for a digital garden JSON file.",
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to garden JSON file (see docstring schema).",
    )
    parser.add_argument(
        "--now",
        type=str,
        default=None,
        help="Override current timestamp (ISO 8601) for reproducible runs.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "brief", "prometheus"],
        default="json",
        help="Output format (json, brief one-line, or prometheus).",
    )
    parser.add_argument(
        "--label",
        type=str,
        default=None,
        help="Optional label for Prometheus output (defaults to file stem).",
    )
    parser.add_argument(
        "--tending-queue",
        type=Path,
        default=None,
        help="Optional path to the vitality tending queue emitted by update_vitality_scores.",
    )
    return parser.parse_args()


def iso_to_datetime(value: str) -> datetime:
    """Convert an ISO 8601 string to a timezone-aware datetime object."""
    return datetime.fromisoformat(value).astimezone(UTC)


def compute_metrics(data: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Compute metrics for the garden.

    Args:
        data: The garden data from the JSON file.
        now: The current timestamp.

    Returns:
        A dictionary of computed metrics.

    """
    plots = data.get("garden", {}).get("plots", [])
    if not plots:
        return {"plots": 0, "link_density": 0.0, "avg_days_since_tend": None}

    link_counts = []
    days_since_tend = []

    for plot in plots:
        inbound = plot.get("inbound_links", []) or []
        outbound = plot.get("outbound_links", []) or []
        link_counts.append(len(set(inbound)) + len(set(outbound)))

        last_tended = plot.get("last_tended")
        if last_tended:
            dt = iso_to_datetime(last_tended)
            days = (now - dt).total_seconds() / 86400
            days_since_tend.append(days)

    avg_links = mean(link_counts) if link_counts else 0.0
    avg_days = mean(days_since_tend) if days_since_tend else None

    return {
        "plots": len(plots),
        "link_density": round(avg_links, 2),
        "avg_days_since_tend": round(avg_days, 2) if avg_days is not None else None,
    }


def summarize_tending_queue(queue_path: Path) -> dict[str, int]:
    """Summarize tending queue entries for telemetry."""
    if not queue_path.exists():
        return {"stale": 0, "probation_overdue": 0}
    queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
    return {
        "stale": len(queue_data.get("stale", [])),
        "probation_overdue": len(queue_data.get("probation_overdue", [])),
    }


def compute_garden_metrics(
    path: Path,
    now: datetime | None = None,
    queue_path: Path | None = None,
) -> dict[str, Any]:
    """Load a digital garden file; compute its key metrics.

    Read the specified JSON garden file; calculate metrics such as link density
    and average days since last tending. Allow overriding the current timestamp
    for reproducible metric calculations.

    Args:
        path: Path to the digital garden's JSON file.
        now: Optional `datetime` object to use as the current time. If not
             provided, use the actual current UTC time.
        queue_path: Optional path to tending queue data for queue-aware metrics.

    Returns:
        Dictionary containing the computed metrics.

    """
    current_time = now or datetime.now(UTC)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    metrics = compute_metrics(data, current_time)
    if queue_path:
        metrics["tending_queue"] = summarize_tending_queue(queue_path)
    return metrics


def main() -> int:
    """Parse arguments, compute metrics, and print the output."""
    args = parse_args()
    now = datetime.fromisoformat(args.now) if args.now else datetime.now(UTC)

    compute_garden_metrics(args.path, now, args.tending_queue)
    if args.format == "brief":
        pass
    elif args.format == "prometheus":
        label = args.label or args.path.stem

        def line(metric: str, value: Any) -> str:
            return f'{metric}{{garden="{label}"}} {value}'

    else:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
