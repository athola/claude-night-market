"""Tests for parallel pipeline stage execution.

Feature: Parallel pipeline stages for independent quality gates

As an egregore orchestrator
I want to identify and dispatch independent pipeline steps concurrently
So that quality gate execution is faster when steps have no
interdependencies.
"""

from __future__ import annotations

import pytest
from stage_parallel import (
    STEP_DEPENDENCIES,
    StageExecutionPlan,
    WaveResult,
    build_parallel_dispatch,
    plan_stage_execution,
)


class TestPlanStageExecution:
    """Plan wave grouping for steps within a pipeline stage.

    Feature: Wave-based execution planning
    Given a set of pipeline steps with a dependency graph,
    group them into waves where each wave's steps are independent.
    """

    @pytest.mark.unit
    def test_quality_stage_produces_two_waves(self) -> None:
        """Scenario: Quality stage with mixed dependencies.

        Given the full quality stage step list
        When planning execution waves
        Then two waves are produced: independents first, dependents second.
        """
        steps = [
            "code-review",
            "unbloat",
            "code-refinement",
            "update-tests",
            "update-docs",
        ]
        plan = plan_stage_execution("quality", steps)
        assert len(plan.waves) == 2

    @pytest.mark.unit
    def test_independent_steps_in_first_wave(self) -> None:
        """Scenario: Independent steps grouped together.

        Given steps code-review, unbloat, and update-docs have no deps
        When planning execution
        Then all three appear in wave 1.
        """
        steps = [
            "code-review",
            "unbloat",
            "code-refinement",
            "update-tests",
            "update-docs",
        ]
        plan = plan_stage_execution("quality", steps)
        wave_1 = plan.waves[0]
        assert "code-review" in wave_1
        assert "unbloat" in wave_1
        assert "update-docs" in wave_1
        assert len(wave_1) == 3

    @pytest.mark.unit
    def test_dependent_steps_in_second_wave(self) -> None:
        """Scenario: Steps depending on code-review wait for wave 2.

        Given code-refinement and update-tests depend on code-review
        When planning execution
        Then both appear in wave 2.
        """
        steps = [
            "code-review",
            "unbloat",
            "code-refinement",
            "update-tests",
            "update-docs",
        ]
        plan = plan_stage_execution("quality", steps)
        wave_2 = plan.waves[1]
        assert "code-refinement" in wave_2
        assert "update-tests" in wave_2
        assert len(wave_2) == 2

    @pytest.mark.unit
    def test_unknown_steps_without_deps_in_first_wave(self) -> None:
        """Scenario: Steps not in the dependency graph default to no deps.

        Given a step "new-check" not listed in STEP_DEPENDENCIES
        When planning execution
        Then it is treated as independent and placed in wave 1.
        """
        steps = ["new-check", "code-review", "unbloat"]
        plan = plan_stage_execution("quality", steps)
        assert "new-check" in plan.waves[0]
        assert "code-review" in plan.waves[0]
        assert "unbloat" in plan.waves[0]

    @pytest.mark.unit
    def test_all_independent_steps_single_wave(self) -> None:
        """Scenario: Only independent steps produce a single wave.

        Given three steps with no interdependencies
        When planning execution
        Then exactly one wave is produced containing all three.
        """
        steps = ["code-review", "unbloat", "update-docs"]
        plan = plan_stage_execution("quality", steps)
        assert len(plan.waves) == 1
        assert len(plan.waves[0]) == 3

    @pytest.mark.unit
    def test_single_step_produces_single_wave(self) -> None:
        """Scenario: A single step is trivially one wave."""
        plan = plan_stage_execution("quality", ["code-review"])
        assert len(plan.waves) == 1
        assert plan.waves[0] == ["code-review"]

    @pytest.mark.unit
    def test_empty_steps_produces_no_waves(self) -> None:
        """Scenario: No steps means no waves."""
        plan = plan_stage_execution("quality", [])
        assert plan.waves == []

    @pytest.mark.unit
    def test_non_quality_stage_all_in_one_wave(self) -> None:
        """Scenario: Steps outside the dependency graph run together.

        Given intake steps not in STEP_DEPENDENCIES
        When planning execution
        Then all are placed in a single wave (no deps = independent).
        """
        steps = ["parse", "validate", "prioritize"]
        plan = plan_stage_execution("intake", steps)
        assert len(plan.waves) == 1
        assert plan.waves[0] == ["parse", "validate", "prioritize"]

    @pytest.mark.unit
    def test_preserves_step_order_within_wave(self) -> None:
        """Scenario: Step order from the input list is preserved in waves.

        Given steps listed in a particular order
        When planning execution
        Then the wave respects that input order.
        """
        steps = ["unbloat", "update-docs", "code-review"]
        plan = plan_stage_execution("quality", steps)
        assert plan.waves[0] == ["unbloat", "update-docs", "code-review"]

    @pytest.mark.unit
    def test_total_steps_matches_input(self) -> None:
        """Scenario: No steps are lost or duplicated during planning."""
        steps = [
            "code-review",
            "unbloat",
            "code-refinement",
            "update-tests",
            "update-docs",
        ]
        plan = plan_stage_execution("quality", steps)
        assert plan.total_steps == len(steps)


