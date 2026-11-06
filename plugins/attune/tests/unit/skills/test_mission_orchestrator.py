"""BDD tests for the attune mission-orchestrator router.

Feature: Mission Orchestrator Router Validation
  As a plugin developer
  I want the mission-orchestrator to stay a router table
  So that it detects the phase and calls the phase skill, and nothing else

Issue #989: 31 logged runs read zero of the skill's 12 modules, so the
SKILL.md body is the whole skill. These tests pin that body.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ATTUNE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PLUGINS_DIR = ATTUNE_DIR.parent
SKILL_DIR = ATTUNE_DIR / "skills" / "mission-orchestrator"
SKILL_FILE = SKILL_DIR / "SKILL.md"

BUILD_PHASE_SKILLS = {
    "brainstorm": "Skill(attune:project-brainstorming)",
    "specify": "Skill(attune:project-specification)",
    "plan": "Skill(attune:project-planning)",
    "execute": "Skill(attune:project-execution)",
}

REVIEW_PHASE_SKILLS = {
    "scope": "Skill(pensive:tiered-audit)",
    "investigate": "Skill(imbue:feature-review)",
    "verify": "Skill(imbue:proof-of-work)",
    "report": "Skill(imbue:structured-output)",
}

DELETED_MODULES = [
    "mission-types.md",
    "state-detection.md",
    "phase-routing.md",
    "mission-state.md",
    "plan-review.md",
    "plan-versioner.md",
    "feedback-collector.md",
    "context-injector.md",
    "iteration-governor.md",
    "reflexion-buffer.md",
    "trust-tier.md",
    "adaptive-constraints.md",
]

REQUIRED_SECTIONS = [
    "## Overview",
    "## When To Use",
    "## Exit Criteria",
]


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


def _body() -> str:
    content = SKILL_FILE.read_text()
    return content[content.index("---", 3) + 3 :]


def _row(text: str, first_cell: str) -> str:
    """Return the table row whose first cell is ``first_cell``."""
    for line in text.splitlines():
        if line.startswith(f"| {first_cell} "):
            return line
    raise AssertionError(f"no table row starts with {first_cell!r}")


class TestMissionOrchestratorSkillFile:
    """Feature: Skill file existence."""

    @pytest.mark.bdd
    def test_skill_file_exists_and_is_not_empty(self) -> None:
        """Given the attune plugin, the router SKILL.md exists with content."""
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"
        assert SKILL_FILE.read_text().strip(), "SKILL.md is empty"


class TestMissionOrchestratorFrontmatter:
    """Feature: Frontmatter matches a flat router."""

    @pytest.mark.bdd
    def test_frontmatter_has_name(self) -> None:
        """The harness resolves the skill by this name."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm.get("name") == "mission-orchestrator"

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """An empty description gives the router nothing to match on."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert len(fm.get("description", "")) > 20

    @pytest.mark.bdd
    def test_frontmatter_category_is_workflow(self) -> None:
        """The category groups the skill with the other orchestrators."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert fm.get("category") == "workflow-orchestration"

    @pytest.mark.bdd
    def test_frontmatter_declares_no_modules_or_references(self) -> None:
        """Given the flattened skill, frontmatter lists nothing to load."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert "modules" not in fm, "router must not declare modules"
        assert "references" not in fm, "router must not declare references"
        assert not fm.get("progressive_loading"), (
            "progressive_loading has nothing to load once modules are gone"
        )

    @pytest.mark.bdd
    def test_every_dependency_resolves_to_a_skill(self) -> None:
        """Given the dependencies list, each names a SKILL.md on disk."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        for dep in fm.get("dependencies", []):
            plugin, name = dep.split(":", 1)
            target = PLUGINS_DIR / plugin / "skills" / name / "SKILL.md"
            assert target.exists(), f"dependency {dep} does not resolve"

    @pytest.mark.bdd
    def test_every_dependency_is_named_in_the_body(self) -> None:
        """A dependency the body never calls is graph fan-out with no use."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        body = _body()
        for dep in fm.get("dependencies", []):
            assert dep in body, f"dependency {dep} is never named in the body"

    @pytest.mark.bdd
    def test_orchestrator_depends_on_bias_defense(self) -> None:
        """leyline:additive-bias-defense lists this skill as a consumer."""
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert "leyline:additive-bias-defense" in fm.get("dependencies", [])


class TestMissionOrchestratorSections:
    """Feature: Required sections."""

    @pytest.mark.bdd
    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_has_required_section(self, section: str) -> None:
        """A router missing one of these cannot be audited (#454)."""
        assert section in SKILL_FILE.read_text(), f"missing {section}"


class TestFlattened:
    """Feature: The skill is one file.

    Issue #989 measured zero module reads in 31 runs. A module that
    comes back is content nobody will load.
    """

    @pytest.mark.bdd
    def test_modules_directory_is_gone(self) -> None:
        """A restored modules/ directory would undo the flattening."""
        assert not (SKILL_DIR / "modules").exists()

    @pytest.mark.bdd
    def test_references_directory_is_gone(self) -> None:
        """The charter and report templates were folded into SKILL.md."""
        assert not (SKILL_DIR / "references").exists()

    @pytest.mark.bdd
    def test_skill_directory_holds_only_skill_md(self) -> None:
        """Any second file is content the router never loads."""
        entries = sorted(p.name for p in SKILL_DIR.iterdir())
        assert entries == ["SKILL.md"], f"unexpected files: {entries}"

    @pytest.mark.bdd
    @pytest.mark.parametrize("module", DELETED_MODULES)
    def test_body_does_not_point_at_a_deleted_module(self, module: str) -> None:
        """A pointer to a removed module sends the reader nowhere."""
        assert module not in SKILL_FILE.read_text()

    @pytest.mark.bdd
    def test_no_attune_file_links_into_deleted_dirs(self) -> None:
        """Repointed links: nothing in attune reaches into the old dirs."""
        pattern = re.compile(r"mission-orchestrator/(modules|references)/")
        offenders = [
            str(p.relative_to(ATTUNE_DIR))
            for p in ATTUNE_DIR.rglob("*.md")
            if pattern.search(p.read_text())
        ]
        assert offenders == [], f"links into deleted dirs: {offenders}"


class TestMissionOrchestratorPluginRegistration:
    """Feature: Plugin registry integration."""

    @pytest.mark.bdd
    def test_skill_registered_in_plugin_json(self) -> None:
        """An unregistered skill is invisible to /attune:mission."""
        plugin_json = ATTUNE_DIR / ".claude-plugin" / "plugin.json"
        config = json.loads(plugin_json.read_text())
        assert any("mission-orchestrator" in s for s in config.get("skills", []))


class TestRouterTable:
    """Feature: Each phase routes to one named skill."""

    @pytest.mark.bdd
    @pytest.mark.parametrize(("phase", "skill"), BUILD_PHASE_SKILLS.items())
    def test_build_phase_routes_to_its_skill(self, phase: str, skill: str) -> None:
        """Each build phase row names the skill that runs it."""
        assert skill in _row(_body(), phase)

    @pytest.mark.bdd
    @pytest.mark.parametrize(("phase", "skill"), REVIEW_PHASE_SKILLS.items())
    def test_review_phase_routes_to_its_skill(self, phase: str, skill: str) -> None:
        """Each review phase row names the skill that runs it."""
        assert skill in _row(_body(), phase)

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        "call", [*BUILD_PHASE_SKILLS.values(), *REVIEW_PHASE_SKILLS.values()]
    )
    def test_phase_skill_targets_exist(self, call: str) -> None:
        """A routed Skill() call must resolve, or the phase cannot start."""
        plugin, name = call[len("Skill(") : -1].split(":")
        assert (PLUGINS_DIR / plugin / "skills" / name / "SKILL.md").exists()

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        ("mission_type", "signal"),
        [
            ("quickfix", "docs/implementation-plan.md"),
            ("tactical", "docs/specification.md"),
            ("standard", "docs/project-brief.md"),
        ],
    )
    def test_type_row_names_its_detection_artifact(
        self, mission_type: str, signal: str
    ) -> None:
        """Type detection keys on the artifact each row names."""
        assert signal in _row(_body(), f"`{mission_type}`")

    @pytest.mark.bdd
    def test_full_mission_leads_with_brainstorm(self) -> None:
        """A full mission specifies only after brainstorming."""
        row = _row(_body(), "`full`")
        assert row.find("brainstorm") < row.find("specify")

    @pytest.mark.bdd
    def test_review_is_detected_before_the_artifact_ladder(self) -> None:
        """Leftover build artifacts must not select quickfix for audit work.

        Discussion #586: a tree full of plans looks the same whether the
        ask is "ship this" or "audit this".
        """
        body = _body()
        review_at = body.index(_row(body, "`review`"))
        quickfix_at = body.index(_row(body, "`quickfix`"))
        assert review_at < quickfix_at, "review row must be checked first"
        assert "request intent" in body

    @pytest.mark.bdd
    def test_review_names_its_output_artifact(self) -> None:
        """The report path is the review mission's exit artifact."""
        assert "reports/<topic>-<YYYY-MM-DD>.md" in _row(_body(), "report")


