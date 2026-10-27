"""Contract tests for the task-planning skill, its agent and /speckit-tasks.

Each test pins a rule stated in ``skills/task-planning``,
``agents/task-generator.md`` or ``commands/speckit-tasks.md``, or checks
that the worked examples in those files obey the rules stated beside
them. These replace tests that checked conftest task lists against
themselves and could not fail.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pytest

from tests._contract import headings, read, section

SKILL = "skills/task-planning/SKILL.md"
PHASES = "skills/task-planning/modules/phase-structure.md"
DEPENDENCIES = "skills/task-planning/modules/dependency-patterns.md"
AGENT = "agents/task-generator.md"
COMMAND = "commands/speckit-tasks.md"

PHASE_NAMES = ["Setup", "Foundation", "Core Implementation", "Integration", "Polish"]
TASK_HEADING = re.compile(r"^### (T\d{3}) - (.+?)( \[P\])?$")
DEPENDS = re.compile(r"^\*\*Dependencies\*\*: (.+)$")
CHECKLIST_LINE = re.compile(
    r"^- \[ \] T\d{3}( \[P\])?( \[US\d+\])?( \[R:(GREEN|YELLOW|RED|CRITICAL)\])? \S.*$"
)


@dataclass
class ExampleTask:
    task_id: str
    parallel: bool
    depends: list[str] = field(default_factory=list)

    @property
    def number(self) -> int:
        return int(self.task_id[1:])


def _example_tasks() -> list[ExampleTask]:
    """Every worked task entry in the skill and its modules.

    IDs repeat across examples, so each fenced block is read on its own.
    """
    tasks: list[ExampleTask] = []
    for relative in (SKILL, PHASES, DEPENDENCIES):
        for block in re.findall(r"```\w*\n(.*?)```", read(relative), re.DOTALL):
            current: ExampleTask | None = None
            for line in block.splitlines():
                heading = TASK_HEADING.match(line)
                if heading:
                    current = ExampleTask(heading.group(1), bool(heading.group(3)))
                    tasks.append(current)
                    continue
                depends = DEPENDS.match(line)
                if depends and current is not None:
                    value = depends.group(1).strip()
                    if value != "None":
                        current.depends = [v.strip() for v in value.split(",")]
    return tasks


def _number(task_id: str) -> int:
    return int(task_id[1:])


def _flat(text: str) -> str:
    return " ".join(text.split())


@pytest.fixture(scope="module")
def skill() -> str:
    return read(SKILL)


@pytest.fixture(scope="module")
def phases() -> str:
    return read(PHASES)


@pytest.fixture(scope="module")
def dependencies() -> str:
    return read(DEPENDENCIES)


@pytest.fixture(scope="module")
def command() -> str:
    return read(COMMAND)


class TestTaskPlanning:
    """The rules tasks are generated, ordered and validated against."""

    def test_should_maintain_phase_order_when_organizing_tasks(
        self, skill: str
    ) -> None:
        """The skill, its phase module and the agent list the same five phases."""
        listed = re.findall(
            r"^- \*\*Phase (\d): (.+?)\*\*", section(skill, "Task Phases"), re.M
        )
        assert listed == [(str(i), name) for i, name in enumerate(PHASE_NAMES, start=1)]
        expected = [f"Phase {i}: {name}" for i, name in enumerate(PHASE_NAMES, start=1)]
        for relative in (PHASES, AGENT):
            found = [h for h in headings(read(relative), 3) if h.startswith("Phase ")]
            assert found == expected, relative

    def test_should_include_all_required_fields_when_validating_tasks(
        self, skill: str
    ) -> None:
        """Task Format and the Exit Criteria name the same fields."""
        fields = re.findall(r"^- \*\*(.+?)\*\*:", section(skill, "Task Format"), re.M)
        assert fields == [
            "ID",
            "Description",
            "Phase",
            "Dependencies",
            "Parallel Marker",
            "Files",
            "Criteria",
        ]
        exit_criteria = _flat(section(skill, "Exit Criteria"))
        for name in (
            "Description",
            "Phase (1-5)",
            "Dependencies list",
            "Files",
            "Criteria",
        ):
            assert name in exit_criteria, name

    def test_should_store_dependencies_as_list_when_defining_tasks(
        self, dependencies: str
    ) -> None:
        """Multiple dependencies are one comma-separated line."""
        multiple = section(dependencies, "Multiple Dependencies")
        assert "**Dependencies**: T001, T003, T007" in multiple

    def test_should_reference_valid_tasks_when_defining_dependencies(
        self, dependencies: str
    ) -> None:
        """The validation rules require every referenced ID to exist."""
        assert "- [ ] All referenced task IDs exist" in section(
            dependencies, "Validation Rules"
        )

    def test_should_have_setup_phase_when_organizing_tasks(self, phases: str) -> None:
        """Phase 1 is Setup: project initialization, with T001 as its example."""
        setup = phases.split("### Phase 1: Setup", 1)[1].split("### Phase 2:", 1)[0]
        assert "- Project initialization" in setup
        assert "### T001 - " in setup

    def test_should_allow_sequential_dependencies_when_in_setup_phase(
        self, dependencies: str
    ) -> None:
        """The sequential example is a chain: each task depends on the previous."""
        chain = dependencies.split("### Sequential Dependencies", 1)[1]
        chain = chain.split("### Parallel Dependencies", 1)[0]
        pairs = re.findall(
            r"^### (T\d{3}) .*\n\*\*Dependencies\*\*: (T\d{3})$", chain, re.M
        )
        assert pairs
        for task_id, dep in pairs:
            assert _number(dep) == _number(task_id) - 1, (task_id, dep)

    def test_should_use_valid_priority_when_setting_task_priority(
        self, command: str
    ) -> None:
        """User-story phases follow the spec's priority order P1, P2, P3."""
        assert "One phase per user story (in priority order from spec.md)" in command
        assert "User Stories in priority order (P1, P2, P3...)" in command

    def test_should_estimate_complexity_when_generating_tasks(self) -> None:
        """The task-generator agent estimates complexity and reports it."""
        agent = read(AGENT)
        assert "- Estimate task complexity" in section(agent, "Capabilities")
        assert "- Estimated complexity" in section(agent, "Output")

    def test_should_detect_cycle_when_dependencies_are_circular(
        self, dependencies: str
    ) -> None:
        assert "- [ ] No circular dependencies" in section(
            dependencies, "Validation Rules"
        )

    def test_should_not_detect_cycle_when_dependencies_are_valid(self) -> None:
        """Every worked example depends only on lower-numbered tasks, so none cycles."""
        tasks = _example_tasks()
        assert len(tasks) >= 20
        for task in tasks:
            for dep in task.depends:
                assert _number(dep) < task.number, (task.task_id, dep)

    def test_should_identify_parallel_tasks_when_no_dependencies_exist(
        self, skill: str
    ) -> None:
        """[P] requires five named conditions, and the Exit Criteria count five."""
        rules = section(skill, "Dependency Rules")
        conditions = re.findall(r"^- ✅ (\w[\w ]*):", rules, re.M)
        assert conditions == ["Files", "State", "Dependencies", "Code paths", "Outputs"]
        assert "pass all 5 nonconflicting criteria" in _flat(
            section(skill, "Exit Criteria")
        )

    def test_should_find_entry_points_when_analyzing_critical_path(
        self, dependencies: str
    ) -> None:
        """In the fan-out example every [P] task hangs off the single entry T001."""
        fan_out = dependencies.split("### Fan-Out Pattern", 1)[1]
        fan_out = fan_out.split("### Fan-In Pattern", 1)[0]
        parallel = re.findall(
            r"^### T\d{3} - .+ \[P\]\n\*\*Dependencies\*\*: (.+)$", fan_out, re.M
        )
        assert parallel == ["T001", "T001", "T001"]

    def test_should_be_longer_than_title_when_writing_description(
        self, skill: str, command: str
    ) -> None:
        """The skill asks for an action statement, the command for a file path too."""
        assert "- **Description**: Clear action statement" in skill
        assert "6. **Description**: Clear action with exact file path" in command

    def test_should_avoid_vague_words_when_writing_descriptions(
        self, command: str
    ) -> None:
        """Each CORRECT example matches the stated format; the malformed WRONG ones fail it."""
        correct = re.findall(r"^- CORRECT: `(.+)`$", command, re.M)
        wrong = dict(re.findall(r"^- WRONG: `(.+)` \((.+)\)$", command, re.M))
        assert len(correct) >= 5
        for line in correct:
            assert CHECKLIST_LINE.match(line), line
        malformed = [
            line
            for line, why in wrong.items()
            if why in {"missing checkbox", "missing Task ID"}
        ]
        assert len(malformed) == 2
        for line in malformed:
            assert not CHECKLIST_LINE.match(line), line

    def test_should_start_with_action_verb_when_writing_descriptions(
        self, command: str
    ) -> None:
        """Each CORRECT example's description, after its labels, opens with a verb."""
        for line in re.findall(r"^- CORRECT: `(.+)`$", command, re.M):
            description = re.sub(r"^- \[ \] T\d{3}( \[[^\]]+\])*\s+", "", line)
            assert description.split()[0] in {"Create", "Implement", "Add"}, line

    def test_should_contain_appropriate_tasks_when_in_specific_phase(
        self, phases: str
    ) -> None:
        """Phase mixing and skipping are named anti-patterns."""
        anti = section(phases, "Anti-Patterns to Avoid")
        assert "**Phase mixing**" in anti
        assert "**Skipping phases**: Every feature needs at least Phase 2" in anti

    def test_should_not_exceed_max_days_when_estimating_large_tasks(
        self, phases: str
    ) -> None:
        """Features of 20+ tasks are a signal to split the feature."""
        large = phases.split("**Large Features** (20+ tasks):", 1)[1]
        assert large.lstrip().startswith("- Consider breaking into multiple features")

    def test_should_meet_minimum_duration_when_estimating_small_tasks(
        self, phases: str
    ) -> None:
        """Small features usually skip Setup because the project exists."""
        small = phases.split("**Small Features** (5-10 tasks):", 1)[1]
        assert small.lstrip().startswith("- Phase 1: Usually skipped (project exists)")

    def test_should_follow_naming_pattern_when_assigning_task_ids(
        self, dependencies: str
    ) -> None:
        """IDs are TNNN, zero-padded to three digits, and TASK-NNN is gone."""
        assert "**Pattern**: `TNNN` where NNN is zero-padded number" in dependencies
        for relative in (SKILL, PHASES, DEPENDENCIES, AGENT, COMMAND):
            text = read(relative)
            assert not re.search(r"TASK-\d", text), relative
            for task_id in re.findall(r"\bT\d+\b", text):
                assert re.fullmatch(r"T\d{3}", task_id), (relative, task_id)

    def test_should_prevent_forward_dependencies_when_organizing_phases(
        self, skill: str, dependencies: str
    ) -> None:
        """Dependencies point back to earlier work, stated in two places."""
        assert "- [ ] Tasks reference dependencies from earlier phases" in dependencies
        assert "no task depends on one with a higher task number" in _flat(
            section(skill, "Exit Criteria")
        )

    def test_should_declare_none_when_task_has_no_dependencies(
        self, dependencies: str
    ) -> None:
        """A task with no dependencies says None rather than omitting the field."""
        assert "**Dependencies**: None" in section(dependencies, "No Dependencies")

    def test_should_reject_missing_dependencies_when_validating_tasks(
        self, dependencies: str
    ) -> None:
        """Every task needs an explicit dependency field."""
        assert "- [ ] Every task has explicit dependency field" in section(
            dependencies, "Validation Rules"
        )

    def test_agent_and_command_agree_on_the_task_id_format(self, command: str) -> None:
        """The agent that writes tasks.md uses the ID format the command defines."""
        assert "Task ID**: Sequential number (T001, T002, T003...)" in command
        assert "T001" in section(read(AGENT), "Task Format")
