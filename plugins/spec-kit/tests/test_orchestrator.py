"""Contract tests for the speckit-orchestrator skill.

The orchestrator is a markdown skill: its behavior is the session steps,
command-to-skill routing and progress items it states. Each test pins one
of those claims, or checks that the skill, its modules and the commands
that load it agree. These replace tests that asserted attributes of a
``Mock()`` the test had configured itself.
"""

from __future__ import annotations

import re

import pytest

from tests._contract import COMMANDS, SKILLS, frontmatter, read, section

SKILL = "skills/speckit-orchestrator/SKILL.md"
MATRIX = "skills/speckit-orchestrator/modules/command-skill-matrix.md"
PROGRESS = "skills/speckit-orchestrator/modules/progress-tracking.md"
ARTIFACTS = "skills/speckit-orchestrator/modules/artifact-structure.md"
STARTUP = "commands/speckit-startup.md"


def _bare(skill: str) -> str:
    return skill.strip().strip("`").split(":", 1)[-1]


def _skill_table() -> dict[str, tuple[str | None, set[str]]]:
    """Command -> (primary, complementary) from the SKILL.md quick reference."""
    rows = re.findall(
        r"^\| `(/speckit-[a-z]+)` \| ([^|]+) \| ([^|]+) \|$", read(SKILL), re.M
    )
    table: dict[str, tuple[str | None, set[str]]] = {}
    for command, primary, complementary in rows:
        primary = primary.strip()
        table[command] = (
            None if primary == "-" else primary,
            {_bare(s) for s in complementary.split(",")},
        )
    return table


def _module_matrix() -> dict[str, tuple[str | None, set[str]]]:
    """Command -> (primary, complementary) from the command-skill-matrix module."""
    entries = re.findall(
        r"^\*\*`(/speckit-[a-z]+)`\*\*\n- \*\*Primary Skill\*\*: (.+)\n"
        r"- \*\*Complementary Skills\*\*: (.+)$",
        read(MATRIX),
        re.M,
    )
    matrix: dict[str, tuple[str | None, set[str]]] = {}
    for command, primary, complementary in entries:
        complementary_set = (
            set()
            if complementary.startswith("None")
            else {_bare(s) for s in complementary.split(",")}
        )
        matrix[command] = (
            None if primary.startswith("None") else _bare(primary),
            complementary_set,
        )
    return matrix


@pytest.fixture(scope="module")
def skill() -> str:
    return read(SKILL)