class TestStageExecutionPlan:
    """Tests for StageExecutionPlan dataclass properties."""

    @pytest.mark.unit
    def test_is_parallel_true_for_multi_step_wave(self) -> None:
        """Scenario: A plan with a multi-step wave is parallel."""
        plan = StageExecutionPlan(
            stage="quality",
            waves=[["code-review", "unbloat"], ["code-refinement"]],
        )
        assert plan.is_parallel is True

    @pytest.mark.unit
    def test_is_parallel_false_for_single_step_waves(self) -> None:
        """Scenario: A plan where every wave has one step is sequential."""
        plan = StageExecutionPlan(
            stage="quality",
            waves=[["code-review"], ["unbloat"]],
        )
        assert plan.is_parallel is False

    @pytest.mark.unit
    def test_is_parallel_false_for_empty(self) -> None:
        """Scenario: An empty plan is not parallel."""
        plan = StageExecutionPlan(stage="quality")
        assert plan.is_parallel is False

    @pytest.mark.unit
    def test_total_steps(self) -> None:
        """Scenario: total_steps sums across all waves."""
        plan = StageExecutionPlan(
            stage="quality",
            waves=[["a", "b", "c"], ["d", "e"]],
        )
        assert plan.total_steps == 5


class TestBuildParallelDispatch:
    """Tests for building agent dispatch configs from a wave.

    Feature: Dispatch instruction generation
    Given a wave of steps ready to execute in parallel,
    produce dispatch configs suitable for agent invocation.
    """

    @pytest.mark.unit
    def test_produces_one_entry_per_step(self) -> None:
        """Scenario: Each step in the wave gets a dispatch entry."""
        wave = ["code-review", "unbloat", "update-docs"]
        dispatches = build_parallel_dispatch(wave, "wrk_001")
        assert len(dispatches) == 3

    @pytest.mark.unit
    def test_dispatch_contains_required_fields(self) -> None:
        """Scenario: Dispatch entry has step, item_id, skill, and args."""
        dispatches = build_parallel_dispatch(["code-review"], "wrk_042")
        d = dispatches[0]
        assert d["step"] == "code-review"
        assert d["item_id"] == "wrk_042"
        assert d["skill"] == "egregore:quality-gate"
        assert d["args"] == "step=code-review"

    @pytest.mark.unit
    def test_dispatch_for_empty_wave(self) -> None:
        """Scenario: An empty wave produces no dispatches."""
        dispatches = build_parallel_dispatch([], "wrk_001")
        assert dispatches == []


class TestWaveResult:
    """Tests for WaveResult pass/fail tracking.

    Feature: Wave result aggregation
    Given results from parallel step execution,
    determine overall wave success and identify failures.
    """

    @pytest.mark.unit
    def test_all_passed_true(self) -> None:
        """Scenario: Every step passes."""
        result = WaveResult(
            wave_index=0,
            results={"code-review": "pass", "unbloat": "pass"},
        )
        assert result.all_passed is True

    @pytest.mark.unit
    def test_all_passed_false_on_failure(self) -> None:
        """Scenario: One failure means the wave did not fully pass."""
        result = WaveResult(
            wave_index=0,
            results={"code-review": "pass", "unbloat": "fail"},
        )
        assert result.all_passed is False

    @pytest.mark.unit
    def test_failed_steps_empty_when_all_pass(self) -> None:
        """Scenario: No failures yields an empty list."""
        result = WaveResult(
            wave_index=0,
            results={"code-review": "pass", "unbloat": "pass"},
        )
        assert result.failed_steps == []

    @pytest.mark.unit
    def test_failed_steps_returns_failures(self) -> None:
        """Scenario: Only failed steps are returned."""
        result = WaveResult(
            wave_index=1,
            results={
                "code-refinement": "fail",
                "update-tests": "pass",
            },
        )
        assert result.failed_steps == ["code-refinement"]

    @pytest.mark.unit
    def test_multiple_failures(self) -> None:
        """Scenario: Multiple non-pass results are all reported."""
        result = WaveResult(
            wave_index=0,
            results={
                "code-review": "fail",
                "unbloat": "error",
                "update-docs": "pass",
            },
        )
        assert set(result.failed_steps) == {"code-review", "unbloat"}

    @pytest.mark.unit
    def test_empty_results(self) -> None:
        """Scenario: A wave with no results vacuously passes."""
        result = WaveResult(wave_index=0)
        assert result.all_passed is True
        assert result.failed_steps == []


class TestStepDependencies:
    """Tests for the STEP_DEPENDENCIES constant.

    Feature: Dependency graph correctness
    The graph must correctly encode which quality steps are
    independent and which require prior step completion.
    """

    @pytest.mark.unit
    def test_independent_steps_have_empty_deps(self) -> None:
        """Scenario: code-review, unbloat, update-docs have no deps."""
        for step in ("code-review", "unbloat", "update-docs"):
            assert STEP_DEPENDENCIES[step] == [], f"{step} should have no dependencies"

    @pytest.mark.unit
    def test_dependent_steps_require_code_review(self) -> None:
        """Scenario: code-refinement and update-tests need code-review."""
        assert "code-review" in STEP_DEPENDENCIES["code-refinement"]
        assert "code-review" in STEP_DEPENDENCIES["update-tests"]
