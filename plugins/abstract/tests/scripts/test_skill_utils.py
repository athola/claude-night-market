"""Tests for the skill_utils shared utilities module.

Feature: Skill evaluation utility functions
    As a developer
    I want shared utility functions tested
    So that score grading and optimisation levels are correct
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from skill_utils import (  # noqa: E402
    EXCELLENT_THRESHOLD,
    GOOD_THRESHOLD,
    NEEDS_IMPROVEMENT_THRESHOLD,
    get_efficiency_grade,
    get_optimization_level,
)


class TestGetEfficiencyGrade:
    """Feature: Efficiency grading based on thresholds

    As a developer
    I want efficiency grades assigned correctly
    So that tool performance is rated consistently
    """

    @pytest.mark.unit
    def test_returns_a_for_value_at_excellent_threshold(self) -> None:
        """Scenario: Value at excellent threshold gets grade A
        Given a value equal to the excellent threshold (1500 default)
        When get_efficiency_grade is called
        Then the result is A
        """
        thresholds = {"excellent": 1500, "good": 2000, "acceptable": 2500}
        assert get_efficiency_grade(1500, thresholds) == "A"

    @pytest.mark.unit
    def test_returns_a_for_value_below_excellent_threshold(self) -> None:
        """Scenario: Value below excellent threshold gets grade A
        Given a value well below the excellent threshold
        When get_efficiency_grade is called
        Then the result is A
        """
        thresholds = {"excellent": 1500, "good": 2000, "acceptable": 2500}
        assert get_efficiency_grade(100, thresholds) == "A"

    @pytest.mark.unit
    def test_returns_b_for_value_between_excellent_and_good(self) -> None:
        """Scenario: Value between excellent and good gets grade B
        Given a value above the excellent threshold but at or below good
        When get_efficiency_grade is called
        Then the result is B
        """
        thresholds = {"excellent": 1500, "good": 2000, "acceptable": 2500}
        assert get_efficiency_grade(1800, thresholds) == "B"

    @pytest.mark.unit
    def test_returns_c_for_value_between_good_and_acceptable(self) -> None:
        """Scenario: Value between good and acceptable gets grade C
        Given a value above good but at or below acceptable
        When get_efficiency_grade is called
        Then the result is C
        """
        thresholds = {"excellent": 1500, "good": 2000, "acceptable": 2500}
        assert get_efficiency_grade(2200, thresholds) == "C"

    @pytest.mark.unit
    def test_returns_d_for_value_above_acceptable_threshold(self) -> None:
        """Scenario: Value above acceptable threshold gets grade D
        Given a value exceeding all thresholds
        When get_efficiency_grade is called
        Then the result is D
        """
        thresholds = {"excellent": 1500, "good": 2000, "acceptable": 2500}
        assert get_efficiency_grade(3000, thresholds) == "D"

    @pytest.mark.unit
    def test_uses_default_excellent_threshold_when_key_absent(self) -> None:
        """Scenario: Missing 'excellent' key uses default of 1500
        Given thresholds dict without 'excellent' key
        When get_efficiency_grade is called with value <= 1500
        Then the result is A
        """
        thresholds = {"good": 2000, "acceptable": 2500}
        assert get_efficiency_grade(1000, thresholds) == "A"

    @pytest.mark.unit
    def test_empty_thresholds_uses_all_defaults(self) -> None:
        """Scenario: Empty thresholds dict uses all defaults
        Given an empty thresholds dict
        When get_efficiency_grade is called with value 0
        Then the result is A (below default excellent of 1500)
        """
        assert get_efficiency_grade(0, {}) == "A"


class TestGetOptimizationLevel:
    """Feature: Optimisation level description from score

    As a developer
    I want human-readable optimisation levels from numeric scores
    So that reports are easy to interpret
    """

    @pytest.mark.unit
    def test_score_at_excellent_threshold_returns_excellent(self) -> None:
        """Scenario: Score at excellent threshold returns 'excellent'
        Given a score equal to EXCELLENT_THRESHOLD
        When get_optimization_level is called
        Then the result is 'excellent'
        """
        assert get_optimization_level(EXCELLENT_THRESHOLD) == "excellent"

    @pytest.mark.unit
    def test_score_above_excellent_threshold_returns_excellent(self) -> None:
        """Scenario: Score above excellent threshold returns 'excellent'
        Given a score of 100
        When get_optimization_level is called
        Then the result is 'excellent'
        """
        assert get_optimization_level(100) == "excellent"

    @pytest.mark.unit
    def test_score_at_good_threshold_returns_good(self) -> None:
        """Scenario: Score at GOOD_THRESHOLD but below EXCELLENT returns 'good'
        Given a score equal to GOOD_THRESHOLD (75)
        When get_optimization_level is called
        Then the result is 'good'
        """
        assert get_optimization_level(GOOD_THRESHOLD) == "good"

    @pytest.mark.unit
    def test_score_between_good_and_excellent_returns_good(self) -> None:
        """Scenario: Score between GOOD and EXCELLENT thresholds returns 'good'
        Given a score of 80
        When get_optimization_level is called
        Then the result is 'good'
        """
        assert get_optimization_level(80) == "good"

    @pytest.mark.unit
    def test_score_at_needs_improvement_threshold(self) -> None:
        """Scenario: Score at NEEDS_IMPROVEMENT threshold returns correct level
        Given a score equal to NEEDS_IMPROVEMENT_THRESHOLD (60)
        When get_optimization_level is called
        Then the result is 'needs improvement'
        """
        assert (
            get_optimization_level(NEEDS_IMPROVEMENT_THRESHOLD) == "needs improvement"
        )

    @pytest.mark.unit
    def test_score_below_needs_improvement_returns_poor(self) -> None:
        """Scenario: Score below NEEDS_IMPROVEMENT returns 'poor'
        Given a score of 0
        When get_optimization_level is called
        Then the result is 'poor'
        """
        assert get_optimization_level(0) == "poor"

    @pytest.mark.unit
    def test_score_just_below_good_threshold_returns_needs_improvement(
        self,
    ) -> None:
        """Scenario: Score just below GOOD threshold returns 'needs improvement'
        Given a score just below GOOD_THRESHOLD (e.g. 74)
        When get_optimization_level is called
        Then the result is 'needs improvement'
        """
        assert get_optimization_level(GOOD_THRESHOLD - 1) == "needs improvement"
