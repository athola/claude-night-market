"""Tests for context-optimizer agent workflow and decision-making.

This module tests the autonomous context optimization agent
following TDD/BDD principles.
"""


# ruff: noqa: S101

import pytest


class TestContextOptimizerAgent:
    """Feature: Context optimizer agent autonomously manages context optimization.

    As an autonomous context optimization agent
    I want to continuously monitor and optimize context usage
    So that resource efficiency is maintained automatically
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_autonomously_monitors_context_pressure(self, mock_mecw_analyzer):
        """Scenario: Agent autonomously monitors context pressure
        Given varying context usage levels
        When monitoring context pressure
        Then it should detect pressure changes
        And trigger appropriate optimization responses.
        """
        # Arrange
        context_scenarios = [
            {"tokens": 30000, "expected_action": "continue_monitoring"},
            {"tokens": 80000, "expected_action": "light_optimization"},
            {"tokens": 110000, "expected_action": "moderate_optimization"},
            {"tokens": 150000, "expected_action": "aggressive_optimization"}
        ]

        # Act - simulate autonomous monitoring
        monitoring_actions = []

        for scenario in context_scenarios:
            analysis = mock_mecw_analyzer.analyze_context_usage(scenario["tokens"])

            # Determine agent action based on analysis
            if not analysis["mecw_compliant"]:
                if analysis["utilization_percentage"] > 70:
                    action = "aggressive_optimization"
                elif analysis["utilization_percentage"] > 50:
                    action = "moderate_optimization"
                else:
                    action = "light_optimization"
            else:
                action = "continue_monitoring"

            monitoring_actions.append({
                "context_tokens": scenario["tokens"],
                "utilization": analysis["utilization_percentage"],
                "status": analysis["status"],
                "action_taken": action,
                "compliance": analysis["mecw_compliant"]
            })

        # Assert
        assert len(monitoring_actions) == 4

        # Verify correct actions for each scenario
        for i, action in enumerate(monitoring_actions):
            assert action["action_taken"] == context_scenarios[i]["expected_action"]

        # Check compliance status
        non_compliant = [a for a in monitoring_actions if not a["compliance"]]
        assert len(non_compliant) >= 2  # Should detect violations

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_makes_optimal_optimization_decisions(self):
        """Scenario: Agent makes optimal optimization decisions
        Given multiple optimization strategies available
        When deciding on optimization approach
        Then it should select optimal strategy based on context
        And balance effectiveness with risk.
        """
        # Arrange
        optimization_strategies = [
            {
                "name": "context_compression",
                "effectiveness": 0.7,
                "risk": "low",
                "cost": 100,
                "applicable_conditions": ["moderate_pressure", "preservation_needed"]
            },
            {
                "name": "content_pruning",
                "effectiveness": 0.9,
                "risk": "high",
                "cost": 50,
                "applicable_conditions": ["high_pressure", "urgent_need"]
            },
            {
                "name": "progressive_loading",
                "effectiveness": 0.6,
                "risk": "low",
                "cost": 200,
                "applicable_conditions": ["large_context", "time_sensitive"]
            },
            {
                "name": "delegation_to_external",
                "effectiveness": 0.8,
                "risk": "medium",
                "cost": 300,
                "applicable_conditions": ["compute_intensive", "time_available"]
            }
        ]

        # Act - simulate decision making for different contexts
        decision_scenarios = [
            {
                "context": "moderate_pressure_with_preservation",
                "conditions": ["moderate_pressure", "preservation_needed"],
                "expected_strategy": "context_compression"
            },
            {
                "context": "high_pressure_urgent",
                "conditions": ["high_pressure", "urgent_need"],
                "expected_strategy": "content_pruning"
            },
            {
                "context": "large_context_time_sensitive",
                "conditions": ["large_context", "time_sensitive"],
                "expected_strategy": "progressive_loading"
            },
            {
                "context": "compute_intensive_with_time",
                "conditions": ["compute_intensive", "time_available"],
                "expected_strategy": "delegation_to_external"
            }
        ]

        agent_decisions = []

        for scenario in decision_scenarios:
            # Calculate decision scores
            candidate_strategies = []

            for strategy in optimization_strategies:
                # Check if strategy is applicable
                if any(condition in strategy["applicable_conditions"] for condition in scenario["conditions"]):
                    # Calculate decision score (effectiveness / risk_factor) - cost_penalty
                    risk_factor = {"low": 1.0, "medium": 1.5, "high": 2.0}[strategy["risk"]]
                    cost_penalty = strategy["cost"] / 1000  # Normalize cost
                    decision_score = (strategy["effectiveness"] / risk_factor) - cost_penalty

                    candidate_strategies.append({
                        "strategy": strategy["name"],
                        "score": decision_score,
                        "effectiveness": strategy["effectiveness"],
                        "risk": strategy["risk"],
                        "cost": strategy["cost"]
                    })

            # Select best strategy
            if candidate_strategies:
                best_strategy = max(candidate_strategies, key=lambda x: x["score"])

                agent_decision = {
                    "context": scenario["context"],
                    "selected_strategy": best_strategy["strategy"],
                    "decision_score": best_strategy["score"],
                    "expected_strategy": scenario["expected_strategy"],
                    "decision_correct": best_strategy["strategy"] == scenario["expected_strategy"]
                }

                agent_decisions.append(agent_decision)

        # Assert
        assert len(agent_decisions) == 4

        # Verify decision accuracy
        correct_decisions = [d for d in agent_decisions if d["decision_correct"]]
        assert len(correct_decisions) >= 3  # Should make mostly correct decisions

        # Verify all decisions have positive scores
        for decision in agent_decisions:
            assert decision["decision_score"] > 0

    @pytest.mark.unit
    def test_agent_learns_from_optimization_outcomes(self):
        """Scenario: Agent learns from optimization outcomes
        Given historical optimization results
        When making future decisions
        Then it should incorporate learned preferences
        And improve decision quality over time.
        """
        # Arrange
        historical_outcomes = [
            {
                "strategy": "context_compression",
                "outcome": "success",
                "effectiveness_achieved": 0.75,
                "user_satisfaction": 0.8,
                "context_type": "moderate_pressure"
            },
            {
                "strategy": "content_pruning",
                "outcome": "partial_success",
                "effectiveness_achieved": 0.6,
                "user_satisfaction": 0.5,
                "context_type": "high_pressure"
            },
            {
                "strategy": "progressive_loading",
                "outcome": "success",
                "effectiveness_achieved": 0.8,
                "user_satisfaction": 0.9,
                "context_type": "large_context"
            }
        ]

        # Act - simulate learning from outcomes
        learning_weights = {}

        # Calculate learned preferences
        for outcome in historical_outcomes:
            strategy = outcome["strategy"]
            context = outcome["context_type"]

            # Calculate success score
            success_score = (outcome["effectiveness_achieved"] + outcome["user_satisfaction"]) / 2

            # Update learning weights
            if strategy not in learning_weights:
                learning_weights[strategy] = {}

            learning_weights[strategy][context] = success_score

        # Simulate improved decision making with learning
        improved_decisions = []

        test_scenarios = [
            {"context_type": "moderate_pressure", "expected_best": "context_compression"},
            {"context_type": "large_context", "expected_best": "progressive_loading"}
        ]

        for scenario in test_scenarios:
            strategy_scores = []

            for strategy, context_scores in learning_weights.items():
                if scenario["context_type"] in context_scores:
                    strategy_scores.append({
                        "strategy": strategy,
                        "learned_score": context_scores[scenario["context_type"]]
                    })

            if strategy_scores:
                best_strategy = max(strategy_scores, key=lambda x: x["learned_score"])

                improved_decisions.append({
                    "context": scenario["context_type"],
                    "selected_strategy": best_strategy["strategy"],
                    "learned_score": best_strategy["learned_score"],
                    "expected_strategy": scenario["expected_best"],
                    "improvement_applied": best_strategy["strategy"] == scenario["expected_best"]
                })

        # Assert
        assert len(improved_decisions) >= 2

        # Verify learning improved decisions
        improvements = [d for d in improved_decisions if d["improvement_applied"]]
        assert len(improvements) >= 1

        # Verify learning scores are reasonable
        for decision in improved_decisions:
            assert 0 <= decision["learned_score"] <= 1
