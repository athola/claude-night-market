#!/usr/bin/env python3
"""Verify plugin behavioral contract history via ERC-8004.

Queries the on-chain Reputation Registry for a plugin's assertion
history and returns a trust assessment based on pass rates at each
verification level (L1, L2, L3).

Usage:
    python verify_plugin.py <plugin-name> [--level L1|L2|L3] [--min-score 0.8]
    python verify_plugin.py sanctum --level L3 --min-score 0.9
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Lazy imports for erc8004 — gracefully degrade when web3 is missing
# ---------------------------------------------------------------------------

_ERC8004_AVAILABLE = False


def _try_import_erc8004() -> Any:
    """Attempt to import the erc8004 package.

    Returns:
        The erc8004 module, or None if unavailable.
    """
    global _ERC8004_AVAILABLE  # noqa: PLW0603
    try:
        from leyline import erc8004  # type: ignore[attr-defined]  # noqa: PLC0415

        _ERC8004_AVAILABLE = True
        return erc8004
    except ImportError:
        _ERC8004_AVAILABLE = False
        return None


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

VALID_LEVELS = ("L1", "L2", "L3")


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
# Core logic
# ---------------------------------------------------------------------------


def _compute_level_scores(
    records: list[dict[str, Any]],
) -> dict[str, LevelScore]:
    """Compute pass rates per assertion level from raw records.

    Args:
        records: List of assertion record dicts, each containing
            at least ``level`` (str) and ``passed`` (bool) keys.

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
) -> dict[str, Any]:
    """Query Reputation Registry and return trust assessment.

    When the erc8004 package is unavailable (e.g. web3 not installed),
    returns an assessment with ``error`` set and ``recommendation``
    of ``"unknown"``.

    Args:
        plugin_name: Name of the plugin to verify.
        level: Minimum assertion level to check (L1, L2, L3).
        min_score: Minimum pass rate threshold (0.0-1.0).

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

    erc8004 = _try_import_erc8004()
    if erc8004 is None:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="unknown",
                error=("ERC-8004 SDK not available. Install with: pip install web3"),
            )
        )

    try:
        config = erc8004.ERC8004Config.from_env()
        client = erc8004.ERC8004Client(config)
        records = client.reputation.get_assertion_history(plugin_name)
    except Exception as exc:
        return asdict(
            TrustAssessment(
                plugin_name=plugin_name,
                meets_threshold=False,
                recommendation="unknown",
                error=f"Failed to query registry: {exc}",
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
            assertion_history=records[-20:],  # last 20 records
        )
    )


def verify_plugin_offline(
    plugin_name: str,
    records: list[dict[str, Any]],
    level: str = "L1",
    min_score: float = 0.8,
) -> dict[str, Any]:
    """Verify trust from pre-fetched assertion records.

    Useful for testing and offline evaluation without an RPC
    connection.

    Args:
        plugin_name: Name of the plugin.
        records: Pre-fetched assertion record dicts.
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
        description="Verify plugin behavioral contract history via ERC-8004.",
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
