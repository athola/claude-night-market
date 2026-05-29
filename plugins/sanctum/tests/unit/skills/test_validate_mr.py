"""Invariant tests for the validate-mr skill structure and contract.

Feature: validate-mr skill generates diff-derived test plans with genuine guards

    As an engineer running /fix-pr or /sanctum:validate-mr
    I want the validate-mr skill to document a stable validation contract
    So that:
    - Every changed area gets at least one targeted verification step
    - Revert-tests use git-based restore (safe on interrupt)
    - The working tree guard prevents data loss before mutation
    - Any FAIL result halts /fix-pr before Step 6 (Complete)
    - Exit Criteria are concrete and falsifiable

These tests are regression guards for the skill's CONTENT CONTRACT.
A failing test means a load-bearing section was changed or removed.
Do NOT silently update the assertion — the failure warrants human review.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "validate-mr"
SKILL_FILE = SKILL_DIR / "SKILL.md"


@pytest.fixture(scope="module")
def skill_content() -> str:
    return SKILL_FILE.read_text(encoding="utf-8")


class TestSkillStructure:
    """Feature: validate-mr SKILL.md is well-formed.

    As a plugin maintainer
    I want the validate-mr skill properly structured
    So that it loads correctly via Skill(sanctum:validate-mr)
    """

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md exists at the expected path.

        Given the validate-mr skill directory
        When checking for SKILL.md
        Then the file exists
        """
        assert SKILL_FILE.exists(), f"validate-mr SKILL.md must exist at {SKILL_FILE}"

    @pytest.mark.unit
    def test_skill_has_yaml_frontmatter(self, skill_content: str) -> None:
        """Scenario: SKILL.md has YAML frontmatter delimiters.

        Given the validate-mr SKILL.md
        When reading its content
        Then it starts with --- and has a closing ---
        """
        assert skill_content.startswith("---"), (
            "SKILL.md must start with YAML frontmatter delimiter"
        )
        assert skill_content.count("---") >= 2, (
            "SKILL.md must have opening and closing frontmatter delimiters"
        )

    @pytest.mark.unit
    def test_skill_name_is_validate_mr(self, skill_content: str) -> None:
        """Scenario: Frontmatter name field matches the skill directory name.

        Given the validate-mr SKILL.md
        When reading frontmatter
        Then name is 'validate-mr'
        """
        assert "name: validate-mr" in skill_content, (
            "Frontmatter must declare name: validate-mr"
        )

    @pytest.mark.unit
    def test_skill_has_description(self, skill_content: str) -> None:
        """Scenario: Frontmatter has a description field.

        Given the validate-mr SKILL.md
        When reading frontmatter
        Then description field is present and non-empty
        """
        assert re.search(r"^description:", skill_content, re.MULTILINE), (
            "Frontmatter must include a description field"
        )

    @pytest.mark.unit
    def test_skill_declares_leyline_git_platform_dependency(
        self, skill_content: str
    ) -> None:
        """Scenario: Skill declares leyline:git-platform as a dependency.

        Given the validate-mr SKILL.md frontmatter
        When reading dependencies
        Then leyline:git-platform is listed
        So diff fetching uses the cross-platform CLI mapping
        """
        assert "leyline:git-platform" in skill_content, (
            "validate-mr must declare leyline:git-platform dependency "
            "for cross-platform gh/glab diff fetching"
        )

    @pytest.mark.unit
    def test_skill_declares_imbue_proof_of_work_dependency(
        self, skill_content: str
    ) -> None:
        """Scenario: Skill declares imbue:proof-of-work as a dependency.

        Given the validate-mr SKILL.md frontmatter
        When reading dependencies
        Then imbue:proof-of-work is listed
        So evidence capture follows the [E1]/[E2] convention
        """
        assert "imbue:proof-of-work" in skill_content, (
            "validate-mr must declare imbue:proof-of-work dependency "
            "for [E1]/[E2] evidence capture patterns"
        )