class TestPlanToExecuteGate:
    """Feature: The plan is challenged before execution.

    leyline:additive-bias-defense names this skill as the consumer that
    scans plan sections before user review.
    """

    @pytest.mark.bdd
    def test_gate_scans_for_additive_bias(self) -> None:
        """additive-bias-defense names this gate as its consumer."""
        assert "Skill(leyline:additive-bias-defense)" in _body()

    @pytest.mark.bdd
    def test_gate_requires_war_room_approval(self) -> None:
        """Execution waits on the war-room verdict for the plan."""
        assert "Skill(attune:war-room)" in _body()

    @pytest.mark.bdd
    def test_review_missions_skip_the_gate(self) -> None:
        """A review produces no plan, so there is nothing to gate."""
        body = re.sub(r"\s+", " ", _body())
        assert "never enters the war-room gate" in body


class TestDirectiveOverrides:
    """Feature: Natural-language trust signals and the safety floor."""

    @pytest.mark.bdd
    def test_skill_documents_user_directive_overrides(self) -> None:
        """Users relax checkpoints in plain language, not flags."""
        assert "User Directive Override" in _body()

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        "phrase", ["ignore scope guard", "ultrathink", "be autonomous"]
    )
    def test_canonical_trust_phrases_are_listed(self, phrase: str) -> None:
        """Each phrase must be recognized as an override."""
        assert phrase in _body()

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        "floor", ["pre-commit hooks", "proof-of-work", "destructive"]
    )
    def test_safety_floor_survives_overrides(self, floor: str) -> None:
        """No directive may switch these checks off."""
        assert floor in _body()


