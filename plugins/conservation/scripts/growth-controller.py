#!/usr/bin/env python3
"""Context Growth Control Strategy Generator.

Generates control strategies based on growth analysis results.
Supports multiple strategy types and implementation planning.
"""

import argparse
import json
import sys
from datetime import datetime


class GrowthController:
    """Generates and manages context growth control strategies."""

    def __init__(self):
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

    def generate_control_strategies(self, analysis_results, strategy_type="moderate"):
        """Generate control strategies based on analysis results."""
        if strategy_type not in self.strategy_types:
            raise ValueError(f"Invalid strategy type: {strategy_type}")

        severity = analysis_results.get("severity", "STABLE")
        urgency = analysis_results.get("urgency", "NONE")
        growth_rate = analysis_results.get("growth_rate", 0)
        controllable_percentage = analysis_results.get("controllable_percentage", 0)

        # Generate strategy components
        strategies = {
            "metadata": {
                "strategy_type": strategy_type,
                "generated_at": datetime.now().isoformat(),
                "analysis_severity": severity,
                "analysis_urgency": urgency,
                "target_growth_rate": self._calculate_target_growth_rate(
                    growth_rate, strategy_type
                ),
            },
            "automated_controls": self._generate_automated_controls(
                severity, urgency, strategy_type
            ),
            "manual_controls": self._generate_manual_controls(
                controllable_percentage, strategy_type
            ),
            "preventive_strategies": self._generate_preventive_strategies(
                growth_rate, strategy_type
            ),
            "implementation_plan": self._generate_implementation_plan(strategy_type),
            "monitoring_requirements": self._generate_monitoring_requirements(severity),
        }

        return strategies

    def _calculate_target_growth_rate(self, current_rate, strategy_type):
        """Calculate target growth rate based on strategy type."""
        if strategy_type == "conservative":
            return min(current_rate * 0.7, 0.05)  # 30% reduction, max 5%
        elif strategy_type == "moderate":
            return min(current_rate * 0.5, 0.03)  # 50% reduction, max 3%
        else:  # aggressive
            return min(current_rate * 0.3, 0.02)  # 70% reduction, max 2%

    def _generate_automated_controls(self, severity, urgency, strategy_type):
        """Generate automated control strategies."""
        controls = []

        # Base controls for all situations
        controls.append(
            {
                "name": "Progressive Context Management",
                "description": "Implement progressive loading and lazy context loading",
                "priority": "High",
                "effectiveness": "80%",
                "implementation_time": "2-3 turns",
            }
        )

        # Severity-based controls
        if severity in ["MODERATE", "SEVERE", "CRITICAL"]:
            controls.append(
                {
                    "name": "Emergency Context Compression",
                    "description": "Automated compression of older, low-priority context",
                    "priority": "Critical" if urgency in ["HIGH", "URGENT"] else "High",
                    "effectiveness": "60-80%",
                    "implementation_time": "1-2 turns",
                }
            )

        if urgency in ["HIGH", "URGENT"]:
            controls.append(
                {
                    "name": "Real-time Growth Monitoring",
                    "description": "Continuous monitoring with automated alerts",
                    "priority": "Critical",
                    "effectiveness": "90%",
                    "implementation_time": "Immediate",
                }
            )

        # Strategy type adjustments
        if strategy_type == "aggressive":
            controls.append(
                {
                    "name": "Aggressive Context Pruning",
                    "description": "Automated removal of non-essential context elements",
                    "priority": "Critical",
                    "effectiveness": "70-90%",
                    "implementation_time": "1 turn",
                }
            )

        return controls

    def _generate_manual_controls(self, controllable_percentage, strategy_type):
        """Generate manual control strategies."""
        controls = []

        if controllable_percentage > 50:
            controls.append(
                {
                    "name": "Category-Specific Optimization",
                    "description": f"Manual optimization of {controllable_percentage:.0f}% controllable growth sources",
                    "priority": "High",
                    "frequency": "Every 5 turns",
                    "effectiveness": "70-85%",
                }
            )

        controls.append(
            {
                "name": "Context Review and Cleanup",
                "description": "Periodic manual review of context elements for relevance",
                "priority": "Medium",
                "frequency": "Every 10 turns"
                if strategy_type == "conservative"
                else "Every 5 turns",
                "effectiveness": "50-70%",
            }
        )

        if strategy_type != "conservative":
            controls.append(
                {
                    "name": "Strategic Content Externalization",
                    "description": "Move large, low-usage content to external storage",
                    "priority": "Medium",
                    "frequency": "As needed",
                    "effectiveness": "60-80%",
                }
            )

        return controls

    def _generate_preventive_strategies(self, growth_rate, strategy_type):
        """Generate preventive strategies."""
        strategies = []

        strategies.append(
            {
                "name": "Context Usage Planning",
                "description": "Proactive planning for context usage and growth limits",
                "priority": "High",
                "implementation": "Immediate",
                "ongoing_maintenance": "Weekly reviews",
            }
        )

        if growth_rate > 0.1:
            strategies.append(
                {
                    "name": "Growth Acceleration Control",
                    "description": "Implement measures to control growth acceleration",
                    "priority": "Critical" if growth_rate > 0.2 else "High",
                    "implementation": "2-3 turns",
                    "ongoing_maintenance": "Continuous monitoring",
                }
            )

        strategies.append(
            {
                "name": "Content Structuring Optimization",
                "description": "Optimize how content is structured to minimize growth",
                "priority": "Medium",
                "implementation": "1-2 turns",
                "ongoing_maintenance": "Monthly reviews",
            }
        )

        return strategies

    def _generate_implementation_plan(self, strategy_type):
        """Generate implementation timeline and steps."""
        self.strategy_types[strategy_type]

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

        elif strategy_type == "moderate":
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

        else:  # aggressive
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

    def _generate_monitoring_requirements(self, severity):
        """Generate monitoring requirements based on severity."""
        base_requirements = {
            "frequency": "Every 10 turns",
            "metrics": ["context_usage", "growth_rate", "content_breakdown"],
            "alerts": ["threshold_breach"],
        }

        if severity in ["MODERATE", "SEVERE", "CRITICAL"]:
            base_requirements.update(
                {
                    "frequency": "Every 5 turns",
                    "alerts": base_requirements["alerts"]
                    + ["growth_spike", "acceleration_detected"],
                }
            )

        if severity in ["SEVERE", "CRITICAL"]:
            base_requirements.update(
                {
                    "frequency": "Every 2 turns",
                    "alerts": base_requirements["alerts"]
                    + ["critical_threshold", "strategy_failure"],
                    "real_time_monitoring": True,
                }
            )

        return base_requirements