class TestRevertTestSafety:
    """Feature: Revert-test uses safe, git-based restore.

    As an engineer running validate-mr
    I want the revert-test to use git checkout for restore
    So that a mid-test interruption cannot leave the working tree in a
    broken state (manual re-edit restore is not interrupt-safe)
    """

    @pytest.mark.unit
    def test_revert_test_uses_git_checkout_restore(self, skill_content: str) -> None:
        """Scenario: Revert-test documents git-based restore.

        Given the validate-mr SKILL.md
        When reading the revert-test section
        Then it instructs: git checkout -- <file>
        So restore is interrupt-safe (not manual re-edit)
        """
        assert "git checkout --" in skill_content, (
            "Revert-test must use `git checkout -- <file>` for restore, "
            "not a manual re-edit (unsafe on interrupt)"
        )

    @pytest.mark.unit
    def test_revert_test_guards_on_clean_working_tree(self, skill_content: str) -> None:
        """Scenario: Revert-test checks for uncommitted changes before mutating.

        Given the validate-mr SKILL.md
        When reading the revert-test section
        Then it documents: git diff --exit-code as a pre-mutation guard
        So uncommitted work is not silently lost by a failed restore
        """
        assert "git diff --exit-code" in skill_content, (
            "Revert-test must guard on a clean working tree "
            "(git diff --exit-code) before any source mutation"
        )

    @pytest.mark.unit
    def test_revert_test_documents_inconclusive_when_no_covering_test(
        self, skill_content: str
    ) -> None:
        """Scenario: INCONCLUSIVE result when no covering test exists.

        Given the validate-mr SKILL.md
        When reading the revert-test section
        Then it documents INCONCLUSIVE as the result when no test covers
        the changed area, rather than fabricating a result
        """
        assert "INCONCLUSIVE" in skill_content, (
            "Skill must document INCONCLUSIVE result when no covering test "
            "exists — fabricating a revert-test result is not acceptable"
        )


class TestWorkflowContract:
    """Feature: validate-mr workflow documents the full algorithm.

    As an engineer reading the skill
    I want each workflow phase explicitly documented
    So that the algorithm is reproducible without guessing
    """

    @pytest.mark.unit
    def test_documents_diff_fetch_command(self, skill_content: str) -> None:
        """Scenario: Skill documents how to fetch the diff.

        Given the validate-mr SKILL.md
        When reading the diff-fetch section
        Then gh pr diff appears as the primary fetch command
        """
        assert "gh pr diff" in skill_content, (
            "Skill must document gh pr diff as the primary diff-fetch command"
        )

    @pytest.mark.unit
    def test_documents_area_grouping(self, skill_content: str) -> None:
        """Scenario: Skill groups changed files into verification areas.

        Given the validate-mr SKILL.md
        When reading the area-detection section
        Then Rust, Python, and Shell are all named as areas
        """
        for area in ("Rust", "Python", "Shell"):
            assert area in skill_content, (
                f"Skill must document {area} as a verification area"
            )

    @pytest.mark.unit
    def test_documents_evidence_labels(self, skill_content: str) -> None:
        """Scenario: Evidence is labelled with [E1], [E2] markers.

        Given the validate-mr SKILL.md
        When reading evidence capture instructions
        Then [E1] and [E2] labels are documented
        So results are traceable per imbue:proof-of-work conventions
        """
        assert "[E1]" in skill_content and "[E2]" in skill_content, (
            "Skill must document [E1]/[E2] evidence labelling"
        )

    @pytest.mark.unit
    def test_documents_summary_table_columns(self, skill_content: str) -> None:
        """Scenario: Summary table has Area, Step, Evidence, Result columns.

        Given the validate-mr SKILL.md
        When reading the summary table format
        Then all four columns are defined
        """
        for column in ("Area", "Step", "Evidence", "Result"):
            assert column in skill_content, (
                f"Summary table must include column: {column}"
            )

    @pytest.mark.unit
    def test_documents_shellcheck_for_shell_area(self, skill_content: str) -> None:
        """Scenario: Shell files trigger shellcheck verification.

        Given the validate-mr SKILL.md
        When reading shell area steps
        Then shellcheck is listed as the verification tool
        """
        assert "shellcheck" in skill_content, (
            "Skill must document shellcheck as the verification tool for "
            ".sh file changes"
        )