class TestStateContract:
    """Feature: The state file callers write and resume from.

    skill-library-mission writes a custom mission into the same file,
    so the field names are a contract between the two skills.
    """

    @pytest.mark.bdd
    def test_names_the_state_file(self) -> None:
        """Resume reads this path, and skill-library-mission writes it."""
        assert ".attune/mission-state.json" in _body()

    @pytest.mark.bdd
    @pytest.mark.parametrize(
        "field",
        [
            "mission_id",
            "type",
            "phases",
            "current_phase",
            "decisions",
            "directive_overrides",
        ],
    )
    def test_state_field_is_named(self, field: str) -> None:
        """Each field is part of the contract shared with skill-library-mission."""
        assert f"`{field}`" in _body()


class TestBrainstormSocraticWiring:
    """Feature: The brainstorm phase keeps its Socratic method.

    These guards pin the brainstorm to Socratic chain end to end, so a
    refactor cannot unwire ideation from the lifecycle.
    """

    _BRAINSTORM_SKILL = ATTUNE_DIR / "skills" / "project-brainstorming" / "SKILL.md"

    @pytest.mark.bdd
    def test_brainstorming_skill_retains_socratic_methodology(self) -> None:
        """The brainstorm phase must keep its probing questions."""
        content = self._BRAINSTORM_SKILL.read_text()
        assert "socratic" in content.lower()
        for marker in ("Probing Assumptions", "Probing Reasoning"):
            assert marker in content, f"'{marker}' stripped from brainstorming"

    @pytest.mark.bdd
    def test_brainstorming_skill_delegates_socratic_to_superpowers(self) -> None:
        """The Socratic method comes from superpowers, not a local copy."""
        content = self._BRAINSTORM_SKILL.read_text()
        assert "Skill(superpowers:brainstorming)" in content


class TestMissionCommand:
    """Feature: /attune:mission still invokes the router."""

    _COMMAND = ATTUNE_DIR / "commands" / "mission.md"

    @pytest.mark.bdd
    def test_command_invokes_the_skill(self) -> None:
        """/attune:mission must reach the router."""
        assert "Skill(attune:mission-orchestrator)" in self._COMMAND.read_text()

    @pytest.mark.bdd
    def test_command_documents_the_review_type(self) -> None:
        """The command lists review so users can request it."""
        assert "`review`" in self._COMMAND.read_text()
