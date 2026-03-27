"""Tests for phantom.cost - token cost tracking per iteration.

Feature: Cost Tracking
    As an automation developer
    I want to track token usage and estimated costs per iteration
    So that I can monitor spending and set budget limits
"""

from __future__ import annotations

from phantom.cost import CostTracker, IterationCost, estimate_screenshot_tokens


class TestEstimateScreenshotTokens:
    """Feature: Screenshot token estimation."""

    def test_small_resolution(self):
        """
        Scenario: 1024x768 screenshot
        Given a display resolution of 1024x768
        When estimating tokens
        Then it returns a reasonable token count
        """
        tokens = estimate_screenshot_tokens(1024, 768)
        assert 100 < tokens < 500_000

    def test_larger_resolution_costs_more(self):
        """
        Scenario: Higher resolution = more tokens
        Given two different resolutions
        When estimating tokens
        Then the larger resolution costs more
        """
        small = estimate_screenshot_tokens(1024, 768)
        large = estimate_screenshot_tokens(1920, 1080)
        assert large > small

    def test_zero_resolution(self):
        tokens = estimate_screenshot_tokens(0, 0)
        assert tokens == 0


class TestIterationCost:
    """Feature: Per-iteration cost tracking."""

    def test_total_tokens(self):
        cost = IterationCost(
            iteration=1,
            input_tokens=1000,
            output_tokens=200,
            screenshot_tokens_est=50000,
        )
        assert cost.total_tokens == 51200

    def test_estimated_cost_usd(self):
        """
        Scenario: Cost estimation
        Given known token counts
        When calculating USD cost
        Then it returns a reasonable estimate
        """
        cost = IterationCost(
            iteration=1,
            input_tokens=10000,
            output_tokens=500,
            screenshot_tokens_est=100000,
        )
        usd = cost.estimated_cost_usd()
        assert usd > 0
        assert usd < 1.0  # Single iteration shouldn't exceed $1


class TestCostTracker:
    """Feature: Cumulative cost tracking across iterations."""

    def test_empty_tracker(self):
        tracker = CostTracker()
        assert tracker.total_input_tokens == 0
        assert tracker.total_output_tokens == 0
        assert tracker.iteration_count == 0

    def test_record_iteration(self):
        """
        Scenario: Record a single iteration
        Given an empty tracker
        When one iteration is recorded
        Then totals reflect that iteration
        """
        tracker = CostTracker()
        tracker.record(
            input_tokens=5000,
            output_tokens=300,
            screenshot_tokens_est=80000,
        )
        assert tracker.iteration_count == 1
        assert tracker.total_input_tokens == 5000
        assert tracker.total_output_tokens == 300

    def test_multiple_iterations_accumulate(self):
        """
        Scenario: Multiple iterations
        Given three recorded iterations
        When checking totals
        Then they are summed correctly
        """
        tracker = CostTracker()
        for _i in range(3):
            tracker.record(
                input_tokens=1000,
                output_tokens=100,
                screenshot_tokens_est=50000,
            )
        assert tracker.iteration_count == 3
        assert tracker.total_input_tokens == 3000
        assert tracker.total_output_tokens == 300

    def test_budget_exceeded(self):
        """
        Scenario: Budget limit
        Given a $0.10 budget
        When costs exceed the budget
        Then budget_exceeded returns True
        """
        tracker = CostTracker(budget_usd=0.001)
        tracker.record(
            input_tokens=100000,
            output_tokens=5000,
            screenshot_tokens_est=500000,
        )
        assert tracker.budget_exceeded is True

    def test_budget_not_exceeded(self):
        tracker = CostTracker(budget_usd=10.0)
        tracker.record(
            input_tokens=1000,
            output_tokens=100,
            screenshot_tokens_est=50000,
        )
        assert tracker.budget_exceeded is False

    def test_no_budget_never_exceeded(self):
        """
        Scenario: No budget set
        Given no budget limit
        When costs are recorded
        Then budget_exceeded is always False
        """
        tracker = CostTracker()
        tracker.record(
            input_tokens=999999,
            output_tokens=999999,
            screenshot_tokens_est=999999,
        )
        assert tracker.budget_exceeded is False

    def test_summary_format(self):
        tracker = CostTracker()
        tracker.record(
            input_tokens=5000,
            output_tokens=500,
            screenshot_tokens_est=100000,
        )
        summary = tracker.summary()
        assert "iteration" in summary.lower()
        assert "token" in summary.lower()
