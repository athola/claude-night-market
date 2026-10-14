"""Cross-file contract tests for the review workflow.

The review workflow is a chain of markdown files: the /structured-review
command, the review-analyst agent, and the review-core, proof-of-work,
structured-output, diff-analysis and catchup skills. The harness runs what
those files say, so the integration that can break is disagreement between
them: a command naming a skill that does not exist, progress items that
drift from their steps, or evidence tags in two formats. Each test pins one
such agreement against the real files.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from _markdown_contract import flat as _flat
from _markdown_contract import load as _load
from _markdown_contract import section as _section

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PLUGIN_ROOT / "skills"
COMMANDS = PLUGIN_ROOT / "commands"
AGENTS = PLUGIN_ROOT / "agents"
EVIDENCE_LOGGING = SKILLS / "proof-of-work" / "modules" / "evidence-logging.md"
WORKFLOW_SKILLS = ["review-core", "proof-of-work", "structured-output", "diff-analysis"]


def _skill(name: str) -> tuple[dict, str]:
    return _load(SKILLS / name / "SKILL.md")


def _progress_items(body: str, prefix: str) -> list[str]:
    return re.findall(rf"`({prefix}:[a-z-]+)`", _section(body, "Required Progress"))


class TestReviewWorkflowIntegration:
    """Feature: the four review skills form one consistent workflow."""

    @pytest.mark.bdd
    def test_command_names_the_four_workflow_skills_and_each_exists(self) -> None:
        """Scenario: The command names the four workflow skills.

        Given the /structured-review command
        When the skills it orchestrates are read
        Then it names four skills, each present with a matching name.
        """
        _meta, body = _load(COMMANDS / "structured-review.md")
        named = re.findall(
            r"^- `([a-z-]+)` - ", _section(body, "Workflow Integration"), re.MULTILINE
        )
        assert named == WORKFLOW_SKILLS
        for name in named:
            meta, _ = _skill(name)
            assert meta["name"] == name

    @pytest.mark.bdd
    def test_progress_items_match_step_headings_in_order(self) -> None:
        """Scenario: Progress items follow the step order.

        Given review-core and diff-analysis
        When their progress items and step headings are read
        Then each item has a step heading, in the same order as the list.
        """
        for name in ("review-core", "diff-analysis"):
            _meta, body = _skill(name)
            items = _progress_items(body, name)
            assert items, name
            headed = re.findall(
                rf"^### Step \d[^\n]*\(`({name}:[a-z-]+)`\)|^## Step \d[^\n]*\(`({name}:[a-z-]+)`\)",
                body,
                re.MULTILINE,
            )
            assert [a or b for a, b in headed] == items, name

    @pytest.mark.bdd
    def test_structured_output_cites_evidence_in_the_log_tag_format(self) -> None:
        """Scenario: Evidence tags match across skills.

        Given structured-output and the evidence-logging module
        When their evidence formats are read
        Then a finding cites evidence as [E1, E2], the tag the log defines
        And structured-output declares its dependency on proof-of-work.
        """
        meta, body = _skill("structured-output")
        assert "imbue:proof-of-work" in meta["dependencies"]
        assert "**Evidence**: [E1, E2] - Reference to evidence log." in body
        assert "(e.g., `[E1]`, `[E2]`)" in EVIDENCE_LOGGING.read_text()

    @pytest.mark.bdd
    def test_report_template_and_anchor_rule_agree_across_skills(self) -> None:
        """Scenario: The report template and grounding rule agree.

        Given structured-output and review-core
        When the review report template and grounding rule are read
        Then the template has summary, findings, recommendations, evidence
        And both files require a verbatim Anchor checked by the verifier.
        """
        _m, output = _skill("structured-output")
        assert (
            "**Review Report**: Summary, Findings, Recommendations, Evidence." in output
        )
        assert "**Anchor is mandatory and grounds the finding.**" in output
        assert (
            "`plugins/imbue/scripts/citation_verifier.py` over the findings" in output
        )
        _m, core = _skill("review-core")
        assert (
            "Use the grounded-finding schema from `Skill(imbue:structured-output)`"
            in core
        )
        assert (PLUGIN_ROOT / "scripts" / "citation_verifier.py").is_file()


class TestCatchupWorkflowIntegration:
    """Feature: /catchup and the catchup skill agree on the method."""

    @pytest.mark.bdd
    def test_catchup_progress_items_steps_and_exit_criteria_agree(self) -> None:
        """Scenario: Catchup phases agree across skill and command.

        Given the catchup skill and command
        When phases are read
        Then four progress items map to four steps
        And the exit criteria require all four
        And the command delegates to the skill.
        """
        _meta, body = _skill("catchup")
        assert _progress_items(body, "catchup") == [
            "catchup:context-confirmed",
            "catchup:delta-captured",
            "catchup:insights-extracted",
            "catchup:followups-recorded",
        ]
        steps = re.findall(r"^### Step \d: ([\w -]+)$", body, re.MULTILINE)
        assert steps == [
            "Confirm Context",
            "Capture Delta",
            "Extract Insights",
            "Record Follow-ups",
        ]
        assert "- [ ] All four `catchup:` progress items are marked complete" in (
            _section(body, "Exit Criteria")
        )
        assert "Invoke `Skill(imbue:catchup)`" in (COMMANDS / "catchup.md").read_text()

    @pytest.mark.bdd
    def test_catchup_defines_scope_baseline_and_current_target(self) -> None:
        """Scenario: Catchup context captures branch and commit info.

        Given the catchup skill and command
        When context confirmation is read
        Then scope, baseline and current target are defined
        And the command's example reports branch, baseline and HEAD.
        """
        _meta, body = _skill("catchup")
        step = _section(body, "Step 1: Confirm Context")
        assert (
            "Define scope (git branch, sprint, meetings), baseline (last state)" in step
        )
        command = (COMMANDS / "catchup.md").read_text()
        assert "# Scope: feature/payments branch" in command
        assert "# Baseline: main (merge-base)" in command
        assert "# Current: HEAD (15 commits ahead)" in command

    @pytest.mark.bdd
    def test_catchup_output_format_lists_the_four_sections(self) -> None:
        """Scenario: Catchup summary contains expected data.

        Given the catchup skill output format
        When its sections are read
        Then it has Summary, Key Changes, Follow-ups and Blockers/Questions
        And the command example shows the Key Changes section.
        """
        _meta, body = _skill("catchup")
        fence = body[body.index("## Output Format") :]
        fence = fence[: fence.index("## Integration")]
        assert re.findall(r"^## ([\w/ -]+)$", fence, re.MULTILINE)[1:] == [
            "Summary",
            "Key Changes",
            "Follow-ups",
            "Blockers/Questions",
        ]
        assert "# Key Changes:" in (COMMANDS / "catchup.md").read_text()


class TestAgentIntegration:
    """Feature: the review-analyst agent agrees with the skills it loads."""

    @pytest.mark.bdd
    def test_agent_loads_the_same_four_skills_as_the_command(self) -> None:
        """Scenario: Agent loads the command's review skills.

        Given the review-analyst agent and the /structured-review command
        When the skills each loads are read
        Then the agent loads the same four existing skills the command uses.
        """
        meta, _ = _load(AGENTS / "review-analyst.md")
        loaded = [s.strip().split(":", 1)[1] for s in meta["skills"].split(",")]
        assert loaded == WORKFLOW_SKILLS
        for name in loaded:
            assert (SKILLS / name / "SKILL.md").is_file(), name

    @pytest.mark.bdd
    def test_agent_requires_evidence_citations_per_finding(self) -> None:
        """Scenario: The agent's report cites evidence for each finding.

        Given the review-analyst agent
        When its dispatch example and output format are read
        Then the report carries evidence citations for each finding.

        Renamed from test_agent_report_is_agent_generated: no imbue file
        states an agent-generated flag or the OWASP/NIST compliance list
        that test asserted, so that intent has no file to check.
        """
        body = (AGENTS / "review-analyst.md").read_text()
        assert "evidence citations for each finding" in body
        assert "**Detailed Findings**: Categorized by severity with evidence." in body

    @pytest.mark.bdd
    def test_evidence_log_and_agent_both_require_attribution(self) -> None:
        """Scenario: Agent evidence is attributed correctly.

        Given the agent and the evidence-logging module
        When attribution is read
        Then the log records the analyst's identity and scope
        And the agent captures commands, outputs and citations.
        """
        assert "Analyst identity and review scope." in EVIDENCE_LOGGING.read_text()
        body = (AGENTS / "review-analyst.md").read_text()
        assert "Captures commands, outputs, and citations systematically" in body

    @pytest.mark.bdd
    def test_agent_and_structured_output_require_a_verbatim_anchor(self) -> None:
        """Scenario: Agent findings meet the grounding bar.

        Given the agent and structured-output
        When finding quality rules are read
        Then every finding carries a Location and a verbatim Anchor
        And structured-output drops a finding whose anchor does not match.
        """
        body = (AGENTS / "review-analyst.md").read_text()
        assert "Every finding carries a `Location` (file:line) and a verbatim" in body
        _m, output = _skill("structured-output")
        assert "treated as a hallucination and dropped" in _flat(output)


class TestEvidenceChainContinuity:
    """Feature: evidence references mean the same thing in every file."""

    @pytest.mark.bdd
    def test_evidence_log_uses_distinct_command_and_citation_prefixes(self) -> None:
        """Scenario: Evidence IDs are unique.

        Given the evidence-logging module
        When its naming convention is read
        Then commands and citations use distinct numbered prefixes.
        """
        module = EVIDENCE_LOGGING.read_text()
        assert "naming convention for evidence references" in module
        assert "[E1] Command:" in module
        assert "[C1] Source:" in module

    @pytest.mark.bdd
    def test_evidence_log_and_proof_of_work_require_traceable_references(self) -> None:
        """Scenario: All evidence references resolve to existing evidence.

        Given the evidence-logging module and proof-of-work
        When their exit rules are read
        Then every finding is traceable to a logged reference
        And proof-of-work requires a real command behind each [E1].
        """
        module = EVIDENCE_LOGGING.read_text()
        assert "All findings traceable to specific evidence references." in module
        _m, proof = _skill("proof-of-work")
        assert "At least one `[E1]`/`[E2]` evidence reference exists" in proof
        assert "backed by a real command invocation and its output" in proof

    @pytest.mark.bdd
    def test_agent_and_command_give_diff_analysis_the_same_role(self) -> None:
        """Scenario: Skill contributions are tracked.

        Given the agent and command naming diff-analysis
        When its role is read in each file
        Then both give it change categorization
        And diff-analysis has a progress item for exactly that.
        """
        agent = (AGENTS / "review-analyst.md").read_text()
        command = (COMMANDS / "structured-review.md").read_text()
        assert "- `diff-analysis` - Change categorization" in agent
        assert "- `diff-analysis` - Change categorization" in command
        _m, diff = _skill("diff-analysis")
        assert "diff-analysis:changes-categorized" in _progress_items(
            diff, "diff-analysis"
        )


class TestCommandSkillOrchestration:
    """Feature: /structured-review dispatches to skills that exist."""

    @pytest.mark.bdd
    def test_command_name_matches_its_file_and_usage(self) -> None:
        """Scenario: Command frontmatter names the command.

        Given the command file
        When its frontmatter is read
        Then its name matches the file and its usage line.
        """
        meta, _ = _load(COMMANDS / "structured-review.md")
        assert meta["name"] == "structured-review"
        assert meta["usage"].startswith("/structured-review ")

    @pytest.mark.bdd
    def test_every_skill_the_command_references_exists(self) -> None:
        """Scenario: Every skill the command calls exists.

        Given the command
        When every Skill(imbue:...) reference is read
        Then each resolves to an imbue skill directory.
        """
        body = (COMMANDS / "structured-review.md").read_text()
        referenced = re.findall(r"Skill\(imbue:([a-z-]+)\)", body)
        assert set(referenced) == {"feature-review", "scope-guard", "review-core"}
        for name in referenced:
            assert (SKILLS / name / "SKILL.md").is_file(), name

    @pytest.mark.bdd
    def test_every_imbue_reference_in_workflow_skills_exists(self) -> None:
        """Scenario: Skill cross-references resolve.

        Given the skills in the workflow
        When their Skill(imbue:...) references are read
        Then each names an imbue skill that exists.
        """
        checked = 0
        for name in WORKFLOW_SKILLS:
            _m, body = _skill(name)
            for ref in re.findall(r"imbue:([a-z-]+)", body):
                assert (SKILLS / ref / "SKILL.md").is_file(), f"{name} -> {ref}"
                checked += 1
        assert checked

    @pytest.mark.bdd
    def test_command_requires_every_review_core_progress_item(self) -> None:
        """Scenario: The command requires review-core's items.

        Given the command's exit criteria and review-core
        When the required progress items are read
        Then the command requires every review-core item
        And review-core defines six.
        """
        body = (COMMANDS / "structured-review.md").read_text()
        assert "- All progress items from review-core created" in body
        _m, core = _skill("review-core")
        assert len(_progress_items(core, "review-core")) == 6

    @pytest.mark.bdd
    def test_command_stages_match_review_core_steps_in_order(self) -> None:
        """Scenario: Command stages match review-core steps.

        Given the command's four stages and review-core's first four steps
        When both are read
        Then they name the same stages in the same order.
        """
        _meta, body = _load(COMMANDS / "structured-review.md")
        stages = re.findall(
            r"^\d+\. \*\*([\w ]+)\*\*", _section(body, "What It Does"), re.MULTILINE
        )
        _m, core = _skill("review-core")
        core_steps = re.findall(r"^## Step \d – ([\w ]+) \(", core, re.MULTILINE)
        assert stages == [
            "Establishes Context",
            "Inventories Scope",
            "Prepares Evidence Log",
            "Structures Deliverables",
        ]
        assert core_steps[:4] == [
            "Establish Context",
            "Inventory Scope",
            "Capture Evidence",
            "Structure Deliverables",
        ]


class TestErrorPropagation:
    """Feature: review-core says what to do when a step fails."""

    @pytest.fixture(scope="class")
    def core(self) -> str:
        return _skill("review-core")[1]

    @pytest.mark.bdd
    def test_review_core_documents_alternatives_for_an_unavailable_skill(
        self, core
    ) -> None:
        """Scenario: The workflow continues past an unavailable skill.

        Given review-core's contingency step
        When a required tool or skill is unavailable
        Then alternative steps are documented instead of stopping.
        """
        step = _section(core, "Step 6 – Contingency Plan")
        assert "If a required tool or skill is unavailable" in step
        assert "document the alternative steps that will be taken" in step

    @pytest.mark.bdd
    def test_review_core_records_owners_for_a_blocking_variance(self, core) -> None:
        """Scenario: A blocking failure is captured.

        Given review-core's evidence step
        When a variance blocks progress
        Then owners and timelines are recorded.
        """
        step = _section(core, "Step 3 – Capture Evidence")
        assert "if they block progress, record owners/timelines now" in step

    @pytest.mark.bdd
    def test_review_core_documents_a_manual_fallback_for_the_verifier(
        self, core
    ) -> None:
        """Scenario: Fallback is applied when the verifier is unavailable.

        Given review-core's verification step
        When the citation verifier script is unavailable
        Then each cited file:line is re-read by hand as the fallback.
        """
        step = _section(core, "Step 5 – Verify Findings Are Grounded")
        assert "fall back to re-reading each cited `file:line` by hand" in _flat(step)

    @pytest.mark.bdd
    def test_review_core_exit_criteria_record_blockers_to_lessons_learned(
        self, core
    ) -> None:
        """Scenario: Error details are logged.

        Given review-core's exit criteria
        When a failed approach or blocker occurred
        Then it is recorded to docs/lessons-learned.md.
        """
        exit_criteria = _section(core, "Exit Criteria")
        assert "Any rework, failed approach, or blocker" in exit_criteria
        assert "recorded to `docs/lessons-learned.md`" in exit_criteria
