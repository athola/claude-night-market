"""A channel that broke must not be re-weighted as if it were searched.

Feature: Adaptive re-planning distinguishes a thin channel from a broken one.

As a research pass deciding where to spend the next round
I want a channel that errored to keep its weight
So that a failed API call does not teach the plan to stop looking there

``replan`` blends each channel's original weight with its share of
findings. A channel that returns nothing scores a proportion of zero and
loses half its weight. That is right when the channel searched cleanly
and the field is thin, and it is backwards when the channel never
searched at all: the second pass then queries the broken source less,
which is the opposite of the correct response to an outage.

This is the concrete cost of conflating "found nothing" with "failed",
and it is why the conflation was worth removing at the record level.
"""

from __future__ import annotations

import pytest

from tome.models import Finding, ResearchPlan
from tome.scripts.research_planner import replan


def _finding(channel: str) -> Finding:
    return Finding(
        source="s",
        channel=channel,
        title="t",
        url=f"https://example.com/{channel}",
        relevance=0.5,
        summary="s",
    )


def _plan() -> ResearchPlan:
    return ResearchPlan(
        channels=["code", "academic"],
        weights={"code": 0.5, "academic": 0.5},
        triz_depth="light",
        estimated_budget=100,
    )


class TestOutcomeAwareReplan:
    """Feature: Only a clean empty channel loses weight."""

    @pytest.mark.unit
    def test_errored_channel_is_penalized_less_than_an_empty_one(self) -> None:
        """Scenario: An outage does not down-weight like a thin field.

        Given academic returned nothing while code returned findings
        When the plan is revised once treating academic as errored
        And once treating it as cleanly empty
        Then the errored revision leaves academic more weight
        Because nothing was learned about academic's usefulness; the
             pass learned only that the source was unreachable, and
             searching it less is the wrong lesson from that.

        The comparison is relative on purpose. Weights are normalized,
        so a protected channel cannot hold its absolute share when a
        sibling legitimately gains. The guarantee that matters is that
        the two outcomes are treated differently, which is the whole
        point of recording them.
        """
        results = {"code": [_finding("code")], "academic": []}
        errored = replan(_plan(), results, outcomes={"code": "ok", "academic": "error"})
        empty = replan(_plan(), results, outcomes={"code": "ok", "academic": "empty"})
        assert errored.weights["academic"] > empty.weights["academic"]

    @pytest.mark.unit
    def test_cleanly_empty_channel_still_loses_weight(self) -> None:
        """Scenario: A thin channel is still de-prioritized.

        Given academic searched cleanly and found nothing
        When the plan is revised with outcomes
        Then academic loses weight
        Because this is the case the original behavior was written for
             and it remains correct: the channel worked and the topic
             is not there.
        """
        revised = replan(
            _plan(),
            {"code": [_finding("code")], "academic": []},
            outcomes={"code": "ok", "academic": "empty"},
        )
        assert revised.weights["academic"] < 0.5

    @pytest.mark.unit
    def test_rate_limited_and_unknown_also_hold(self) -> None:
        """Scenario: Every non-clean outcome holds its weight.

        Given channels that were rate-limited or never recorded
        Then their weights are preserved
        Because none of these outcomes is evidence about the channel's
             usefulness for this topic.
        """
        results = {"code": [_finding("code")], "academic": []}
        empty = replan(_plan(), results, outcomes={"code": "ok", "academic": "empty"})
        for status in ("rate_limited", "unknown", "degraded"):
            revised = replan(
                _plan(), results, outcomes={"code": "ok", "academic": status}
            )
            assert revised.weights["academic"] > empty.weights["academic"], status

    @pytest.mark.unit
    def test_weights_still_sum_to_one(self) -> None:
        """Scenario: Preserving a weight does not break normalization."""
        revised = replan(
            _plan(),
            {"code": [_finding("code")], "academic": []},
            outcomes={"code": "ok", "academic": "error"},
        )
        assert abs(sum(revised.weights.values()) - 1.0) < 1e-9

    @pytest.mark.unit
    def test_without_outcomes_behavior_is_unchanged(self) -> None:
        """Scenario: The parameter is optional and defaults to the old rule.

        Given no outcomes are supplied
        When the plan is revised
        Then an empty channel loses weight as it always did
        Because callers that predate outcome tracking must keep
             working, and the four existing tests in
             test_adaptive_planning.py pin that behavior.
        """
        revised = replan(_plan(), {"code": [_finding("code")], "academic": []})
        assert revised.weights["academic"] < 0.5
