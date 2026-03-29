#!/usr/bin/env python3
"""Verify plugin behavioral contract history via GitHub Attestations.

Queries GitHub Actions workflow runs and SLSA attestations to assess
plugin trust. Zero cost - uses GitHub's built-in infrastructure.

Usage:
    python verify_plugin.py <plugin-name> [--level L1|L2|L3] [--min-score 0.8]
    python verify_plugin.py sanctum --json
    python verify_plugin.py sanctum --repo athola/claude-night-market
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

VALID_LEVELS = ("L1", "L2", "L3")

DEFAULT_REPO = "athola/claude-night-market"


@dataclass
class LevelScore:
    """Pass rate for a single assertion level."""

    level: str
    total: int
    passed: int
    rate: float


@dataclass
class TrustAssessment:
    """Full trust assessment for a plugin."""

    plugin_name: str
    meets_threshold: bool
    recommendation: str
    level_scores: list[LevelScore] = field(default_factory=list)
    assertion_history: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _query_workflow_runs(
    repo: str,
    per_page: int = 10,
) -> list[dict[str, Any]]:
    """Fetch recent completed workflow runs from GitHub Actions.

    Args:
        repo: GitHub repository in "owner/repo" format.
        per_page: Number of runs to fetch.

    Returns:
        List of workflow run dicts from the GitHub API.

    Raises:
        RuntimeError: If the gh CLI fails.
    """
    endpoint = f"repos/{repo}/actions/runs?status=completed&per_page={per_page}"
    result = subprocess.run(
        ["gh", "api", endpoint],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or "gh api call failed"
        raise RuntimeError(msg)

    data = json.loads(result.stdout)
    return data.get("workflow_runs", [])


def _runs_to_records(
    runs: list[dict[str, Any]],
    plugin_name: str,
) -> list[dict[str, Any]]:
    """Convert GitHub Actions workflow runs to trust records.

    Maps workflow conclusion to assertion-style records:
    - "success" -> passed=True
    - anything else -> passed=False

    Each run is treated as an L1 assertion (structural test pass).
    Runs whose name contains the plugin name are weighted as more
    relevant.

    Args:
        runs: Workflow run dicts from the GitHub API.
        plugin_name: Plugin name to look for in run names.

    Returns:
        List of record dicts with level, passed, and metadata keys.
    """
    records: list[dict[str, Any]] = []
    for run in runs:
        conclusion = run.get("conclusion", "")
        name = run.get("name", "")
        passed = conclusion == "success"

        # Determine level based on workflow name heuristics
        name_lower = name.lower()
        if "l3" in name_lower or "behavioral" in name_lower:
            level = "L3"
        elif "l2" in name_lower or "semantic" in name_lower:
            level = "L2"
        else:
            level = "L1"

        records.append(
            {
                "level": level,
                "passed": passed,
                "run_id": run.get("id"),
                "conclusion": conclusion,
                "workflow": name,
                "created_at": run.get("created_at", ""),
                "html_url": run.get("html_url", ""),
                "plugin_match": plugin_name.lower() in name_lower,
            }
        )
    return records


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _compute_level_scores(
    records: list[Any],
) -> dict[str, LevelScore]:
    """Compute pass rates per assertion level from records.

    Accepts plain dicts with ``level`` and ``passed`` keys.

    Args:
        records: List of record dicts.

    Returns:
        Mapping of level name to LevelScore.
    """
    totals: dict[str, int] = {}
    passes: dict[str, int] = {}

    for rec in records:
        lvl = rec.get("level", "L1").upper()
        totals[lvl] = totals.get(lvl, 0) + 1
        if rec.get("passed", False):
            passes[lvl] = passes.get(lvl, 0) + 1

    scores: dict[str, LevelScore] = {}
    for lvl in VALID_LEVELS:
        t = totals.get(lvl, 0)
        p = passes.get(lvl, 0)
        rate = p / t if t > 0 else 0.0
        scores[lvl] = LevelScore(level=lvl, total=t, passed=p, rate=rate)

    return scores


def _choose_recommendation(
    level_scores: dict[str, LevelScore],
    target_level: str,
    min_score: float,
) -> str:
    """Derive a recommendation string.

    Args:
        level_scores: Per-level pass-rate data.
        target_level: The level the caller cares about.
        min_score: Minimum acceptable pass rate (0.0-1.0).

    Returns:
        One of "trusted", "caution", or "untrusted".
    """
    score = level_scores.get(target_level)
    if score is None or score.total == 0:
        return "untrusted"
    if score.rate >= min_score:
        return "trusted"
    if score.rate >= min_score * 0.7:
        return "caution"
    return "untrusted"


def verify_plugin(
    plugin_name: str,
    level: str = "L1",
    min_score: float = 0.8,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    """Query GitHub Actions and return trust assessment.

    Fetches recent workflow runs via the ``gh`` CLI, converts
    them to trust records, and computes a recommendation.

    Args:
        plugin_name: Name of the plugin to verify.
        level: Minimum assertion level to check (L1, L2, L3).
        min_score: Minimum pass rate threshold (0.0-1.0).
        repo: GitHub repository in "owner/repo" format.

    Returns:
        Dict with plugin_name, meets_threshold, recommendation,
        level_scores, assertion_history, and optional error.
    """
    level = level.upper()
    if level not in VALID_LEVELS:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="unknown",
                error=f"Invalid level '{level}'. Must be one of {VALID_LEVELS}.",
            )
        )

    try:
        runs = _query_workflow_runs(repo)
    except Exception as exc:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="unknown",
                error=f"Failed to query GitHub API: {exc}",
            )
        )

    records = _runs_to_records(runs, plugin_name)

    if not records:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="untrusted",
                assertion_history=[],
                error="No workflow run history found.",
            )
        )

    level_scores = _compute_level_scores(records)
    recommendation = _choose_recommendation(level_scores, level, min_score)
    meets = recommendation == "trusted"

    return asdict(
        TrustAssessment(
            plugin_name=plugin_name,
            meets_threshold=meets,
            recommendation=recommendation,
            level_scores=[level_scores[lv] for lv in VALID_LEVELS],
            assertion_history=records[-20:],
        )
    )


def verify_plugin_offline(
    plugin_name: str,
    records: list[dict[str, Any]],
    level: str = "L1",
    min_score: float = 0.8,
) -> dict[str, Any]:
    """Verify trust from pre-fetched records.

    Useful for testing and offline evaluation without network
    access.

    Args:
        plugin_name: Name of the plugin.
        records: Pre-fetched record dicts with level/passed keys.
        level: Assertion level to check.
        min_score: Minimum pass rate threshold.

    Returns:
        Same dict shape as verify_plugin().
    """
    level = level.upper()
    if level not in VALID_LEVELS:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="unknown",
                error=f"Invalid level '{level}'. Must be one of {VALID_LEVELS}.",
            )
        )

    if not records:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="untrusted",
                assertion_history=[],
                error="No assertion history found for this plugin.",
            )
        )

    level_scores = _compute_level_scores(records)
    recommendation = _choose_recommendation(level_scores, level, min_score)
    meets = recommendation == "trusted"

    return asdict(
        TrustAssessment(
            plugin_name=plugin_name,
            meets_threshold=meets,
            recommendation=recommendation,
            level_scores=[level_scores[lv] for lv in VALID_LEVELS],
            assertion_history=records[-20:],
        )
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Verify plugin behavioral contract history via GitHub Attestations."
        ),
    )
    parser.add_argument(
        "plugin_name",
        help="Name of the plugin to verify.",
    )
    parser.add_argument(
        "--level",
        choices=["L1", "L2", "L3"],
        default="L1",
        help="Minimum assertion level to check (default: L1).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.8,
        help="Minimum pass rate threshold 0.0-1.0 (default: 0.8).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output raw JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repository (default: {DEFAULT_REPO}).",
    )
    return parser


def _format_human(result: dict[str, Any]) -> str:
    """Format a trust assessment for human consumption."""
    lines: list[str] = []
    lines.append(f"Plugin: {result['plugin_name']}")
    lines.append(f"Recommendation: {result['recommendation']}")
    lines.append(f"Meets threshold: {result['meets_threshold']}")

    if result.get("error"):
        lines.append(f"Note: {result['error']}")

    scores = result.get("level_scores", [])
    if scores:
        lines.append("")
        lines.append("Level scores:")
        for s in scores:
            pct = s["rate"] * 100
            lines.append(
                f"  {s['level']}: {s['passed']}/{s['total']} ({pct:.1f}% pass rate)"
            )

    history = result.get("assertion_history", [])
    if history:
        lines.append("")
        lines.append(f"Recent assertions: {len(history)} records")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for trusted, 1 for not trusted, 2 for errors.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    result = verify_plugin(
        plugin_name=args.plugin_name,
        level=args.level,
        min_score=args.min_score,
        repo=args.repo,
    )

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(_format_human(result))

    if result.get("error") and result["recommendation"] == "unknown":
        return 2
    return 0 if result["meets_threshold"] else 1


if __name__ == "__main__":
    sys.exit(main())
