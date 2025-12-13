#!/usr/bin/env python3
"""Recalculate autonomy levels from decision history."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memory_palace.lifecycle.autonomy_state import AutonomyStateStore

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_HISTORY = PLUGIN_ROOT / "telemetry" / "autonomy_history.json"
DEFAULT_STATE = PLUGIN_ROOT / "data" / "state" / "autonomy-state.yaml"
DEFAULT_ALERTS = PLUGIN_ROOT / "telemetry" / "alerts" / "autonomy.json"
GLOBAL_MIN_EVENTS = 20
GLOBAL_PROMOTE_ACCURACY = 0.9
GLOBAL_PROMOTE_REGRET = 0.02
GLOBAL_MAX_LEVEL = 5
GLOBAL_DEMOTE_REGRET = 0.05
DOMAIN_MIN_EVENTS = 10
DOMAIN_PROMOTE_ACCURACY = 0.92
DOMAIN_PROMOTE_REGRET = 0.015
DOMAIN_MAX_LEVEL = 5
DOMAIN_DEMOTE_REGRET = 0.05
MIN_LEVEL = 0


@dataclass
class HistoryStats:
    """Aggregate accuracy/regret stats for autonomy decisions."""

    total: int
    correct: int
    regret: int
    accuracy: float
    regret_rate: float


def load_history(path: Path) -> list[dict[str, Any]]:
    """Load autonomy decision history from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"History file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def compute_stats(events: list[dict[str, Any]]) -> tuple[HistoryStats, dict[str, HistoryStats]]:
    """Compute aggregate and per-domain accuracy/regret statistics."""
    if not events:
        return HistoryStats(0, 0, 0, 0.0, 0.0), {}

    domain_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        for domain in event.get("domains", []) or ["*"]:
            domain_events[domain].append(event)

    def stats(items: list[dict[str, Any]]) -> HistoryStats:
        total = len(items)
        counts = Counter(item.get("result", "correct") for item in items)
        correct = counts.get("correct", 0)
        regret = counts.get("regret", 0)
        accuracy = correct / total if total else 0.0
        regret_rate = regret / total if total else 0.0
        return HistoryStats(total, correct, regret, accuracy, regret_rate)

    aggregate = stats(events)
    per_domain = {domain: stats(items) for domain, items in domain_events.items()}
    return aggregate, per_domain


def _global_demote_command() -> list[str]:
    return ["python", "-m", "memory_palace.cli", "autonomy", "demote"]


def _domain_demote_command(domain: str) -> list[str]:
    return [
        "python",
        "-m",
        "memory_palace.cli",
        "garden",
        "demote",
        "--domain",
        domain,
    ]


def compute_regret_alerts(
    events: list[dict[str, Any]],
    *,
    global_threshold: float = 0.05,
    domain_threshold: float | None = None,
) -> dict[str, Any]:
    """Derive actionable regret alerts from event history."""
    aggregate, per_domain = compute_stats(events)
    alerts: dict[str, Any] = {}
    if domain_threshold is None:
        domain_threshold = global_threshold

    if aggregate.total and aggregate.regret_rate >= global_threshold:
        alerts["global"] = {
            "regret_rate": aggregate.regret_rate,
            "total_decisions": aggregate.total,
            "recommended_command": _global_demote_command(),
        }

    for domain, stats in per_domain.items():
        if domain == "*" or not stats.total:
            continue
        if stats.regret_rate >= domain_threshold:
            alerts[domain] = {
                "regret_rate": stats.regret_rate,
                "total_decisions": stats.total,
                "recommended_command": _domain_demote_command(domain),
            }

    return alerts


def write_alerts_file(alerts: dict[str, Any], path: Path) -> Path:
    """Persist alert payload for downstream scoring jobs."""
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total_alerts": len(alerts),
        "alerts": alerts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def adjust_state(
    store: AutonomyStateStore,
    aggregate: HistoryStats,
    per_domain: dict[str, HistoryStats],
    dry_run: bool,
) -> dict[str, Any]:
    """Adjust global and per-domain autonomy levels based on stats."""
    state = store.load()
    changes: dict[str, Any] = {
        "global_before": state.current_level,
        "global_after": state.current_level,
        "domains": {},
    }

    if aggregate.total >= GLOBAL_MIN_EVENTS:
        if (
            aggregate.accuracy >= GLOBAL_PROMOTE_ACCURACY
            and aggregate.regret_rate <= GLOBAL_PROMOTE_REGRET
            and state.current_level < GLOBAL_MAX_LEVEL
        ):
            changes["global_after"] = state.current_level + 1
            if not dry_run:
                store.set_level(changes["global_after"])
        elif aggregate.regret_rate >= GLOBAL_DEMOTE_REGRET and state.current_level > MIN_LEVEL:
            changes["global_after"] = state.current_level - 1
            if not dry_run:
                store.set_level(changes["global_after"])

    for domain, stats in per_domain.items():
        if domain == "*":
            continue
        before = state.domain_controls.get(domain)
        level_before = before.level if before else state.current_level
        level_after = level_before
        if stats.total >= DOMAIN_MIN_EVENTS:
            if (
                stats.accuracy >= DOMAIN_PROMOTE_ACCURACY
                and stats.regret_rate <= DOMAIN_PROMOTE_REGRET
                and level_before < DOMAIN_MAX_LEVEL
            ):
                level_after += 1
                if not dry_run:
                    store.set_level(level_after, domain=domain)
            elif stats.regret_rate >= DOMAIN_DEMOTE_REGRET and level_before > MIN_LEVEL:
                level_after -= 1
                if not dry_run:
                    store.set_level(level_after, domain=domain)
        changes["domains"][domain] = {
            "before": level_before,
            "after": level_after,
            "stats": stats.__dict__,
        }

    return changes


def main() -> None:
    """Update autonomy state based on decision history."""
    parser = argparse.ArgumentParser(description="Update autonomy state based on decision history")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--alerts-json",
        type=Path,
        nargs="?",
        const=DEFAULT_ALERTS,
        default=None,
        help="Optional path for regret alerts JSON (defaults to telemetry/alerts/autonomy.json).",
    )
    parser.add_argument(
        "--alerts-threshold",
        type=float,
        default=0.05,
        help="Regret-rate threshold (0-1) for emitting alerts.",
    )
    args = parser.parse_args()

    events = load_history(args.history)
    aggregate, per_domain = compute_stats(events)
    store = AutonomyStateStore(state_path=args.state)
    changes = adjust_state(store, aggregate, per_domain, args.dry_run)
    alerts = compute_regret_alerts(
        events,
        global_threshold=args.alerts_threshold,
        domain_threshold=args.alerts_threshold,
    )
    if args.alerts_json:
        write_alerts_file(alerts, args.alerts_json)

    print(
        json.dumps(
            {"aggregate": aggregate.__dict__, "changes": changes, "alerts": alerts},
            indent=2,
        )
    )


if __name__ == "__main__":
    PLUGIN_ROOT = Path(__file__).resolve().parents[1]
    main()
