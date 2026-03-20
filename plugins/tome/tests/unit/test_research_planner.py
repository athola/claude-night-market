"""
Feature: Research planner

As a research pipeline orchestrator
I want to turn a domain classification into an executable research plan
So that channel runners know which sources to query and at what cost
"""

from __future__ import annotations

import pytest
from tome.models import DomainClassification, ResearchPlan
from tome.scripts.research_planner import plan


def _make_classification(
    domain: str,
    triz_depth: str,
    confidence: float = 0.80,
) -> DomainClassification:
    """Build a minimal classification for planner tests."""
    weights_by_domain = {
        "ui-ux": {"code": 0.35, "discourse": 0.40, "academic": 0.15, "triz": 0.10},
        "algorithm": {"code": 0.25, "discourse": 0.20, "academic": 0.40, "triz": 0.15},
        "architecture": {
            "code": 0.30,
            "discourse": 0.30,
            "academic": 0.20,
            "triz": 0.20,
        },
        "data-structure": {
            "code": 0.25,
            "discourse": 0.15,
            "academic": 0.35,
            "triz": 0.25,
        },
        "scientific": {"code": 0.15, "discourse": 0.10, "academic": 0.50, "triz": 0.25},
        "financial": {"code": 0.20, "discourse": 0.30, "academic": 0.35, "triz": 0.15},
        "devops": {"code": 0.35, "discourse": 0.40, "academic": 0.10, "triz": 0.15},
        "security": {"code": 0.30, "discourse": 0.25, "academic": 0.30, "triz": 0.15},
        "general": {"code": 0.30, "discourse": 0.35, "academic": 0.20, "triz": 0.15},
    }
    return DomainClassification(
        domain=domain,
        triz_depth=triz_depth,
        channel_weights=weights_by_domain[domain],
        confidence=confidence,
    )


class TestResearchPlannerChannelInclusion:
    """
    Feature: Channel inclusion rules

    As a pipeline executor
    I want the plan to include exactly the channels warranted by TRIZ depth
    So that expensive channels are not invoked unnecessarily
    """

    @pytest.mark.unit
    def test_light_depth_includes_code_and_discourse_only(self) -> None:
        """
        Scenario: Light depth uses only community channels
        Given a ui-ux/light classification
        When plan is called
        Then channels contains code and discourse, not academic or triz
        """

        classification = _make_classification("ui-ux", "light")
        result = plan(classification)

        assert "code" in result.channels
        assert "discourse" in result.channels
        assert "academic" not in result.channels
        assert "triz" not in result.channels

    @pytest.mark.unit
    def test_medium_depth_includes_academic_not_triz(self) -> None:
        """
        Scenario: Medium depth adds academic channel
        Given an algorithm/medium classification
        When plan is called
        Then channels contains code, discourse, and academic but not triz
        """

        classification = _make_classification("algorithm", "medium")
        result = plan(classification)

        assert "code" in result.channels
        assert "discourse" in result.channels
        assert "academic" in result.channels
        assert "triz" not in result.channels

    @pytest.mark.unit
    def test_deep_depth_includes_all_four_channels(self) -> None:
        """
        Scenario: Deep depth uses all channels including triz
        Given a data-structure/deep classification
        When plan is called
        Then channels contains code, discourse, academic, and triz
        """

        classification = _make_classification("data-structure", "deep")
        result = plan(classification)

        assert set(result.channels) == {"code", "discourse", "academic", "triz"}

    @pytest.mark.unit
    def test_maximum_depth_includes_all_four_channels(self) -> None:
        """
        Scenario: Maximum depth also uses all channels
        Given a scientific/maximum classification
        When plan is called
        Then channels contains all four
        """

        classification = DomainClassification(
            domain="scientific",
            triz_depth="maximum",
            channel_weights={
                "code": 0.15,
                "discourse": 0.10,
                "academic": 0.50,
                "triz": 0.25,
            },
            confidence=0.90,
        )
        result = plan(classification)

        assert set(result.channels) == {"code", "discourse", "academic", "triz"}


