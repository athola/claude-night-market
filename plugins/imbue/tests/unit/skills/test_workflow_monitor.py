"""Contract tests for the workflow-monitor skill.

The skill is markdown a session follows, so its behavior is what the
files say. These tests pin the detection thresholds, severities, penalty
tables, issue templates and guardrails in SKILL.md and its modules, and
check that files which repeat a value agree. Where the module ships
reference code, the tests run that code, so a changed threshold in the
code or the table shows up here.
"""

from __future__ import annotations

import re
import runpy
import tempfile
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "workflow-monitor"
MODULES = SKILL_DIR / "modules"
SKILL = (SKILL_DIR / "SKILL.md").read_text()
DETECTION = (MODULES / "detection-patterns.md").read_text()
EFFICIENCY = (MODULES / "efficiency-metrics.md").read_text()
TEMPLATES = (MODULES / "issue-templates.md").read_text()


def _between(text: str, start: str, end: str) -> str:
    """Return text from the first ``start`` up to the next ``end``."""
    begin = text.index(start)
    return text[begin : text.index(end, begin + len(start))]


def _run_block(text: str, name: str, init: dict | None = None) -> dict:
    """Run the fenced python block that defines ``name``; return its globals."""
    for block in re.findall(r"```python\n(.*?)```", text, re.S):
        if f"def {name}(" in block or f"class {name}:" in block:
            with tempfile.TemporaryDirectory() as scratch:
                script = Path(scratch) / "doc_block.py"
                prelude = (
                    "from __future__ import annotations\n"
                    "from dataclasses import dataclass, field\n"
                )
                script.write_text(prelude + block)
                return runpy.run_path(str(script), init_globals=init)
    raise AssertionError(f"no python block defines {name}")


def _skill_config() -> str:
    return _between(SKILL, "# .workflow-monitor.yaml", "```")


def _config_value(key: str) -> str:
    match = re.search(rf"^\s*{key}: (\S+)", _skill_config(), re.M)
    assert match, key
    return match.group(1).strip('"')


def _skill_error_severities() -> dict[str, str]:
    table = _between(SKILL, "### Error Detection", "### Efficiency Detection")
    return dict(
        re.findall(r"^\| ([A-Z][\w ]+?) \| [^|]+ \| (High|Medium|Low) \|", table, re.M)
    )


def _module_default_severities() -> dict[str, str]:
    table = _between(DETECTION, "## Severity Classification", "## Evidence Collection")
    return dict(re.findall(r"^\| ([A-Z][\w ]+?) \| (High|Medium|Low) \|", table, re.M))


def _metrics(**overrides):
    # The scoring block uses the WorkflowMetrics dataclass defined in the
    # block before it, as a reader following the module top to bottom would.
    dataclass_block = _run_block(EFFICIENCY, "WorkflowMetrics")
    namespace = _run_block(EFFICIENCY, "calculate_efficiency_score", dataclass_block)
    return namespace, namespace["WorkflowMetrics"](**overrides)


