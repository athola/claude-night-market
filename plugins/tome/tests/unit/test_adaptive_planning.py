"""
Feature: Adaptive research replanning

As a research orchestrator
I want to adjust channel weights based on partial results
So that channels yielding nothing lose budget to productive ones
"""

from __future__ import annotations

import pytest
from tome.models import ResearchPlan
from tome.scripts.research_planner import replan

from tests.factories import make_finding


class TestReplan:
    """
    Feature: Adaptive weight redistribution

    As the research planner
    I want to shift budget from empty channels to productive ones
    So that a second research pass focuses effort where results exist
    """

    @pytest.mark.unit
    def test_empty_channel_loses_weight(self) -> None:
        """
        Scenario: One channel returned nothing
        Given a plan with code and discourse channels
        And code returned 5 findings but discourse returned 0
        When replan is called
        Then discourse weight decreases
        """
        original = ResearchPlan(
            channels=["code", "discourse"],
            weights={"code": 0.5, "discourse": 0.5},
            triz_depth="medium",
            estimated_budget=4000,
        )
        partial_results = {
            "code": [make_finding(0.7) for _ in range(5)],
            "discourse": [],
        }

        new_plan = replan(original, partial_results)

        assert new_plan.weights["code"] > new_plan.weights["discourse"]

    @pytest.mark.unit
    def test_weights_still_sum_to_one(self) -> None:
        """
        Scenario: Weights remain normalized
        Given any partial results
        When replan is called
        Then weights sum to 1.0
        """
        original = ResearchPlan(
            channels=["code", "discourse", "academic"],
            weights={"code": 0.33, "discourse": 0.33, "academic": 0.34},
            triz_depth="medium",
            estimated_budget=4000,
        )
        partial_results = {
            "code": [make_finding(0.7)],
            "discourse": [],
            "academic": [make_finding(0.8), make_finding(0.6)],
        }

        new_plan = replan(original, partial_results)

        assert abs(sum(new_plan.weights.values()) - 1.0) < 0.01

    @pytest.mark.unit
    def test_all_empty_returns_equal_weights(self) -> None:
        """
        Scenario: No channels produced results
        Given all channels returned empty lists
        When replan is called
        Then weights are distributed equally
        """
        original = ResearchPlan(
            channels=["code", "discourse"],
            weights={"code": 0.5, "discourse": 0.5},
            triz_depth="light",
            estimated_budget=2000,
        )
        partial_results = {"code": [], "discourse": []}

        new_plan = replan(original, partial_results)

        assert abs(new_plan.weights["code"] - 0.5) < 0.01
        assert abs(new_plan.weights["discourse"] - 0.5) < 0.01

    @pytest.mark.unit
    def test_preserves_channels_and_depth(self) -> None:
        """
        Scenario: Plan metadata unchanged
        Given an original plan
        When replan is called
        Then channels and triz_depth are preserved
        """
        original = ResearchPlan(
            channels=["code", "academic"],
            weights={"code": 0.6, "academic": 0.4},
            triz_depth="deep",
            estimated_budget=6000,
        )
        partial_results = {
            "code": [make_finding(0.7)],
            "academic": [make_finding(0.9)],
        }

        new_plan = replan(original, partial_results)

        assert new_plan.channels == original.channels
        assert new_plan.triz_depth == original.triz_depth
