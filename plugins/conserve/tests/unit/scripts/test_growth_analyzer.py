#!/usr/bin/env python3
"""Tests for growth-analyzer.py script - actual implementation tests.

This module tests the GrowthAnalyzer class following TDD/BDD principles,
exercising the actual implementation instead of mocks.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the growth-analyzer module dynamically (hyphenated filename)
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "growth_analyzer_module", scripts_dir / "growth-analyzer.py"
)
assert spec is not None
assert spec.loader is not None
growth_analyzer_module = importlib.util.module_from_spec(spec)
sys.modules["growth_analyzer_module"] = growth_analyzer_module
spec.loader.exec_module(growth_analyzer_module)

GrowthAnalyzer = growth_analyzer_module.GrowthAnalyzer


class TestGrowthAnalyzerImplementation:
    """Feature: Growth analyzer detects and projects context growth patterns.

    As a context growth monitoring system
    I want to analyze growth patterns and project future usage
    So that users can proactively optimize resource consumption
    """

    @pytest.fixture
    def analyzer(self) -> GrowthAnalyzer:
        """Provide a GrowthAnalyzer instance."""
        return GrowthAnalyzer()

    @pytest.fixture
    def stable_growth_data(self) -> dict:
        """Provide test data for stable growth scenario."""
        return {
            "growth_trend": {
                "current_usage": 1000,
                "rate": 0.03,  # 3% growth rate - stable
                "acceleration": 0.001,
            },
            "content_breakdown": {
                "code_blocks": {
                    "growth_contribution": 200,
                    "growth_rate": 0.05,
                },
                "comments": {
                    "growth_contribution": 300,
                    "growth_rate": 0.15,  # >10% - controllable
                },
                "documentation": {
                    "growth_contribution": 500,
                    "growth_rate": 0.02,
                },
            },
        }

    @pytest.fixture
    def critical_growth_data(self) -> dict:
        """Provide test data for critical growth scenario."""
        return {
            "growth_trend": {
                "current_usage": 8000,
                "rate": 0.30,  # 30% growth rate - critical
                "acceleration": 0.025,
            },
            "content_breakdown": {
                "code_blocks": {
                    "growth_contribution": 2000,
                    "growth_rate": 0.25,  # >10% - controllable
                },
                "comments": {
                    "growth_contribution": 3000,
                    "growth_rate": 0.30,  # >10% - controllable
                },
                "documentation": {
                    "growth_contribution": 3000,
                    "growth_rate": 0.35,  # >10% - controllable
                },
            },
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_assesses_stable_growth_correctly(
        self, analyzer: GrowthAnalyzer, stable_growth_data: dict
    ) -> None:
        """Scenario: Analyzer correctly identifies stable growth patterns.

        Given context growth data with low growth rate
        When analyzing growth patterns
        Then it should classify as STABLE severity
        And urgency should be low or none
        """
        # Act
        result = analyzer.analyze_growth_patterns(stable_growth_data)

        # Assert
        assert result["severity"] == "STABLE", "Should classify as STABLE growth"
        assert result["urgency"] in [
            "NONE",
            "LOW",
        ], "Urgency should be minimal for stable growth"
        assert result["current_usage"] == 1000
        assert result["growth_rate"] == 0.03
        assert "projections" in result
        assert "analysis_timestamp" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_detects_critical_growth(
        self, analyzer: GrowthAnalyzer, critical_growth_data: dict
    ) -> None:
        """Scenario: Analyzer detects critical growth requiring urgent action.

        Given context growth data with high growth rate and acceleration
        When analyzing growth patterns
        Then it should classify as CRITICAL severity
        And urgency should be high or urgent
        """
        # Act
        result = analyzer.analyze_growth_patterns(critical_growth_data)

        # Assert
        assert result["severity"] == "CRITICAL", "Should classify as CRITICAL growth"
        assert result["urgency"] in [
            "HIGH",
            "URGENT",
        ], "Urgency should be high for critical growth"
        assert result["current_usage"] == 8000
        assert result["growth_rate"] == 0.30
        assert result["acceleration"] == 0.025

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_generates_valid_projections(
        self, analyzer: GrowthAnalyzer, stable_growth_data: dict
    ) -> None:
        """Scenario: Analyzer generates accurate growth projections.

        Given current growth metrics
        When generating projections
        Then it should project growth for multiple horizons
        And projections should increase with time
        """
        # Act
        result = analyzer.analyze_growth_patterns(stable_growth_data)

        # Assert
        projections = result["projections"]
        assert len(projections) > 0, "Should generate projections"

        # Projections are keyed by turn count (e.g., "5_turns", "10_turns")
        turn_keys = [
            k
            for k in projections.keys()
            if k.endswith("_turns") and k != "mecw_violation_turns"
        ]
        assert len(turn_keys) > 0, "Should have turn-based projections"

        # Verify projection structure
        for turn_key in turn_keys:
            projection = projections[turn_key]
            assert "projected_usage" in projection
            assert "projected_growth" in projection
            assert "growth_percentage" in projection

            # With positive growth rate, projections should increase
            if result["growth_rate"] > 0:
                assert projection["projected_usage"] >= result["current_usage"], (
                    "Projections should be >= current usage with positive growth"
                )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_calculates_controllable_growth(
        self, analyzer: GrowthAnalyzer, stable_growth_data: dict
    ) -> None:
        """Scenario: Analyzer identifies controllable vs uncontrollable growth.

        Given content breakdown data
        When analyzing growth components
        Then it should calculate percentage of controllable growth
        And provide insights for optimization
        """
        # Act
        result = analyzer.analyze_growth_patterns(stable_growth_data)

        # Assert
        assert "controllable_percentage" in result
        assert 0 <= result["controllable_percentage"] <= 100  # Returns percentage 0-100
        assert "content_breakdown" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "growth_rate,expected_severity",
        [
            (0.01, "STABLE"),  # 1% growth (< 0.05)
            (0.08, "STABLE"),  # 8% growth (< 0.10 threshold for MILD)
            (0.12, "MILD"),  # 12% growth (>= 0.10, < 0.15)
            (0.18, "MODERATE"),  # 18% growth (>= 0.15, < 0.20)
            (0.30, "CRITICAL"),  # 30% growth (>= 0.25)
        ],
    )
    def test_severity_classification_thresholds(
        self,
        analyzer: GrowthAnalyzer,
        growth_rate: float,
        expected_severity: str,
    ) -> None:
        """Scenario: Analyzer classifies growth severity based on rate thresholds.

        Given various growth rates
        When assessing severity
        Then it should apply correct threshold classifications
        """
        # Arrange
        test_data = {
            "growth_trend": {
                "current_usage": 5000,
                "rate": growth_rate,
                "acceleration": 0.001,
            },
            "content_breakdown": {
                "code_blocks": {
                    "growth_contribution": 1000,
                    "growth_rate": 0.05,
                }
            },
        }

        # Act
        result = analyzer.analyze_growth_patterns(test_data)

        # Assert
        assert result["severity"] == expected_severity, (
            f"Growth rate {growth_rate} should be {expected_severity}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_handles_zero_growth(self, analyzer: GrowthAnalyzer) -> None:
        """Scenario: Analyzer handles zero or negative growth gracefully.

        Given context with no growth or shrinking
        When analyzing patterns
        Then it should return valid results without errors
        And classify as stable
        """
        # Arrange
        zero_growth_data = {
            "growth_trend": {
                "current_usage": 3000,
                "rate": 0.0,
                "acceleration": 0.0,
            },
            "content_breakdown": {},
        }

        # Act
        result = analyzer.analyze_growth_patterns(zero_growth_data)

        # Assert
        assert result["severity"] == "STABLE"
        assert result["growth_rate"] == 0.0
        assert "projections" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_handles_missing_optional_data(
        self, analyzer: GrowthAnalyzer
    ) -> None:
        """Scenario: Analyzer handles missing optional data gracefully.

        Given incomplete context data
        When analyzing growth patterns
        Then it should use defaults and not crash
        And still provide meaningful results
        """
        # Arrange - minimal data
        minimal_data = {
            "growth_trend": {
                "current_usage": 2000,
                "rate": 0.05,
            },
        }

        # Act
        result = analyzer.analyze_growth_patterns(minimal_data)

        # Assert
        assert "severity" in result
        assert "urgency" in result
        assert "projections" in result
        assert result["current_usage"] == 2000

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_urgency_considers_both_rate_and_acceleration(
        self, analyzer: GrowthAnalyzer
    ) -> None:
        """Scenario: Urgency assessment considers both rate and acceleration.

        Given growth with moderate rate but high acceleration
        When assessing urgency
        Then it should elevate urgency due to acceleration
        """
        # Arrange - moderate rate but high acceleration
        accelerating_data = {
            "growth_trend": {
                "current_usage": 5000,
                "rate": 0.10,  # 10% rate - mild
                "acceleration": 0.020,  # High acceleration
            },
            "content_breakdown": {
                "code": {
                    "growth_contribution": 1000,
                    "growth_rate": 0.12,
                }
            },
        }

        # Act
        result = analyzer.analyze_growth_patterns(accelerating_data)

        # Assert
        # High acceleration should increase urgency even with moderate rate
        assert result["urgency"] in ["MEDIUM", "HIGH", "URGENT"]
        assert result["acceleration"] == 0.020

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_detects_severe_growth(self, analyzer: GrowthAnalyzer) -> None:
        """Scenario: Analyzer correctly identifies severe growth.

        Given context with severe growth rate
        When analyzing patterns
        Then it should classify as SEVERE
        """
        # Arrange
        severe_data = {
            "growth_trend": {
                "current_usage": 6000,
                "rate": 0.22,  # 22% - between 20-25%, should be SEVERE
                "acceleration": 0.015,
            },
            "content_breakdown": {
                "code": {
                    "growth_contribution": 1000,
                    "growth_rate": 0.20,
                }
            },
        }

        # Act
        result = analyzer.analyze_growth_patterns(severe_data)

        # Assert
        assert result["severity"] == "SEVERE"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_projects_mecw_violation(self, analyzer: GrowthAnalyzer) -> None:
        """Scenario: Analyzer projects turns until MECW violation.

        Given high growth rate approaching limits
        When analyzing projections
        Then it should estimate turns to MECW violation
        """
        # Arrange
        high_growth_data = {
            "growth_trend": {
                "current_usage": 70,  # Close to 100% limit
                "rate": 0.10,  # 10% growth
                "acceleration": 0.005,
            },
            "content_breakdown": {},
        }

        # Act
        result = analyzer.analyze_growth_patterns(high_growth_data)

        # Assert
        assert "projections" in result
        if "mecw_violation_turns" in result["projections"]:
            # Should predict violation in finite turns
            assert result["projections"]["mecw_violation_turns"] < 1000


class TestGrowthAnalyzerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def analyzer(self) -> GrowthAnalyzer:
        """Provide a GrowthAnalyzer instance."""
        return GrowthAnalyzer()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_handles_extreme_values(self, analyzer: GrowthAnalyzer) -> None:
        """Scenario: Analyzer handles extreme values gracefully.

        Given extreme growth values
        When analyzing patterns
        Then it should cap or handle values appropriately
        And not produce invalid results
        """
        # Arrange
        extreme_data = {
            "growth_trend": {
                "current_usage": 50000,  # Very high usage
                "rate": 0.95,  # 95% growth rate - extreme
                "acceleration": 0.10,  # Extreme acceleration
            },
            "content_breakdown": {
                "code": {
                    "growth_contribution": 10000,
                    "growth_rate": 0.50,
                }
            },
        }

        # Act
        result = analyzer.analyze_growth_patterns(extreme_data)

        # Assert
        assert result["severity"] == "CRITICAL"
        assert result["urgency"] in ["HIGH", "URGENT"]
        assert result["current_usage"] == 50000

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_produces_consistent_results(
        self, analyzer: GrowthAnalyzer
    ) -> None:
        """Scenario: Analyzer produces consistent results for same input.

        Given identical input data
        When running analysis multiple times
        Then results should be deterministic (except timestamps)
        """
        # Arrange
        test_data = {
            "growth_trend": {
                "current_usage": 4000,
                "rate": 0.15,
                "acceleration": 0.010,
            },
            "content_breakdown": {
                "code": {
                    "growth_contribution": 1000,
                    "growth_rate": 0.12,
                }
            },
        }

        # Act
        result1 = analyzer.analyze_growth_patterns(test_data)
        result2 = analyzer.analyze_growth_patterns(test_data)

        # Assert - key metrics should be identical
        assert result1["severity"] == result2["severity"]
        assert result1["urgency"] == result2["urgency"]
        assert result1["current_usage"] == result2["current_usage"]
        assert result1["growth_rate"] == result2["growth_rate"]
        assert result1["acceleration"] == result2["acceleration"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_handles_zero_growth_rate_mecw(
        self, analyzer: GrowthAnalyzer
    ) -> None:
        """Scenario: MECW estimation handles zero growth rate.

        Given zero or negative growth
        When estimating MECW violation
        Then it should return infinite turns
        """
        # Arrange
        zero_growth_data = {
            "growth_trend": {
                "current_usage": 50,
                "rate": 0.0,
                "acceleration": 0.0,
            },
            "content_breakdown": {},
        }

        # Act
        result = analyzer.analyze_growth_patterns(zero_growth_data)

        # Assert
        if "mecw_violation_turns" in result["projections"]:
            # Zero growth means it never hits limit
            import math

            assert (
                result["projections"]["mecw_violation_turns"] == math.inf
                or result["projections"]["mecw_violation_turns"] > 1000
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyzer_mecw_with_positive_acceleration(
        self, analyzer: GrowthAnalyzer
    ) -> None:
        """Scenario: MECW estimation handles positive acceleration.

        Given positive acceleration
        When estimating MECW violation
        Then it should use iterative approach
        """
        # Arrange
        accelerating_data = {
            "growth_trend": {
                "current_usage": 60,
                "rate": 0.05,
                "acceleration": 0.01,  # Positive acceleration
            },
            "content_breakdown": {},
        }

        # Act
        result = analyzer.analyze_growth_patterns(accelerating_data)

        # Assert
        assert "projections" in result
        if "mecw_violation_turns" in result["projections"]:
            # Should calculate violation turns
            assert isinstance(
                result["projections"]["mecw_violation_turns"], int | float
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