class TestErrorDetection:
    """Feature: Workflow errors are detected and classified."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_failure_detection(self) -> None:
        """Scenario: Command failures are detected by exit code.

        Given the error-detection table and the detection module
        When each states the command-failure signal
        Then both say a non-zero exit code flags the command.
        """
        assert "| Command failure | Exit code > 0 | High |" in SKILL
        assert "- Command failures (exit codes > 0)" in SKILL
        assert "# Detection: Exit code > 0" in DETECTION
        assert "if [ $exit_code -ne 0 ]; then" in DETECTION

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_failure_severity_classification(self) -> None:
        """Scenario: Failures are classified by severity.

        Given SKILL.md's error table and the module's severity table
        When the four shared error patterns are compared
        Then both files give each the same default severity.
        """
        skill = _skill_error_severities()
        module = _module_default_severities()
        shared = ("Command failure", "Timeout", "Retry loop", "Context exhaustion")
        assert {p: skill[p] for p in shared} == {p: module[p] for p in shared}
        assert skill["Command failure"] == "High"
        assert skill["Retry loop"] == "Medium"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_timeout_detection(self) -> None:
        """Scenario: Timeout events are detected.

        Given the timeout pattern
        When the module's detection snippet runs a command under timeout
        Then exit code 124 is the flag, and SKILL.md rates it High.
        """
        assert "| Timeout | Exceeded timeout limit | High |" in SKILL
        assert "if [ $? -eq 124 ]; then" in DETECTION
        assert "- Exit code 124 (timeout)" in DETECTION

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_retry_loop_detection(self) -> None:
        """Scenario: Retry loops are detected as patterns.

        Given the module's detect_retry_loop
        When a command repeats four times, and another three
        Then only the fourth repetition trips it, matching SKILL.md's ">3".
        """
        assert "| Retry loop | Same command >3 times | Medium |" in SKILL
        detect = _run_block(DETECTION, "detect_retry_loop")["detect_retry_loop"]
        assert detect(["npm test"] * 4) is True
        assert detect(["npm test"] * 3 + ["git push"]) is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_context_exhaustion_detection(self) -> None:
        """Scenario: Context exhaustion is flagged at threshold.

        Given the context-exhaustion pattern
        When both files state the threshold
        Then both say more than 90% context used.
        """
        assert "| Context exhaustion | >90% context used | Medium |" in SKILL
        assert '- "/context" shows >90% usage' in DETECTION
        assert "context_exhaustion: true" in _skill_config()


class TestEfficiencyAnalysis:
    """Feature: Workflow efficiency is analyzed and scored."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_redundant_read_detection(self) -> None:
        """Scenario: Redundant file reads are detected.

        Given the module's detect_redundant_reads and the configured limit
        When one file is read three times and another twice
        Then only the first is flagged, and every file states 2 reads max.
        """
        detect = _run_block(DETECTION, "detect_redundant_reads")[
            "detect_redundant_reads"
        ]
        events = [{"file_path": "a.py"}] * 3 + [{"file_path": "b.py"}] * 2
        assert detect(events) == ["a.py"]
        assert "| Redundant reads | Same file read >2 times | 2 reads max |" in SKILL
        assert _config_value("max_file_reads") == "2"
        assert "max_file_reads: 2     # Per file before penalty" in EFFICIENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_verbose_output_detection(self) -> None:
        """Scenario: Verbose command output is flagged.

        Given the verbose-output limit
        When SKILL.md, its config, the detection snippet and the metrics
            module state it
        Then all use 500 lines.
        """
        assert (
            "| Verbose output | >1000 lines from command | 500 lines recommended |"
            in SKILL
        )
        assert _config_value("verbose_output_limit") == "500"
        assert "if [ $output_lines -gt 500 ]; then" in DETECTION
        assert "output_limit: 500     # Lines before penalty" in EFFICIENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_parallel_opportunity_detection(self) -> None:
        """Scenario: Tasks that could run in parallel are identified.

        Given the sequential-vs-parallel pattern
        When the module states what makes operations independent
        Then it names the three criteria and SKILL.md enables the check.
        """
        assert (
            "| Sequential vs parallel | Independent tasks run sequentially | "
            "Should parallelize |" in SKILL
        )
        criteria = _between(DETECTION, "def detect_parallelizable", "```")
        assert "# - No data dependencies between them" in criteria
        assert "# - Different target files/resources" in criteria
        assert "# - No ordering requirements" in criteria
        assert _config_value("parallel_detection") == "true"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_efficiency_score_calculation(self) -> None:
        """Scenario: Overall efficiency score is calculated.

        Given the module's calculate_efficiency_score and penalty caps
        When the caps are summed and the report's example is scored
        Then the caps total the 1.0 max_penalty the formula divides by,
            the example breakdown totals 0.28, and SKILL.md's sample
            report shows the matching 0.72.
        """
        caps = [float(c) for c in re.findall(r"\(max ([\d.]+) penalty\)", EFFICIENCY)]
        assert len(caps) == 5
        assert sum(caps) == pytest.approx(1.0)
        assert "efficiency_score = 1.0 - (penalty_sum / max_penalty)" in EFFICIENCY

        breakdown = _between(EFFICIENCY, "### Penalty Breakdown", "### Recommendations")
        rows = [
            float(p)
            for p in re.findall(r"^\| [A-Z][\w -]+ \| ([\d.]+) \|", breakdown, re.M)
        ]
        total = float(re.search(r"\*\*Total\*\* \| \*\*([\d.]+)\*\*", breakdown)[1])
        assert sum(rows) == pytest.approx(total)
        assert "**Efficiency Score:** 0.72 (72%)" in SKILL
        assert 1.0 - total == pytest.approx(0.72)

        namespace, metrics = _metrics(
            total_output_lines=750,
            operation_counts={"read config.json": 3},
            large_reads_without_limit=1,
            context_usage_percent=65.0,
        )
        assert namespace["calculate_efficiency_score"](metrics) == pytest.approx(
            1.0 - total
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_over_fetching_detection(self) -> None:
        """Scenario: Over-fetching (reading entire files) is flagged.

        Given the over-fetching penalty table and the reference code
        When one large read without offset/limit is recorded, then three
        Then the penalty steps from 0.05 to the 0.15 cap, as the table says.
        """
        assert (
            "| Over-fetching | Read entire file when snippet needed | Use offset/limit |"
            in SKILL
        )
        table = _between(
            EFFICIENCY, "### Over-Fetching (max 0.15 penalty)", "**Detection:**"
        )
        assert "| 1-2 | 0.05 |" in table
        assert "| > 2 | 0.15 |" in table
        namespace, one = _metrics(large_reads_without_limit=1)
        _, three = _metrics(large_reads_without_limit=3)
        score = namespace["calculate_efficiency_score"]
        assert 1.0 - score(one) == pytest.approx(0.05)
        assert 1.0 - score(three) == pytest.approx(0.15)


class TestIssueCreation:
    """Feature: Detected issues become platform issues."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_identifies_its_source_session(self) -> None:
        """Scenario: Every issue names the workflow and session it came from.

        Renamed from test_issue_title_format: neither SKILL.md nor the
        templates define an issue title format (the old test asserted a
        "[workflow-monitor]" prefix nothing documents). What they do pin is
        the Source line, in SKILL.md's template and in all four module
        templates.
        """
        assert "**Source:** [workflow name] session [session-id]" in SKILL
        assert (
            TEMPLATES.count("**Source:** {{WORKFLOW_NAME}} session {{SESSION_ID}}") == 4
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_labels_assignment(self) -> None:
        """Scenario: Issues get appropriate labels.

        Given the template-selection table
        When labels are read per issue type
        Then each carries its documented labels, drawn from the set
            SKILL.md's report phase names.
        """
        table = _between(
            TEMPLATES, "| Issue Type | Template | Labels |", "## Error Report"
        )
        labels = dict(
            re.findall(r"^\| ([A-Z][\w ]+?) \| [\w-]+ \| ([\w, ]+?) \|", table, re.M)
        )
        labels.pop("Issue Type")
        assert labels == {
            "Command failure": "bug, workflow",
            "Timeout": "performance, workflow",
            "Retry loop": "bug, flaky",
            "Efficiency issue": "enhancement, optimization",
        }
        assert "2. **Assign labels** - workflow, bug, enhancement" in SKILL

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_body_structure(self) -> None:
        """Scenario: Issue body contains required sections.

        Given SKILL.md's issue template and the four module templates
        When their headings are read
        Then each has Background, Suggested Fix and Acceptance Criteria,
            and SKILL.md's template adds Problem.
        """
        skill_template = _between(SKILL, "## Issue Template", "## Configuration")
        for heading in (
            "## Background",
            "## Problem",
            "## Suggested Fix",
            "## Acceptance Criteria",
        ):
            assert heading in skill_template, heading
        assert "*Created automatically by workflow-monitor*" in skill_template
        for name in (
            "Error Report",
            "Performance Issue",
            "Flaky Workflow",
            "Enhancement",
        ):
            body = _between(
                TEMPLATES, f"## {name} Template", "*Created by workflow-monitor*"
            )
            assert "## Background" in body, name
            assert "## Acceptance Criteria" in body, name

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_duplicate_detection(self) -> None:
        """Scenario: Duplicate issues are prevented.

        Given the duplicate guardrail
        When the three places state it
        Then SKILL.md checks existing issues first and the exit criterion
            and the module search with ``gh issue list --search``.
        """
        assert (
            "1. **No duplicate issues** - Check existing issues before creating"
            in SKILL
        )
        assert "1. **Check for duplicates** - Search existing issues" in SKILL
        assert "Duplicate check run via `gh issue list --search` before" in SKILL
        assert (
            'gh issue list --state all --search "{{COMMAND}} OR {{ERROR_EXCERPT}}"'
            in TEMPLATES
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rate_limiting(self) -> None:
        """Scenario: Issue creation is rate limited per session.

        Given the rate-limit guardrail
        When SKILL.md, its exit criteria and the module state it
        Then all cap issues at 5 per session.
        """
        assert "4. **Rate limiting** - Max 5 issues per session" in SKILL
        assert "No more than 5 issues created per session" in SKILL
        assert "- Maximum 5 issues per session" in TEMPLATES
        assert "- Minimum 10 minutes between issue creation" in TEMPLATES


class TestWorkflowConfiguration:
    """Feature: Monitoring behavior is configurable."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_severity_threshold_filtering(self) -> None:
        """Scenario: Only issues at/above threshold are reported.

        Given the default severity threshold
        When the error table's severities are filtered at it
        Then Tool misuse (Low) is the one pattern excluded.
        """
        threshold = _config_value("severity_threshold")
        assert threshold == "medium"
        assert "# Only report medium+ severity" in _skill_config()
        rank = {"Low": 0, "Medium": 1, "High": 2}
        floor = rank[threshold.capitalize()]
        excluded = [p for p, s in _skill_error_severities().items() if rank[s] < floor]
        assert excluded == ["Tool misuse"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_efficiency_threshold_flagging(self) -> None:
        """Scenario: Workflows below efficiency threshold are flagged.

        Given the efficiency threshold in SKILL.md and the metrics module
        When both are read
        Then both are 0.7, the floor of the module's "Good" rating.
        """
        assert _config_value("efficiency_threshold") == "0.7"
        assert "# Flag workflows below 70% efficiency" in _skill_config()
        assert "score_threshold: 0.7  # Report if below" in EFFICIENCY
        assert "| 0.7-0.9 | Good | Minor improvements possible |" in EFFICIENCY

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detection_toggles(self) -> None:
        """Scenario: Detection types can be individually toggled.

        Given the detection block in the config
        When its keys are read
        Then there is one toggle per error pattern in SKILL.md's table.
        """
        block = _between(_skill_config(), "detection:", "efficiency:")
        toggles = re.findall(r"^\s+(\w+): true$", block, re.M)
        assert toggles == [
            "command_failures",
            "timeouts",
            "retry_loops",
            "context_exhaustion",
            "tool_misuse",
        ]
        assert len(toggles) == len(_skill_error_severities())

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_auto_create_requires_approval(self) -> None:
        """Scenario: Auto-create issues requires explicit opt-in.

        Given the default configuration
        When auto_create_issues is read
        Then it is false, and both guardrails require approval unless it
            is set true.
        """
        assert _config_value("auto_create_issues") == "false"
        assert "2. **Approval required** - Unless `auto_create_issues: true`" in SKILL
        assert (
            "- Require user confirmation unless `auto_create_issues: true`" in TEMPLATES
        )


class TestEfficiencyReport:
    """Feature: Efficiency reports summarize a session."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_report_summary_generation(self) -> None:
        """Scenario: Report summary captures key metrics.

        Given SKILL.md's report and the module's report template
        When their header fields are read
        Then both carry session, duration and score.
        """
        report = _between(SKILL, "## Workflow Efficiency Report", "### Issues Detected")
        assert "**Session:** [session-id]" in report
        assert "**Duration:** 12m 34s" in report
        assert "**Efficiency Score:** 0.72 (72%)" in report
        template = _between(EFFICIENCY, "### Efficiency Report Format", "### Penalty")
        for field in (
            "**Session:** {{SESSION_ID}}",
            "**Duration:** {{DURATION}}",
            "**Overall Score:** {{SCORE}} ({{RATING}})",
        ):
            assert field in template, field

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_issue_impact_classification(self) -> None:
        """Scenario: Issues are classified by impact.

        Given SKILL.md's sample "Issues Detected" table
        When its impact column is read
        Then verbose output and sequential tasks are Medium and redundant
            reads Low, each a level SKILL.md's severity scale uses.
        """
        table = _between(SKILL, "### Issues Detected", "### Recommendations")
        impacts = dict(
            re.findall(r"^\| ([A-Z][\w ]+?) \| \d+ \| (\w+) \|", table, re.M)
        )
        assert impacts == {
            "Verbose output": "Medium",
            "Redundant reads": "Low",
            "Sequential tasks": "Medium",
        }
        assert set(impacts.values()) <= {"High", "Medium", "Low"}

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recommendation_generation(self) -> None:
        """Scenario: Recommendations are generated from issues.

        Given the sample report's issues
        When its recommendations are read
        Then each detected issue type has a matching recommendation, using
            the quiet flags the detection module lists for verbose output.
        """
        recommendations = _between(SKILL, "### Recommendations", "### Create Issues?")
        assert "1. Use `--quiet` flags for npm/pip commands" in recommendations
        assert "2. Cache file contents instead of re-reading" in recommendations
        assert "3. Parallelize independent file operations" in recommendations
        assert "- Cache file contents in variables" in DETECTION
        assert "- `pip install` without `--quiet`" in DETECTION