def main():
    parser = argparse.ArgumentParser(
        description="Generate context growth control strategies"
    )
    parser.add_argument(
        "--analysis-file", required=True, help="Path to analysis results JSON file"
    )
    parser.add_argument(
        "--output-json", action="store_true", help="Output strategies as JSON"
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
        print(f"Error: Analysis file '{args.analysis_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in analysis file '{args.analysis_file}'")
        sys.exit(1)

    # Generate control strategies
    controller = GrowthController()
    strategies = controller.generate_control_strategies(
        analysis_results, args.strategy_type
    )

    if args.output_json:
        print(json.dumps(strategies, indent=2))
    else:
        print(f"=== Context Growth Control Strategy ({args.strategy_type.title()}) ===")
        metadata = strategies["metadata"]
        print(
            f"Target Growth Rate: {metadata['target_growth_rate'] * 100:.2f}% per turn"
        )
        print(
            f"Generated for: {metadata['analysis_severity']} severity, {metadata['analysis_urgency']} urgency"
        )

        print("\n=== Automated Controls ===")
        for control in strategies["automated_controls"]:
            print(f"• {control['name']}: {control['description']}")
            print(
                f"  Priority: {control['priority']}, Effectiveness: {control['effectiveness']}, Time: {control['implementation_time']}"
            )

        print("\n=== Manual Controls ===")
        for control in strategies["manual_controls"]:
            print(f"• {control['name']}: {control['description']}")
            print(
                f"  Priority: {control['priority']}, Frequency: {control['frequency']}, Effectiveness: {control['effectiveness']}"
            )

        print("\n=== Preventive Strategies ===")
        for strategy in strategies["preventive_strategies"]:
            print(f"• {strategy['name']}: {strategy['description']}")
            print(
                f"  Priority: {strategy['priority']}, Implementation: {strategy['implementation']}"
            )

        if args.verbose:
            print("\n=== Implementation Plan ===")
            for phase, details in strategies["implementation_plan"].items():
                print(f"{phase.replace('_', ' ').title()}:")
                print(f"  Duration: {details['duration']}")
                print(f"  Actions: {', '.join(details['actions'])}")
                print(f"  Priority: {details['priority']}")

            print("\n=== Monitoring Requirements ===")
            monitoring = strategies["monitoring_requirements"]
            print(f"Frequency: {monitoring['frequency']}")
            print(f"Metrics: {', '.join(monitoring['metrics'])}")
            print(f"Alerts: {', '.join(monitoring['alerts'])}")


if __name__ == "__main__":
    main()
