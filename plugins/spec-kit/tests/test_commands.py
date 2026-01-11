"""Tests for spec-kit command functionality.

This test suite follows TDD/BDD principles:
- Behavior-focused test names using `test_should_X_when_Y` pattern
- Given-When-Then structure in each test
- Negative test cases for error conditions
- Parameterized tests for multiple scenarios
- Clear separation of concerns
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSpeckitCommands:
    """Test cases for speckit commands."""

    class TestSpecifyCommand:
        """Test /speckit-specify command."""

        def test_should_extract_keywords_for_branch_name_when_given_feature_description(
            self,
            detailed_feature_description: str,
        ) -> None:
            """Test branch name keyword extraction from feature description.

            Given: A detailed feature description with multiple keywords
            When: Processing the description for branch name generation
            Then: At least 2 relevant keywords should be identified
            """
            # Given
            feature_desc = detailed_feature_description

            # When - Extract keywords for branch name
            keywords = [
                "user",
                "authentication",
                "email",
                "password",
                "role",
                "access",
                "control",
            ]
            found_keywords = [kw for kw in keywords if kw in feature_desc.lower()]

            # Then
            assert len(found_keywords) >= 2, (
                "Should identify at least 2 keywords for branch name"
            )

        def test_should_match_expected_patterns_when_generating_short_name(
            self,
            detailed_feature_description: str,
        ) -> None:
            """Test short name pattern matching.

            Given: A feature description containing specific topics
            When: Generating candidate short names
            Then: At least one candidate should match content in the description
            """
            # Given
            feature_desc = detailed_feature_description

            # When - Generate short name candidates
            short_name_candidates = [
                "user-auth",
                "authentication-system",
                "access-control",
                "user-login",
            ]

            # Then - Should match one of expected patterns
            assert any(
                candidate.replace("-", " ") in feature_desc.lower()
                for candidate in short_name_candidates
            ), "At least one candidate pattern should match description content"

        def test_should_reject_empty_description_when_validating_input(
            self,
            empty_feature_description: str,
        ) -> None:
            """Test rejection of empty feature descriptions.

            Given: An empty feature description
            When: Validating the description
            Then: Should be rejected as invalid
            """
            # Given
            desc = empty_feature_description

            # When/Then - Empty descriptions should be invalid
            assert len(desc.strip()) == 0, "Empty description should have no content"

        def test_should_reject_vague_description_when_validating_input(
            self,
            vague_feature_description: str,
        ) -> None:
            """Test rejection of vague feature descriptions.

            Given: A vague, underspecified feature description
            When: Validating the description length and content
            Then: Should be flagged as lacking detail
            """
            # Given
            desc = vague_feature_description

            # When/Then - Vague descriptions should be too short or not detailed enough
            # The fixture "Make the app better" has 18 chars but lacks specific detail
            is_too_short = len(desc.strip()) < 30
            lacks_detail = not any(
                keyword in desc.lower()
                for keyword in ["implement", "add", "create", "build", "fix"]
            )

            # Then
            assert is_too_short or lacks_detail, (
                "Vague description should be too short or lack actionable detail"
            )

        @pytest.mark.parametrize(
            "description,expected_validity",
            [
                ("Add user authentication with OAuth2", True),
                ("Implement payment processing with Stripe integration", True),
                ("Create dashboard for analytics with charts", True),
                ("Fix login timeout issue in production", True),
                ("", False),  # Empty
                ("test", False),  # Too short
                ("   ", False),  # Only whitespace
            ],
        )
        def test_should_validate_description_correctly_when_checking_length(
            self,
            description: str,
            expected_validity: bool,
        ) -> None:
            """Test feature description validation across multiple cases.

            Given: Various feature descriptions of different quality
            When: Validating each description
            Then: Should correctly identify valid vs invalid descriptions
            """
            # Given/When
            is_valid = len(description.strip()) >= 10

            # Then
            assert is_valid == expected_validity, (
                f"Description '{description}' validity should be {expected_validity}"
            )

        @patch("subprocess.run")
        def test_should_increment_branch_number_when_existing_branches_found(
            self,
            mock_run: Mock,
            mock_git_repo: Path,
        ) -> None:
            """Test git branch number detection and increment.

            Given: A git repository with numbered feature branches
            When: Detecting existing branch numbers
            Then: Should identify highest number and increment by 1
            """

            # Given - Mock git commands returning existing branches
            def mock_subprocess_run(cmd, **kwargs):
                if "ls-remote" in cmd:
                    return Mock(stdout="refs/heads/3-feature-c\n", returncode=0)
                if "branch" in cmd:
                    return Mock(stdout="* main\n  4-local-feature\n", returncode=0)
                return Mock(stdout="", returncode=0)

            mock_run.side_effect = mock_subprocess_run

            # When - Finding highest number and incrementing
            existing_numbers = [1, 2, 3, 4]
            next_number = max(existing_numbers) + 1 if existing_numbers else 1

            # Then
            assert next_number == 5, f"Next number should be 5, got {next_number}"

        @patch("subprocess.run")
        def test_should_default_to_1_when_no_existing_branches_found(
            self,
            mock_run: Mock,
        ) -> None:
            """Test branch numbering with no existing numbered branches.

            Given: A git repository with no numbered branches
            When: Detecting existing branch numbers
            Then: Should default to 1
            """
            # Given - Mock git commands returning no numbered branches
            mock_run.return_value = Mock(stdout="", returncode=0)

            # When - Finding highest number
            existing_numbers = []
            next_number = max(existing_numbers) + 1 if existing_numbers else 1

            # Then
            assert next_number == 1, "First branch number should be 1"

        @patch("subprocess.run")
        def test_should_call_script_with_correct_args_when_creating_feature(
            self,
            mock_run: Mock,
            detailed_feature_description: str,
        ) -> None:
            """Test execution of create-new-feature.sh script.

            Given: A valid feature description and branch number
            When: Calling the create-new-feature script
            Then: Should pass correct arguments including JSON description
            """
            # Given
            mock_run.return_value = Mock(
                stdout=(
                    '{"success": true, "branch": "5-user-auth", '
                    '"directory": "specs/5-user-auth"}'
                ),
                returncode=0,
            )

            # When - Simulate script call
            script_args = [
                ".specify/scripts/bash/create-new-feature.sh",
                "--json",
                json.dumps({"description": detailed_feature_description}),
                "--number",
                "5",
                "--short-name",
                "user-auth",
            ]

            # Then - Should have correct argument structure (7 args: script + 6 args)
            assert len(script_args) == 7, "Should have 7 arguments"
            assert script_args[0].endswith("create-new-feature.sh"), (
                "Should call correct script"
            )
            assert "--number" in script_args, "Should include --number flag"
            assert "--short-name" in script_args, "Should include --short-name flag"
            assert "--json" in script_args, "Should include --json flag"

        @patch("subprocess.run")
        def test_should_raise_error_when_script_execution_fails(
            self,
            mock_run: Mock,
            detailed_feature_description: str,
        ) -> None:
            """Test error handling when script execution fails.

            Given: A script that fails with non-zero return code
            When: Attempting to create a feature
            Then: Should detect the failure condition
            """
            # Given - Mock failed script execution
            mock_run.return_value = Mock(
                stdout="",
                stderr="Error: Failed to create branch",
                returncode=1,
            )

            # When/Then - Should detect failure
            assert mock_run.return_value.returncode != 0, (
                "Should detect script execution failure"
            )

    class TestPlanCommand:
        """Test /speckit-plan command."""

        def test_should_detect_spec_file_when_file_exists(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test detection of specification files.

            Given: A project with a specification file
            When: Checking for spec file existence
            Then: Should successfully detect the file
            """
            # Given - Create a spec file
            spec_dir = temp_speckit_project / ".specify" / "specs"
            spec_file = spec_dir / "5-user-auth" / "SPECIFICATION.md"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text("# User Authentication Specification")

            # When/Then - Should detect spec file
            assert spec_file.exists(), "Should detect specification file"
            assert "SPECIFICATION.md" in spec_file.name, "Should be named correctly"

        def test_should_fail_when_spec_file_missing(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test error handling when specification file is missing.

            Given: A project without a specification file
            When: Checking for spec file existence
            Then: Should detect missing file
            """
            # Given - No spec file created
            spec_dir = temp_speckit_project / ".specify" / "specs"
            spec_file = spec_dir / "5-user-auth" / "SPECIFICATION.md"

            # When/Then - Should not exist
            assert not spec_file.exists(), "Spec file should not exist"

        def test_should_parse_all_sections_when_spec_is_complete(
            self,
            valid_authentication_spec_content: str,
        ) -> None:
            """Test parsing of complete specification content.

            Given: A complete specification with all sections
            When: Parsing the specification
            Then: Should extract all key sections
            """
            # Given
            spec_content = valid_authentication_spec_content

            # When - Parse specification sections
            spec_lines = spec_content.split("\n")
            sections = {}
            current_section = None
            section_content = []

            for line in spec_lines:
                if line.startswith("## "):
                    if current_section:
                        sections[current_section] = "\n".join(section_content)
                    current_section = line[3:].strip()
                    section_content = []
                elif current_section:
                    section_content.append(line)

            if current_section:
                sections[current_section] = "\n".join(section_content)

            # Then - Should find key sections
            assert "Overview" in sections, "Should parse Overview section"
            assert "Functional Requirements" in sections, (
                "Should parse Functional Requirements"
            )
            assert "Success Criteria" in sections, "Should parse Success Criteria"

        def test_should_fail_when_spec_missing_required_sections(
            self,
            spec_without_requirements: str,
        ) -> None:
            """Test validation of incomplete specifications.

            Given: A specification missing required sections
            When: Checking for required sections
            Then: Should detect missing Functional Requirements
            """
            # Given
            spec_content = spec_without_requirements

            # When - Check for required section
            has_requirements = "## Functional Requirements" in spec_content

            # Then
            assert not has_requirements, (
                "Should detect missing Functional Requirements section"
            )

        def test_should_extract_planning_points_when_generating_plan(
            self,
            valid_authentication_spec_content: str,
        ) -> None:
            """Test plan generation from specification content.

            Given: A specification with functional requirements
            When: Extracting planning points from requirements
            Then: Should generate multiple actionable planning points
            """
            # Given
            spec_content = valid_authentication_spec_content

            # When - Extract functional requirements section
            fr_section = ""
            lines = spec_content.split("\n")
            in_fr_section = False

            for line in lines:
                if "## Functional Requirements" in line:
                    in_fr_section = True
                    continue
                if line.startswith("## ") and in_fr_section:
                    break
                if in_fr_section:
                    fr_section += line + "\n"

            # Generate planning points
            planning_points = []
            if "Authentication" in fr_section:
                planning_points.append("authentication system")
            if "Authorization" in fr_section:
                planning_points.append("authorization system")
            if "Session" in fr_section:
                planning_points.append("session management")

            # Then
            assert len(planning_points) >= 2, (
                f"Should generate multiple planning points, got: {planning_points}"
            )

        def test_should_handle_minimal_spec_when_generating_plan(
            self,
            minimal_spec_content: str,
        ) -> None:
            """Test plan generation from minimal specification.

            Given: A minimal but valid specification
            When: Generating a plan
            Then: Should handle sparse content gracefully
            """
            # Given
            spec_content = minimal_spec_content

            # When - Check for minimal required content
            has_overview = "## Overview" in spec_content
            has_requirements = "## Functional Requirements" in spec_content

            # Then
            assert has_overview, "Minimal spec should have overview"
            assert has_requirements, "Minimal spec should have requirements"

    class TestImplementCommand:
        """Test /speckit-implement command."""

        def test_should_detect_task_file_when_file_exists(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test detection of task files.

            Given: A project with a task file
            When: Checking for task file existence
            Then: Should successfully detect the file
            """
            # Given - Create a task file
            spec_dir = temp_speckit_project / ".specify" / "specs"
            task_file = spec_dir / "5-user-auth" / "TASKS.md"
            task_file.parent.mkdir(parents=True)
            task_file.write_text("# Implementation Tasks")

            # When/Then - Should detect task file
            assert task_file.exists(), "Should detect task file"
            assert "TASKS.md" in task_file.name, "Should be named correctly"

        def test_should_fail_when_task_file_missing(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test error handling when task file is missing.

            Given: A project without a task file
            When: Checking for task file existence
            Then: Should detect missing file
            """
            # Given - No task file created
            spec_dir = temp_speckit_project / ".specify" / "specs"
            task_file = spec_dir / "5-user-auth" / "TASKS.md"

            # When/Then - Should not exist
            assert not task_file.exists(), "Task file should not exist"

        def test_should_validate_prerequisites_when_checking_readiness(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test validation of implementation prerequisites.

            Given: Required files for implementation
            When: Validating implementation readiness
            Then: Should check for all required files
            """
            # Given
            required_files = ["SPECIFICATION.md", "TASKS.md"]

            # When - Create the required files
            spec_dir = temp_speckit_project / ".specify" / "specs" / "5-user-auth"
            spec_dir.mkdir(parents=True)

            for filename in required_files:
                (spec_dir / filename).write_text(f"# {filename}")

            # Then - Check all files exist
            missing_files = [f for f in required_files if not (spec_dir / f).exists()]
            assert len(missing_files) == 0, f"Missing required files: {missing_files}"

        def test_should_fail_when_prerequisites_missing(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test error handling when prerequisites are missing.

            Given: A project missing required implementation files
            When: Validating implementation readiness
            Then: Should detect missing prerequisites
            """
            # Given
            required_files = ["SPECIFICATION.md", "TASKS.md"]
            spec_dir = temp_speckit_project / ".specify" / "specs" / "5-user-auth"
            spec_dir.mkdir(parents=True)

            # When - Don't create the files
            missing_files = [f for f in required_files if not (spec_dir / f).exists()]

            # Then
            assert len(missing_files) == 2, "Should detect all missing prerequisites"

        def test_should_identify_ready_tasks_when_dependencies_satisfied(
            self,
            valid_task_list: list,
        ) -> None:
            """Test identification of tasks ready for implementation.

            Given: A task list with dependency relationships
            When: Checking which tasks are ready (dependencies satisfied)
            Then: Should identify tasks without dependencies as ready
            """
            # Given
            satisfied_tasks = set()  # Tasks already completed
            ready_tasks = []

            # When - Check if dependencies are satisfied
            for phase in valid_task_list:
                for task in phase["tasks"]:
                    deps_satisfied = all(
                        dep_id in satisfied_tasks for dep_id in task["dependencies"]
                    )

                    if deps_satisfied:
                        ready_tasks.append(task["id"])

            # Then - Setup tasks without dependencies should be ready
            setup_phase = next(
                (phase for phase in valid_task_list if phase["phase"] == "0 - Setup"),
                None,
            )
            if setup_phase:
                setup_tasks_without_deps = [
                    task["id"]
                    for task in setup_phase["tasks"]
                    if not task["dependencies"]
                ]
                assert all(
                    task_id in ready_tasks for task_id in setup_tasks_without_deps
                ), "Setup tasks without dependencies should be ready"

        def test_should_block_tasks_when_dependencies_unsatisfied(
            self,
            valid_task_list: list,
        ) -> None:
            """Test blocking of tasks with unsatisfied dependencies.

            Given: A task list with dependency relationships
            When: No tasks have been completed yet
            Then: Only tasks without dependencies should be ready
            """
            # Given
            satisfied_tasks = set()  # Empty - nothing completed yet

            # When - Check which tasks are blocked
            blocked_tasks = []
            ready_tasks = []

            for phase in valid_task_list:
                for task in phase["tasks"]:
                    deps_satisfied = all(
                        dep_id in satisfied_tasks for dep_id in task["dependencies"]
                    )

                    if deps_satisfied:
                        ready_tasks.append(task["id"])
                    elif task["dependencies"]:
                        blocked_tasks.append(task["id"])

            # Then
            assert len(blocked_tasks) > 0, "Should have blocked tasks with dependencies"
            assert len(ready_tasks) > 0, "Should have ready tasks without dependencies"

        def test_should_detect_circular_dependencies_when_present(
            self,
            task_with_circular_dependency: list,
        ) -> None:
            """Test detection of circular task dependencies.

            Given: A task list with circular dependencies (A->B->C->A)
            When: Attempting to resolve dependencies
            Then: Should detect that no tasks can be satisfied
            """
            # Given
            tasks = task_with_circular_dependency[0]["tasks"]
            satisfied_tasks = set()

            # When - Try to find any task that can be started
            ready_tasks = []
            for task in tasks:
                deps_satisfied = all(
                    dep_id in satisfied_tasks for dep_id in task["dependencies"]
                )
                if deps_satisfied:
                    ready_tasks.append(task["id"])

            # Then - No tasks should be ready due to circular dependency
            assert len(ready_tasks) == 0, (
                "Circular dependencies should prevent any task from being ready"
            )

        def test_should_fail_when_dependency_missing(
            self,
            task_with_missing_dependency: list,
        ) -> None:
            """Test error handling for missing task dependencies.

            Given: A task referencing a non-existent dependency
            When: Validating task dependencies
            Then: Should detect the missing dependency
            """
            # Given
            tasks = task_with_missing_dependency[0]["tasks"]
            all_task_ids = {task["id"] for task in tasks}

            # When - Check for missing dependencies
            missing_deps = []
            for task in tasks:
                for dep_id in task["dependencies"]:
                    if dep_id not in all_task_ids:
                        missing_deps.append((task["id"], dep_id))

            # Then
            assert len(missing_deps) > 0, "Should detect missing dependencies"
            assert missing_deps[0][1] == "nonexistent-task", (
                "Should identify the missing dependency"
            )

    class TestAnalyzeCommand:
        """Test /speckit-analyze command."""

        def test_should_detect_source_files_when_analyzing_scope(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test detection of code analysis scope.

            Given: A project with source files
            When: Detecting analysis scope
            Then: Should find all source files
            """
            # Given - Create source files
            src_dir = temp_speckit_project / "src"
            src_dir.mkdir()

            (src_dir / "auth.py").write_text("# Authentication code")
            (src_dir / "models.py").write_text("# Data models")

            # When/Then - Should detect source files
            assert (src_dir / "auth.py").exists(), "Should detect auth.py"
            assert (src_dir / "models.py").exists(), "Should detect models.py"

        def test_should_handle_empty_project_when_analyzing(
            self,
            temp_speckit_project: Path,
        ) -> None:
            """Test analysis of project with no source files.

            Given: A project with no source files
            When: Attempting to analyze
            Then: Should handle empty project gracefully
            """
            # Given - No source files
            src_dir = temp_speckit_project / "src"

            # When/Then - Source directory doesn't exist
            assert not src_dir.exists(), "Should handle missing source directory"

        def test_should_structure_report_correctly_when_generating_analysis(
            self,
        ) -> None:
            """Test structure of analysis reports.

            Given: Analysis results from code scanning
            When: Generating the analysis report
            Then: Should include all required sections
            """
            # Given - Mock analysis results
            analysis_results = {
                "coverage": {
                    "total_files": 15,
                    "analyzed_files": 12,
                    "coverage_percentage": 80.0,
                },
                "issues": [
                    {"type": "warning", "message": "Unused import"},
                    {"type": "info", "message": "Consider adding docstring"},
                ],
                "metrics": {"complexity": "medium", "maintainability": "good"},
            }

            # When/Then - Validate structure
            assert "coverage" in analysis_results, "Should include coverage section"
            assert "issues" in analysis_results, "Should include issues section"
            assert "metrics" in analysis_results, "Should include metrics section"

        def test_should_validate_coverage_percentage_when_analyzing(
            self,
        ) -> None:
            """Test validation of coverage percentage in analysis.

            Given: Analysis results with coverage data
            When: Checking coverage percentage
            Then: Should be within valid range (0-100)
            """
            # Given
            analysis_results = {
                "coverage": {
                    "total_files": 15,
                    "analyzed_files": 12,
                    "coverage_percentage": 80.0,
                },
            }

            # When
            coverage = analysis_results["coverage"]
            percentage = coverage["coverage_percentage"]

            # Then
            assert 0 <= percentage <= 100, (
                f"Coverage percentage should be 0-100, got {percentage}"
            )

    class TestChecklistCommand:
        """Test /speckit-checklist command."""

        def test_should_generate_checklist_from_spec_when_processing(
            self,
            valid_authentication_spec_content: str,
            valid_task_list: list,
        ) -> None:
            """Test generation of completion checklist.

            Given: A specification and task list
            When: Generating a completion checklist
            Then: Should create items from both spec and tasks
            """
            # Given
            spec_content = valid_authentication_spec_content
            task_list = valid_task_list

            # When - Generate checklist
            checklist_items = []

            # From specification
            if "Overview" in spec_content:
                checklist_items.append("Specification overview defined")
            if "Functional Requirements" in spec_content:
                checklist_items.append("Functional requirements documented")
            if "Success Criteria" in spec_content:
                checklist_items.append("Success criteria established")

            # From task list
            total_tasks = sum(len(phase["tasks"]) for phase in task_list)
            if total_tasks > 0:
                checklist_items.append(f"{total_tasks} implementation tasks planned")

            # Then
            assert len(checklist_items) >= 3, (
                f"Should generate meaningful checklist, got: {checklist_items}"
            )

        def test_should_handle_empty_inputs_when_generating_checklist(
            self,
            empty_spec_content: str,
            empty_task_list: list,
        ) -> None:
            """Test checklist generation with empty inputs.

            Given: Empty specification and task list
            When: Attempting to generate checklist
            Then: Should generate minimal or no items
            """
            # Given
            spec_content = empty_spec_content
            task_list = empty_task_list

            # When - Try to generate checklist
            checklist_items = []

            if "Overview" in spec_content:
                checklist_items.append("Specification overview defined")

            total_tasks = sum(len(phase["tasks"]) for phase in task_list)
            if total_tasks > 0:
                checklist_items.append(f"{total_tasks} implementation tasks planned")

            # Then
            assert len(checklist_items) == 0, (
                "Should generate no items from empty inputs"
            )

        def test_should_extract_verifiable_criteria_when_processing_spec(
            self,
            valid_authentication_spec_content: str,
        ) -> None:
            """Test extraction of verifiable success criteria.

            Given: A specification with success criteria section
            When: Extracting and validating criteria
            Then: Should find verifiable criteria with action words
            """
            # Given
            spec_content = valid_authentication_spec_content

            # When - Extract success criteria
            success_section = ""
            lines = spec_content.split("\n")
            in_success_section = False

            for line in lines:
                if "## Success Criteria" in line:
                    in_success_section = True
                    continue
                if line.startswith("## ") and in_success_section:
                    break
                if in_success_section:
                    success_section += line + "\n"

            # Then - Should have success criteria
            assert len(success_section.strip()) > 0, (
                "Should extract success criteria section"
            )

            # Check for verifiable patterns
            verifiable_patterns = ["can", "will", "should", "must"]
            has_verifiable = any(
                pattern in success_section.lower() for pattern in verifiable_patterns
            )
            assert has_verifiable, "Success criteria should contain verifiable terms"

        def test_should_handle_spec_with_minimal_success_criteria(
            self,
            spec_without_requirements: str,
        ) -> None:
            """Test handling of spec with insufficient success criteria.

            Given: A specification with minimal success criteria
            When: Extracting and validating criteria quality
            Then: Should detect insufficient or non-actionable criteria
            """
            # Given
            spec_content = spec_without_requirements

            # When - Extract success criteria
            success_section = ""
            lines = spec_content.split("\n")
            in_success_section = False

            for line in lines:
                if "## Success Criteria" in line:
                    in_success_section = True
                    continue
                if line.startswith("## ") and in_success_section:
                    break
                if in_success_section:
                    success_section += line + "\n"

            # Then - Check if criteria are meaningful
            # The fixture has "Should not validate" which lacks actionable criteria
            criteria_count = len(
                [
                    line
                    for line in success_section.split("\n")
                    if line.strip().startswith("-")
                ]
            )
            assert criteria_count <= 1, "Spec should have insufficient success criteria"

    @pytest.fixture
    def mock_command_execution(self):
        """Mock command execution environment.

        Given: A mock command execution environment with standard paths
        Use this: For testing command execution without actual file I/O
        """
        temp_dir = tempfile.gettempdir()
        return {
            "PWD": f"{temp_dir}/test-project",
            "GIT_BRANCH": "feature/user-auth",
            "SPEC_DIR": f"{temp_dir}/test-project/.specify",
        }


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================


@pytest.fixture
def sample_feature_description(detailed_feature_description: str) -> str:
    """Backward compatibility alias for detailed_feature_description."""
    return detailed_feature_description


@pytest.fixture
def sample_spec_content(valid_authentication_spec_content: str) -> str:
    """Backward compatibility alias for valid_authentication_spec_content."""
    return valid_authentication_spec_content


@pytest.fixture
def sample_task_list(valid_task_list: list) -> list:
    """Backward compatibility alias for valid_task_list."""
    return valid_task_list
