"""Contract tests for the behaviors ported from github/spec-kit v1.4.0.

The plugin last synced with upstream v0.5.0. Each test anchors on the
clause that carries one ported behavior, so deleting that clause turns
the test red. The upstream PR is named in each docstring because the
plugin re-implements the commands rather than vendoring them, and the
PR is where a future sync checks whether the behavior moved again.
"""

from __future__ import annotations

import json

import yaml

from ._contract import PLUGIN_ROOT, read, section


def prose(relative: str) -> str:
    """Return a file with whitespace collapsed, so line wrapping cannot hide a clause."""
    return " ".join(read(relative).split())


class TestConstitutionIsReadAtRuntime:
    """Upstream #3790 and #2460: commands read the constitution themselves."""

    def test_implement_loads_constitution_for_governance(self) -> None:
        text = read("commands/speckit-implement.md")
        assert ".specify/memory/constitution.md" in text

    def test_tasks_loads_constitution_for_governance(self) -> None:
        text = read("commands/speckit-tasks.md")
        assert ".specify/memory/constitution.md" in text

    def test_clarify_loads_constitution_for_governance(self) -> None:
        text = read("commands/speckit-clarify.md")
        assert ".specify/memory/constitution.md" in text


class TestConstitutionCommandStaysInScope:
    """Upstream #3646, #3790 and #4432."""

    def test_constitution_no_longer_propagates_into_templates(self) -> None:
        text = read("commands/speckit-constitution.md")
        assert "propagate any amendments across dependent artifacts" not in text
        assert "syncing dependent templates" not in text

    def test_constitution_refuses_feature_work_as_deferred_intent(self) -> None:
        guard = section(read("commands/speckit-constitution.md"), "Scope Guard")
        assert "MUST NOT" in guard
        assert "Next Actions" in guard

    def test_sync_impact_report_is_review_only(self) -> None:
        text = read("commands/speckit-constitution.md")
        assert "removed before the amended constitution file is committed" in text


class TestClarifyQuestionQuality:
    """Upstream #3745, #4507 and #2715."""

    def test_every_question_is_a_real_interrogative(self) -> None:
        text = read("commands/speckit-clarify.md")
        assert "**Question:**" in text
        assert "Why it matters" in text

    def test_defer_to_planning_is_limited_to_method_stack_and_breakdown(
        self,
    ) -> None:
        text = read("commands/speckit-clarify.md")
        assert "Information is better deferred to planning phase" not in text
        assert "implementation method, tech-stack comparison, or task breakdown" in text

    def test_clarify_revalidates_spec_quality_checklist(self) -> None:
        text = read("commands/speckit-clarify.md")
        assert "checklists/requirements.md" in text
        assert "Regressions" in text


class TestImplementTreatsChecklistsAsReadOnlyGate:
    """Upstream checklist-ownership change (0.16.3 #4028)."""

    def test_implement_does_not_modify_checklist_markers(self) -> None:
        text = read("commands/speckit-implement.md")
        assert "NOT modify checklist files or markers" in text

    def test_checked_box_does_not_mean_implementation_done(self) -> None:
        text = read("commands/speckit-implement.md")
        assert "does NOT mean implementation work is complete" in text


class TestTasksQuoteDataModelConstraints:
    """Upstream #4430."""

    def test_field_constraints_are_quoted_verbatim(self) -> None:
        text = read("commands/speckit-tasks.md")
        assert "quote the constraint verbatim" in text


class TestConvergeDistrustsCompletionClaims:
    """Upstream #4621."""

    def test_every_task_is_assessed_regardless_of_checkbox(self) -> None:
        text = prose("commands/speckit-converge.md")
        assert "regardless of checkbox state" in text

    def test_completion_claims_are_not_evidence(self) -> None:
        text = prose("commands/speckit-converge.md")
        assert "completion claims are not evidence" in text


class TestManifestsAgree:
    """openpackage.yml and plugin.json must ship the same commands."""

    def test_openpackage_lists_every_plugin_json_command(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8",
            ),
        )
        package = yaml.safe_load(
            (PLUGIN_ROOT / "openpackage.yml").read_text(encoding="utf-8"),
        )
        shipped = {path.removeprefix("./") for path in manifest["commands"]}
        assert shipped == set(package["commands"])


class TestChecklistOwnership:
    """Upstream #4028: a reviewer owns checklist checkboxes."""

    def test_generated_items_are_left_unchecked(self) -> None:
        text = prose("commands/speckit-checklist.md")
        assert "MUST NOT mark generated items `[x]`" in text

    def test_checklist_loads_constitution(self) -> None:
        assert ".specify/memory/constitution.md" in read(
            "commands/speckit-checklist.md"
        )


class TestSpecifyLoadsConstitution:
    """Upstream 1.2.6 (#5187) composed specify around the constitution read."""

    def test_specify_loads_constitution(self) -> None:
        assert ".specify/memory/constitution.md" in read("commands/speckit-specify.md")


class TestPlanQuickstartIsAValidationGuide:
    """Upstream #2805: quickstart.md proves the feature runs; it holds no implementation."""

    def test_plan_has_a_step_that_writes_quickstart(self) -> None:
        text = prose("commands/speckit-plan.md")
        assert "quickstart validation guide" in text

    def test_quickstart_excludes_implementation_code(self) -> None:
        text = prose("commands/speckit-plan.md")
        assert "Do not include full implementation code" in text
