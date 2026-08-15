"""Tests for phantom.cost - token cost tracking per iteration.

Feature: Cost Tracking
    As an automation developer
    I want to track token usage and estimated costs per iteration
    So that I can monitor spending and set budget limits
"""

from __future__ import annotations

from phantom.cost import (
    DEPRECATED_MODELS,
    PRICING,
    CostTracker,
    IterationCost,
    estimate_screenshot_tokens,
)


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
        Given known token counts and an explicit model
        When calculating USD cost
        Then it returns a reasonable estimate

        The model is pinned so this exercises the arithmetic rather than
        whatever the fallback rate happens to be. It previously omitted
        the model and so silently asserted a property of the default.
        """
        cost = IterationCost(
            iteration=1,
            model="claude-sonnet-5",
            input_tokens=10000,
            output_tokens=500,
            screenshot_tokens_est=100000,
        )
        usd = cost.estimated_cost_usd()
        assert usd > 0
        assert usd < 1.0  # Single Sonnet iteration shouldn't exceed $1


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


class TestPricingTracksTheModelCard:
    """Feature: Pricing matches published per-MTok rates.

    As an automation developer
    I want cost estimates to match Anthropic's published pricing
    So that budget_exceeded stops a run at the budget I actually set

    Rates from the model card:
    https://platform.claude.com/docs/en/about-claude/models/overview
    """

    def test_current_models_are_priced(self):
        """
        Scenario: A run uses a current model
        Given the models Claude Code ships today
        When pricing is looked up
        Then each has an explicit entry rather than falling to default
        """
        for model in (
            "claude-opus-5",
            "claude-sonnet-5",
            "claude-fable-5",
            "claude-haiku-4-5-20251001",
        ):
            assert model in PRICING, f"{model} falls through to default pricing"

    def test_published_rates_are_correct(self):
        """
        Scenario: Cost is estimated for a known model
        Given the published per-MTok input and output rates
        When the pricing table is read
        Then the entries match the model card
        """
        assert PRICING["claude-fable-5"] == {"input": 10.0, "output": 50.0}
        assert PRICING["claude-opus-5"] == {"input": 5.0, "output": 25.0}
        assert PRICING["claude-sonnet-5"] == {"input": 3.0, "output": 15.0}
        assert PRICING["claude-haiku-4-5-20251001"] == {"input": 1.0, "output": 5.0}

    def test_legacy_opus_46_rate_is_not_opus_41_rate(self):
        """
        Scenario: A legacy rate was copied from an older generation
        Given Opus 4.6 is published at $5/$25 per MTok
        When its entry is read
        Then it is not the $15/$75 Opus 4.1 rate

        This entry read $15/$75, overstating Opus 4.6 cost threefold.
        """
        assert PRICING["claude-opus-4-6"] == {"input": 5.0, "output": 25.0}

    def test_frontier_model_is_priced_from_its_own_entry(self):
        """
        Scenario: Fable 5 runs against a budget
        Given Fable 5 is published at $10 per MTok input
        When a million input tokens are billed
        Then the estimate is exactly $10
        """
        cost = IterationCost(
            iteration=1,
            model="claude-fable-5",
            input_tokens=1_000_000,
            output_tokens=0,
        )
        assert cost.estimated_cost_usd() == 10.0

    def test_default_rate_is_never_cheaper_than_a_current_model(self):
        """
        Scenario: A model ships that this table does not list
        Given budget_exceeded compares cumulative cost to a limit
        When an unrecognized model is billed at the default rate
        Then that rate is at least the most expensive known rate

        A budget guard must fail toward stopping early. The default was
        Sonnet's $3/$15, so an unrecognized frontier model burned 3.3x
        its budget before the guard noticed. This invariant is what
        stops the next model release from recreating that.
        """
        current = [
            v
            for k, v in PRICING.items()
            if k != "default" and k not in DEPRECATED_MODELS
        ]
        default = PRICING["default"]
        assert default["input"] >= max(p["input"] for p in current)
        assert default["output"] >= max(p["output"] for p in current)

    def test_deprecated_models_are_still_priced_accurately(self):
        """
        Scenario: A run bills a deprecated model before its retirement
        Given Opus 4.1 remains callable until 2026-08-05
        When its cost is estimated
        Then it uses its own published rate, not the fallback

        Excluding it from the fallback calculation must not remove it
        from the table. It is still billable until it is retired.
        """
        for model in DEPRECATED_MODELS:
            assert model in PRICING
        assert PRICING["claude-opus-4-1-20250805"] == {"input": 15.0, "output": 75.0}
