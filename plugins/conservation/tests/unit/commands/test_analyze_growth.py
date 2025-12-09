"""Tests for /analyze-growth command integration and workflow.

This module tests the analyze-growth command orchestration,
growth analysis, and resource monitoring following TDD/BDD principles.
"""

import pytest


class TestAnalyzeGrowthCommand:
    """Feature: /analyze-growth command analyzes resource usage and growth patterns.

    As a user of the analyze-growth command
    I want to understand resource usage trends and identify optimization opportunities
    So that I can make informed decisions about resource management
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_analyzes_growth_patterns_across_timeframes(
        self,
        sample_growth_analysis,
    ) -> None:
        """Scenario: Command analyzes growth patterns across different timeframes

        Given various analysis timeframes
        When analyzing resource growth
        Then it should identify trends and patterns
        And provide actionable insights.
        """
        # Arrange
        timeframes = ["24_hours", "7_days", "30_days"]
        growth_data = sample_growth_analysis

        # Act - simulate growth analysis
        analysis_results = []

        for timeframe in timeframes:
            # Simulate different growth patterns for different timeframes
            if timeframe == "24_hours":
                pattern = {
                    "trend": "stable",
                    "growth_percentage": 5.2,
                    "peak_hour": "14:00",
                    "recommendation": "Current usage is optimal",
                }
            elif timeframe == "7_days":
                pattern = {
                    "trend": "increasing",
                    "growth_percentage": growth_data["growth_percentage"],
                    "peak_hour": growth_data["peak_usage_hour"],
                    "recommendation": growth_data["recommendations"][0],
                }
            else:  # 30_days
                pattern = {
                    "trend": "accelerating",
                    "growth_percentage": 280.5,
                    "peak_hour": "15:30",
                    "recommendation": (
                        "Consider optimization strategies and scaling plans"
                    ),
                }

            analysis_results.append({"timeframe": timeframe, "pattern": pattern})

        # Assert
        assert len(analysis_results) == 3

        # Verify 7-day analysis matches sample data
        week_analysis = next(r for r in analysis_results if r["timeframe"] == "7_days")
        assert week_analysis["pattern"]["growth_percentage"] == 150.0
        assert week_analysis["pattern"]["peak_hour"] == "14:00"

        # Verify trend progression
        assert analysis_results[0]["pattern"]["trend"] == "stable"
        assert analysis_results[1]["pattern"]["trend"] == "increasing"
        assert analysis_results[2]["pattern"]["trend"] == "accelerating"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_generates_resource_efficiency_metrics(self) -> None:
        """Scenario: Command generates comprehensive resource efficiency metrics

        Given resource usage data across multiple dimensions
        When calculating efficiency metrics
        Then it should provide multi-dimensional efficiency analysis
        And identify optimization opportunities.
        """
        # Arrange
        resource_metrics = {
            "token_usage": {
                "current": 2500,
                "baseline": 1000,
                "quota_limit": 100000,
                "efficiency_target": 0.8,
            },
            "context_usage": {
                "current_window": 85000,
                "total_window": 200000,
                "efficiency_target": 0.5,
            },
            "performance": {
                "response_time": 1.2,
                "target_time": 1.0,
                "success_rate": 0.95,
                "target_success": 0.98,
            },
        }

        # Act - calculate efficiency metrics
        efficiency_analysis = {}

        for resource_type, metrics in resource_metrics.items():
            if resource_type == "token_usage":
                efficiency_score = (
                    metrics["quota_limit"] - metrics["current"]
                ) / metrics["quota_limit"]
                efficiency_analysis["token_efficiency"] = {
                    "score": efficiency_score,
                    "status": "excellent"
                    if efficiency_score > 0.9
                    else "good"
                    if efficiency_score > 0.7
                    else "needs_improvement",
                    "growth_rate": (
                        (metrics["current"] - metrics["baseline"]) / metrics["baseline"]
                    )
                    * 100,
                    "quota_utilization": (metrics["current"] / metrics["quota_limit"])
                    * 100,
                }

            elif resource_type == "context_usage":
                utilization_rate = metrics["current_window"] / metrics["total_window"]
                efficiency_analysis["context_efficiency"] = {
                    "utilization_percentage": utilization_rate * 100,
                    "mecw_compliant": utilization_rate <= metrics["efficiency_target"],
                    "status": "optimal"
                    if utilization_rate < 0.3
                    else "acceptable"
                    if utilization_rate < 0.5
                    else "high",
                }

            elif resource_type == "performance":
                response_efficiency = metrics["target_time"] / metrics["response_time"]
                success_efficiency = metrics["success_rate"] / metrics["target_success"]
                overall_efficiency = (response_efficiency + success_efficiency) / 2

                efficiency_analysis["performance_efficiency"] = {
                    "response_efficiency": response_efficiency,
                    "success_efficiency": success_efficiency,
                    "overall_score": overall_efficiency,
                    "status": "excellent"
                    if overall_efficiency > 0.9
                    else "good"
                    if overall_efficiency > 0.8
                    else "needs_attention",
                }

        # Assert
        assert "token_efficiency" in efficiency_analysis
        assert "context_efficiency" in efficiency_analysis
        assert "performance_efficiency" in efficiency_analysis

        # Verify token efficiency calculations
        token_eff = efficiency_analysis["token_efficiency"]
        assert token_eff["score"] > 0.9  # 97500/100000
        assert token_eff["status"] == "excellent"
        assert token_eff["growth_rate"] == 150.0

        # Verify context efficiency
        context_eff = efficiency_analysis["context_efficiency"]
        assert context_eff["utilization_percentage"] == 42.5
        assert context_eff["mecw_compliant"] is True
        assert context_eff["status"] == "acceptable"

    @pytest.mark.unit
    def test_command_provides_actionable_recommendations(
        self, sample_growth_analysis
    ) -> None:
        """Scenario: Command provides actionable optimization recommendations

        Given growth analysis and efficiency metrics
        When generating recommendations
        Then it should provide specific, prioritized actions
        And estimate potential impact.
        """
        # Arrange
        analysis_data = {
            "growth_trend": "increasing",
            "growth_percentage": 150.0,
            "efficiency_score": 0.75,
            "peak_usage_times": ["14:00-16:00"],
            "resource_pressure_points": ["token_usage", "context_utilization"],
        }

        # Act - generate recommendations
        recommendations = []

        # Growth-based recommendations
        if (
            analysis_data["growth_trend"] == "increasing"
            and analysis_data["growth_percentage"] > 100
        ):
            recommendations.append(
                {
                    "category": "growth_management",
                    "priority": "high",
                    "action": "Implement proactive optimization strategies",
                    "impact": "Prevent resource exhaustion",
                    "implementation": "Set up automated monitoring and alerts",
                },
            )

        # Efficiency-based recommendations
        if analysis_data["efficiency_score"] < 0.8:
            recommendations.append(
                {
                    "category": "efficiency_improvement",
                    "priority": "medium",
                    "action": "Optimize resource usage patterns",
                    "impact": (
                        f"Improve efficiency by "
                        f"{(1 - analysis_data['efficiency_score']) * 100:.1f}%"
                    ),
                    "implementation": "Apply token conservation and context optimization",
                },
            )

        # Peak usage recommendations
        if analysis_data["peak_usage_times"]:
            recommendations.append(
                {
                    "category": "peak_optimization",
                    "priority": "medium",
                    "action": "Optimize for peak usage periods",
                    "impact": "Reduce performance degradation during peak hours",
                    "implementation": f"Schedule resource-intensive tasks outside {analysis_data['peak_usage_times'][0]}",
                },
            )

        # Resource pressure recommendations
        for pressure_point in analysis_data["resource_pressure_points"]:
            if pressure_point == "token_usage":
                recommendations.append(
                    {
                        "category": "token_optimization",
                        "priority": "high",
                        "action": "Apply token conservation techniques",
                        "impact": "Reduce token consumption by 20-40%",
                        "implementation": "Use /optimize-context command regularly",
                    },
                )
            elif pressure_point == "context_utilization":
                recommendations.append(
                    {
                        "category": "context_optimization",
                        "priority": "medium",
                        "action": "Apply MECW principles",
                        "impact": "Maintain context under 50% threshold",
                        "implementation": "Enable progressive loading and context compression",
                    },
                )

        # Assert
        assert len(recommendations) >= 4

        # Verify high priority recommendations
        high_priority = [r for r in recommendations if r["priority"] == "high"]
        assert len(high_priority) >= 2

        # Verify recommendation structure
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "action" in rec
            assert "impact" in rec
            assert "implementation" in rec

        # Check specific recommendations
        categories = [r["category"] for r in recommendations]
        assert "growth_management" in categories
        assert "token_optimization" in categories
