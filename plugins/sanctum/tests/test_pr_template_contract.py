"""Test: the PR description structure holds across every copy of it.

Before ADR-0021 the template existed in three places that had already
drifted. `prepare-pr.md` had grown two sections and two checklist items
that `modules/pr-template.md` never learned about, and nothing was red.
The drift was invisible because no test named the sections.

These tests name them. `modules/pr-template.md` is the source of record;
the skill, the agent, the command, and the `.github` templates are its
consumers. Deleting a section from any of them turns one of these red.

Feature: six dimensions in two registers, consumed consistently.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

PR_PREP = PLUGIN_ROOT / "skills" / "pr-prep"
TEMPLATE_MODULE = PR_PREP / "modules" / "pr-template.md"
PR_PREP_SKILL = PR_PREP / "SKILL.md"
PR_AGENT = PLUGIN_ROOT / "agents" / "pr-agent.md"
PREPARE_PR = PLUGIN_ROOT / "commands" / "prepare-pr.md"
VALIDATE_PR = PLUGIN_ROOT / "commands" / "validate-pr.md"

GITHUB_TEMPLATES = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE"
DEFAULT_TEMPLATE = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
ADR = REPO_ROOT / "docs" / "adr" / "0021-pr-descriptions-in-two-registers.md"

# The facts table rows. Each is a lookup, not an argument, so each costs
# one row rather than a heading. Dropping one drops a dimension.
TABLE_ROWS = ("**Who**", "**Where**", "**When**")

# The prose sections. These carry arguments a reader cannot reconstruct
# from the diff.
PROSE_SECTIONS = ("## Why", "## What and how")

# The four conditions that make a manual test plan mandatory. Losing one
# means a class of change ships without a reviewer-runnable plan.
TEST_PLAN_TRIGGERS = (
    "no automated coverage",
    "user-facing",
    "bug fix",
    "external contract",
)


def _normalize(text: str) -> str:
    """Collapse whitespace runs so anchors survive an 80-column reflow.

    The repo wraps prose at 80 characters, so any anchor phrase long
    enough to be meaningful will eventually straddle a line break.
    Matching raw text would make these tests fail on a pure reflow and
    tempt an author to "fix" red by unwrapping a line.

    Collapsing whitespace keeps the property that matters: deleting the
    guarded passage still turns the test red.
    """
    return re.sub(r"\s+", " ", text)


def _read(path: Path) -> str:
    """Read a guarded file, failing loudly when it has been moved."""
    if not path.exists():
        pytest.fail(f"guarded file is missing: {path.relative_to(REPO_ROOT)}")
    return _normalize(path.read_text(encoding="utf-8"))


def _structure_block(path: Path) -> str:
    """Return the canonical structure fence under `## The structure`.

    Scoping matters more than it looks. `**Who**` appears four times in
    the module: the canonical block, two worked examples, and the row
    guidance. A whole-file substring check stays green when the row is
    deleted from the canonical block alone, which is exactly the edit
    this test has to catch. Verified by revert test: deleting the row
    passes a file-wide check and fails this one.
    """
    raw = path.read_text(encoding="utf-8")
    after = raw.split("## The structure", 1)
    if len(after) < 2:
        pytest.fail(f"{path.name} lost its '## The structure' heading")
    fences = re.findall(r"```markdown\n(.*?)```", after[1], re.DOTALL)
    if not fences:
        pytest.fail(f"{path.name} has no fenced block under '## The structure'")
    return _normalize(fences[0])


@pytest.fixture(scope="module")
def template() -> str:
    """The source of record for PR description structure."""
    return _read(TEMPLATE_MODULE)


@pytest.fixture(scope="module")
def structure() -> str:
    """The canonical structure block, scoped away from the examples."""
    return _structure_block(TEMPLATE_MODULE)


class TestSourceOfRecord:
    """`modules/pr-template.md` defines the structure everything else uses."""

    @pytest.mark.parametrize("row", TABLE_ROWS)
    def test_facts_table_declares_row(self, structure: str, row: str) -> None:
        """GIVEN the canonical structure block in pr-template.md
        WHEN one of the Who/Where/When rows is deleted from it
        THEN this fails and names the dimension that went missing.
        """
        assert row in structure, (
            f"the canonical structure block lost its {row} row. Who, Where, "
            "and When are the three dimensions cheap enough to state on "
            "every PR; dropping one drops it from every description."
        )

    @pytest.mark.parametrize("section", PROSE_SECTIONS)
    def test_prose_section_present(self, structure: str, section: str) -> None:
        """GIVEN the canonical structure block
        WHEN the Why or What-and-how heading is removed
        THEN this fails, since neither is reconstructable from a diff.
        """
        assert section in structure, (
            f"the canonical structure block lost the {section} section"
        )

    @pytest.mark.parametrize("section", ["## Test plan", "## Checklist"])
    def test_conditional_section_declared(self, structure: str, section: str) -> None:
        """GIVEN the canonical structure block
        WHEN Test plan or Checklist is dropped from the declaration
        THEN this fails; conditional on the change is not optional here.
        """
        assert section in structure, (
            f"the canonical structure block lost {section}. It is "
            "conditional on the change, not optional in the structure."
        )

    def test_external_half_of_where_is_explicit(self, template: str) -> None:
        """GIVEN a change with no consumers outside this repository
        WHEN the template stops showing how to write `External: none`
        THEN this fails, because an omitted row and a row saying none
        become indistinguishable to a reader.
        """
        assert "External: none" in template, (
            "the template must show how to state an empty external blast "
            "radius. ADR-0021 rejected deleting inapplicable rows because a "
            "reader cannot tell an omitted blast radius from one of none."
        )

    def test_title_carries_the_summary(self, template: str) -> None:
        """GIVEN the title doubles as the one-line summary
        WHEN the imperative and self-contained rule is dropped
        THEN this fails, re-admitting the "Fix bug" titles Google's
        eng-practices names as the failure mode.
        """
        assert "imperative and self-contained" in template, (
            "the template must say the title is imperative and "
            "self-contained. Google's eng-practices names 'Fix bug' and "
            "'Phase 1' as the failure this rule prevents."
        )

    @pytest.mark.parametrize("trigger", TEST_PLAN_TRIGGERS)
    def test_manual_test_plan_trigger(self, template: str, trigger: str) -> None:
        """GIVEN the four conditions that make a manual plan mandatory
        WHEN one trigger is removed from the template
        THEN this fails, since that class of change would ship with no
        reviewer-runnable plan.
        """
        assert trigger in template, (
            f"the manual test plan trigger '{trigger}' is gone. Without it, "
            "that class of change ships with no reviewer-runnable plan."
        )

    def test_every_step_states_an_expected_result(self, template: str) -> None:
        """GIVEN a test plan step written without an expected result
        WHEN the template stops requiring one
        THEN this fails; a step nobody can fail proves nothing.
        """
        assert "a step the reviewer cannot fail" in template, (
            "the template must require an expected result on every test "
            "plan step. A step without one cannot be failed, so it proves "
            "nothing."
        )

    def test_gherkin_rejection_is_recorded(self, template: str) -> None:
        """GIVEN Gherkin was considered and rejected for PR bodies
        WHEN that rationale disappears from the template
        THEN this fails, and the question returns every review.
        """
        assert "Gherkin" in template, (
            "the template must say why Gherkin was rejected for PR bodies, "
            "or the question gets relitigated on every review."
        )

    def test_checklist_is_bounded(self, template: str) -> None:
        """GIVEN attention is a fixed budget across checklist items
        WHEN the rationale for a short checklist is removed
        THEN this fails, and the checklist grows back unopposed.
        """
        assert "lowers the scrutiny the hard items get" in template, (
            "the template must carry the attention-budget rationale for a "
            "short checklist. Without it, the checklist grows back."
        )


class TestConsumersDoNotDrift:
    """Every copy of the structure names the same sections."""

    @pytest.mark.parametrize(
        "path",
        [PR_PREP_SKILL, PR_AGENT, PREPARE_PR],
        ids=["pr-prep-skill", "pr-agent", "prepare-pr-command"],
    )
    @pytest.mark.parametrize("dimension", ["Who", "Where", "When"])
    def test_consumer_names_table_dimensions(self, path: Path, dimension: str) -> None:
        """GIVEN a consumer copy of the structure
        WHEN it stops naming Who, Where, or When
        THEN this fails; that silent drift is what ADR-0021 ended.
        """
        assert dimension in _read(path), (
            f"{path.name} does not mention the {dimension} row. This is the "
            "drift ADR-0021 was written to end."
        )

    @pytest.mark.parametrize(
        "path",
        [PR_PREP_SKILL, PR_AGENT, PREPARE_PR],
        ids=["pr-prep-skill", "pr-agent", "prepare-pr-command"],
    )
    def test_consumer_points_at_source_of_record(self, path: Path) -> None:
        """GIVEN several copies of the same structure
        WHEN a copy stops pointing at modules/pr-template.md
        THEN this fails, leaving no way to tell which copy wins.
        """
        assert "pr-template.md" in _read(path), (
            f"{path.name} must point at modules/pr-template.md so a reader "
            "knows which copy wins when they disagree."
        )

    def test_skill_carries_test_plan_triggers(self) -> None:
        """GIVEN a bug fix needs reproduce, fix, and verify steps
        WHEN pr-prep Step 4 drops that shape
        THEN this fails, and regression tests become demonstrations.
        """
        skill = _read(PR_PREP_SKILL)
        assert "reproduce, fix, and verify" in skill, (
            "pr-prep Step 4 must spell out the bug-fix test plan shape, "
            "including that the reproduce step fails on the parent commit."
        )

    def test_validate_pr_consumes_the_test_plan(self) -> None:
        """GIVEN the author wrote a manual test plan in the PR body
        WHEN validate-pr stops reading the section
        THEN this fails
        AND it fails again if an unrunnable step stops being reported
        as MANUAL, since the plan would silently shrink to whatever CI
        happens to be able to run.
        """
        validate = _read(VALIDATE_PR)
        assert "## Test plan" in validate, (
            "validate-pr must read the PR body's Test plan section. "
            "Generating diff-derived steps while ignoring the author's "
            "manual plan is the parallel-mechanism ADR-0021 avoided."
        )
        assert "MANUAL" in validate, (
            "validate-pr must report an unrunnable step as MANUAL rather "
            "than dropping it, or a plan silently shrinks to what CI can do."
        )


class TestGithubTemplates:
    """The repo's own PRs inherit the structure."""

    def test_default_template_exists(self) -> None:
        """GIVEN a PR opened against this repository
        WHEN .github/PULL_REQUEST_TEMPLATE.md is absent
        THEN this fails, because that PR inherits no structure at all.
        """
        assert DEFAULT_TEMPLATE.exists(), (
            ".github/PULL_REQUEST_TEMPLATE.md is missing, so PRs opened "
            "against this repo inherit nothing."
        )

    @pytest.mark.parametrize("row", TABLE_ROWS)
    def test_default_template_has_table_row(self, row: str) -> None:
        """GIVEN the repo's own default template
        WHEN a facts table row is dropped
        THEN this fails; the repo would stop dogfooding its own rule.
        """
        assert row in _read(DEFAULT_TEMPLATE)

    @pytest.mark.parametrize("section", [*PROSE_SECTIONS, "## Test plan"])
    def test_default_template_has_prose_section(self, section: str) -> None:
        """GIVEN the facts table answers only Who, Where, and When
        WHEN Why, What-and-how, or Test plan leaves the default template
        THEN this fails, keeping the cheap half of the six dimensions
        while dropping the half reviewers cannot reconstruct.
        """
        assert section in _read(DEFAULT_TEMPLATE), (
            f".github/PULL_REQUEST_TEMPLATE.md lost {section}. The facts "
            "table without the prose registers answers the cheap half of "
            "the six dimensions and drops the load-bearing half."
        )

    @pytest.mark.parametrize(
        "variant", ["bugfix.md", "feature.md", "breaking-change.md"]
    )
    def test_variant_exists_and_carries_the_table(self, variant: str) -> None:
        """GIVEN a size-tiered variant selected by ?template=
        WHEN it loses a facts table row
        THEN this fails; a variant is a different emphasis, not a
        different structure.
        """
        body = _read(GITHUB_TEMPLATES / variant)
        for row in TABLE_ROWS:
            assert row in body, f"{variant} lost its {row} row"

    def test_breaking_change_variant_requires_migration_guide(self) -> None:
        """GIVEN a downstream owner reading a breaking change
        WHEN the migration guide is softened to optional
        THEN this fails
        AND it fails again if the external blast radius stops being
        required, since those are the two sections that owner needs.
        """
        body = _read(GITHUB_TEMPLATES / "breaking-change.md")
        assert "## Migration guide" in body, (
            "the breaking-change template must require a migration guide. "
            "It is the one section a downstream owner needs."
        )
        assert "External: REQUIRED" in body, (
            "the breaking-change template must mark the external blast "
            "radius as required, not optional."
        )

    def test_feature_variant_requires_the_rejected_alternative(self) -> None:
        """GIVEN feature.md exists as a separate file from the default
        WHEN its rejected-alternative prompt is removed
        THEN this fails, because the file no longer differs from the
        default template and should be deleted rather than kept.
        """
        body = _read(GITHUB_TEMPLATES / "feature.md")
        assert "the alternative rejected" in body, (
            "the feature template must prompt for the rejected "
            "alternative. Drop it and the variant no longer differs from "
            "the default template, so it should be deleted instead."
        )

    def test_bugfix_variant_requires_a_failing_reproduce_step(self) -> None:
        """GIVEN a bug fix whose test passes on the parent commit
        WHEN the bugfix template stops requiring a failing reproduce
        THEN this fails, admitting tests that demonstrate rather than
        guard against regression.
        """
        body = _read(GITHUB_TEMPLATES / "bugfix.md")
        assert "fail on the parent commit" in body, (
            "the bugfix template must require a reproduce step that fails "
            "before the fix. Otherwise the test demonstrates rather than "
            "guards."
        )


