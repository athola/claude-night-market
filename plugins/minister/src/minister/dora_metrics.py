"""DORA delivery-performance metrics for engineering management.

Computes the four DORA metrics (Deployment Frequency, Lead Time for Changes,
Change Failure Rate, Time to Restore Service) from git history and a list of
failure events. Classifies each metric into Elite/High/Medium/Low using
thresholds from DORA's State of DevOps research.

The module is intentionally dependency-free at import time. The CLI layer
shells out to ``git`` and ``gh`` for event collection.

Returns (JSON, when used as a CLI):
    success (bool): Whether computation succeeded.
    data.window_days (int): Measurement window in days.
    data.metrics (dict): The four metric values.
    data.tiers (dict): Per-metric classification.
    data.bottleneck (str): Weakest dimension key.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_FAILURE_LABEL = "bug"
DEFAULT_WINDOW_DAYS = 30

# Tier names ordered weakest -> strongest for ranking.
_TIER_RANK = {"Low": 0, "Medium": 1, "High": 2, "Elite": 3}


# =============================================================================
# Event types
# =============================================================================


@dataclass(frozen=True)
class DeploymentEvent:
    """A deploy to production. ``commit_at`` is the source-commit timestamp."""

    sha: str
    deployed_at: datetime
    commit_at: datetime


@dataclass(frozen=True)
class FailureEvent:
    """A production failure. ``resolved_at`` may be None for ongoing incidents."""

    opened_at: datetime
    resolved_at: datetime | None = None


# =============================================================================
# Tier classification (DORA thresholds)
# =============================================================================


def classify_deployment_frequency(per_day: float) -> str:
    """Classify DF: Elite >=1/day, High >=1/week, Medium >=1/month, else Low."""
    if per_day >= 1.0:
        return "Elite"
    if per_day >= 1 / 7:
        return "High"
    if per_day >= 1 / 30:
        return "Medium"
    return "Low"


def classify_lead_time(hours: float) -> str:
    """Classify LT: Elite <=24h, High <=1 week, Medium <=1 month, else Low."""
    if hours <= 24.0:
        return "Elite"
    if hours <= 24 * 7:
        return "High"
    if hours <= 24 * 30:
        return "Medium"
    return "Low"


def classify_change_failure_rate(rate: float) -> str:
    """Classify CFR: Elite 0-15%, High 16-30%, Medium 31-45%, Low 46%+."""
    if rate <= 0.15:
        return "Elite"
    if rate <= 0.30:
        return "High"
    if rate <= 0.45:
        return "Medium"
    return "Low"


def classify_time_to_restore(hours: float) -> str:
    """Classify TRS: Elite <1h, High <24h, Medium <1 week, else Low."""
    if hours < 1.0:
        return "Elite"
    if hours < 24.0:
        return "High"
    if hours < 24 * 7:
        return "Medium"
    return "Low"


# =============================================================================
# Aggregate
# =============================================================================


@dataclass(frozen=True)
class DORAMetrics:
    """Frozen value object holding all four DORA metric values."""

    deployment_frequency: float  # deploys per day
    lead_time_hours: float  # median commit -> deploy hours
    change_failure_rate: float  # 0.0 - 1.0
    time_to_restore_hours: float  # median resolve - open hours

    def tier(self) -> dict[str, str]:
        """Return per-metric tier classification."""
        return {
            "deployment_frequency": classify_deployment_frequency(
                self.deployment_frequency
            ),
            "lead_time": classify_lead_time(self.lead_time_hours),
            "change_failure_rate": classify_change_failure_rate(
                self.change_failure_rate
            ),
            "time_to_restore": classify_time_to_restore(self.time_to_restore_hours),
        }

    def bottleneck(self) -> str:
        """Return the tier key of the weakest metric.

        Ties break deterministically by declaration order (DF, LT, CFR, TRS).
        """
        tiers = self.tier()
        ordered_keys = (
            "deployment_frequency",
            "lead_time",
            "change_failure_rate",
            "time_to_restore",
        )
        return min(ordered_keys, key=lambda k: _TIER_RANK[tiers[k]])

    def overall_tier(self) -> str:
        """Return the weakest tier across all four metrics."""
        tiers = self.tier()
        return min(tiers.values(), key=lambda t: _TIER_RANK[t])


# =============================================================================
# Computation
# =============================================================================


def _median_or_zero(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def compute_metrics(
    deployments: list[DeploymentEvent],
    failures: list[FailureEvent],
    window_days: int = DEFAULT_WINDOW_DAYS,
    window_end: datetime | None = None,
) -> DORAMetrics:
    """Compute DORA metrics over a window.

    Args:
        deployments: Deployment events; events outside the window are filtered.
        failures: Failure events; only those opened in the window count.
        window_days: Width of the measurement window.
        window_end: Right edge of the window (defaults to now in UTC).
    """
    if window_end is None:
        window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=window_days)

    in_window_deploys = [
        d for d in deployments if window_start <= d.deployed_at <= window_end
    ]
    in_window_failures = [
        f for f in failures if window_start <= f.opened_at <= window_end
    ]

    df = len(in_window_deploys) / window_days if window_days > 0 else 0.0

    lead_times = [
        (d.deployed_at - d.commit_at).total_seconds() / 3600.0
        for d in in_window_deploys
        if d.deployed_at >= d.commit_at
    ]
    lt = _median_or_zero(lead_times)

    cfr = len(in_window_failures) / len(in_window_deploys) if in_window_deploys else 0.0

    restore_times = [
        (f.resolved_at - f.opened_at).total_seconds() / 3600.0
        for f in in_window_failures
        if f.resolved_at is not None and f.resolved_at >= f.opened_at
    ]
    trs = _median_or_zero(restore_times)

    return DORAMetrics(
        deployment_frequency=df,
        lead_time_hours=lt,
        change_failure_rate=cfr,
        time_to_restore_hours=trs,
    )


# =============================================================================
# Reporting
# =============================================================================


def format_report(m: DORAMetrics, window_days: int) -> str:
    """Render a human-readable summary suitable for terminal or PR comment."""
    tiers = m.tier()
    bottleneck = m.bottleneck()

    rows = [
        (
            "Deployment Frequency",
            f"{m.deployment_frequency:.2f}/day",
            tiers["deployment_frequency"],
            "deployment_frequency",
        ),
        (
            "Lead Time for Changes",
            f"{m.lead_time_hours:.1f} hours",
            tiers["lead_time"],
            "lead_time",
        ),
        (
            "Change Failure Rate",
            f"{m.change_failure_rate * 100:.1f}%",
            tiers["change_failure_rate"],
            "change_failure_rate",
        ),
        (
            "Time to Restore Service",
            f"{m.time_to_restore_hours:.2f} hours",
            tiers["time_to_restore"],
            "time_to_restore",
        ),
    ]

    lines = [
        f"DORA Metrics ({window_days}-day window)",
        "=" * 48,
    ]
    for label, value, tier, key in rows:
        marker = "  <- bottleneck" if key == bottleneck else ""
        lines.append(f"{label:<26} {value:>14} {tier:<7}{marker}")

    lines.append("")
    lines.append(f"Overall Tier: {m.overall_tier()} (bottleneck: {bottleneck})")
    return "\n".join(lines)


# =============================================================================
# Git / GitHub event collection (CLI helpers)
# =============================================================================


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def collect_deployments_from_git(
    branch: str,
    window_days: int,
    window_end: datetime | None = None,
    cwd: Path | None = None,
) -> list[DeploymentEvent]:
    """Treat each commit on ``branch`` as a deployment event.

    This is the simplest mapping that works for trunk-based and merge-PR
    workflows; teams with explicit deploy events should override this with a
    custom collector. ``commit_at`` and ``deployed_at`` collapse to the same
    timestamp here, giving lead time = 0; pass real deploy data for accuracy.
    """
    if window_end is None:
        window_end = datetime.now(timezone.utc)
    since = (window_end - timedelta(days=window_days)).isoformat()
    output = _run_git(
        [
            "log",
            branch,
            f"--since={since}",
            "--pretty=format:%H|%aI|%cI",
            "--no-merges",
        ],
        cwd=cwd,
    )
    events: list[DeploymentEvent] = []
    for line in output.strip().splitlines():
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        sha, author_iso, commit_iso = parts
        commit_at = datetime.fromisoformat(author_iso)
        deployed_at = datetime.fromisoformat(commit_iso)
        events.append(
            DeploymentEvent(sha=sha, deployed_at=deployed_at, commit_at=commit_at)
        )
    return events


def collect_failures_from_gh(
    failure_label: str,
    window_days: int,
    window_end: datetime | None = None,
    cwd: Path | None = None,
) -> list[FailureEvent]:
    """Pull GitHub issues with ``failure_label`` opened in the window."""
    if window_end is None:
        window_end = datetime.now(timezone.utc)
    since = (window_end - timedelta(days=window_days)).date().isoformat()
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--label",
                failure_label,
                "--state",
                "all",
                "--search",
                f"created:>={since}",
                "--json",
                "createdAt,closedAt,state",
                "--limit",
                "200",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    events: list[FailureEvent] = []
    for row in rows:
        opened_iso = row.get("createdAt")
        closed_iso = row.get("closedAt")
        if not opened_iso:
            continue
        opened_at = datetime.fromisoformat(opened_iso.replace("Z", "+00:00"))
        resolved_at = (
            datetime.fromisoformat(closed_iso.replace("Z", "+00:00"))
            if closed_iso
            else None
        )
        events.append(FailureEvent(opened_at=opened_at, resolved_at=resolved_at))
    return events


# =============================================================================
# CLI
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="minister-dora",
        description="Compute DORA metrics from local git and gh CLI.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="Measurement window in days (default: 30).",
    )
    parser.add_argument(
        "--branch",
        default="HEAD",
        help="Production branch (default: HEAD).",
    )
    parser.add_argument(
        "--failure-label",
        default=DEFAULT_FAILURE_LABEL,
        help=f"GitHub label marking prod failures (default: {DEFAULT_FAILURE_LABEL}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON payload instead of human-readable report.",
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=None,
        help="Path to the repository (default: current dir).",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    deployments = collect_deployments_from_git(
        branch=args.branch, window_days=args.window, cwd=args.repo_path
    )
    failures = collect_failures_from_gh(
        failure_label=args.failure_label, window_days=args.window, cwd=args.repo_path
    )
    metrics = compute_metrics(
        deployments=deployments, failures=failures, window_days=args.window
    )

    if args.json:
        payload: dict[str, Any] = {
            "success": True,
            "data": {
                "window_days": args.window,
                "metrics": {
                    "deployment_frequency": metrics.deployment_frequency,
                    "lead_time_hours": metrics.lead_time_hours,
                    "change_failure_rate": metrics.change_failure_rate,
                    "time_to_restore_hours": metrics.time_to_restore_hours,
                },
                "tiers": metrics.tier(),
                "overall_tier": metrics.overall_tier(),
                "bottleneck": metrics.bottleneck(),
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(metrics, window_days=args.window))
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
