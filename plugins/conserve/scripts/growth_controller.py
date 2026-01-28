#!/usr/bin/env python3
"""Context Growth Control Strategy Generator.

Generates control strategies based on growth analysis results.
Supports multiple strategy types and implementation planning.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any

# Constants
CONTROLLABLE_THRESHOLD = 50  # Percentage threshold for controllable growth
GROWTH_RATE_WARNING = 0.1  # Growth rate threshold for warning
GROWTH_RATE_CRITICAL = 0.2  # Growth rate threshold for critical priority


class GrowthController:
    """Generates and manages context growth control strategies."""

    def __init__(self) -> None:
        """Initialize the growth controller with strategy definitions."""
        self.strategy_types = {
            "conservative": {
                "description": "Minimal disruption, gradual optimization",
                "priority": ["Prevention", "Monitoring", "Manual Control"],
                "implementation_speed": "Slow (5-10 turns)",
                "risk_level": "Low",
            },
            "moderate": {
                "description": "Balanced approach with automated controls",
                "priority": ["Automated Control", "Prevention", "Manual Control"],
                "implementation_speed": "Medium (3-7 turns)",
                "risk_level": "Medium",
            },
            "aggressive": {
                "description": "Immediate action with strong controls",
                "priority": ["Automated Control", "Manual Control", "Prevention"],
                "implementation_speed": "Fast (1-3 turns)",
                "risk_level": "High",
            },
        }

    def generate_control_strategies(
        self, analysis_results: dict, strategy_type: str = "moderate"
    ) -> dict:
        """Generate control strategies based on analysis results."""
        if strategy_type not in self.strategy_types:
            msg = f"Invalid strategy type: {strategy_type}"
            raise ValueError(msg)

        severity = analysis_results.get("severity", "STABLE")
        urgency = analysis_results.get("urgency", "NONE")
        growth_rate = analysis_results.get("growth_rate", 0)
        controllable_percentage = analysis_results.get("controllable_percentage", 0)

        # Generate strategy components
        return {
            "metadata": {
                "strategy_type": strategy_type,
                "generated_at": datetime.now().isoformat(),
                "analysis_severity": severity,
                "analysis_urgency": urgency,
                "target_growth_rate": self._calculate_target_growth_rate(
                    growth_rate,
                    strategy_type,
                ),
            },
            "automated_controls": self._generate_automated_controls(
                severity,
                urgency,
                strategy_type,
            ),
            "manual_controls": self._generate_manual_controls(
                controllable_percentage,
                strategy_type,
            ),
            "preventive_strategies": self._generate_preventive_strategies(
                growth_rate,
                strategy_type,
            ),
            "implementation_plan": self._generate_implementation_plan(strategy_type),
            "monitoring_requirements": self._generate_monitoring_requirements(severity),
        }

    def _calculate_target_growth_rate(
        self, current_rate: float, strategy_type: str
    ) -> float:
        """Calculate target growth rate based on strategy type."""
        if strategy_type == "conservative":
            return min(current_rate * 0.7, 0.05)  # 30% reduction, max 5%
        if strategy_type == "moderate":
            return min(current_rate * 0.5, 0.03)  # 50% reduction, max 3%
        # aggressive
        return min(current_rate * 0.3, 0.02)  # 70% reduction, max 2%

    def _generate_automated_controls(
        self, severity: str, urgency: str, strategy_type: str
    ) -> list[dict]:
        """Generate automated control strategies."""
        controls: list[dict] = []

        # Base controls for all situations
        controls.append(
            {
                "name": "Progressive Context Management",
                "description": "Implement progressive loading and lazy context loading",
                "priority": "High",
                "effectiveness": "80%",
                "implementation_time": "2-3 turns",
            },
        )

        # Severity-based controls
        if severity in ["MODERATE", "SEVERE", "CRITICAL"]:
            controls.append(
                {
                    "name": "Emergency Context Compression",
                    "description": (
                        "Automated compression of older, low-priority context"
                    ),
                    "priority": "Critical" if urgency in ["HIGH", "URGENT"] else "High",
                    "effectiveness": "60-80%",
                    "implementation_time": "1-2 turns",
                },
            )

        if urgency in ["HIGH", "URGENT"]:
            controls.append(
                {
                    "name": "Real-time Growth Monitoring",
                    "description": "Continuous monitoring with automated alerts",
                    "priority": "Critical",
                    "effectiveness": "90%",
                    "implementation_time": "Immediate",
                },
            )

        # Strategy type adjustments
        if strategy_type == "aggressive":
            controls.append(
                {
                    "name": "Aggressive Context Pruning",
                    "description": (
                        "Automated removal of non-essential context elements"
                    ),
                    "priority": "Critical",
                    "effectiveness": "70-90%",
                    "implementation_time": "1 turn",
                },
            )

        return controls

    def _generate_manual_controls(
        self, controllable_percentage: float, strategy_type: str
    ) -> list[dict]:
        """Generate manual control strategies."""
        controls = []

        if controllable_percentage > CONTROLLABLE_THRESHOLD:
            controls.append(
                {
                    "name": "Category-Specific Optimization",
                    "description": (
                        f"Manual optimization of {controllable_percentage:.0f}% "
                        f"controllable growth sources"
                    ),
                    "priority": "High",
                    "frequency": "Every 5 turns",
                    "effectiveness": "70-85%",
                },
            )

        controls.append(
            {
                "name": "Context Review and Cleanup",
                "description": (
                    "Periodic manual review of context elements for relevance"
                ),
                "priority": "Medium",
                "frequency": "Every 10 turns"
                if strategy_type == "conservative"
                else "Every 5 turns",
                "effectiveness": "50-70%",
            },
        )

        if strategy_type != "conservative":
            controls.append(
                {
                    "name": "Strategic Content Externalization",
                    "description": "Move large, low-usage content to external storage",
                    "priority": "Medium",
                    "frequency": "As needed",
                    "effectiveness": "60-80%",
                },
            )

        return controls

    def _generate_preventive_strategies(
        self, growth_rate: float, strategy_type: str
    ) -> list[dict]:
        """Generate preventive strategies."""
        strategies = []

        strategies.append(
            {
                "name": "Context Usage Planning",
                "description": "Proactive planning for context usage and growth limits",
                "priority": "High",
                "implementation": "Immediate",
                "ongoing_maintenance": "Weekly reviews",
            },
        )

        if growth_rate > GROWTH_RATE_WARNING:
            strategies.append(
                {
                    "name": "Growth Acceleration Control",
                    "description": "Implement measures to control growth acceleration",
                    "priority": "Critical"
                    if growth_rate > GROWTH_RATE_CRITICAL
                    else "High",
                    "implementation": "2-3 turns",
                    "ongoing_maintenance": "Continuous monitoring",
                },
            )

        strategies.append(
            {
                "name": "Content Structuring Optimization",
                "description": "Optimize how content is structured to minimize growth",
                "priority": "Medium",
                "implementation": "1-2 turns",
                "ongoing_maintenance": "Monthly reviews",
            },
        )

        return strategies

    def _generate_implementation_plan(
        self, strategy_type: str
    ) -> dict[str, dict[str, object]]:
        """Generate implementation timeline and steps."""
        _ = self.strategy_types[strategy_type]

        if strategy_type == "conservative":
            return {
                "phase_1": {
                    "duration": "2-3 turns",
                    "actions": ["Setup monitoring", "Begin content structuring"],
                    "priority": "Low",
                },
                "phase_2": {
                    "duration": "5-7 turns",
                    "actions": [
                        "Implement preventive strategies",
                        "Begin manual optimization",
                    ],
                    "priority": "Medium",
                },
                "phase_3": {
                    "duration": "Ongoing",
                    "actions": ["Continuous monitoring", "Regular optimization"],
                    "priority": "Low",
                },
            }

        if strategy_type == "moderate":
            return {
                "phase_1": {
                    "duration": "1-2 turns",
                    "actions": [
                        "Setup automated monitoring",
                        "Implement progressive management",
                    ],
                    "priority": "High",
                },
                "phase_2": {
                    "duration": "2-4 turns",
                    "actions": [
                        "Deploy automated controls",
                        "Begin manual optimization",
                    ],
                    "priority": "High",
                },
                "phase_3": {
                    "duration": "Ongoing",
                    "actions": ["Monitoring and adjustment", "Preventive maintenance"],
                    "priority": "Medium",
                },
            }

        # aggressive
        return {
            "phase_1": {
                "duration": "Immediate",
                "actions": ["Emergency compression", "Real-time monitoring"],
                "priority": "Critical",
            },
            "phase_2": {
                "duration": "1-2 turns",
                "actions": ["Aggressive pruning", "Automated control deployment"],
                "priority": "Critical",
            },
            "phase_3": {
                "duration": "2-3 turns",
                "actions": ["Manual optimization", "Structural changes"],
                "priority": "High",
            },
        }

    def _generate_monitoring_requirements(self, severity: str) -> dict[str, Any]:
        """Generate monitoring requirements based on severity."""
        base_requirements: dict[str, Any] = {
            "frequency": "Every 10 turns",
            "metrics": ["context_usage", "growth_rate", "content_breakdown"],
            "alerts": ["threshold_breach"],
        }

        if severity in ["MODERATE", "SEVERE", "CRITICAL"]:
            base_requirements.update(
                {
                    "frequency": "Every 5 turns",
                    "alerts": list(base_requirements["alerts"])
                    + ["growth_spike", "acceleration_detected"],
                },
            )

        if severity in ["SEVERE", "CRITICAL"]:
            base_requirements.update(
                {
                    "frequency": "Every 2 turns",
                    "alerts": list(base_requirements["alerts"])
                    + ["critical_threshold", "strategy_failure"],
                    "real_time_monitoring": True,
                },
            )

        return base_requirements


def main() -> None:
    """Generate context growth control strategies."""
    parser = argparse.ArgumentParser(
        description="Generate context growth control strategies",
    )
    parser.add_argument(
        "--analysis-file",
        required=True,
        help="Path to analysis results JSON file",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output strategies as JSON",
    )
    parser.add_argument(
        "--strategy-type",
        choices=["conservative", "moderate", "aggressive"],
        default="moderate",
        help="Type of control strategy to generate",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Load analysis results
    try:
        with open(args.analysis_file) as f:
            analysis_results = json.load(f)
    except FileNotFoundError:
        sys.exit(1)
    except json.JSONDecodeError:
        sys.exit(1)

    # Generate control strategies
    controller = GrowthController()
    strategies = controller.generate_control_strategies(
        analysis_results,
        args.strategy_type,
    )

    if args.output_json:
        print(json.dumps(strategies, indent=2, default=str))
    else:
        meta = strategies["metadata"]
        print(f"Strategy Type: {meta.get('strategy_type', 'unknown')}")
        print(f"Generated: {meta.get('generated_at', 'unknown')}")

        print("\nAutomated Controls:")
        for control in strategies["automated_controls"]:
            name = control.get("name", "unnamed")
            desc = control.get("description", "")
            print(f"  - {name}: {desc}")

        print("\nManual Controls:")
        for control in strategies["manual_controls"]:
            name = control.get("name", "unnamed")
            desc = control.get("description", "")
            print(f"  - {name}: {desc}")

        print("\nPreventive Strategies:")
        for strategy in strategies["preventive_strategies"]:
            name = strategy.get("name", "unnamed")
            desc = strategy.get("description", "")
            print(f"  - {name}: {desc}")

        if args.verbose:
            print("\nImplementation Plan:")
            for phase, details in strategies["implementation_plan"].items():
                print(f"  {phase}: {details}")

            print(f"\nMonitoring: {strategies['monitoring_requirements']}")


if __name__ == "__main__":
    main()
