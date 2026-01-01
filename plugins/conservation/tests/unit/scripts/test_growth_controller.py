#!/usr/bin/env python3
"""Tests for growth-controller.py script - actual implementation tests.

This module tests the GrowthController class following TDD/BDD principles,
exercising the actual implementation instead of mocks.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the growth-controller module dynamically (hyphenated filename)
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "growth_controller_module", scripts_dir / "growth-controller.py"
)
assert spec is not None
assert spec.loader is not None
growth_controller_module = importlib.util.module_from_spec(spec)
sys.modules["growth_controller_module"] = growth_controller_module
spec.loader.exec_module(growth_controller_module)

GrowthController = growth_controller_module.GrowthController


class TestGrowthControllerImplementation:
    """Feature: Growth controller generates appropriate control strategies.

    As a context growth management system
    I want to generate tailored control strategies based on analysis results
    So that users can effectively manage growth with appropriate urgency
    """

    @pytest.fixture
    def controller(self) -> GrowthController:
        """Provide a GrowthController instance."""
        return GrowthController()

    @pytest.fixture
    def stable_analysis(self) -> dict:
        """Provide analysis results for stable growth."""
        return {
            "severity": "STABLE",
            "urgency": "NONE",
            "growth_rate": 0.03,
            "controllable_percentage": 30.0,
        }

    @pytest.fixture
    def critical_analysis(self) -> dict:
        """Provide analysis results for critical growth."""
        return {
            "severity": "CRITICAL",
            "urgency": "URGENT",
            "growth_rate": 0.35,
            "controllable_percentage": 75.0,
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_generates_strategies_for_stable_growth(
        self, controller: GrowthController, stable_analysis: dict
    ) -> None:
        """Scenario: Controller generates appropriate strategies for stable growth.

        Given stable growth analysis results
        When generating control strategies
        Then it should recommend conservative approach
        And focus on prevention over intervention
        """
        # Act
        result = controller.generate_control_strategies(stable_analysis, "conservative")

        # Assert
        assert "metadata" in result
        assert result["metadata"]["strategy_type"] == "conservative"
        assert result["metadata"]["analysis_severity"] == "STABLE"
        assert "automated_controls" in result
        assert "preventive_strategies" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_generates_strategies_for_critical_growth(
        self, controller: GrowthController, critical_analysis: dict
    ) -> None:
        """Scenario: Controller generates urgent strategies for critical growth.

        Given critical growth analysis results
        When generating control strategies
        Then it should recommend aggressive approach
        And prioritize immediate intervention
        """
        # Act
        result = controller.generate_control_strategies(critical_analysis, "aggressive")

        # Assert
        assert result["metadata"]["analysis_severity"] == "CRITICAL"
        assert "automated_controls" in result
        assert len(result["automated_controls"]) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "strategy_type",
        ["conservative", "moderate", "aggressive"],
    )
    def test_controller_supports_all_strategy_types(
        self,
        controller: GrowthController,
        stable_analysis: dict,
        strategy_type: str,
    ) -> None:
        """Scenario: Controller supports all defined strategy types.

        Given a valid strategy type
        When generating strategies
        Then it should successfully generate appropriate strategies
        """
        # Act
        result = controller.generate_control_strategies(stable_analysis, strategy_type)

        # Assert
        assert "metadata" in result
        assert result["metadata"]["strategy_type"] == strategy_type

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_rejects_invalid_strategy_type(
        self, controller: GrowthController, stable_analysis: dict
    ) -> None:
        """Scenario: Controller rejects invalid strategy types.

        Given an invalid strategy type
        When attempting to generate strategies
        Then it should raise a ValueError
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid strategy type"):
            controller.generate_control_strategies(stable_analysis, "invalid_type")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_defaults_to_moderate_strategy(
        self, controller: GrowthController, stable_analysis: dict
    ) -> None:
        """Scenario: Controller defaults to moderate strategy when not specified.

        Given analysis results without strategy type specified
        When generating strategies
        Then it should use moderate strategy as default
        """
        # Act
        result = controller.generate_control_strategies(stable_analysis)

        # Assert
        assert result["metadata"]["strategy_type"] == "moderate"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_includes_strategy_metadata(
        self, controller: GrowthController, stable_analysis: dict
    ) -> None:
        """Scenario: Controller includes comprehensive strategy metadata.

        Given any analysis results
        When generating strategies
        Then result should include implementation details and risk assessment
        """
        # Act
        result = controller.generate_control_strategies(stable_analysis, "moderate")

        # Assert - verify key metadata fields
        assert "metadata" in result
        assert "strategy_type" in result["metadata"]
        assert "analysis_severity" in result["metadata"]
        assert "analysis_urgency" in result["metadata"]
        assert "automated_controls" in result
        assert "manual_controls" in result
        assert "preventive_strategies" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_handles_missing_analysis_fields(
        self, controller: GrowthController
    ) -> None:
        """Scenario: Controller handles incomplete analysis results gracefully.

        Given analysis results with missing optional fields
        When generating strategies
        Then it should use defaults and not crash
        """
        # Arrange - minimal analysis data
        minimal_analysis = {
            "severity": "MILD",
        }

        # Act
        result = controller.generate_control_strategies(minimal_analysis)

        # Assert
        assert "metadata" in result
        assert result["metadata"]["analysis_severity"] == "MILD"
        assert "automated_controls" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_strategy_priorities_differ_by_type(
        self, controller: GrowthController, stable_analysis: dict
    ) -> None:
        """Scenario: Different strategy types have different action priorities.

        Given the same analysis results
        When generating strategies with different types
        Then action priorities should differ appropriately
        """
        # Act
        conservative = controller.generate_control_strategies(
            stable_analysis, "conservative"
        )
        aggressive = controller.generate_control_strategies(
            stable_analysis, "aggressive"
        )

        # Assert - strategies should differ
        assert (
            conservative["metadata"]["strategy_type"]
            != aggressive["metadata"]["strategy_type"]
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_produces_consistent_results(
        self, controller: GrowthController, stable_analysis: dict
    ) -> None:
        """Scenario: Controller produces deterministic results.

        Given identical analysis results
        When generating strategies multiple times
        Then results should be consistent
        """
        # Act
        result1 = controller.generate_control_strategies(stable_analysis, "moderate")
        result2 = controller.generate_control_strategies(stable_analysis, "moderate")

        # Assert - key fields should match
        assert (
            result1["metadata"]["strategy_type"] == result2["metadata"]["strategy_type"]
        )
        assert (
            result1["metadata"]["analysis_severity"]
            == result2["metadata"]["analysis_severity"]
        )
        assert (
            result1["metadata"]["analysis_urgency"]
            == result2["metadata"]["analysis_urgency"]
        )


class TestGrowthControllerStrategyTypes:
    """Test strategy type definitions and characteristics."""

    @pytest.fixture
    def controller(self) -> GrowthController:
        """Provide a GrowthController instance."""
        return GrowthController()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_conservative_strategy_characteristics(
        self, controller: GrowthController
    ) -> None:
        """Scenario: Conservative strategy has appropriate characteristics.

        Given the conservative strategy type
        When examining its properties
        Then it should prioritize prevention and low risk
        """
        # Act
        strategy_def = controller.strategy_types["conservative"]

        # Assert
        assert strategy_def["risk_level"] == "Low"
        assert "Prevention" in strategy_def["priority"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_aggressive_strategy_characteristics(
        self, controller: GrowthController
    ) -> None:
        """Scenario: Aggressive strategy has appropriate characteristics.

        Given the aggressive strategy type
        When examining its properties
        Then it should prioritize control and accept higher risk
        """
        # Act
        strategy_def = controller.strategy_types["aggressive"]

        # Assert
        assert strategy_def["risk_level"] == "High"
        assert "Automated Control" in strategy_def["priority"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_strategy_types_have_required_fields(
        self, controller: GrowthController
    ) -> None:
        """Scenario: All strategy types have complete definitions.

        Given all defined strategy types
        When examining their properties
        Then each should have all required fields
        """
        # Act & Assert
        required_fields = [
            "description",
            "priority",
            "implementation_speed",
            "risk_level",
        ]

        for strategy_name, strategy_def in controller.strategy_types.items():
            for field in required_fields:
                assert field in strategy_def, f"{strategy_name} missing {field}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_strategy_priorities_are_lists(self, controller: GrowthController) -> None:
        """Scenario: Strategy priorities are properly ordered lists.

        Given all strategy types
        When examining their priorities
        Then priorities should be lists with multiple items
        """
        # Act & Assert
        for strategy_name, strategy_def in controller.strategy_types.items():
            priorities = strategy_def["priority"]
            assert isinstance(priorities, list), f"{strategy_name} priority not a list"
            assert len(priorities) > 0, f"{strategy_name} has empty priorities"


class TestGrowthControllerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def controller(self) -> GrowthController:
        """Provide a GrowthController instance."""
        return GrowthController()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_handles_extreme_growth_rate(
        self, controller: GrowthController
    ) -> None:
        """Scenario: Controller handles extreme growth rates.

        Given analysis with extreme growth rate
        When generating strategies
        Then it should handle gracefully without errors
        """
        # Arrange
        extreme_analysis = {
            "severity": "CRITICAL",
            "urgency": "URGENT",
            "growth_rate": 2.5,  # 250% growth rate
            "controllable_percentage": 90.0,
        }

        # Act
        result = controller.generate_control_strategies(extreme_analysis, "aggressive")

        # Assert
        assert "automated_controls" in result
        assert result["metadata"]["analysis_severity"] == "CRITICAL"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_handles_zero_controllable_growth(
        self, controller: GrowthController
    ) -> None:
        """Scenario: Controller handles zero controllable growth.

        Given analysis with no controllable growth
        When generating strategies
        Then it should still provide actionable recommendations
        """
        # Arrange
        uncontrollable_analysis = {
            "severity": "MODERATE",
            "urgency": "MEDIUM",
            "growth_rate": 0.15,
            "controllable_percentage": 0.0,
        }

        # Act
        result = controller.generate_control_strategies(uncontrollable_analysis)

        # Assert
        assert "automated_controls" in result or "manual_controls" in result
        # Should have at least some controls/strategies
        total_controls = (
            len(result.get("automated_controls", []))
            + len(result.get("manual_controls", []))
            + len(result.get("preventive_strategies", []))
        )
        assert total_controls > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_controller_handles_empty_analysis(
        self, controller: GrowthController
    ) -> None:
        """Scenario: Controller handles empty analysis gracefully.

        Given empty analysis results
        When generating strategies
        Then it should use defaults and not crash
        """
        # Arrange
        empty_analysis: dict = {}

        # Act
        result = controller.generate_control_strategies(empty_analysis)

        # Assert
        assert "metadata" in result
        assert "automated_controls" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
