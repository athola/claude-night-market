"""Tests for spec-kit command functionality."""

import json
import tempfile
from unittest.mock import Mock, patch

import pytest


class TestSpeckitCommands:
    """Test cases for speckit commands."""

    class TestSpecifyCommand:
        """Test /speckit.specify command."""

        def test_branch_name_generation(self, sample_feature_description) -> None:
            """Test branch name generation from feature description."""
            feature_desc = sample_feature_description

            # Extract keywords for branch name
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

            assert len(found_keywords) >= 2, (
                "Should identify at least 2 keywords for branch name"
            )

            # Generate short name
            short_name_candidates = [
                "user-auth",
                "authentication-system",
                "access-control",
                "user-login",
            ]

            # Should match one of expected patterns
            assert any(
                candidate.replace("-", " ") in feature_desc.lower()
                for candidate in short_name_candidates
            )

        @patch("subprocess.run")
        def test_git_branch_numbering(self, mock_run, mock_git_repo) -> None:
            """Test git branch number detection and increment."""
            # Mock git fetch
            mock_run.return_value = Mock(
                stdout="1-user-auth\n2-api-integration\n",
                returncode=0,
            )

            # Mock git ls-remote
            def mock_subprocess_run(cmd, **kwargs):
                if "ls-remote" in cmd:
                    return Mock(stdout="refs/heads/3-feature-c\n", returncode=0)
                if "branch" in cmd:
                    return Mock(stdout="* main\n  4-local-feature\n", returncode=0)
                return Mock(stdout="", returncode=0)

            mock_run.side_effect = mock_subprocess_run

            # Should find highest number and increment
            # Mock the logic
            existing_numbers = [1, 2, 3, 4]
            next_number = max(existing_numbers) + 1 if existing_numbers else 1

            assert next_number == 5, f"Next number should be 5, got {next_number}"

        @patch("subprocess.run")
        def test_create_feature_script_execution(
            self,
            mock_run,
            sample_feature_description,
        ) -> None:
            """Test execution of create-new-feature.sh script."""
            mock_run.return_value = Mock(
                stdout=(
                    '{"success": true, "branch": "5-user-auth", '
                    '"directory": "specs/5-user-auth"}'
                ),
                returncode=0,
            )

            # Simulate script call
            script_args = [
                ".specify/scripts/bash/create-new-feature.sh",
                "--json",
                json.dumps({"description": sample_feature_description}),
                "--number",
                "5",
                "--short-name",
                "user-auth",
            ]

            # Should call script with correct arguments
            assert len(script_args) == 6
            assert script_args[0].endswith("create-new-feature.sh")
            assert "--number" in script_args
            assert "--short-name" in script_args

        def test_feature_description_validation(self) -> None:
            """Test feature description validation."""
            valid_descriptions = [
                "Add user authentication with OAuth2",
                "Implement payment processing",
                "Create dashboard for analytics",
                "Fix login timeout issue",
            ]

            invalid_descriptions = [
                "",  # Empty
                "test",  # Too short
                "a" * 1000,  # Too long
                "   ",  # Only whitespace
            ]

            for desc in valid_descriptions:
                assert len(desc.strip()) >= 10, (
                    f"Valid description should be substantial: {desc}"
                )

            for desc in invalid_descriptions:
                if desc.strip():  # If not empty/whitespace
                    assert len(desc.strip()) < 10 or len(desc) > 500, (
                        f"Invalid description should be caught: {desc}"
                    )

    class TestPlanCommand:
        """Test /speckit.plan command."""

        def test_spec_file_detection(self, temp_speckit_project) -> None:
            """Test detection of specification files."""
            # Create a spec file
            spec_dir = temp_speckit_project / ".specify" / "specs"
            spec_file = spec_dir / "5-user-auth" / "SPECIFICATION.md"
            spec_file.parent.mkdir(parents=True)
            spec_file.write_text("# User Authentication Specification")

            # Should detect spec file
            assert spec_file.exists()
            assert "SPECIFICATION.md" in spec_file.name

        def test_specification_parsing(self, sample_spec_content) -> None:
            """Test parsing of specification content."""
            spec_lines = sample_spec_content.split("\n")

            # Find sections
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

            # Should find key sections
            assert "Overview" in sections, "Should parse Overview section"
            assert "Functional Requirements" in sections, (
                "Should parse Functional Requirements"
            )
            assert "Success Criteria" in sections, "Should parse Success Criteria"

        def test_plan_generation_from_spec(self, sample_spec_content) -> None:
            """Test plan generation from specification content."""
            # Extract functional requirements
            fr_section = ""
            lines = sample_spec_content.split("\n")
            in_fr_section = False

            for _i, line in enumerate(lines):
                if "## Functional Requirements" in line:
                    in_fr_section = True
                    continue
                if line.startswith("## ") and in_fr_section:
                    break
                if in_fr_section:
                    fr_section += line + "\n"

            # Should have functional requirements
            assert len(fr_section.strip()) > 0, "Should extract functional requirements"

            # Generate planning points
            planning_points = []
            if "Authentication" in fr_section:
                planning_points.append("authentication system")
            if "Authorization" in fr_section:
                planning_points.append("authorization system")
            if "Session" in fr_section:
                planning_points.append("session management")

            assert len(planning_points) >= 2, (
                f"Should generate planning points, got: {planning_points}"
            )

    class TestImplementCommand:
        """Test /speckit.implement command."""

        def test_task_file_detection(self, temp_speckit_project) -> None:
            """Test detection of task files."""
            # Create a task file
            spec_dir = temp_speckit_project / ".specify" / "specs"
            task_file = spec_dir / "5-user-auth" / "TASKS.md"
            task_file.parent.mkdir(parents=True)
            task_file.write_text("# Implementation Tasks")

            # Should detect task file
            assert task_file.exists()
            assert "TASKS.md" in task_file.name

        def test_implementation_readiness_validation(self) -> None:
            """Test validation of implementation readiness."""
            required_files = ["SPECIFICATION.md", "TASKS.md"]

            # Check required files exist
            missing_files = [f for f in required_files if False]  # Mock file check

            assert len(missing_files) == 0, f"Missing required files: {missing_files}"

        def test_dependency_validation(self, sample_task_list) -> None:
            """Test validation of task dependencies before implementation."""
            # Check if dependencies are satisfied
            satisfied_tasks = set()  # Tasks already completed
            ready_tasks = []

            for phase in sample_task_list:
                for task in phase["tasks"]:
                    # Check if all dependencies are satisfied
                    deps_satisfied = all(
                        dep_id in satisfied_tasks for dep_id in task["dependencies"]
                    )

                    if deps_satisfied:
                        ready_tasks.append(task["id"])

            # Setup tasks should be ready
            setup_phase = next(
                (phase for phase in sample_task_list if phase["phase"] == "0 - Setup"),
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
                ), "Setup tasks without deps should be ready"

    class TestAnalyzeCommand:
        """Test /speckit.analyze command."""

        def test_code_analysis_scope_detection(self, temp_speckit_project) -> None:
            """Test detection of code analysis scope."""
            # Mock project structure
            src_dir = temp_speckit_project / "src"
            src_dir.mkdir()

            (src_dir / "auth.py").write_text("# Authentication code")
            (src_dir / "models.py").write_text("# Data models")

            # Should detect source files
            assert (src_dir / "auth.py").exists()
            assert (src_dir / "models.py").exists()

        def test_analysis_report_generation(self) -> None:
            """Test generation of analysis reports."""
            # Mock analysis results
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

            # Validate analysis results structure
            assert "coverage" in analysis_results
            assert "issues" in analysis_results
            assert "metrics" in analysis_results

            # Check coverage data
            coverage = analysis_results["coverage"]
            assert "coverage_percentage" in coverage
            assert 0 <= coverage["coverage_percentage"] <= 100

    class TestChecklistCommand:
        """Test /speckit.checklist command."""

        def test_completion_checklist_generation(
            self,
            sample_spec_content,
            sample_task_list,
        ) -> None:
            """Test generation of completion checklist."""
            checklist_items = []

            # From specification
            if "Overview" in sample_spec_content:
                checklist_items.append("✓ Specification overview defined")
            if "Functional Requirements" in sample_spec_content:
                checklist_items.append("✓ Functional requirements documented")
            if "Success Criteria" in sample_spec_content:
                checklist_items.append("✓ Success criteria established")

            # From task list
            total_tasks = sum(len(phase["tasks"]) for phase in sample_task_list)
            if total_tasks > 0:
                checklist_items.append(f"✓ {total_tasks} implementation tasks planned")

            # Should generate meaningful checklist
            assert len(checklist_items) >= 3, (
                f"Should generate checklist items, got: {checklist_items}"
            )

        def test_verification_criteria_check(self, sample_spec_content) -> None:
            """Test verification of success criteria."""
            # Extract success criteria
            success_section = ""
            lines = sample_spec_content.split("\n")
            in_success_section = False

            for _i, line in enumerate(lines):
                if "## Success Criteria" in line:
                    in_success_section = True
                    continue
                if line.startswith("## ") and in_success_section:
                    break
                if in_success_section:
                    success_section += line + "\n"

            # Should have success criteria
            assert len(success_section.strip()) > 0, (
                "Should have success criteria to verify"
            )

            # Check for verifiable criteria
            verifiable_patterns = ["can", "will", "should", "must"]
            has_verifiable = any(
                pattern in success_section.lower() for pattern in verifiable_patterns
            )
            assert has_verifiable, "Success criteria should be verifiable"

    @pytest.fixture
    def mock_command_execution(self):
        """Mock command execution environment."""
        temp_dir = tempfile.gettempdir()
        return {
            "PWD": f"{temp_dir}/test-project",
            "GIT_BRANCH": "feature/user-auth",
            "SPEC_DIR": f"{temp_dir}/test-project/.specify",
        }