class TestSkillExitCriteria:
    """pr-prep can tell when it is done, per .claude/rules/skill-exit-criteria.

    A skill whose exit criteria drift out of sync with the structure it
    emits will declare done on a description missing half its dimensions.
    These anchor the three criteria added with ADR-0021.
    """

    @pytest.mark.parametrize(
        "criterion",
        [
            "Facts table present with all three rows",
            "Why section grounded",
            "Manual test plan attached",
        ],
        ids=["facts-table", "grounded-why", "manual-plan"],
    )
    def test_exit_criterion_present(self, criterion: str) -> None:
        """GIVEN pr-prep decides when a PR description is done
        WHEN a structural criterion leaves its Exit Criteria
        THEN this fails, since the skill would declare done on a
        description that skipped the check.
        """
        raw = PR_PREP_SKILL.read_text(encoding="utf-8")
        section = raw.split("## Exit Criteria", 1)
        if len(section) < 2:
            pytest.fail("pr-prep SKILL.md lost its Exit Criteria section")
        assert criterion in _normalize(section[1]), (
            f"pr-prep Exit Criteria lost '{criterion}'. Without it the "
            "skill declares done on a description that skipped the check."
        )

    def test_step_four_and_exit_criteria_agree_on_trigger_count(self) -> None:
        """GIVEN the Exit Criteria promises "four triggers in Step 4"
        WHEN Step 4 gains or loses a trigger bullet
        THEN this fails, catching a cross-reference that silently
        became a wrong count.
        """
        raw = PR_PREP_SKILL.read_text(encoding="utf-8")
        step_four = raw.split("## Step 4", 1)[1].split("## Step 5", 1)[0]
        bullets = [ln for ln in step_four.splitlines() if ln.startswith("- ")]
        assert len(bullets) == len(TEST_PLAN_TRIGGERS), (
            f"Step 4 lists {len(bullets)} manual test plan triggers but the "
            f"Exit Criteria promises {len(TEST_PLAN_TRIGGERS)}. Update both "
            "together, or the criterion points at a count that is wrong."
        )


