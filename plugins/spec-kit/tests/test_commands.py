"""Contract tests for the spec-kit slash commands.

The commands are markdown instructions, so their behavior is what the
files tell the session to do. Each test pins a rule a command states, or
checks that two files which hand work to each other agree. The specify,
plan, implement, analyze and checklist classes replace tests that
compared keyword lists declared in the test body with conftest fixtures
and could not fail.
"""

import json
import re
from pathlib import Path

from tests._contract import read

SPECIFY = "commands/speckit-specify.md"
CLARIFY = "commands/speckit-clarify.md"
PLAN = "commands/speckit-plan.md"
IMPLEMENT = "commands/speckit-implement.md"
ANALYZE = "commands/speckit-analyze.md"
CHECKLIST = "commands/speckit-checklist.md"
CONVERGE = "commands/speckit-converge.md"
DIMENSIONS = "skills/spec-writing/modules/checklist-dimensions.md"


class TestSpeckitCommands:
    """Test cases for speckit commands."""

    class TestSpecifyCommand:
        """Rules /speckit-specify states for naming, numbering and the script."""

        def test_should_extract_keywords_for_branch_name_when_given_feature_description(
            self,
        ) -> None:
            """The short name is 2-4 words built from the description's keywords."""
            specify = read(SPECIFY)
            assert (
                "1. **Generate a concise short name** (2-4 words) for the branch:"
                in specify
            )
            assert "extract the most meaningful keywords" in specify

        def test_should_match_expected_patterns_when_generating_short_name(
            self,
        ) -> None:
            """Every worked example yields a 2-4 word kebab-case short name."""
            examples = re.findall(r'^\s+- "(.+)" → "(.+)"$', read(SPECIFY), re.M)
            assert len(examples) == 4
            for description, short_name in examples:
                assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+){1,3}", short_name), (
                    description
                )

        def test_should_reject_empty_description_when_validating_input(self) -> None:
            """An empty command is the one case where the user is asked again."""
            specify = read(SPECIFY)
            assert (
                "Do not ask the user to repeat it unless they provided an empty command."
                in specify
            )
            assert 'If empty: ERROR "No feature description provided"' in specify

        def test_should_reject_vague_description_when_validating_input(self) -> None:
            """A vague requirement must fail the testable-and-unambiguous item."""
            specify = read(SPECIFY)
            assert "Every vague requirement should fail the" in specify
            assert "- [ ] Requirements are testable and unambiguous" in specify

        def test_should_keep_acronyms_in_short_name_examples(
            self,
        ) -> None:
            """Short-name examples keep acronyms the description contained."""
            specify = read(SPECIFY)
            assert (
                "- Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)"
                in specify
            )
            assert (
                '"Implement OAuth2 integration for the API" → "oauth2-api-integration"'
                in specify
            )

        def test_should_increment_branch_number_when_existing_branches_found(
            self,
        ) -> None:
            """The next number is one above the highest across all three sources."""
            specify = read(SPECIFY)
            assert "- Find the highest number N" in specify
            assert "- Use N+1 for the new branch number" in specify
            assert (
                "Check all three sources (remote branches, local branches, specs directories)"
                in specify
            )

        def test_should_default_to_1_when_no_existing_branches_found(self) -> None:
            assert (
                "If no existing branches/directories found with this short-name, start with number 1"
                in read(SPECIFY)
            )

        def test_should_call_script_with_correct_args_when_creating_feature(
            self,
        ) -> None:
            """The feature script gets --json, --number and --short-name, once."""
            specify = read(SPECIFY)
            assert (
                '`.specify/scripts/bash/create-new-feature.sh --json "$ARGUMENTS"`'
                in specify
            )
            assert (
                '- Pass `--number N+1` and `--short-name "your-short-name"`' in specify
            )
            assert "You must only ever run this script once per feature" in specify

        def test_should_read_branch_and_spec_paths_from_script_json(self) -> None:
            """Paths come from the script's JSON, not from guesses."""
            specify = read(SPECIFY)
            assert (
                "The JSON output will contain BRANCH_NAME and SPEC_FILE paths"
                in specify
            )
            assert "5. Write the specification to SPEC_FILE" in specify

    class TestPlanCommand:
        """Rules /speckit-plan states for inputs, gates and outputs."""

        def test_should_read_feature_paths_from_setup_plan_json(self) -> None:
            """setup-plan.sh supplies FEATURE_SPEC and the other paths as JSON."""
            assert (
                "Run `.specify/scripts/bash/setup-plan.sh --json` from repo root and parse "
                "JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH." in read(PLAN)
            )

        def test_should_fail_when_spec_file_missing(self) -> None:
            """Clarify refuses to create a spec, and plan errors on open questions."""
            assert (
                "- If spec file missing, instruct user to run `/speckit-specify` first "
                "(do not create a new spec here)." in read(CLARIFY)
            )
            assert "- ERROR on gate failures or unresolved clarifications" in read(PLAN)

        def test_should_load_spec_and_constitution_before_filling_the_plan(
            self,
        ) -> None:
            """Planning reads the spec and the constitution before filling the plan."""
            assert (
                "2. **Load context**: Read FEATURE_SPEC and `.specify/memory/constitution.md`."
                in read(PLAN)
            )

        def test_should_evaluate_constitution_gates_before_and_after_design(
            self,
        ) -> None:
            """Constitution gates are evaluated before and after design."""
            plan = read(PLAN)
            assert "- Evaluate gates (ERROR if violations unjustified)" in plan
            assert "- Re-evaluate Constitution Check post-design" in plan

        def test_should_write_the_artifacts_implement_reads(self) -> None:
            """The artifacts plan writes are the ones implement reads if present."""
            plan, implement = read(PLAN), read(IMPLEMENT)
            assert (
                "**Output**: research.md with all NEEDS CLARIFICATION resolved" in plan
            )
            assert "**Output**: data-model.md, /contracts/*, quickstart.md" in plan
            for artifact in (
                "data-model.md",
                "contracts/",
                "research.md",
                "quickstart.md",
            ):
                assert f"- **IF EXISTS**: Read {artifact}" in implement, artifact

        def test_should_turn_clarifications_into_research_tasks_and_stop_after_phase_2(
            self,
        ) -> None:
            """Each NEEDS CLARIFICATION becomes a research task, and plan stops after design."""
            plan = read(PLAN)
            assert "- For each NEEDS CLARIFICATION → research task" in plan
            assert (
                "4. **Stop and report**: Command ends after Phase 2 planning." in plan
            )

    class TestImplementCommand:
        """Rules /speckit-implement states for readiness and execution."""

        def test_should_require_tasks_and_plan_reads(self) -> None:
            """tasks.md and plan.md are required reads."""
            implement = read(IMPLEMENT)
            assert (
                "- **REQUIRED**: Read tasks.md for the complete task list" in implement
            )
            assert "- **REQUIRED**: Read plan.md for tech stack" in implement

        def test_should_demand_tasks_from_the_prerequisite_script(self) -> None:
            """Implement and analyze both demand tasks.md from the prerequisite script."""
            flag = "check-prerequisites.sh --json --require-tasks --include-tasks"
            assert flag in read(IMPLEMENT)
            assert flag in read(ANALYZE)

        def test_should_pass_checklists_only_when_every_item_is_complete(self) -> None:
            """Checklist status is PASS only when every checklist is complete."""
            implement = read(IMPLEMENT)
            assert "- **PASS**: All checklists have 0 incomplete items" in implement
            assert (
                "- **FAIL**: One or more checklists have incomplete items" in implement
            )

        def test_should_stop_and_ask_when_checklists_are_incomplete(self) -> None:
            """Incomplete checklists stop and wait for the user."""
            implement = read(IMPLEMENT)
            assert "- **STOP** and ask:" in implement
            assert (
                '- If user says "no" or "wait" or "stop", halt execution' in implement
            )

        def test_should_invoke_ready_parallel_tasks_in_one_response(self) -> None:
            """Ready [P] tasks run together in one response."""
            assert (
                "When multiple [P] tasks are ready, invoke ALL Task tools in ONE response"
                in read(IMPLEMENT)
            )

        def test_should_halt_on_failed_sequential_task_and_finish_phases_in_order(
            self,
        ) -> None:
            """A failed sequential task halts the run; phases complete in order."""
            implement = read(IMPLEMENT)
            assert "- Halt execution if any non-parallel task fails" in implement
            assert "Complete each phase before moving to the next" in implement

        def test_should_serialize_tasks_that_touch_the_same_file(self) -> None:
            """Implement and the task-planning skill share the same-file rule."""
            assert "Tasks affecting the same files MUST run sequentially" in read(
                IMPLEMENT
            )
            assert "Tasks affecting same files MUST run sequentially" in read(
                "skills/task-planning/SKILL.md"
            )

        def test_should_mark_completed_tasks_so_converge_can_tell_them_apart(
            self,
        ) -> None:
            """Implement marks done tasks [X], which is how converge reads them."""
            assert "make sure to mark the task off as [X] in the tasks file" in read(
                IMPLEMENT
            )
            assert (
                "Tasks already marked complete `[X]` versus incomplete `[ ]`"
                in read(CONVERGE)
            )

    class TestAnalyzeCommand:
        """Rules /speckit-analyze states for scope and its report."""

        def test_should_cover_spec_plan_and_tasks_only_after_tasks_exist(self) -> None:
            """Analysis covers spec, plan and tasks, and only after tasks exist."""
            analyze = read(ANALYZE)
            assert (
                "across the three core artifacts (`spec.md`, `plan.md`, `tasks.md`)"
                in analyze
            )
            assert "This command MUST run only after `/speckit-tasks`" in analyze

        def test_should_report_zero_issues_with_coverage_statistics(self) -> None:
            assert (
                "**Report zero issues gracefully** (emit success report with coverage statistics)"
                in read(ANALYZE)
            )

        def test_should_structure_report_correctly_when_generating_analysis(
            self,
        ) -> None:
            """The report has a fixed findings table and the command writes nothing."""
            analyze = read(ANALYZE)
            assert (
                "| ID | Category | Severity | Location(s) | Summary | Recommendation |"
                in analyze
            )
            assert "**STRICTLY READ-ONLY**: Do **not** modify any files." in analyze

        def test_should_validate_coverage_percentage_when_analyzing(self) -> None:
            """Coverage is requirements with a task, backed by a per-requirement table."""
            analyze = read(ANALYZE)
            assert "- Coverage % (requirements with >=1 task)" in analyze
            assert "| Requirement Key | Has Task? | Task IDs | Notes |" in analyze

    class TestChecklistCommand:
        """Rules /speckit-checklist states, and their agreement with spec-writing."""

        def test_should_number_checklist_items_from_chk001(self) -> None:
            """Items are numbered from CHK001, in the steps and in the fallback layout."""
            checklist = read(CHECKLIST)
            assert "- Number items sequentially starting from CHK001" in checklist
            assert "`- [ ] CHK### <requirement item>`" in checklist

        def test_should_ask_at_most_three_questions_without_inventing_context(
            self,
        ) -> None:
            """With little input it asks at most three questions and does not invent context."""
            checklist = read(CHECKLIST)
            assert (
                "Derive up to THREE initial contextual clarifying questions"
                in checklist
            )
            assert "(do NOT hallucinate)" in checklist

        def test_should_set_the_traceability_floor_the_dimensions_module_sets(
            self,
        ) -> None:
            """The command and the dimensions module set the same 80% traceability floor."""
            assert "traceability (at least 80% of" in read(CHECKLIST)
            assert (
                "≥80% of items MUST include at least one traceability reference"
                in read(DIMENSIONS)
            )

        def test_should_give_each_quality_dimension_a_category(self) -> None:
            """Each quality dimension in the module has a category in the command."""
            categories = read(CHECKLIST).split("**Category Structure**", 1)[1]
            categories = categories.split("**Scenario Classification", 1)[0]
            dimensions = re.findall(r"^### \d\. (.+)$", read(DIMENSIONS), re.M)
            assert dimensions == [
                "Completeness",
                "Clarity",
                "Consistency",
                "Measurability",
                "Coverage",
                "Edge Cases",
                "Success Criteria",
            ]
            for dimension in (
                "Completeness",
                "Clarity",
                "Consistency",
                "Coverage",
                "Success Criteria",
            ):
                assert dimension in categories, dimension
            assert "Edge Case Coverage" in categories
            assert "measurable" in categories

    class TestConvergeCommand:
        """Test /speckit-converge command (post-implement spec-to-code convergence)."""

        PLUGIN_ROOT = Path(__file__).resolve().parent.parent

        def test_should_register_command_when_converge_adopted(self) -> None:
            """Test that speckit-converge is registered in the plugin manifest.

            Given: the spec-kit plugin.json manifest on disk
            When: reading the registered commands
            Then: speckit-converge.md should be listed
            """
            # Given
            manifest_path = self.PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text())

            # When
            commands = manifest["commands"]

            # Then
            assert "./commands/speckit-converge.md" in commands, (
                "speckit-converge must be registered in plugin.json"
            )

        def test_should_have_valid_frontmatter_when_loading_converge(self) -> None:
            """Test the converge command file exists with a description.

            Given: the converge command file on disk
            When: parsing its YAML frontmatter
            Then: it should declare a non-empty description
            """
            # Given
            command_file = self.PLUGIN_ROOT / "commands" / "speckit-converge.md"
            assert command_file.exists(), "speckit-converge.md must exist on disk"
            content = command_file.read_text()

            # When
            frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)

            # Then
            assert frontmatter_match, "converge command should have frontmatter"
            desc_match = re.search(
                r"^description:\s*(.+)$",
                frontmatter_match.group(1),
                re.MULTILINE,
            )
            assert desc_match, "converge command should declare a description"
            description = desc_match.group(1).strip().strip("\"'")
            assert len(description) > 10, "description should be meaningful"

        def test_should_only_write_tasks_md_when_appending_convergence(self) -> None:
            """Drift-guard: converge documents its append-only write contract.

            Given: the converge command file on disk
            When: reading its operating constraints
            Then: it declares append-only writes and forbids modifying
                  spec.md or plan.md
            """
            # Given
            content = (
                self.PLUGIN_ROOT / "commands" / "speckit-converge.md"
            ).read_text()

            # Then - the contract must live in the command itself, not just
            # in this test. If these anchors drift, a human reviews the change.
            assert "APPEND-ONLY, NEVER REWRITE" in content, (
                "converge must document its append-only write constraint"
            )
            assert "MUST NOT" in content, "converge must state its write prohibitions"
            assert "spec.md" in content and "plan.md" in content, (
                "converge must name spec.md and plan.md as protected artifacts"
            )

        def test_should_leave_tasks_unchanged_when_codebase_satisfies_spec(
            self,
        ) -> None:
            """Drift-guard: converge leaves tasks.md unchanged on a clean result.

            Given: the converge command file on disk
            When: reading its clean-result contract
            Then: it states tasks.md is left byte-for-byte unchanged when the
                  codebase already satisfies spec/plan/tasks
            """
            # Given
            content = (
                self.PLUGIN_ROOT / "commands" / "speckit-converge.md"
            ).read_text()

            # Then
            assert "byte-for-byte unchanged" in content, (
                "converge must document the clean-result no-op guarantee"
            )

        def test_should_rank_constitution_violation_as_highest_severity(self) -> None:
            """Drift-guard: converge documents constitution authority.

            Given: the converge command file on disk
            When: reading its constitution-authority contract
            Then: it states a MUST-principle violation is the highest-severity
                  finding
            """
            # Given
            content = (
                self.PLUGIN_ROOT / "commands" / "speckit-converge.md"
            ).read_text()

            # Then
            assert "highest-severity finding" in content, (
                "converge must rank constitution violations as highest severity"
            )

    class TestArgumentHintContract:
        """The advertised argument must be the argument the body reads.

        ``argument-hint`` is what the user sees before typing. A command
        that derives ``SPEC``/``PLAN``/``TASKS`` from
        ``check-prerequisites.sh`` never reads a path off the command line,
        so advertising "Path to ..." sends the user to type an argument
        that is silently discarded.
        """

        COMMANDS_DIR = Path(__file__).resolve().parent.parent / "commands"

        @staticmethod
        def _hint(content: str) -> str:
            frontmatter = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not frontmatter:
                return ""
            match = re.search(
                r"^argument-hint:\s*(.+)$", frontmatter.group(1), re.MULTILINE
            )
            return match.group(1).strip().strip("\"'") if match else ""

        def test_should_find_commands_when_scanning_directory(self) -> None:
            """The scan must find files, or every assertion below is vacuous.

            Given: the spec-kit commands directory
            When: globbing for command files
            Then: at least one is found
            """
            assert list(self.COMMANDS_DIR.glob("speckit-*.md")), (
                "no spec-kit commands found; the hint contract test would pass "
                "on an empty set"
            )

        def test_should_not_promise_a_path_when_paths_come_from_prerequisites(
            self,
        ) -> None:
            """A script-discovered command must not advertise a path argument.

            Given: every spec-kit command file
            When: the body derives its artifact paths from check-prerequisites
            Then: its argument-hint must not promise a path to those artifacts
            """
            liars = []
            for command in sorted(self.COMMANDS_DIR.glob("speckit-*.md")):
                content = command.read_text()
                if "check-prerequisites" not in content:
                    continue
                hint = self._hint(content)
                if re.match(r"^path to\b", hint, re.IGNORECASE):
                    liars.append(f"{command.name}: {hint!r}")

            assert not liars, (
                "these commands advertise a path they never read (paths come "
                "from check-prerequisites.sh):\n  " + "\n  ".join(liars)
            )

        def test_should_declare_a_hint_when_body_reads_arguments(self) -> None:
            """A command that consumes $ARGUMENTS must say what to pass.

            Given: every spec-kit command file
            When: the body interpolates $ARGUMENTS
            Then: the frontmatter declares a non-empty argument-hint
            """
            missing = [
                command.name
                for command in sorted(self.COMMANDS_DIR.glob("speckit-*.md"))
                if "$ARGUMENTS" in command.read_text()
                and not self._hint(command.read_text())
            ]
            assert not missing, f"commands read $ARGUMENTS with no hint: {missing}"