class TestIntegrationContract:
    """Feature: validate-mr integrates correctly with /fix-pr.

    As a /fix-pr workflow
    I want validate-mr to halt before Gate 3 on failure
    So that broken fixes never reach the summary comment
    """

    @pytest.mark.unit
    def test_documents_failure_halts_fix_pr_before_step_6(
        self, skill_content: str
    ) -> None:
        """Scenario: FAIL result halts /fix-pr before Step 6.

        Given the validate-mr SKILL.md
        When reading the Failure Behaviour section
        Then it states that FAIL halts /fix-pr before Step 6
        So broken fixes do not reach the summary/Gate 3 comment
        """
        # The skill must explicitly mention halting before Step 6
        assert "Step 6" in skill_content, (
            "Failure Behaviour must mention halting /fix-pr before Step 6"
        )
        assert "FAIL" in skill_content, (
            "Skill must describe behaviour when a step produces FAIL"
        )

    @pytest.mark.unit
    def test_documents_skip_validate_bypass(self, skill_content: str) -> None:
        """Scenario: --skip-validate flag bypasses validate-mr.

        Given the validate-mr SKILL.md
        When reading the When NOT To Use section
        Then --skip-validate is listed as a bypass condition
        """
        assert "--skip-validate" in skill_content, (
            "Skill must document --skip-validate as a bypass condition "
            "for minor/formatting-only PRs"
        )

    @pytest.mark.unit
    def test_documents_scope_minor_bypass(self, skill_content: str) -> None:
        """Scenario: --scope minor skips validate-mr for formatting changes.

        Given the validate-mr SKILL.md
        When reading skip conditions
        Then --scope minor is documented as a bypass for doc/format-only diffs
        """
        assert "--scope minor" in skill_content, (
            "Skill must document --scope minor as a skip condition "
            "when only formatting/doc changes are present"
        )


class TestExitCriteria:
    """Feature: validate-mr has concrete, falsifiable Exit Criteria.

    As a skill author
    I want every new SKILL.md to include an Exit Criteria section
    So the model can determine when to stop (per project rule skill-exit-criteria)
    """

    @pytest.mark.unit
    def test_has_exit_criteria_section(self, skill_content: str) -> None:
        """Scenario: SKILL.md contains an Exit Criteria section.

        Given the validate-mr SKILL.md
        When reading the document structure
        Then an 'Exit Criteria' section heading is present
        """
        assert "## Exit Criteria" in skill_content, (
            "Every SKILL.md must have an ## Exit Criteria section "
            "(per .claude/rules/skill-exit-criteria.md)"
        )

    @pytest.mark.unit
    def test_exit_criteria_has_checkboxes(self, skill_content: str) -> None:
        """Scenario: Exit Criteria items are observable checkboxes.

        Given the validate-mr SKILL.md Exit Criteria section
        When reading its items
        Then at least three checkbox items (- [ ]) are present
        So criteria are concrete and falsifiable
        """
        criteria_match = re.search(
            r"## Exit Criteria(.+?)(?=^##|\Z)", skill_content, re.DOTALL | re.MULTILINE
        )
        assert criteria_match, "Exit Criteria section content not found"

        criteria_body = criteria_match.group(1)
        checkboxes = re.findall(r"- \[ \]", criteria_body)
        assert len(checkboxes) >= 3, (
            f"Exit Criteria must have at least 3 checkbox items, found {len(checkboxes)}"
        )