class TestDecisionIsRecorded:
    """The structure is a decision, so it has an ADR with its evidence."""

    def test_adr_exists(self) -> None:
        """GIVEN the structure is a decision, not a preference
        WHEN ADR-0021 is deleted
        THEN this fails, leaving the structure with no recorded rationale.
        """
        assert ADR.exists(), "ADR-0021 is missing"

    @pytest.mark.parametrize(
        "alternative",
        ["Six fixed prose headings", "Dynamic risk-scaled templates"],
        ids=["six-headings", "dynamic-templates"],
    )
    def test_rejected_alternative_recorded(self, alternative: str) -> None:
        """GIVEN a design alternative that was considered and rejected
        WHEN its record leaves the ADR
        THEN this fails, and the alternative gets proposed again.
        """
        assert alternative in _read(ADR), (
            f"ADR-0021 must record why '{alternative}' was rejected, or it "
            "gets proposed again."
        )

    def test_evidence_is_cited(self) -> None:
        """GIVEN the structure rests on empirical findings
        WHEN the understanding-activity citation is dropped
        THEN this fails
        AND it fails again if the patch-size predictor citation goes,
        leaving the structure arbitrary to whoever changes it next.
        """
        adr = _read(ADR)
        assert "Bacchelli" in adr, (
            "ADR-0021 rests on the finding that review is an understanding "
            "activity. Losing the citation makes the structure look "
            "arbitrary."
        )
        assert "arXiv:2109.15141" in adr, (
            "ADR-0021 must keep the citation showing patch size, not "
            "description length, is the validated latency predictor."
        )
