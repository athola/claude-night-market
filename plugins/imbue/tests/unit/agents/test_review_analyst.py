"""Contract tests for the review-analyst agent.

The agent is a markdown definition the harness loads, so its behavior is
what the definition says. These tests pin the claims callers depend on:
the tools it may use, the skills it loads, the workflow it follows, and the
report it returns, and they check that the skills it names agree with it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _markdown_contract import flat as _flat
from _markdown_contract import load as _load
from _markdown_contract import section as _section

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
AGENT = PLUGIN_ROOT / "agents" / "review-analyst.md"
SKILLS = PLUGIN_ROOT / "skills"


@pytest.fixture(scope="module")
def agent() -> tuple[dict, str]:
    return _load(AGENT)


class TestReviewAnalystAgent:
    """Feature: Review analyst agent conducts autonomous reviews.

    As a user delegating review work
    I want the agent to follow imbue methodology
    So that reviews are consistent and thorough
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_loads_four_existing_skills_and_lists_six_steps(
        self, agent
    ) -> None:
        """Scenario: Agent uses all imbue skills correctly.

        Given the agent definition
        When its skills and Integration section are read
        Then it loads review-core, proof-of-work, structured-output and
            diff-analysis, each of which exists as an imbue skill
        And its workflow runs the six steps in order.
        """
        meta, body = agent
        loaded = [s.strip() for s in meta["skills"].split(",")]
        assert loaded == [
            "imbue:review-core",
            "imbue:proof-of-work",
            "imbue:structured-output",
            "imbue:diff-analysis",
        ]
        integration = _section(body, "Integration")
        for qualified in loaded:
            name = qualified.split(":", 1)[1]
            assert (SKILLS / name / "SKILL.md").is_file(), name
            assert f"- `{name}` - " in _flat(integration)
        workflow = _section(body, "Agent Workflow")
        steps = re.findall(r"^\d+\. \*\*(\w+)\*\*", workflow, re.MULTILINE)
        assert steps == [
            "Initialize",
            "Discover",
            "Analyze",
            "Categorize",
            "Format",
            "Report",
        ]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_requires_evidence_references_and_an_appendix(
        self, agent
    ) -> None:
        """Scenario: Agent captures reproducible evidence.

        Given the agent definition
        When its capabilities and quality standards are read
        Then evidence is captured systematically and cited as [E1], [E2]
        And the report carries the full command/citation log.
        """
        _meta, body = agent
        assert "Captures commands, outputs, and citations systematically" in _flat(
            _section(body, "Capabilities")
        )
        assert "All findings include evidence references `[E1]`, `[E2]`" in _flat(
            _section(body, "Quality Standards")
        )
        assert "**Evidence Appendix**: Full command/citation log" in _flat(
            _section(body, "Output Format")
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_groups_by_severity_on_structured_output_scale(
        self, agent
    ) -> None:
        """Scenario: Agent categorizes findings by severity with justification.

        Given the agent and the structured-output skill it loads
        When severity handling is read
        Then findings are grouped by severity and type with justified levels
        And structured-output defines the severity scale used.
        """
        _meta, body = agent
        assert "**Categorize**: Group findings by severity and type" in _flat(
            _section(body, "Agent Workflow")
        )
        assert "Severity levels justified with specific criteria" in _flat(
            _section(body, "Quality Standards")
        )
        _m, output_skill = _load(SKILLS / "structured-output" / "SKILL.md")
        assert "Severity levels: CRITICAL, HIGH, MEDIUM, LOW, INFO." in _flat(
            output_skill
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_requires_specific_recommendations_and_action_items(
        self, agent
    ) -> None:
        """Scenario: Agent generates actionable and specific recommendations.

        Given the agent definition
        When the quality standards and output format are read
        Then recommendations are actionable and specific
        And the report lists prioritized remediation steps.
        """
        _meta, body = agent
        assert "Recommendations are actionable and specific" in _flat(
            _section(body, "Quality Standards")
        )
        assert "**Action Items**: Prioritized remediation steps" in _flat(
            _section(body, "Output Format")
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_report_sections_match_review_core_skeleton(self, agent) -> None:
        """Scenario: Agent produces reports with consistent template structure.

        Given the agent and review-core's shared reporting skeleton
        When the output format is read
        Then the agent returns summary, findings, actions and evidence appendix
        And review-core's skeleton names the same four parts.
        """
        _meta, body = agent
        output = _section(body, "Output Format")
        sections = re.findall(r"^- \*\*([\w ]+)\*\*:", output, re.MULTILINE)
        assert sections == [
            "Executive Summary",
            "Detailed Findings",
            "Action Items",
            "Evidence Appendix",
        ]
        assert "Report follows consistent template structure" in _flat(body)
        _m, core = _load(SKILLS / "review-core" / "SKILL.md")
        skeleton = _section(core, "Step 4 – Structure Deliverables")
        for part in (
            "Summary (",
            "Ordered findings",
            "Follow-up tasks",
            "Evidence appendix",
        ):
            assert part in _flat(skeleton)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_is_read_only_and_drops_unverified_findings(self, agent) -> None:
        """Scenario: Agent handles tool failures gracefully.

        Given the agent definition
        When its tools and verification rule are read
        Then it is limited to read and search tools plus Bash
        And a finding the citation verifier fails is dropped or labeled
            UNVERIFIED rather than reported.
        """
        meta, body = agent
        assert meta["tools"] == ["Read", "Glob", "Grep", "Bash"]
        assert "drop or label `UNVERIFIED` any finding the verifier fails" in _flat(
            body
        )
        assert "citation_verifier.py --findings .review/findings.json" in _flat(body)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_definition_scopes_before_analysis_and_routes_quick_checks_away(
        self, agent
    ) -> None:
        """Scenario: Agent bounds its work on large codebases.

        Given the agent definition
        When the workflow is read
        Then scope discovery precedes analysis, so analysis covers only the
            artifacts inventoried in scope
        And dispatch is reserved for formal reviews, not quick checks.

        The definition states no time budget; the bound it does state is
        the in-scope inventory and the when-not-to-use routing.
        """
        meta, body = agent
        workflow = _section(body, "Agent Workflow")
        assert "**Discover**: Inventory files and artifacts in scope" in _flat(workflow)
        assert workflow.index("**Discover**") < workflow.index("**Analyze**")
        assert "Do not use when quick code check without formal review" in _flat(
            AGENT.read_text()
        )
        assert meta["effort"] == "high"
