"""Contract tests for the /pr-review workflow documents.

The workflow is executed by the model from three shipped documents:
`skills/pr-review/SKILL.md`, its `modules/`, and `commands/pr-review.md`.
Each test pins one rule those documents state, so editing the rule out
(or contradicting it between files) turns the test red.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = PLUGIN_ROOT / "skills" / "pr-review"


def _read(*parts: str) -> str:
    return PLUGIN_ROOT.joinpath(*parts).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skill_text() -> str:
    return _read("skills", "pr-review", "SKILL.md")


@pytest.fixture(scope="module")
def command_text() -> str:
    return _read("commands", "pr-review.md")


@pytest.fixture(scope="module")
def version_text() -> str:
    return _read("skills", "pr-review", "modules", "version-validation.md")


@pytest.fixture(scope="module")
def slop_text() -> str:
    return _read("skills", "pr-review", "modules", "slop-detection.md")


@pytest.fixture(scope="module")
def severity_rows(version_text: str) -> dict[str, str]:
    """Map each issue type in the classification table to its severity."""
    table = version_text.split("## Classification of Version Issues")[1].split(
        "## Bypass Mechanism", maxsplit=1
    )[0]
    rows = re.findall(r"^\| (?!Issue Type|-)([^|]+) \| ([A-Z-]+) \|", table, re.M)
    return {issue.strip(): severity for issue, severity in rows}


@pytest.mark.unit
class TestVersionValidation:
    def test_branch_name_version_mismatch_is_blocking(
        self, severity_rows: dict[str, str]
    ) -> None:
        assert (
            severity_rows["Branch name version ≠ marketplace/project version"]
            == "BLOCKING"
        )

    def test_version_mismatch_between_files_is_blocking(
        self, severity_rows: dict[str, str]
    ) -> None:
        assert severity_rows["Version mismatch between files"] == "BLOCKING"

    def test_marketplace_versus_plugin_mismatch_is_blocking(
        self, severity_rows: dict[str, str]
    ) -> None:
        assert severity_rows["Marketplace vs plugin version mismatch"] == "BLOCKING"

    def test_missing_changelog_entry_is_blocking(
        self, severity_rows: dict[str, str]
    ) -> None:
        assert severity_rows["Missing CHANGELOG entry"] == "BLOCKING"

    def test_stale_readme_version_is_in_scope_not_blocking(
        self, severity_rows: dict[str, str]
    ) -> None:
        assert severity_rows["README references old version"] == "IN-SCOPE"

    def test_changelog_check_greps_for_the_bracketed_new_version(
        self, version_text: str
    ) -> None:
        assert 'grep -q "\\[$NEW_VERSION\\]" CHANGELOG.md' in version_text

    def test_skill_states_all_mismatches_block_unless_waived(
        self, skill_text: str
    ) -> None:
        assert (
            "All version mismatches are BLOCKING unless explicitly waived" in skill_text
        )

    def test_waiver_can_come_from_flag_label_or_pr_marker(
        self, version_text: str
    ) -> None:
        bypass = version_text.split("## Bypass Mechanism")[1].split(
            "## Output Format", maxsplit=1
        )[0]
        assert "`/pr-review <pr> --skip-version-check`" in bypass
        assert "`skip-version-check` label" in bypass
        assert "`[skip-version-check]` in PR body" in bypass

    def test_waived_findings_are_still_reported_not_dropped(
        self, version_text: str
    ) -> None:
        assert "Still run validation and report findings" in version_text
        assert "Mark as `[WAIVED]` instead of `[BLOCKING]`" in version_text

    def test_command_exposes_the_skip_flag(self, command_text: str) -> None:
        assert "[--skip-version-check]" in command_text


@pytest.mark.unit
class TestCodeQualityAnalysis:
    def test_the_version_waiver_does_not_waive_code_quality_analysis(
        self, command_text: str, version_text: str
    ) -> None:
        """The waiver's scope is the behavior; the heading's wording is not."""
        assert "### Code Quality Analysis" in command_text
        bypass = version_text.split("## Bypass Mechanism")[1].split(
            "## Output Format", maxsplit=1
        )[0]
        flag = command_text.split("/pr-review --skip-version-check", maxsplit=1)[0]
        flag_comment = flag.rsplit("\n#", 1)[1]
        for waiver in (bypass, flag_comment):
            assert "quality" not in waiver.lower()
            assert "duplication" not in waiver.lower()

    def test_exact_duplication_over_ten_lines_is_blocking(
        self, command_text: str
    ) -> None:
        assert "- **BLOCKING**: Exact duplication >10 lines" in command_text

    def test_similar_patterns_to_consolidate_are_in_scope(
        self, command_text: str
    ) -> None:
        assert "- **IN-SCOPE**: Similar patterns to consolidate" in command_text

    def test_minor_redundancy_is_a_suggestion(self, command_text: str) -> None:
        assert "- **SUGGESTION**: Minor redundancy" in command_text

    def test_analysis_runs_duplication_and_redundancy_detection(
        self, command_text: str
    ) -> None:
        assert "**Duplication detection**" in command_text
        assert "**Redundancy analysis**" in command_text


@pytest.mark.unit
class TestMandatoryOutputPhases:
    def test_three_outputs_are_declared_mandatory(self, command_text: str) -> None:
        assert (
            "**MANDATORY OUTPUTS:** Review comment, Test plan comment, "
            "PR description update." in command_text
        )

    def test_missing_output_marks_the_review_incomplete(
        self, command_text: str
    ) -> None:
        assert "If any are missing, the review is INCOMPLETE." in command_text

    def test_verification_checks_cover_review_test_plan_and_description(
        self, command_text: str
    ) -> None:
        checklist = command_text.split("### Verification Checklist")[1]
        assert "# 1. Verify review comment exists" in checklist
        assert "# 2. Verify test plan exists" in checklist
        assert "# 3. Verify PR description is not empty" in checklist

    def test_failed_verification_check_blocks_completion(
        self, command_text: str
    ) -> None:
        assert (
            "**If any check returns `false`, the review is INCOMPLETE.**"
            in command_text
        )

    def test_concise_mode_waives_test_plan_and_description(
        self, command_text: str, skill_text: str
    ) -> None:
        # Whitespace is collapsed before comparing. Re-wrapping the prose
        # must not read as a change in what it says.
        assert "only the review comment applies" in " ".join(command_text.split())
        assert "no test plan comment or description update was posted" in " ".join(
            skill_text.split()
        )


@pytest.mark.unit
class TestPRDescriptionUpdate:
    def test_description_is_updated_through_the_api_not_pr_edit(
        self, command_text: str
    ) -> None:
        section = command_text.split("### PR Description Update (CRITICAL)")[1]
        assert "**DO NOT use `gh pr edit`**" in section
        assert 'gh api "repos/$OWNER_REPO/pulls/$PR_NUM"' in section
        assert "-X PATCH" in section

    def test_pr_edit_prohibition_names_the_missing_scope(
        self, command_text: str
    ) -> None:
        assert "requires `read:org` scope" in command_text

    def test_failed_api_update_falls_back_to_a_comment(self, command_text: str) -> None:
        assert (
            "**Fallback if API fails**: Post description as a comment" in command_text
        )

    def test_empty_description_is_created_from_commits_or_scope(
        self, command_text: str
    ) -> None:
        assert "Update PR body OR create from commits/scope if empty" in command_text


@pytest.mark.unit
class TestReportStructure:
    def test_report_headings_carry_per_category_counts(self, skill_text: str) -> None:
        report = skill_text.split("### Phase 6: Generate Report")[1]
        for heading in ("Blocking", "In-Scope", "Suggestions"):
            assert re.search(rf"^### {heading} \(\d+\)$", report, re.M)

    def test_every_finding_category_is_defined_in_the_scope_framework(self) -> None:
        framework = _read("skills", "pr-review", "modules", "scope-classification.md")
        for category in ("BLOCKING", "IN-SCOPE", "SUGGESTION", "BACKLOG", "IGNORE"):
            assert f"| **{category}** |" in framework

    def test_approval_requires_no_blocking_issues(self, skill_text: str) -> None:
        gates = skill_text.split("## Quality Gates")[1]
        assert "- [ ] No BLOCKING issues remain" in gates


@pytest.mark.unit
class TestSlopDetectionPhase:
    def test_changed_markdown_is_scanned_with_the_scribe_detector(
        self, slop_text: str
    ) -> None:
        assert "For all changed `.md` files, invoke `Skill(scribe:slop-detector)`" in (
            slop_text
        )

    def test_doc_slop_is_in_scope_at_three_and_blocking_at_five_in_strict_mode(
        self, slop_text: str
    ) -> None:
        assert "Score ≥ 3.0: Flag as IN-SCOPE" in slop_text
        assert "Score ≥ 5.0: Flag as BLOCKING if `--strict` mode" in slop_text

    def test_commit_message_slop_is_only_a_suggestion(self, slop_text: str) -> None:
        assert "If commits contain slop, add a SUGGESTION" in slop_text

    def test_commit_scan_reads_message_bodies_of_the_pr(self, slop_text: str) -> None:
        assert "gh pr view <number> --json commits" in slop_text

    def test_slop_detection_is_mandatory_and_skippable_for_docs(
        self, command_text: str
    ) -> None:
        assert "**Slop Detection** - AI content markers in docs, commits" in (
            command_text
        )
        assert "(MANDATORY)" in command_text
        assert "[--skip-doc-review]" in command_text

    def test_skill_points_at_the_slop_module(self, skill_text: str) -> None:
        assert "[`modules/slop-detection.md`](modules/slop-detection.md)" in skill_text