class TestResearchPlannerBudget:
    """
    Feature: Budget estimation by TRIZ depth

    As a cost-aware pipeline
    I want the plan to carry an estimated token budget
    So that callers can decide whether to proceed
    """

    @pytest.mark.unit
    def test_light_depth_budget_is_2000(self) -> None:
        """
        Scenario: Light depth maps to 2000 token budget
        Given a ui-ux/light classification
        When plan is called
        Then estimated_budget is 2000
        """

        result = plan(_make_classification("ui-ux", "light"))

        assert result.estimated_budget == 2000

    @pytest.mark.unit
    def test_medium_depth_budget_is_4000(self) -> None:
        """
        Scenario: Medium depth maps to 4000 token budget
        Given an algorithm/medium classification
        When plan is called
        Then estimated_budget is 4000
        """

        result = plan(_make_classification("algorithm", "medium"))

        assert result.estimated_budget == 4000

    @pytest.mark.unit
    def test_deep_depth_budget_is_6000(self) -> None:
        """
        Scenario: Deep depth maps to 6000 token budget
        Given a data-structure/deep classification
        When plan is called
        Then estimated_budget is 6000
        """

        result = plan(_make_classification("data-structure", "deep"))

        assert result.estimated_budget == 6000

    @pytest.mark.unit
    def test_maximum_depth_budget_is_8000(self) -> None:
        """
        Scenario: Maximum depth maps to 8000 token budget
        Given a scientific/maximum classification
        When plan is called
        Then estimated_budget is 8000
        """

        classification = DomainClassification(
            domain="scientific",
            triz_depth="maximum",
            channel_weights={
                "code": 0.15,
                "discourse": 0.10,
                "academic": 0.50,
                "triz": 0.25,
            },
            confidence=0.90,
        )
        result = plan(classification)

        assert result.estimated_budget == 8000


class TestResearchPlannerWeights:
    """
    Feature: Weight propagation from classification to plan

    As a channel executor
    I want plan weights to reflect only the active channels
    So that token allocation matches actual work performed
    """

    @pytest.mark.unit
    def test_weights_sum_to_one_for_light_plan(self) -> None:
        """
        Scenario: Light plan weights are normalised over active channels
        Given a ui-ux/light plan
        When plan is called
        Then the active-channel weights sum to 1.0
        """

        result = plan(_make_classification("ui-ux", "light"))

        total = sum(result.weights[ch] for ch in result.channels)
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.unit
    def test_weights_sum_to_one_for_medium_plan(self) -> None:
        """
        Scenario: Medium plan weights are normalised over active channels
        Given an algorithm/medium plan
        When plan is called
        Then the active-channel weights sum to 1.0
        """

        result = plan(_make_classification("algorithm", "medium"))

        total = sum(result.weights[ch] for ch in result.channels)
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.unit
    def test_weights_sum_to_one_for_deep_plan(self) -> None:
        """
        Scenario: Deep plan weights are normalised over active channels
        Given a data-structure/deep plan
        When plan is called
        Then the active-channel weights sum to 1.0
        """

        result = plan(_make_classification("data-structure", "deep"))

        total = sum(result.weights[ch] for ch in result.channels)
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.unit
    def test_plan_weights_preserve_relative_ratios(self) -> None:
        """
        Scenario: Relative weight ordering from classification is preserved
        Given an algorithm/medium classification where academic > code > discourse
        When plan is called
        Then plan weights for active channels preserve that ordering
        """

        # algorithm: code=0.25, discourse=0.20, academic=0.40, triz=0.15
        # active channels for medium: code, discourse, academic
        # after normalisation: academic > code > discourse
        result = plan(_make_classification("algorithm", "medium"))

        assert result.weights["academic"] > result.weights["code"]
        assert result.weights["code"] > result.weights["discourse"]

    @pytest.mark.unit
    def test_returns_research_plan_instance(self) -> None:
        """
        Scenario: Return type is always ResearchPlan
        Given any classification
        When plan is called
        Then result is a ResearchPlan
        """

        result = plan(_make_classification("devops", "light"))

        assert isinstance(result, ResearchPlan)
