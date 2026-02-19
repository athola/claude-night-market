#!/usr/bin/env python3
"""Analyze context growth patterns, detect acceleration, and project future growth.

Support multiple output formats and customizable projection horizons.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

# Constants
CONTROLLABLE_GROWTH_THRESHOLD = 0.10
MECW_USAGE_LIMIT = 100
SAFETY_LIMIT_TURNS = 1000
PROJECTION_TURNS = [5, 10, 20]


class GrowthAnalyzer:
    """Analyze context growth patterns and generate projections."""

    def __init__(self) -> None:
        """Initialize the GrowthAnalyzer with default thresholds."""
        self.growth_thresholds = {
            "stable": 0.05,  # < 5% growth per turn
            "mild": 0.10,  # 5-10% growth per turn
            "moderate": 0.15,  # 10-15% growth per turn
            "severe": 0.20,  # 15-20% growth per turn
            "critical": 0.25,  # > 20% growth per turn
        }

        self.urgency_levels = {
            "none": (0.05, 0.001),
            "low": (0.10, 0.005),
            "medium": (0.15, 0.010),
            "high": (0.20, 0.015),
            "urgent": (1.0, 0.020),
        }

    def analyze_growth_patterns(self, context_data: dict) -> dict:
        """Analyze growth patterns and determine severity."""
        growth_trend = context_data.get("growth_trend", {})
        current_usage = growth_trend.get("current_usage", 0)
        growth_rate = growth_trend.get("rate", 0)
        acceleration = growth_trend.get("acceleration", 0)

        # Determine growth severity
        severity = self._assess_severity(growth_rate)
        urgency = self._assess_urgency(growth_rate, acceleration)

        # Analyze controllable growth
        context_data.get("growth_metrics", {})
        content_breakdown = context_data.get("content_breakdown", {})
        controllable_percentage = self._calculate_controllable_growth(content_breakdown)

        # Project future growth
        projections = self._project_growth(current_usage, growth_rate, acceleration)

        return {
            "severity": severity,
            "urgency": urgency,
            "current_usage": current_usage,
            "growth_rate": growth_rate,
            "acceleration": acceleration,
            "controllable_percentage": controllable_percentage,
            "projections": projections,
            "content_breakdown": content_breakdown,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def _assess_severity(self, growth_rate: float) -> str:
        """Determine growth severity level."""
        if growth_rate < self.growth_thresholds["mild"]:
            return "STABLE"
        if growth_rate < self.growth_thresholds["moderate"]:
            return "MILD"
        if growth_rate < self.growth_thresholds["severe"]:
            return "MODERATE"
        if growth_rate < self.growth_thresholds["critical"]:
            return "SEVERE"
        return "CRITICAL"

    def _assess_urgency(self, growth_rate: float, acceleration: float) -> str:
        """Determine control urgency level."""
        for level, (rate_threshold, acc_threshold) in self.urgency_levels.items():
            if growth_rate <= rate_threshold and acceleration <= acc_threshold:
                return level.upper()
        return "URGENT"

    def _calculate_controllable_growth(self, content_breakdown: dict) -> float:
        """Calculate percentage of growth that can be controlled."""
        total_contribution = 0
        controllable_contribution = 0

        for data in content_breakdown.values():
            contribution = data.get("growth_contribution", 0)
            growth_rate = data.get("growth_rate", 0)
            total_contribution += contribution

            # Consider categories with growth rate > 10% as controllable
            if growth_rate > CONTROLLABLE_GROWTH_THRESHOLD:
                controllable_contribution += contribution

        if total_contribution == 0:
            return 0

        return round((controllable_contribution / total_contribution) * 100, 2)

    def _project_growth(
        self,
        current_usage: float,
        growth_rate: float,
        acceleration: float,
        turns: int = 20,
    ) -> dict[str, float | dict[str, float]]:
        """Project growth over specified number of turns."""
        projections: dict[str, float | dict[str, float]] = {}

        for turn in PROJECTION_TURNS:
            if turn > turns:
                continue

            # Compound growth with acceleration
            projected_usage = current_usage * ((1 + growth_rate) ** turn)

            # Add acceleration effect
            if acceleration > 0:
                accel_factor = 1 + (acceleration * turn * (turn - 1) / 2)
                projected_usage *= accel_factor

            projections[f"{turn}_turns"] = {
                "projected_usage": round(projected_usage, 2),
                "projected_growth": round(projected_usage - current_usage, 2),
                "growth_percentage": (
                    round(((projected_usage / current_usage) - 1) * 100, 2)
                    if current_usage > 0
                    else 0
                ),
            }

        # Estimate time to MECW violation (assuming 100% limit)
        if current_usage > 0 and growth_rate > 0:
            turns_to_mecw = self._estimate_mecw_violation(
                current_usage,
                growth_rate,
                acceleration,
            )
            projections["mecw_violation_turns"] = turns_to_mecw

        return projections

    def _estimate_mecw_violation(
        self,
        current_usage: float,
        growth_rate: float,
        acceleration: float,
    ) -> float:
        """Estimate turns until MECW violation (100% usage)."""
        if current_usage >= MECW_USAGE_LIMIT:
            return 0

        if growth_rate <= 0:
            return float("inf")

        # Simple estimation for positive growth without acceleration
        if acceleration <= 0:
            return math.ceil(math.log(100 / current_usage) / math.log(1 + growth_rate))

        # For positive acceleration, use iterative approach
        usage = current_usage
        turns = 0
        while usage < MECW_USAGE_LIMIT and turns < SAFETY_LIMIT_TURNS:  # Safety limit
            turns += 1
            growth = usage * growth_rate + usage * acceleration * turns
            usage += growth

        return turns if usage >= MECW_USAGE_LIMIT else float("inf")


def main() -> None:
    """Analyze context growth patterns."""
    parser = argparse.ArgumentParser(description="Analyze context growth patterns")
    parser.add_argument(
        "--context-file",
        required=True,
        help="Path to context JSON file",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--turns",
        type=int,
        default=20,
        help="Number of turns to project",
    )

    args = parser.parse_args()

    # Load context data
    try:
        with open(args.context_file) as f:
            context_data = json.load(f)
    except FileNotFoundError:
        sys.exit(1)
    except json.JSONDecodeError:
        sys.exit(1)

    # Analyze growth patterns
    analyzer = GrowthAnalyzer()
    results = analyzer.analyze_growth_patterns(context_data)

    if args.output_json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"Severity: {results['severity']}")
        print(f"Urgency: {results['urgency']}")
        print(f"Current Usage: {results['current_usage']}%")
        print(f"Growth Rate: {results['growth_rate']:.2%}")
        print(f"Controllable: {results['controllable_percentage']}%")
        print("\nProjections:")
        for key, projection in results["projections"].items():
            if key == "mecw_violation_turns":
                if projection == float("inf"):
                    print("  MECW Violation: Never (growth is sustainable)")
                else:
                    print(f"  MECW Violation: ~{projection} turns")
            else:
                proj_data = projection
                usage = proj_data["projected_usage"]
                growth = proj_data["growth_percentage"]
                print(f"  {key}: {usage}% (+{growth}%)")

        if args.verbose:
            print("\nContent Breakdown:")
            for category, data in results["content_breakdown"].items():
                rate = data.get("growth_rate", 0)
                contrib = data.get("growth_contribution", 0)
                print(f"  {category}: {rate:.2%} rate, {contrib:.1%} contribution")


if __name__ == "__main__":
    import math

    main()