class TestSpeckitOrchestrator:
    """Session steps, routing and progress items the orchestrator states."""

    def test_should_verify_repository_context_when_initializing_session(
        self, skill: str
    ) -> None:
        """Session start checks .specify/, in the skill and its progress items."""
        init = skill.split("### Session Initialization", 1)[1]
        assert "- Check for `.specify/` directory structure." in init
        assert "- [ ] Verify repository context and .specify/ structure" in read(
            PROGRESS
        )

    def test_should_detect_missing_directory_when_specify_dir_absent(self) -> None:
        """speckit-startup confirms .specify/ exists before anything else."""
        first_step = read(STARTUP).split("2. **Load Orchestrator Skill**", 1)[0]
        assert (
            "- Confirm `.specify/` directory exists in the project root" in first_step
        )

    def test_should_map_commands_to_correct_skills_when_querying_mapping(self) -> None:
        """The quick-reference table and the matrix module route commands alike."""
        table, matrix = _skill_table(), _module_matrix()
        shared = set(table) & set(matrix)
        assert len(shared) >= 7
        for command in sorted(shared):
            assert table[command] == matrix[command], command

    def test_should_load_primary_and_complementary_skills_when_executing_specify_command(
        self,
    ) -> None:
        """/speckit-specify loads brainstorming, then spec-writing."""
        assert _module_matrix()["/speckit-specify"] == (
            "spec-writing",
            {"brainstorming"},
        )
        specify = read(MATRIX).split("**`/speckit-specify`**", 1)[1]
        assert specify.split("\n- **Loading Order**: ", 1)[1].startswith(
            "brainstorming → spec-writing"
        )
        assert "- [ ] Load spec-writing and brainstorming skills" in read(PROGRESS)

    def test_should_load_task_planning_dependencies_when_executing_plan_command(
        self,
    ) -> None:
        """/speckit-plan loads task-planning with writing-plans."""
        assert _module_matrix()["/speckit-plan"] == ("task-planning", {"writing-plans"})
        assert "- [ ] Load task-planning and writing-plans skills" in read(PROGRESS)

    def test_should_load_only_complementary_skills_when_executing_implement_command(
        self,
    ) -> None:
        """/speckit-implement has no primary skill in either source."""
        expected = (None, {"executing-plans", "systematic-debugging"})
        assert _skill_table()["/speckit-implement"] == expected
        assert _module_matrix()["/speckit-implement"] == expected

    def test_should_open_with_the_progress_items_startup_creates(
        self, skill: str
    ) -> None:
        """The skill and speckit-startup open with the same three progress items."""
        items = re.findall(
            r"^- \[ \] (.+?)\.$", section(skill, "Progress Tracking Items"), re.M
        )
        assert len(items) == 5
        startup_items = re.findall(r"^\s+- \[ \] (.+)$", read(STARTUP), re.M)
        assert startup_items == items[:3]

    def test_should_validate_artifact_consistency_when_checking_related_files(
        self,
    ) -> None:
        """The spec.md layout lists the four sections spec-writing makes mandatory."""
        spec_layout = read(ARTIFACTS).split("### spec.md - Feature Specification", 1)[1]
        spec_layout = spec_layout.split("### plan.md", 1)[0]
        mandatory = re.findall(
            r"^\d\. \*\*(.+?)\*\*",
            section(read("skills/spec-writing/SKILL.md"), "Mandatory Sections"),
            re.M,
        )
        for name in mandatory:
            heading = name.split("/", 1)[0]
            assert f"## {heading}\n" in spec_layout, heading

    def test_should_verify_required_dependencies_when_validating_skill(
        self, skill: str
    ) -> None:
        """Each superpowers skill under Related Skills is a declared dependency."""
        declared = set(frontmatter(SKILL)["dependencies"])
        related = re.findall(
            r"^- `(superpowers:[a-z-]+)`", section(skill, "Related Skills"), re.M
        )
        assert related
        assert set(related) <= declared

    def test_should_run_session_initialization_steps_in_a_fixed_order(
        self, skill: str
    ) -> None:
        """Session initialization runs its four steps in a fixed order."""
        init = skill.split("### Session Initialization", 1)[1].split("###", 1)[0]
        steps = re.findall(r"^\d\. \*\*(.+?)\*\*", init, re.M)
        assert steps == [
            "Verify Repository Context",
            'Load Persistent State ("presence")',
            "Load Command Dependencies",
            "Initialize Progress Tracking",
        ]

    def test_should_name_only_existing_spec_kit_skills_when_mapping_commands(
        self,
    ) -> None:
        """Every plugin-local skill and command in the routing exists on disk."""
        for source in (_skill_table(), _module_matrix()):
            for command, (primary, _complementary) in source.items():
                assert (COMMANDS / f"{command[1:]}.md").is_file(), command
                if primary is not None:
                    assert (SKILLS / primary / "SKILL.md").is_file(), primary

    def test_should_validate_scripts_under_specify_scripts_bash(
        self, skill: str
    ) -> None:
        """The skill validates scripts, and startup names where they live."""
        assert "- Validate required scripts exist." in skill
        assert "- Check for required scripts in `.specify/scripts/bash/`" in read(
            STARTUP
        )

    def test_should_read_the_constitution_for_persistent_state(
        self, skill: str
    ) -> None:
        """Persistent state comes from the constitution, in the skill and startup."""
        assert (
            "- Read `.specify/memory/constitution.md` for constraints/principles."
            in skill
        )
        assert (
            "- Read `.specify/memory/constitution.md` (constraints and principles)"
            in read(STARTUP)
        )

    def test_should_use_the_phase_sequence_speckit_tasks_prescribes(self) -> None:
        """The tasks.md layout uses the phase sequence /speckit-tasks prescribes."""
        layout = read(ARTIFACTS).split("### tasks.md - Implementation Tasks", 1)[1]
        phases = re.findall(r"^## (Phase \d|Final Phase): (.+)$", layout, re.M)
        assert phases[:2] == [("Phase 1", "Setup"), ("Phase 2", "Foundational")]
        assert phases[2][1].startswith("User Story 1 (P1)")
        tasks_command = read("commands/speckit-tasks.md")
        assert "- **Phase 1**: Setup (project initialization)" in tasks_command
        assert "- **Phase 2**: Foundational" in tasks_command
