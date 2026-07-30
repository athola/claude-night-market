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
    data.overall_tier (str): Weakest tier across all four metrics.
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
from typing import Any, Literal

DEFAULT_FAILURE_LABEL = "bug"
DEFAULT_WINDOW_DAYS = 30

# Issue #529: constrain tier strings to a Literal so a typo
# ("elite" lowercase, "medum") fails type-check at the boundary
# rather than silently misclassifying.
# Issue #527: "N/A" extends the alias for metrics that have no signal
# (empty input). N/A is excluded from bottleneck and overall_tier
# ranking so a team that hasn't shipped is not classified Elite.
Tier = Literal["Low", "Medium", "High", "Elite", "N/A"]

# Tier names ordered weakest -> strongest for ranking.
# N/A is intentionally not in this map; rankers must skip N/A entries.
_TIER_RANK: dict[Tier, int] = {"Low": 0, "Medium": 1, "High": 2, "Elite": 3}

# DORA tier thresholds (State of DevOps research). Named so a reviewer
# changing a boundary edits one constant instead of hunting for a bare
# literal buried in a comparison.
_LT_ELITE_MAX_HOURS = 24.0
_TRS_HIGH_MAX_HOURS = 24.0
_CFR_ELITE_MAX_RATE = 0.15
_CFR_HIGH_MAX_RATE = 0.30
_CFR_MEDIUM_MAX_RATE = 0.45

# Expected `git log --pretty=format:%H|%aI|%cI` field count (sha, author
# date, commit date). Any other count means the pretty-format broke.
_GIT_LOG_PRETTY_FIELD_COUNT = 3


# =============================================================================
# Collection result envelope
# =============================================================================


@dataclass(frozen=True)
class CollectionResult:
    """Envelope for collector output.

    A bare list cannot distinguish "we found zero events" from "the
    collector failed and we have no signal." This envelope carries the
    distinction so the CLI can refuse to silently classify a broken
    `gh` invocation as Elite (issue #525).
    """

    events: list[Any]
    partial: bool = False
    warnings: tuple[str, ...] = ()


# =============================================================================
# Event types
# =============================================================================


