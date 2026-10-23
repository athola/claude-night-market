"""Contract tests for the /catchup command.

The command is a thin markdown entry point: it invokes the catchup skill
and shows how it is called. These tests pin what the command states and
check that it agrees with the skill it delegates to, so the two cannot
drift apart silently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _markdown_contract import load as _load

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
COMMAND = PLUGIN_ROOT / "commands" / "catchup.md"
SKILL = PLUGIN_ROOT / "skills" / "catchup" / "SKILL.md"


def _fenced_after(body: str, heading: str) -> str:
    """Return the first fenced block under a heading."""
    match = re.search(
        rf"^## {re.escape(heading)}\n.*?```bash\n(.*?)```", body, re.DOTALL | re.M
    )
    assert match, f"no fenced block under {heading!r}"
    return match.group(1)


@pytest.fixture(scope="module")
def command() -> tuple[dict, str]:
    return _load(COMMAND)


@pytest.fixture(scope="module")
def skill_body() -> str:
    return _load(SKILL)[1]


def _invocations(body: str) -> list[str]:
    """Every /catchup invocation line in the command's code blocks."""
    return re.findall(r"^(/catchup.*)$", body, re.MULTILINE)


class TestCatchupCommand:
    """Feature: /catchup command provides efficient change summarization."""

    @pytest.mark.unit
    def test_catchup_command_workflow_orchestration(
        self, command: tuple[dict, str], skill_body: str
    ) -> None:
        """Scenario: /catchup orchestrates complete workflow.

        Given the command delegates to the catchup skill
        When both are read
        Then the command names the four steps in the order the skill
        defines them, and invokes the skill rather than restating it.
        """
        _meta, body = command
        assert "Invoke `Skill(imbue:catchup)`" in body
        assert (
            "confirm context, capture delta, extract insights, and record follow-ups"
            in body
        )
        steps = re.findall(r"^### Step \d: (.+)$", skill_body, re.MULTILINE)
        assert steps == [
            "Confirm Context",
            "Capture Delta",
            "Extract Insights",
            "Record Follow-ups",
        ]

    @pytest.mark.unit
    def test_catchup_handles_different_baselines(
        self, command: tuple[dict, str]
    ) -> None:
        """Scenario: /catchup handles various baseline specifications.

        Given the usage examples
        When they are read
        Then no baseline, a relative ref and a date are all shown.
        """
        _meta, body = command
        usage = _fenced_after(body, "Usage")
        assert "/catchup\n" in usage
        assert "/catchup HEAD~10" in usage
        assert '/catchup --since "2 days ago"' in usage

    @pytest.mark.unit
    def test_catchup_token_conservation(
        self, command: tuple[dict, str], skill_body: str
    ) -> None:
        """Scenario: /catchup conserves tokens with large change sets.

        Given the command defers token rules to the skill
        When both are read
        Then the skill carries the rule to reference, not reproduce.
        """
        _meta, body = command
        assert "the token-conservation rules" in body
        assert "Reference paths and lines (don't reproduce)." in skill_body

    @pytest.mark.unit
    def test_catchup_generates_structured_output(
        self, command: tuple[dict, str], skill_body: str
    ) -> None:
        """Scenario: /catchup generates consistent structured output.

        Given the command's example output and the skill's output format
        When both are read
        Then the example carries the Key Changes and Follow-ups sections the
        skill's format defines.
        """
        _meta, body = command
        example = _fenced_after(body, "Examples")
        assert "# Key Changes:" in example
        assert "# Follow-ups:" in example
        assert "## Key Changes" in skill_body
        assert "## Follow-ups" in skill_body

    @pytest.mark.unit
    def test_catchup_and_diff_analysis_route_work_to_each_other(
        self, skill_body: str
    ) -> None:
        """Scenario: /catchup and diff-analysis point at each other.

        Given the catchup skill and the diff-analysis skill
        When both are read
        Then catchup hands risk assessment to diff-analysis, and each skill
        points detailed or quick work at the other.
        """
        diff_body = _load(PLUGIN_ROOT / "skills" / "diff-analysis" / "SKILL.md")[1]
        assert "Use `imbue:diff-analysis` for risk assessment" in skill_body
        assert "diff analysis - use diff-analysis instead" in skill_body
        assert "Quick context catchup - use catchup instead" in diff_body

    @pytest.mark.unit
    def test_catchup_records_actionable_followups(
        self, command: tuple[dict, str], skill_body: str
    ) -> None:
        """Scenario: /catchup records actionable follow-up items.

        Given the example output
        When its follow-ups are read
        Then each is an unchecked checkbox naming a specific action, the
        same shape as the skill's follow-up template.
        """
        _meta, body = command
        example = _fenced_after(body, "Examples")
        followups = re.findall(r"^# - \[ \] (.+)$", example, re.MULTILINE)
        assert followups == [
            "Review Stripe API key handling",
            "Verify webhook endpoint security",
        ]
        assert "- [ ] [Action with owner]" in skill_body

    @pytest.mark.unit
    def test_catchup_error_handling(
        self, command: tuple[dict, str], skill_body: str
    ) -> None:
        """Scenario: /catchup handles repository errors gracefully.

        Given the command carries no recovery text of its own
        When the skill it invokes is read
        Then the skill's git module states the recovery when sem fails.
        """
        _meta, body = command
        assert "Skill(imbue:catchup)" in body
        assert "`modules/git-catchup-patterns.md`" in skill_body
        module = (
            PLUGIN_ROOT / "skills" / "catchup" / "modules" / "git-catchup-patterns.md"
        ).read_text()
        assert "When sem is unavailable, fall back to the git commands" in module

    @pytest.mark.unit
    def test_catchup_parameter_parsing(self, command: tuple[dict, str]) -> None:
        """Scenario: /catchup parses command parameters correctly.

        Given the usage line and every example invocation
        When they are read
        Then one optional baseline is declared, and every example is bare,
        a single ref, or a --since date.
        """
        meta, body = command
        assert meta["usage"] == "/catchup [baseline]"
        invocations = _invocations(body)
        assert invocations
        for line in invocations:
            args = line.split(None, 1)[1:] if " " in line else []
            assert not args or re.fullmatch(r'(\S+|--since "[^"]+")', args[0]), line

    @pytest.mark.unit
    def test_catchup_example_reports_history_as_counts_not_listings(
        self, command: tuple[dict, str]
    ) -> None:
        """Scenario: /catchup summarizes a long history by counts.

        Given the example output
        When it is read
        Then history is reported as a commit count against a merge base,
        and key changes as file counts, not as listed commits or diffs.
        """
        _meta, body = command
        example = _fenced_after(body, "Examples")
        assert "# Baseline: main (merge-base)" in example
        assert "# Current: HEAD (15 commits ahead)" in example
        assert "# - Payment processing overhaul (12 files)" in example
