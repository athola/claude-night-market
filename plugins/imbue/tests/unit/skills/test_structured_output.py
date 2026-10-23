"""Contract tests for the structured-output skill.

The skill is markdown the harness loads. Its behavior is the templates,
finding format, action format, appendix and checklist that SKILL.md states.
Each test pins one of those claims, and where another file depends on it
(review-core's citation step, the verifier script) checks that they agree.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest
from _markdown_contract import section_to_same_level as _section
from scripts.citation_verifier import parse_markdown_findings

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SKILL = PLUGIN_ROOT / "skills" / "structured-output" / "SKILL.md"


@pytest.fixture(scope="module")
def body() -> str:
    return SKILL.read_text().split("---\n", 2)[2]


def _templates(body: str) -> dict[str, list[str]]:
    """Map each template name in Step 1 to its ordered section list."""
    step = _section(
        body, "Step 1: Select Template (`structured-output:template-selected`)"
    )
    return {
        name: [part.strip() for part in sections.rstrip(".").split(",")]
        for name, sections in re.findall(r"- \*\*(.+?)\*\*: (.+)$", step, re.M)
    }


def _finding_step(body: str) -> str:
    return _section(
        body, "Step 2: Format Findings (`structured-output:findings-formatted`)"
    )


class TestStructuredOutputSkill:
    """Feature: Structured output validates consistent deliverable formatting."""

    @pytest.mark.unit
    def test_template_selection_review_report(self, body: str) -> None:
        """Scenario: Template selection works for review reports.

        Given the template list
        When the review report template is read
        Then it has Summary, Findings, Recommendations and Evidence.
        """
        assert _templates(body)["Review Report"] == [
            "Summary",
            "Findings",
            "Recommendations",
            "Evidence",
        ]

    @pytest.mark.unit
    def test_template_selection_pull_request(self, body: str) -> None:
        """Scenario: Template selection works for pull requests.

        Given the template list
        When the PR template is read
        Then it has Summary, Changes, Test Plan and Notes.
        """
        assert _templates(body)["PR Description"] == [
            "Summary",
            "Changes",
            "Test Plan",
            "Notes",
        ]

    @pytest.mark.unit
    def test_findings_formatting_by_severity(self, body: str) -> None:
        """Scenario: Findings are formatted by severity level.

        Given the finding rules
        When they are read
        Then five severities are defined, highest first, and findings are
        ordered by severity, then by file location.
        """
        step = _finding_step(body)
        assert "Severity levels: CRITICAL, HIGH, MEDIUM, LOW, INFO." in step
        assert "Order findings by severity, then by file location." in step

    @pytest.mark.unit
    def test_markdown_formatting_quality(self, body: str) -> None:
        """Scenario: Markdown output is properly formatted.

        Given the finding template
        When it is read
        Then each finding is a severity-tagged heading followed by the
        fields Location, Anchor, Category, Description, Evidence and
        Recommendation, and the checklist requires it to render.
        """
        step = _finding_step(body)
        assert "### [SEVERITY] Finding Title" in step
        fields = re.findall(r"^\s*(?:- )?\*\*(\w+)\*\*: ", step, re.MULTILINE)
        assert fields == [
            "Location",
            "Anchor",
            "Category",
            "Description",
            "Evidence",
            "Recommendation",
        ]
        assert "Format renders correctly in target medium" in _section(
            body, "Output Quality Checklist"
        )

    @pytest.mark.unit
    def test_the_template_parses_with_the_citation_verifier(self, body: str) -> None:
        """Scenario: a report written to the template passes the verifier.

        Given the finding template
        When citation_verifier parses it as a findings document
        Then it reads one finding at file.rs:123 with its anchor.

        The verifier matches only a bulleted ``- **Location**:`` line, so
        a template without the dash produced reports the guard rejected.
        """
        block = _finding_step(body).split("```markdown\n", 1)[1].split("```", 1)[0]
        findings = parse_markdown_findings(textwrap.dedent(block))
        assert len(findings) == 1
        assert findings[0]["file"] == "file.rs"
        assert findings[0]["line"] == 123
        assert findings[0]["anchor"].startswith("verbatim source text")

    @pytest.mark.unit
    def test_action_item_conversion_and_assignment(self, body: str) -> None:
        """Scenario: Action items are converted and assigned appropriately.

        Given the action step
        When it is read
        Then each action is a checkbox with severity, owner and a P1-P3
        priority, and owners are assigned where known.
        """
        step = _section(
            body, "Step 3: Assign Actions (`structured-output:actions-assigned`)"
        )
        assert (
            "- [ ] [HIGH] Fix SQL injection in auth.py:45 (@security-team, P1)" in step
        )
        assert re.findall(r"\(@[\w-]+, (P\d)\)", step) == ["P1", "P2", "P3"]
        assert "Include owner assignment where known." in step
        assert "Note dependencies between actions." in step

    @pytest.mark.unit
    def test_appendix_compilation_and_navigation(self, body: str) -> None:
        """Scenario: Appendix is compiled with proper navigation.

        Given the appendix step
        When it is read
        Then it has lettered sections, takes its command log from
        proof-of-work, and requires clear section headers.
        """
        step = _section(
            body, "Step 4: Attach Appendix (`structured-output:appendix-attached`)"
        )
        assert re.findall(r"^\s*### ([A-C])\. ", step, re.MULTILINE) == ["A", "B", "C"]
        assert "[Full evidence log from imbue:proof-of-work]" in step
        assert "navigable with clear section headers" in step

    @pytest.mark.unit
    def test_template_variable_substitution(self, body: str) -> None:
        """Scenario: Template variables are properly substituted.

        Given the quality checklist
        When it is read
        Then a deliverable with placeholder text does not pass.
        """
        assert "- [ ] No orphaned sections or placeholder text." in _section(
            body, "Output Quality Checklist"
        )

    @pytest.mark.unit
    def test_output_format_consistency(self, body: str) -> None:
        """Scenario: Output format maintains consistency across templates.

        Given the four templates and the evidence rule
        When they are read
        Then every template is listed, every finding cites evidence ids,
        and the checklist requires evidence references on all findings.
        """
        assert set(_templates(body)) == {
            "Review Report",
            "PR Description",
            "Release Notes",
            "Incident Report",
        }
        assert "**Evidence**: [E1, E2] - Reference to evidence log." in _finding_step(
            body
        )
        assert "- [ ] All findings have evidence references." in _section(
            body, "Output Quality Checklist"
        )

    @pytest.mark.unit
    def test_error_handling_invalid_data(self, body: str) -> None:
        """Scenario: Template formatting handles invalid data gracefully.

        Given a finding whose anchor is not at its cited line
        When the skill's anchor rule is read
        Then the finding is dropped, the check is the verifier script that
        review-core's Step 5 runs, and both files name the same script.
        """
        step = _finding_step(body)
        assert "treated as a hallucination and" in step
        assert "dropped." in step
        script = "plugins/imbue/scripts/citation_verifier.py"
        assert script in step
        assert (PLUGIN_ROOT / "scripts" / "citation_verifier.py").is_file()
        review_core = (PLUGIN_ROOT / "skills" / "review-core" / "SKILL.md").read_text()
        step5 = _section(
            review_core,
            "Step 5 – Verify Findings Are Grounded (`review-core:findings-verified`)",
        )
        assert script in step5

    @pytest.mark.unit
    def test_large_finding_set_formatting(self, body: str) -> None:
        """Scenario: Template formatting performs efficiently with many findings.

        Given a large result set
        When the appendix rules are read
        Then the main report stays concise and raw output goes to appendix C.
        """
        step = _section(
            body, "Step 4: Attach Appendix (`structured-output:appendix-attached`)"
        )
        assert "Keep main report concise; details in appendix." in step
        assert "[Large outputs, full diffs, or data exports]" in step
