"""Contract tests for the cpu-gpu-performance skill document.

The performance discipline is executed by the model from
`skills/cpu-gpu-performance/SKILL.md`. These tests read that file: the
progress items, the step each names, the baseline commands, and the exit
criteria.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_PATH = (
    Path(__file__).resolve().parents[3] / "skills" / "cpu-gpu-performance" / "SKILL.md"
)
EXPECTED_ITEMS = [
    "cpu-gpu-performance:baseline",
    "cpu-gpu-performance:scope",
    "cpu-gpu-performance:instrument",
    "cpu-gpu-performance:throttle",
    "cpu-gpu-performance:log",
]


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _section(skill_text: str, heading_prefix: str) -> str:
    body = skill_text.split(heading_prefix, 1)[1]
    return body.split("\n## ", 1)[0]


@pytest.mark.unit
class TestProgressItems:
    """Document contract: progress items."""

    def test_required_progress_items_are_the_five_performance_steps(
        self, skill_text: str
    ) -> None:
        """Scenario: required progress items are the five performance steps."""
        listed = re.findall(
            r"^\d\. `(cpu-gpu-performance:[\w-]+)`$",
            _section(skill_text, "## Required Progress Items"),
            re.M,
        )
        assert listed == EXPECTED_ITEMS

    def test_there_is_one_step_heading_per_progress_item(self, skill_text: str) -> None:
        """Scenario: there is one step heading per progress item."""
        assert len(re.findall(r"^## Step \d: ", skill_text, re.M)) == len(
            EXPECTED_ITEMS
        )

    def test_step_order_runs_baseline_scope_instrument_throttle_log(
        self, skill_text: str
    ) -> None:
        """Scenario: step order runs baseline scope instrument throttle log."""
        headings = re.findall(r"^## Step \d: (.+)$", skill_text, re.M)
        assert headings == [
            "Establish Current Baseline",
            "Narrow the Scope",
            "Instrument Before You Optimize",
            "Throttle and Sequence Work",
            "Log Decisions and Next Steps",
        ]


@pytest.mark.unit
class TestBaselineAndScope:
    """Document contract: baseline and scope."""

    def test_baseline_captures_uptime_and_ps(self, skill_text: str) -> None:
        """Scenario: baseline captures uptime and ps."""
        step = _section(skill_text, "## Step 1")
        assert "`uptime`" in step
        assert "`ps -eo pcpu,cmd | head`" in step

    def test_baseline_queries_gpu_utilization(self, skill_text: str) -> None:
        """Scenario: baseline queries gpu utilization."""
        step = _section(skill_text, "## Step 1")
        assert "nvidia-smi --query-gpu=utilization.gpu,memory.used" in step

    def test_baseline_sets_a_per_task_budget(self, skill_text: str) -> None:
        """Scenario: baseline sets a per task budget."""
        step = _section(skill_text, "## Step 1")
        assert "Set a per-task CPU minute / GPU minute budget" in step

    def test_scope_prefers_selective_testing_over_whole_world_jobs(
        self, skill_text: str
    ) -> None:
        """Scenario: scope prefers selective testing over whole world jobs."""
        step = _section(skill_text, "## Step 2")
        assert 'Avoid running "whole world" jobs' in step
        assert "`pytest -k`" in step
        assert "`cargo test <module>`" in step


@pytest.mark.unit
class TestInstrumentAndThrottle:
    """Document contract: instrument and throttle."""

    def test_instrumentation_precedes_optimization_with_cpu_and_gpu_profilers(
        self, skill_text: str
    ) -> None:
        """Scenario: instrumentation precedes optimization with cpu and gpu profilers."""
        step = _section(skill_text, "## Step 3")
        assert "`perf`" in step
        assert "`nsys`" in step

    def test_throttling_uses_nice_and_escalates_from_the_failed_module(
        self, skill_text: str
    ) -> None:
        """Scenario: throttling uses nice and escalates from the failed module."""
        step = _section(skill_text, "## Step 4")
        assert "`nice`, `ionice`" in step
        assert "Rerun only the failed test/module" in step
        assert "Reserve the full suite for the final gate" in step


@pytest.mark.unit
class TestExitCriteria:
    """Document contract: exit criteria."""

    def test_exit_criteria_are_four_unchecked_boxes(self, skill_text: str) -> None:
        """Scenario: exit criteria are four unchecked boxes."""
        criteria = _section(skill_text, "## Exit Criteria")
        assert len(re.findall(r"^- \[ \] ", criteria, re.M)) == 4

    def test_baseline_must_precede_any_build_or_test_run(self, skill_text: str) -> None:
        """Scenario: baseline must precede any build or test run."""
        criteria = " ".join(_section(skill_text, "## Exit Criteria").split())
        assert (
            "baseline captured and recorded before any build, training run" in criteria
        )

    def test_summary_reports_duration_and_resource_percentage(
        self, skill_text: str
    ) -> None:
        """Scenario: summary reports duration and resource percentage."""
        criteria = " ".join(_section(skill_text, "## Exit Criteria").split())
        assert "duration, CPU% or GPU% consumed" in criteria
