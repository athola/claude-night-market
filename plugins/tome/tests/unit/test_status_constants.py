"""Channel and canary statuses come from one module, not repeated literals.

Feature: Status vocabulary is defined once in tome.synthesis.quality.

Four modules compared against the same bare strings. A rename in the
producer (``channel_outcomes``) would then leave the consumers silently
matching nothing, so these tests tie each consumer to the exported set.
"""

from __future__ import annotations

import ast
import inspect
from types import ModuleType

import pytest

from tome.models import QueryLog, ResearchSession
from tome.output import report
from tome.scripts import research_planner
from tome.synthesis import frontier, quality, verifier
from tome.synthesis.quality import (
    CANARY_ABSENT,
    CANARY_FAILED,
    CANARY_OUTCOMES,
    CANARY_PASSED,
    CHANNEL_OUTCOMES,
    OUTCOME_DEGRADED,
    OUTCOME_EMPTY,
    OUTCOME_ERROR,
    OUTCOME_OK,
    OUTCOME_RATE_LIMITED,
    OUTCOME_UNKNOWN,
    channel_outcomes,
)


def _session(channel: str, logs: list[QueryLog]) -> ResearchSession:
    return ResearchSession(
        topic="t",
        domain="d",
        triz_depth="light",
        channels=[channel],
        findings=[],
        query_log=logs,
    )


class TestExportedValues:
    @pytest.mark.unit
    def test_channel_outcome_values_are_unchanged(self) -> None:
        assert (
            frozenset({"unknown", "ok", "empty", "degraded", "error", "rate_limited"})
            == CHANNEL_OUTCOMES
        )

    @pytest.mark.unit
    def test_canary_outcome_values_are_unchanged(self) -> None:
        assert frozenset({"pass", "fail", "absent"}) == CANARY_OUTCOMES


class TestProducersReturnExportedSet:
    @pytest.mark.unit
    def test_channel_outcomes_can_return_exactly_the_exported_set(self) -> None:
        def ok(n: int) -> QueryLog:
            return QueryLog("c", "q", "s", result_count=n)

        def failed(kind: str) -> QueryLog:
            return QueryLog("c", "q", "s", error=kind)

        scenarios = [
            [],
            [ok(3)],
            [ok(0)],
            [ok(3), failed("source_error")],
            [failed("rate_limit")],
            [failed("source_error")],
        ]
        returned = {channel_outcomes(_session("c", logs))["c"] for logs in scenarios}

        assert returned == CHANNEL_OUTCOMES

    @pytest.mark.unit
    def test_canary_outcomes_can_return_exactly_the_exported_set(self) -> None:
        canary = quality.CANARY_SOURCE
        scenarios = [
            [],
            [QueryLog("code", "q", canary, result_count=1)],
            [QueryLog("code", "q", canary, result_count=0)],
        ]
        returned = {
            frontier.canary_outcomes(_session("code", logs))["code"]
            for logs in scenarios
        }

        assert returned == CANARY_OUTCOMES


class TestConsumersUseSharedConstants:
    @pytest.mark.unit
    def test_report_notes_cover_exactly_the_channel_outcomes(self) -> None:
        assert set(report._EMPTY_CHANNEL_NOTES) == CHANNEL_OUTCOMES

    @pytest.mark.unit
    def test_clean_statuses_are_ok_and_empty_in_verifier_and_frontier(self) -> None:
        expected = {OUTCOME_OK, OUTCOME_EMPTY}

        assert set(verifier._CLEAN) == expected
        assert set(frontier._CLEAN) == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("module", [verifier, frontier, report, research_planner])
    def test_module_has_no_bare_status_literal(self, module: ModuleType) -> None:
        statuses = CHANNEL_OUTCOMES | CANARY_OUTCOMES
        tree = ast.parse(inspect.getsource(module))
        dict_keys = {
            id(key)
            for node in ast.walk(tree)
            if isinstance(node, ast.Dict)
            for key in node.keys
            if key is not None
        }
        bare = sorted(
            {
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in statuses
                and id(node) not in dict_keys
            }
        )

        assert bare == []


class TestNamesMatchValues:
    @pytest.mark.unit
    def test_each_constant_holds_its_documented_value(self) -> None:
        assert (
            OUTCOME_UNKNOWN,
            OUTCOME_OK,
            OUTCOME_EMPTY,
            OUTCOME_DEGRADED,
            OUTCOME_ERROR,
            OUTCOME_RATE_LIMITED,
        ) == ("unknown", "ok", "empty", "degraded", "error", "rate_limited")
        assert (CANARY_PASSED, CANARY_FAILED, CANARY_ABSENT) == (
            "pass",
            "fail",
            "absent",
        )
