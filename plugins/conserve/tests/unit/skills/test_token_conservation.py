"""Contract tests for the token-conservation skill document.

The workflow is executed by the model from `skills/token-conservation/
SKILL.md`. These tests read that file: the progress items, the step each
item names, the discovery read budgets, and the exit criteria.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "token-conservation"
EXPECTED_ITEMS = [
    "token-conservation:quota-check",
    "token-conservation:context-plan",
    "token-conservation:delegation-check",
    "token-conservation:compression-review",
    "token-conservation:logging",
]


@pytest.fixture(scope="module")
def skill_text() -> str:
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def _section(skill_text: str, heading_prefix: str) -> str:
    body = skill_text.split(heading_prefix, 1)[1]
    return body.split("\n## ", 1)[0]


@pytest.mark.unit
class TestProgressItems:
    """Document contract: progress items."""

    def test_required_progress_items_are_the_five_conservation_steps(
        self, skill_text: str
    ) -> None:
        """Scenario: required progress items are the five conservation steps."""
        listed = re.findall(
            r"^\d\. `(token-conservation:[\w-]+)`$",
            _section(skill_text, "## Required Progress Items"),
            re.M,
        )
        assert listed == EXPECTED_ITEMS

    def test_each_progress_item_has_a_matching_step_heading(
        self, skill_text: str
    ) -> None:
        """Scenario: each progress item has a matching step heading."""
        headings = re.findall(r"^## Step \d .* \(`([\w-]+)`\)$", skill_text, re.M)
        assert [f"token-conservation:{name}" for name in headings] == EXPECTED_ITEMS

    def test_exit_criteria_name_the_items_in_order(self, skill_text: str) -> None:
        """Scenario: exit criteria name the items in order."""
        criteria = _section(skill_text, "## Exit Criteria")
        flattened = " ".join(criteria.split())
        assert (
            "`quota-check`, `context-plan`, `delegation-check`, "
            "`compression-review`, `logging`" in flattened
        )


@pytest.mark.unit
class TestQuotaCheck:
    """Document contract: quota check."""

    def test_quota_check_records_session_and_weekly_usage(
        self, skill_text: str
    ) -> None:
        """Scenario: quota check records session and weekly usage."""
        step = _section(skill_text, "## Step 1")
        assert "Record current session duration and weekly usage" in step
        assert "5-hour rolling cap and weekly cap" in step

    def test_quota_check_sets_a_max_token_target(self, skill_text: str) -> None:
        """Scenario: quota check sets a max token target."""
        step = _section(skill_text, "## Step 1")
        assert "set a max token target for this task" in step


@pytest.mark.unit
class TestContextPlan:
    """Document contract: context plan."""

    @pytest.mark.parametrize(
        ("task", "limit"),
        [
            ("Implement from spec/requirements", "max 8 reads"),
            ("Bug fix at known location", "max 5 reads"),
            ("Refactor with known scope", "max 1 read per file being changed"),
            ("Open exploration", "max 15 reads"),
        ],
    )
    def test_read_budget_per_task_type(
        self, skill_text: str, task: str, limit: str
    ) -> None:
        """Scenario: read budget per task type."""
        step = _section(skill_text, "## Step 2")
        assert f"{task}: **{limit}**" in step

    def test_budget_is_set_before_the_first_read(self, skill_text: str) -> None:
        """Scenario: budget is set before the first read."""
        step = _section(skill_text, "## Step 2")
        assert "Set a discovery read budget BEFORE reading any files" in step

    def test_exhausted_budget_requires_user_approval(self, skill_text: str) -> None:
        """Scenario: exhausted budget requires user approval."""
        step = _section(skill_text, "## Step 2")
        assert "Do NOT\n  self-authorize additional reads" in step

    def test_glob_and_files_with_matches_grep_are_free(self, skill_text: str) -> None:
        """Scenario: glob and files with matches grep are free."""
        step = _section(skill_text, "## Step 2")
        assert "Glob and files-with-matches Grep are free" in step

    def test_pdf_reads_are_bounded(self, skill_text: str) -> None:
        """Scenario: pdf reads are bounded."""
        step = _section(skill_text, "## Step 2")
        assert "**100 pages max, 20MB max per PDF**" in step


@pytest.mark.unit
class TestDelegationAndCompression:
    """Document contract: delegation and compression."""

    def test_delegation_prefers_deterministic_scripts_for_local_work(
        self, skill_text: str
    ) -> None:
        """Scenario: delegation prefers deterministic scripts for local work."""
        step = _section(skill_text, "## Step 3")
        assert "favor deterministic scripts" in step

    def test_compression_review_offers_new_compact_and_summarize(
        self, skill_text: str
    ) -> None:
        """Scenario: compression review offers new compact and summarize."""
        step = _section(skill_text, "## Step 4")
        assert '**"Summarize from here"**' in step
        assert "`/new`" in step
        assert "`/compact`" in step


@pytest.mark.unit
class TestLoggingAndOutput:
    """Document contract: logging and output."""

    def test_logging_warns_when_the_budget_is_low(self, skill_text: str) -> None:
        """Scenario: logging warns when the budget is low."""
        step = _section(skill_text, "## Step 5")
        assert "If the budget is low, explicitly warn the user" in step

    def test_output_states_remaining_runway(self, skill_text: str) -> None:
        """Scenario: output states remaining runway."""
        output = _section(skill_text, "## Output Expectations")
        assert "remaining runway" in output

    def test_exit_criteria_require_a_read_budget_before_the_first_read(
        self, skill_text: str
    ) -> None:
        """Scenario: exit criteria require a read budget before the first read."""
        criteria = _section(skill_text, "## Exit Criteria")
        assert re.search(
            r"Discovery read budget set before the first `Read` call", criteria
        )

    def test_exit_criteria_are_all_unchecked_boxes(self, skill_text: str) -> None:
        """Scenario: exit criteria are all unchecked boxes."""
        criteria = _section(skill_text, "## Exit Criteria")
        assert len(re.findall(r"^- \[ \] ", criteria, re.M)) == 5

    def test_skill_links_its_source_selection_module_and_it_exists(
        self, skill_text: str
    ) -> None:
        """Scenario: skill links its source selection module and it exists."""
        assert "- modules/source-selection.md" in skill_text
        assert (SKILL_DIR / "modules" / "source-selection.md").is_file()