def _require_aware(name: str, dt: datetime) -> None:
    """Issue #529: reject naive datetimes at construction.

    A naive datetime silently breaks the window-comparison arithmetic
    in compute_metrics; callers that pass datetime.now() (instead of
    datetime.now(timezone.utc)) would discover this deep inside the
    metric calculation. Catching at the boundary makes the bug
    reachable from a single line of test scaffolding.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(
            f"{name} must be tz-aware (timezone-attached); got naive datetime {dt!r}"
        )


@dataclass(frozen=True)
class DeploymentEvent:
    """A deploy to production. ``commit_at`` is the source-commit timestamp.

    Both timestamps must be tz-aware (issue #529). Naive datetimes are
    rejected at construction so window-comparison arithmetic never
    silently uses mixed-offset values.
    """

    sha: str
    deployed_at: datetime
    commit_at: datetime

    def __post_init__(self) -> None:
        """Reject naive deployed_at/commit_at so downstream window math never mixes offsets."""
        _require_aware("deployed_at", self.deployed_at)
        _require_aware("commit_at", self.commit_at)


@dataclass(frozen=True)
class FailureEvent:
    """A production failure. ``resolved_at`` may be None for ongoing incidents.

    Invariants enforced at construction (issue #529):

    - ``opened_at`` and (if set) ``resolved_at`` must be tz-aware.
    - ``resolved_at`` (if set) must be >= ``opened_at``. A backwards
      pair is a data-integrity bug, not a TRS sample to silently
      filter downstream.
    """

    opened_at: datetime
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        """Reject naive datetimes and a resolved_at that precedes opened_at."""
        _require_aware("opened_at", self.opened_at)
        if self.resolved_at is not None:
            _require_aware("resolved_at", self.resolved_at)
            if self.resolved_at < self.opened_at:
                raise ValueError(
                    f"resolved_at {self.resolved_at!r} is before "
                    f"opened_at {self.opened_at!r}; backwards events "
                    "are a data-integrity bug, not a TRS sample"
                )


# =============================================================================
# Tier classification (DORA thresholds)
# =============================================================================


def classify_deployment_frequency(per_day: float | None) -> Tier:
    """Classify DF: Elite >=1/day, High >=1/week, Medium >=1/month, else Low.

    Issue #527: None input maps to "N/A".
    """
    if per_day is None:
        return "N/A"
    if per_day >= 1.0:
        return "Elite"
    if per_day >= 1 / 7:
        return "High"
    if per_day >= 1 / 30:
        return "Medium"
    return "Low"


def classify_lead_time(hours: float | None) -> Tier:
    """Classify LT: Elite <=24h, High <=1 week, Medium <=1 month, else Low.

    Issue #527: None input (no deploys in window) maps to "N/A" rather
    than the previous "0 hours -> Elite" silent misclassification.
    """
    if hours is None:
        return "N/A"
    if hours <= _LT_ELITE_MAX_HOURS:
        return "Elite"
    if hours <= 24 * 7:
        return "High"
    if hours <= 24 * 30:
        return "Medium"
    return "Low"


def classify_change_failure_rate(rate: float | None) -> Tier:
    """Classify CFR: Elite 0-15%, High 16-30%, Medium 31-45%, Low 46%+.

    Issue #527: None input (no deploys, so the ratio is undefined) maps
    to "N/A".
    """
    if rate is None:
        return "N/A"
    if rate <= _CFR_ELITE_MAX_RATE:
        return "Elite"
    if rate <= _CFR_HIGH_MAX_RATE:
        return "High"
    if rate <= _CFR_MEDIUM_MAX_RATE:
        return "Medium"
    return "Low"


def classify_time_to_restore(hours: float | None) -> Tier:
    """Classify TRS: Elite <1h, High <24h, Medium <1 week, else Low.

    Issue #527: None input (no resolved failures in window) maps to "N/A".
    """
    if hours is None:
        return "N/A"
    if hours < 1.0:
        return "Elite"
    if hours < _TRS_HIGH_MAX_HOURS:
        return "High"
    if hours < 24 * 7:
        return "Medium"
    return "Low"


# =============================================================================
# Aggregate
# =============================================================================


@dataclass(frozen=True)
class DORAMetrics:
    """Frozen value object holding all four DORA metric values.

    Issue #527: lead_time_hours, change_failure_rate, and
    time_to_restore_hours may be None when the input window contained
    no relevant events. None classifies as "N/A" rather than 0/Elite
    so a team that has not shipped anything is not silently promoted
    to the highest tier. deployment_frequency stays float because
    "0 deploys per day" is well-defined and correctly classifies as
    Low.
    """

    deployment_frequency: float | None  # deploys per day
    lead_time_hours: float | None  # median commit -> deploy hours
    change_failure_rate: float | None  # 0.0 - 1.0
    time_to_restore_hours: float | None  # median resolve - open hours

    def tier(self) -> dict[str, Tier]:
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
        """Return the tier key of the weakest computable metric.

        N/A entries are excluded from the comparison; they have no
        signal to rank against. If every metric is N/A, returns
        "insufficient_data" so the caller can see that the window
        contained no signal at all.

        Ties break deterministically by declaration order (DF, LT, CFR, TRS).
        """
        tiers = self.tier()
        ordered_keys = (
            "deployment_frequency",
            "lead_time",
            "change_failure_rate",
            "time_to_restore",
        )
        computable = [k for k in ordered_keys if tiers[k] != "N/A"]
        if not computable:
            return "insufficient_data"
        return min(computable, key=lambda k: _TIER_RANK[tiers[k]])

    def overall_tier(self) -> Tier:
        """Return the weakest tier across all *computable* metrics.

        N/A is excluded from the comparison so partial-data still
        gives the operator a tier floor on the metrics that ARE
        measurable. If every metric is N/A, returns "N/A".
        """
        tiers = self.tier()
        computable: list[Tier] = [t for t in tiers.values() if t != "N/A"]
        if not computable:
            return "N/A"
        # Restrict the comparator's input type so _TIER_RANK lookup
        # type-checks (N/A keys are intentionally absent).
        return min(computable, key=lambda t: _TIER_RANK[t])


# =============================================================================
# Computation
# =============================================================================


def _median_or_none(values: list[float]) -> float | None:
    """Return the median of values, or None when the input is empty.

    Issue #527: callers previously used ``_median_or_zero`` and the 0.0
    return classified as Elite for LT/TRS, indistinguishable from
    "perfect quality." None classifies as N/A and is excluded from the
    bottleneck/overall_tier ranking so operators see honest signal.
    """
    return statistics.median(values) if values else None


def compute_metrics(
    deployments: list[DeploymentEvent],
    failures: list[FailureEvent],
    window_days: int = DEFAULT_WINDOW_DAYS,
    window_end: datetime | None = None,
) -> DORAMetrics:
    """Compute DORA metrics over a window.

    Empty inputs produce None for LT, CFR, and TRS (issue #527). DF
    stays a float because "zero deploys per day" is well-defined.

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
    lt: float | None = _median_or_none(lead_times)

    cfr: float | None = (
        len(in_window_failures) / len(in_window_deploys)
        if in_window_deploys
        else None  # No deploys -> CFR is undefined, not "0% / Elite"
    )

    restore_times = [
        (f.resolved_at - f.opened_at).total_seconds() / 3600.0
        for f in in_window_failures
        if f.resolved_at is not None and f.resolved_at >= f.opened_at
    ]
    trs: float | None = _median_or_none(restore_times)

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
    """Render a human-readable summary suitable for terminal or PR comment.

    None metrics (issue #527) render as "N/A" rather than "0.00" so the
    operator can distinguish "no signal" from "perfect quality."
    """
    tiers = m.tier()
    bottleneck = m.bottleneck()

    def fmt_df(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.2f}/day"

    def fmt_hours(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.1f} hours"

    def fmt_pct(value: float | None) -> str:
        return "N/A" if value is None else f"{value * 100:.1f}%"

    def fmt_hours2(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.2f} hours"

    rows = [
        (
            "Deployment Frequency",
            fmt_df(m.deployment_frequency),
            tiers["deployment_frequency"],
            "deployment_frequency",
        ),
        (
            "Lead Time for Changes",
            fmt_hours(m.lead_time_hours),
            tiers["lead_time"],
            "lead_time",
        ),
        (
            "Change Failure Rate",
            fmt_pct(m.change_failure_rate),
            tiers["change_failure_rate"],
            "change_failure_rate",
        ),
        (
            "Time to Restore Service",
            fmt_hours2(m.time_to_restore_hours),
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
) -> CollectionResult:
    """Treat each commit on ``branch`` as a deployment event.

    This is the simplest mapping that works for trunk-based and merge-PR
    workflows; teams with explicit deploy events should override this with a
    custom collector. ``commit_at`` and ``deployed_at`` collapse to the same
    timestamp here, giving lead time = 0; pass real deploy data for accuracy.

    Returns a CollectionResult so the CLI can distinguish between "no
    deploys in window" and "collector failed." Malformed timestamps are
    skipped with a warning rather than aborting the whole run.
    """
    if window_end is None:
        window_end = datetime.now(timezone.utc)
    since = (window_end - timedelta(days=window_days)).isoformat()
    # Place "--" before the branch so a value like "--upload-pack=..."
    # is treated as a positional rather than a git log flag (issue #526).
    output = _run_git(
        [
            "log",
            f"--since={since}",
            "--pretty=format:%H|%aI|%cI",
            "--no-merges",
            "--",
            branch,
        ],
        cwd=cwd,
    )
    events: list[DeploymentEvent] = []
    warnings: list[str] = []
    partial = False
    for line in output.strip().splitlines():
        if not line:
            continue
        parts = line.split("|")
        if len(parts) != _GIT_LOG_PRETTY_FIELD_COUNT:
            # A line with the wrong field count means the pretty-format
            # broke or the output was truncated. Skipping it silently
            # would let a corrupted log still classify as Elite, so
            # flag partial like the malformed-timestamp branch below
            # (issue #575, B3).
            warnings.append(
                f"skipped git log line with unexpected field count "
                f"({len(parts)} != 3): {line!r}"
            )
            partial = True
            continue
        sha, author_iso, commit_iso = parts
        try:
            commit_at = datetime.fromisoformat(author_iso)
            deployed_at = datetime.fromisoformat(commit_iso)
        except ValueError as exc:
            warnings.append(
                f"skipped git log line with malformed timestamp ({sha[:12]}): {exc}"
            )
            partial = True
            continue
        events.append(
            DeploymentEvent(sha=sha, deployed_at=deployed_at, commit_at=commit_at)
        )
    return CollectionResult(events=events, partial=partial, warnings=tuple(warnings))


def collect_failures_from_gh(
    failure_label: str,
    window_days: int,
    window_end: datetime | None = None,
    cwd: Path | None = None,
) -> CollectionResult:
    """Pull GitHub issues with ``failure_label`` opened in the window.

    A `gh` failure (auth expired, rate-limited, missing binary,
    paginator banner) returns ``CollectionResult(events=[], partial=True)``
    so the caller can refuse to silently classify a broken collector
    as zero failures (issue #525).
    """
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
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        msg = f"gh CLI failed: {type(exc).__name__}: {exc}"
        print(f"[dora] WARNING: {msg}", file=sys.stderr)
        return CollectionResult(events=[], partial=True, warnings=(msg,))

    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        preview = result.stdout[:200].replace("\n", " ")
        msg = f"gh json parse failed: {exc}; head: {preview!r}"
        print(f"[dora] WARNING: {msg}", file=sys.stderr)
        return CollectionResult(events=[], partial=True, warnings=(msg,))

    events: list[FailureEvent] = []
    warnings: list[str] = []
    partial = False
    for row in rows:
        opened_iso = row.get("createdAt")
        closed_iso = row.get("closedAt")
        if not opened_iso:
            continue
        try:
            opened_at = datetime.fromisoformat(opened_iso.replace("Z", "+00:00"))
            resolved_at = (
                datetime.fromisoformat(closed_iso.replace("Z", "+00:00"))
                if closed_iso
                else None
            )
        except ValueError as exc:
            warnings.append(f"skipped gh row with malformed timestamp: {exc}")
            partial = True
            continue
        events.append(FailureEvent(opened_at=opened_at, resolved_at=resolved_at))
    return CollectionResult(events=events, partial=partial, warnings=tuple(warnings))


# =============================================================================
# CLI
# =============================================================================


def _positive_int(value: str) -> int:
    """Argparse type-checker: window must be a positive integer (issue #526).

    Zero produces a zero-by-zero classification trap; negative produces a
    future-dated window that includes commits ahead of the head.
    """
    try:
        ivalue = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"expected a positive integer, got {value!r}"
        ) from exc
    if ivalue < 1:
        raise argparse.ArgumentTypeError(f"window must be >= 1, got {ivalue}")
    return ivalue


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for the standalone `minister-dora` entry point."""
    parser = argparse.ArgumentParser(
        prog="minister-dora",
        description="Compute DORA metrics from local git and gh CLI.",
    )
    parser.add_argument(
        "--window",
        type=_positive_int,
        default=DEFAULT_WINDOW_DAYS,
        help="Measurement window in days (must be >= 1; default: 30).",
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit non-zero when any collector returns partial data (issue "
            "#525). Use in CI to refuse silent 'Elite' tier reports caused "
            "by a broken gh CLI."
        ),
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    """Collect events, compute DORA metrics, print a report, and return the exit code.

    Returns 2 when `--strict` is set and either collector reported partial
    data (issue #525), so CI can refuse a silent Elite-tier report from a
    broken collector; otherwise returns 0.
    """
    args = build_parser().parse_args(argv)
    deploy_result = collect_deployments_from_git(
        branch=args.branch, window_days=args.window, cwd=args.repo_path
    )
    failure_result = collect_failures_from_gh(
        failure_label=args.failure_label, window_days=args.window, cwd=args.repo_path
    )
    metrics = compute_metrics(
        deployments=deploy_result.events,
        failures=failure_result.events,
        window_days=args.window,
    )

    partial = bool(deploy_result.partial or failure_result.partial)
    warnings = list(deploy_result.warnings) + list(failure_result.warnings)

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
                "partial": partial,
                "warnings": warnings,
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(metrics, window_days=args.window))
        if partial:
            print(
                "\nNOTE: results are partial. One or more collectors failed; "
                "the reported tier may not reflect reality. See stderr for "
                "specific warnings.",
                file=sys.stderr,
            )

    if args.strict and partial:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
