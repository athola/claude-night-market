"""Contract tests for the catchup skill.

The skill is a markdown methodology the harness loads, so its behavior is
what SKILL.md and its modules say. Each test pins one claim a caller relies
on: a step, a command, an output section, or a conservation rule. Removing
that claim from the markdown fails the test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _markdown_contract import load as _load

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "catchup"


def _section(body: str, heading: str) -> str:
    """Return the text under a markdown heading, up to the next heading."""
    match = re.search(
        rf"^#+ {re.escape(heading)}\n(.*?)(?=^#+ |\Z)", body, re.DOTALL | re.MULTILINE
    )
    assert match, f"heading {heading!r} not found"
    return match.group(1)


@pytest.fixture(scope="module")
def skill() -> tuple[dict, str]:
    return _load(SKILL_DIR / "SKILL.md")


@pytest.fixture(scope="module")
def git_module() -> str:
    return (SKILL_DIR / "modules" / "git-catchup-patterns.md").read_text()


def _output_format(body: str) -> str:
    match = re.search(r"## Output Format\n```\n(.*?)```", body, re.DOTALL)
    assert match, "Output Format code block not found"
    return match.group(1)


class TestCatchupSkill:
    """Feature: Catchup skill efficiently reviews recent changes."""

    @pytest.mark.unit
    def test_catchup_confirms_repository_context(
        self, skill: tuple[dict, str], git_module: str
    ) -> None:
        """Scenario: Catchup confirms repository context and state.

        Given the skill's first step and its git module
        When they are read
        Then step 1 defines scope, baseline and target
        And the module captures pwd, branch status and the tracked upstream.
        """
        _meta, body = skill
        step = _section(body, "Step 1: Confirm Context")
        assert "baseline (last state), and current target" in step
        assert "`catchup:context-confirmed`" in body
        context = _section(git_module, "Git Context Establishment")
        assert "git status -sb | head -n 1" in context
        assert "--symbolic-full-name @{u}" in context
        assert "Is this branch tracking a remote?" in context

    @pytest.mark.unit
    def test_catchup_identifies_relevant_changes(self, skill: tuple[dict, str]) -> None:
        """Scenario: Catchup filters changes by relevance.

        Given the delta step
        When it is read
        Then source, config and docs outrank generated artifacts
        And blockers have their own output section.
        """
        _meta, body = skill
        step = _section(body, "Step 2: Capture Delta")
        assert "Prioritize source/config/docs over generated artifacts." in step
        assert "## Blockers/Questions" in _output_format(body)

    @pytest.mark.unit
    def test_catchup_captures_delta_efficiently(self, git_module: str) -> None:
        """Scenario: Catchup captures change delta without full reproduction.

        Given the git delta patterns
        When they are read
        Then delta is captured as stats and names, not content
        And the three-dot range limits it to the branch since divergence.
        """
        delta = _section(git_module, "Git Delta Capture")
        assert "git diff --stat ${BASE}...HEAD" in delta
        assert "Use `--name-only` for enumeration without content" in delta
        assert (
            "three-dot syntax to show changes on current branch since divergence"
            in (delta)
        )

    @pytest.mark.unit
    def test_catchup_extracts_insights(self, skill: tuple[dict, str]) -> None:
        """Scenario: Catchup extracts actionable insights from changes.

        Given the insights step
        When it is read
        Then each item gets what, why and implications, rolled up into themes.
        """
        _meta, body = skill
        step = _section(body, "Step 3: Extract Insights")
        assert (
            "**What** (change), **Why** (motivation), "
            "**Implications** (tests/risks/deps)"
        ) in step
        assert "Rollup into themes." in step

    @pytest.mark.unit
    def test_catchup_records_followups(self, skill: tuple[dict, str]) -> None:
        """Scenario: Catchup records actionable follow-up items.

        Given the follow-up step and the output format
        When they are read
        Then follow-ups are categorized, an empty list is stated explicitly
        And each follow-up is a checkbox naming an owner.
        """
        _meta, body = skill
        step = _section(body, "Step 4: Record Follow-ups")
        assert "Capture: Tests, Documentation, Reviews, Blockers, Questions." in step
        assert "If none, state explicitly." in step
        assert "- [ ] [Action with owner]" in _output_format(body)

    @pytest.mark.unit
    def test_catchup_token_conservation(
        self, skill: tuple[dict, str], git_module: str
    ) -> None:
        """Scenario: Catchup conserves tokens in large repositories.

        Given the conservation rules
        When they are read
        Then content is referenced by path and line, never reproduced
        And unbounded patch logs are called out as token-heavy.
        """
        _meta, body = skill
        rules = _section(body, "Token Conservation")
        assert "Reference paths and lines (don't reproduce)." in rules
        assert "Summarize outputs." in rules
        assert "Avoid `git log -p` without limits (token-heavy)" in git_module

    @pytest.mark.unit
    def test_catchup_handles_different_baselines(self, git_module: str) -> None:
        """Scenario: Catchup handles various baseline specifications.

        Given the common git patterns
        When they are read
        Then a merge base, a release tag range and a date are all baselines.
        """
        patterns = _section(git_module, "Common Patterns")
        assert "BASE=$(git merge-base main HEAD)" in patterns
        assert "git diff --stat v1.0.0...v1.1.0" in patterns
        assert 'git log --since="yesterday" --oneline --all' in patterns

    @pytest.mark.unit
    def test_catchup_detects_blockers_and_conflicts(
        self, skill: tuple[dict, str]
    ) -> None:
        """Scenario: Catchup identifies potential blockers and conflicts.

        Given the output format
        When it is read
        Then blockers are listed as items requiring resolution.
        """
        _meta, body = skill
        output = _output_format(body)
        blockers = output[output.index("## Blockers/Questions") :]
        assert "- [Item requiring resolution]" in blockers

    @pytest.mark.unit
    def test_catchup_error_handling(self, git_module: str) -> None:
        """Scenario: Catchup handles repository errors gracefully.

        Given the semantic delta section
        When sem rejects a range or is missing
        Then the module names the recovery: resolve the merge base, or
        fall back to plain git.
        """
        start = git_module.index("## Semantic Delta Capture (sem)")
        semantic = git_module[start : git_module.index("## Git-Specific", start)]
        assert "If `sem diff` fails with a range" in semantic
        assert "resolve the merge base first" in semantic
        assert "When sem is unavailable, fall back to the git commands" in semantic

    @pytest.mark.unit
    def test_catchup_loads_modules_progressively_and_defers_deep_analysis(
        self, skill: tuple[dict, str]
    ) -> None:
        """Scenario: Catchup bounds what a long history loads.

        Given the skill's loading and conservation rules
        When they are read
        Then modules load progressively and deep analysis is deferred,
        so a long history does not pull every module and patch into context.
        """
        meta, body = skill
        assert meta["progressive_loading"] is True
        assert "Load modules based on context:" in _section(body, "Progressive Loading")
        assert "Defer deep analysis." in _section(body, "Token Conservation")

    @pytest.mark.unit
    def test_catchup_generates_structured_output(self, skill: tuple[dict, str]) -> None:
        """Scenario: Catchup generates structured output for consumption.

        Given the output format
        When it is read
        Then it has Summary, Key Changes, Follow-ups and Blockers/Questions,
        in that order, and the summary is a short theme and risk overview.
        """
        _meta, body = skill
        output = _output_format(body)
        headings = re.findall(r"^## (.+)$", output, re.MULTILINE)
        assert headings == [
            "Summary",
            "Key Changes",
            "Follow-ups",
            "Blockers/Questions",
        ]
        assert "[2-3 sentence theme + risk overview]" in output


@pytest.mark.unit
def test_exit_criteria_are_checkable_boxes(skill: tuple[dict, str]) -> None:
    """Each exit criterion is a `- [ ]` item a reader can verify from the output.

    "Stakeholders understand state" named no file, section or count, so
    nobody could tell when it held.
    """
    _meta, body = skill
    # An item may wrap; its continuation lines are indented.
    lines = [
        ln
        for ln in _section(body, "Exit Criteria").splitlines()
        if ln.strip() and not ln.startswith("  ")
    ]
    assert lines
    assert all(ln.startswith("- [ ] ") for ln in lines), lines
    criteria = _section(body, "Exit Criteria")
    assert "Stakeholders understand" not in criteria
    for named in ("catchup:", "baseline", "Key Changes", "Follow-ups"):
        assert named in criteria, named
