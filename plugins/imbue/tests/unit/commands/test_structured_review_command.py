"""Contract tests for the /structured-review command.

The command is a markdown file the harness expands into instructions, so
its behavior is what the file says. These tests pin its arguments, the
skills it orchestrates, and the scaffold it promises, and check that the
skills it names exist and agree with it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _markdown_contract import load as _load
from _markdown_contract import section as _section

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
COMMAND = PLUGIN_ROOT / "commands" / "structured-review.md"
SKILLS = PLUGIN_ROOT / "skills"


def _review_core_items() -> list[str]:
    _meta, body = _load(SKILLS / "review-core" / "SKILL.md")
    return re.findall(r"`(review-core:[a-z-]+)`", _section(body, "Required Progress"))


@pytest.fixture(scope="module")
def command() -> tuple[dict, str]:
    return _load(COMMAND)


class TestStructuredReviewCommand:
    """Feature: /structured-review command initiates structured review workflow.

    As a user starting a review
    I want the command to set up the entire workflow
    So that I can focus on analysis rather than scaffolding
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_creates_workflow_scaffold(self, command) -> None:
        """Scenario: /structured-review creates complete workflow.

        Given the command and the review-core skill
        When the scaffold it promises is read
        Then it runs context, scope, evidence-log and deliverable steps
        And every progress item in its example is a review-core item,
            in review-core's order
        And its exit criteria require the evidence log and template.
        """
        _meta, body = command
        steps = re.findall(
            r"^\d+\. \*\*([\w ]+)\*\*", _section(body, "What It Does"), re.MULTILINE
        )
        assert steps == [
            "Establishes Context",
            "Inventories Scope",
            "Prepares Evidence Log",
            "Structures Deliverables",
        ]
        example_items = re.findall(r"- \[ \] (review-core:[a-z-]+)", body)
        core_items = _review_core_items()
        assert example_items
        assert [i for i in core_items if i in example_items] == example_items
        exit_criteria = _section(body, "Exit Criteria")
        assert "All progress items from review-core created" in exit_criteria
        assert "Evidence log initialized with session context" in exit_criteria
        assert "Deliverable template ready for findings" in exit_criteria

    @pytest.mark.unit
    def test_command_example_lists_every_review_core_item(self, command) -> None:
        """The exit criteria demand all review-core items; the example agrees."""
        _meta, body = command
        example_items = re.findall(r"- \[ \] (review-core:[a-z-]+)", body)
        assert example_items == _review_core_items()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_handles_target_parameter(self, command) -> None:
        """Scenario: /structured-review accepts scope targets.

        Given the command definition
        When its usage is read
        Then it takes an optional target and shows a path-scoped review.
        """
        meta, body = command
        assert meta["usage"] == "/structured-review [target]"
        usage = _section(body, "Usage")
        assert "# Review specific target\n/structured-review src/auth/" in usage

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_handles_focus_parameters(self, command) -> None:
        """Scenario: /structured-review accepts focus parameters.

        Given the command definition
        When its usage and examples are read
        Then a --focus flag narrows the review to a concern and a path.
        """
        _meta, body = command
        assert "/structured-review --focus security src/api/" in body
        assert "/structured-review src/api --focus performance" in body
        assert "# Scoped review with performance focus" in body

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_orchestrates_multiple_skills(self, command) -> None:
        """Scenario: /structured-review orchestrates multiple imbue skills.

        Given the command and the review-analyst agent
        When the skills each one names are read
        Then the command names four existing imbue skills
        And the agent loads the same four in the same order.
        """
        _meta, body = command
        named = re.findall(
            r"^- `([a-z-]+)` - ", _section(body, "Workflow Integration"), re.MULTILINE
        )
        assert named == [
            "review-core",
            "proof-of-work",
            "structured-output",
            "diff-analysis",
        ]
        for name in named:
            assert (SKILLS / name / "SKILL.md").is_file(), name
        agent_meta, _ = _load(PLUGIN_ROOT / "agents" / "review-analyst.md")
        agent_skills = [
            s.strip().split(":")[1] for s in agent_meta["skills"].split(",")
        ]
        assert agent_skills == named
        assert "- `diff-analysis` - Change categorization (if diffs involved)" in body

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_output_formatting(self, command) -> None:
        """Scenario: /structured-review provides structured output format.

        Given the command definition
        When the Output section and example are read
        Then the scaffold has context, scope, evidence-log and outline parts
        And the example output reports repository, branch and baseline.
        """
        _meta, body = command
        output = _section(body, "Output")
        for part in (
            "- Context summary (repo, branch, baseline)",
            "- Scope inventory (files, configs, specs)",
            "- Evidence log template",
            "- Deliverable outline",
        ):
            assert part in output
        assert "# Review Workflow Initialized" in body
        assert "# Baseline: main (3 commits behind)" in body

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_error_handling(self, command) -> None:
        """Scenario: /structured-review handles errors gracefully.

        Given the command delegates its workflow to review-core
        When review-core's contingency step is read
        Then an unavailable tool or skill gets documented alternative steps.

        The command file states no error handling of its own; it inherits
        review-core's, which this test pins through the delegation.
        """
        _meta, body = command
        assert "- `review-core` - Core workflow scaffolding" in body
        _m, core = _load(SKILLS / "review-core" / "SKILL.md")
        contingency = _section(core, "Step 6 – Contingency Plan")
        assert "If a required tool or skill is unavailable" in contingency
        assert "document the alternative steps" in contingency

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_parameter_validation(self, command) -> None:
        """Scenario: /structured-review validates command parameters.

        Given the feature-review mode of the command
        When its usage is read
        Then each mode flag is documented, including a config validator
        And issue creation is shown only together with --suggest.
        """
        _meta, body = command
        usage = _section(body, "Feature Review Usage")
        for flag in (
            "--inventory",
            "--suggest",
            "--create-issues",
            "--validate-config",
        ):
            assert f" {flag}" in usage, flag
        assert (
            "# Validate configuration file\n/structured-review --mode feature --validate-config"
            in usage
        )
        create_lines = [
            line for line in usage.splitlines() if "--create-issues" in line
        ]
        assert create_lines
        assert all("--suggest" in line for line in create_lines)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_and_review_core_both_confirm_branch_and_baseline(
        self, command
    ) -> None:
        """Scenario: /structured-review and review-core agree on context.

        Given the command and review-core
        When context establishment is read in both
        Then the command confirms repository, branch and baseline
        And review-core names the git commands that do it.
        """
        _meta, body = command
        assert (
            "**Establishes Context**: Confirms repository, branch, and comparison baseline"
            in body
        )
        _m, core = _load(SKILLS / "review-core" / "SKILL.md")
        context = _section(core, "Step 1 – Establish Context")
        assert "`git status -sb`" in context
        assert "`git rev-parse --abbrev-ref HEAD`" in context

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_narrows_large_repositories_by_target_path(self, command) -> None:
        """Scenario: /structured-review bounds work on large repositories.

        Given the command definition
        When its usage and output are read
        Then a large repository is narrowed by a target path, and the
            scope inventory is limited to files, configs and specs.

        The file states no time budget; scoping is the bound it states.
        """
        _meta, body = command
        assert "**Inventories Scope**: Lists relevant artifacts for review" in body
        assert "/structured-review src/auth/" in body
        assert "- Scope inventory (files, configs, specs)" in _section(body, "Output")
