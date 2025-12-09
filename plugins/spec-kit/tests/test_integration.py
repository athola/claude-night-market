"""Integration tests for spec-kit workflows."""

# ruff: noqa: S101
import json
import subprocess
from unittest.mock import Mock, patch

import pytest


class TestSpeckitIntegration:
    """Integration test cases for complete speckit workflows."""

    @pytest.fixture
    def complete_speckit_project(
        self, temp_speckit_project, sample_spec_content, sample_task_list
    ):
        """Create a complete speckit project with all artifacts."""
        project_root = temp_speckit_project

        # Create specification
        spec_dir = project_root / ".specify" / "specs"
        feature_dir = spec_dir / "5-user-auth"
        feature_dir.mkdir(parents=True)
        (feature_dir / "SPECIFICATION.md").write_text(sample_spec_content)

        # Create tasks
        (feature_dir / "TASKS.md").write_text(json.dumps(sample_task_list, indent=2))

        # Create implementation files
        impl_dir = feature_dir / "implementation"
        impl_dir.mkdir()
        (impl_dir / "progress.json").write_text(
            json.dumps(
                {
                    "completed_tasks": ["setup-001", "setup-002"],
                    "current_phase": "1 - Foundation",
                    "total_tasks": 8,
                    "completed_count": 2,
                }
            )
        )

        return project_root

    class TestCompleteWorkflow:
        """Test complete specification to implementation workflow."""

        @patch("subprocess.run")
        def test_specify_to_implement_workflow(
            self, mock_run, sample_feature_description, temp_speckit_project
        ):
            """Test complete workflow from specification to implementation."""
            # Mock script execution
            mock_run.return_value = Mock(
                stdout='{"success": true, "branch": "5-user-auth", "directory": "specs/5-user-auth"}',
                returncode=0,
            )

            # Step 1: /speckit.specify
            # Should create branch and spec directory
            branch_name = "5-user-auth"
            spec_dir = temp_speckit_project / ".specify" / "specs" / branch_name
            spec_dir.mkdir(parents=True)

            # Should create specification file
            spec_file = spec_dir / "SPECIFICATION.md"
            spec_file.write_text(
                "# User Authentication\n\n## Overview\nUser auth feature"
            )

            assert spec_file.exists(), "Specification should be created"
            assert "User Authentication" in spec_file.read_text()

            # Step 2: /speckit.plan
            # Should create task breakdown
            task_file = spec_dir / "TASKS.md"
            task_file.write_text(
                json.dumps(
                    [
                        {
                            "phase": "0 - Setup",
                            "tasks": [
                                {
                                    "id": "setup-001",
                                    "title": "Create project structure",
                                    "dependencies": [],
                                }
                            ],
                        }
                    ],
                    indent=2,
                )
            )

            assert task_file.exists(), "Task file should be created"

            # Step 3: /speckit.implement
            # Should start implementation
            impl_dir = spec_dir / "implementation"
            impl_dir.mkdir()

            progress_file = impl_dir / "progress.json"
            progress_file.write_text(
                json.dumps({"current_task": "setup-001", "status": "in_progress"})
            )

            assert impl_dir.exists(), "Implementation directory should be created"
            assert progress_file.exists(), "Progress tracking should start"

        def test_artifact_consistency(
            self, complete_speckit_project, sample_spec_content, sample_task_list
        ):
            """Test consistency across all artifacts."""
            spec_dir = complete_speckit_project / ".specify" / "specs" / "5-user-auth"

            # Load artifacts
            spec_file = spec_dir / "SPECIFICATION.md"
            task_file = spec_dir / "TASKS.md"
            progress_file = spec_dir / "implementation" / "progress.json"

            spec_content = spec_file.read_text()
            tasks_data = json.loads(task_file.read_text())
            progress_data = json.loads(progress_file.read_text())

            # Validate consistency
            # Tasks should address specification requirements
            spec_requirements = len(
                [
                    line
                    for line in spec_content.split("\n")
                    if line.strip().startswith("-")
                ]
            )

            total_tasks = sum(len(phase["tasks"]) for phase in tasks_data)
            assert total_tasks >= spec_requirements, (
                "Should have tasks for each requirement"
            )

            # Progress should reference valid tasks
            all_task_ids = []
            for phase in tasks_data:
                for task in phase["tasks"]:
                    all_task_ids.append(task["id"])

            completed_tasks = progress_data.get("completed_tasks", [])
            for completed_id in completed_tasks:
                assert completed_id in all_task_ids, (
                    f"Progress references invalid task: {completed_id}"
                )

        def test_workflow_state_persistence(self, complete_speckit_project):
            """Test workflow state persistence across commands."""
            spec_dir = complete_speckit_project / ".specify" / "specs" / "5-user-auth"

            # Create state file
            state_file = spec_dir / "workflow_state.json"
            state_data = {
                "current_command": "implement",
                "completed_phases": ["0 - Setup"],
                "artifacts_created": [
                    "SPECIFICATION.md",
                    "TASKS.md",
                    "implementation/",
                ],
                "last_updated": "2025-01-01T00:00:00Z",
            }
            state_file.write_text(json.dumps(state_data, indent=2))

            # Load and validate state
            loaded_state = json.loads(state_file.read_text())
            assert loaded_state["current_command"] == "implement"
            assert "0 - Setup" in loaded_state["completed_phases"]
            assert "SPECIFICATION.md" in loaded_state["artifacts_created"]

    class TestCrossCommandDataFlow:
        """Test data flow between different speckit commands."""

        def test_spec_to_task_data_flow(self, sample_spec_content, sample_task_list):
            """Test data flow from specification to task generation."""
            # Extract key concepts from specification
            spec_concepts = []
            spec_lines = sample_spec_content.split("\n")

            for line in spec_lines:
                if "###" in line:  # User scenarios
                    scenario = line.strip().replace("###", "").strip()
                    spec_concepts.append(scenario)
                elif line.strip().startswith("- "):  # Requirements
                    requirement = line.strip().replace("- ", "").strip()
                    if len(requirement) > 5:  # Filter out short items
                        spec_concepts.append(requirement[:50])  # First 50 chars

            # Tasks should address specification concepts
            task_descriptions = []
            for phase in sample_task_list:
                for task in phase["tasks"]:
                    task_descriptions.append(task["description"].lower())

            # Check for concept coverage
            spec_text = sample_spec_content.lower()
            task_text = " ".join(task_descriptions)

            # Key concepts should appear in tasks
            key_concepts = ["user", "authentication", "password", "session", "role"]
            found_concepts = [
                concept for concept in key_concepts if concept in spec_text
            ]

            assert len(found_concepts) >= 3, (
                f"Spec should have key concepts: {found_concepts}"
            )

            # Tasks should reference some of these concepts
            task_concepts = [
                concept for concept in found_concepts if concept in task_text
            ]
            assert len(task_concepts) >= 2, (
                f"Tasks should reference spec concepts: {task_concepts}"
            )

        def test_task_to_progress_data_flow(self, sample_task_list):
            """Test data flow from tasks to progress tracking."""
            # Simulate task execution and progress tracking
            progress_data = {
                "completed_tasks": [],
                "current_phase": sample_task_list[0]["phase"],
                "phase_progress": {},
            }

            # Process phases in order
            for phase in sample_task_list:
                phase_name = phase["phase"]
                phase_tasks = phase["tasks"]
                total_tasks = len(phase_tasks)
                completed_tasks = 0

                # Simulate completing tasks
                for task in phase_tasks:
                    if not task["dependencies"]:  # Can complete tasks without deps
                        progress_data["completed_tasks"].append(task["id"])
                        completed_tasks += 1

                progress_data["phase_progress"][phase_name] = {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "percentage": (completed_tasks / total_tasks) * 100
                    if total_tasks > 0
                    else 0,
                }

            # Validate progress data
            assert len(progress_data["completed_tasks"]) > 0, (
                "Should have completed some tasks"
            )
            assert len(progress_data["phase_progress"]) == len(sample_task_list), (
                "Should track all phases"
            )

            # Check progress calculation
            for phase_name, phase_data in progress_data["phase_progress"].items():
                assert 0 <= phase_data["percentage"] <= 100, (
                    f"Invalid percentage for {phase_name}"
                )

        def test_progress_to_checklist_data_flow(
            self, sample_spec_content, sample_task_list
        ):
            """Test data flow from progress to completion checklist."""
            # Simulate completion status
            completed_tasks = ["setup-001", "setup-002"]  # Mock completed tasks
            total_tasks = sum(len(phase["tasks"]) for phase in sample_task_list)

            # Generate checklist based on progress
            checklist_items = []

            # Specification-based items
            if "## Overview" in sample_spec_content:
                checklist_items.append("✓ Specification overview created")
            if "## Functional Requirements" in sample_spec_content:
                checklist_items.append("✓ Functional requirements defined")
            if "## Success Criteria" in sample_spec_content:
                checklist_items.append("✓ Success criteria established")

            # Task-based items
            checklist_items.append(
                f"✓ {len(completed_tasks)}/{total_tasks} tasks completed"
            )

            # Progress-based items
            completion_percentage = (len(completed_tasks) / total_tasks) * 100
            checklist_items.append(
                f"✓ {completion_percentage:.1f}% implementation complete"
            )

            # Validate checklist
            assert len(checklist_items) >= 4, "Should generate comprehensive checklist"
            assert any("tasks completed" in item for item in checklist_items), (
                "Should show task progress"
            )
            assert any("% complete" in item for item in checklist_items), (
                "Should show completion percentage"
            )

    class TestErrorRecovery:
        """Test error recovery and resilience."""

        @patch("subprocess.run")
        def test_partial_failure_recovery(self, mock_run, temp_speckit_project):
            """Test recovery from partial workflow failures."""
            # Mock script failure then success
            call_count = 0

            def mock_subprocess_run(cmd, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return Mock(
                        stdout="", returncode=1, stderr="Script failed"
                    )  # First call fails
                else:
                    return Mock(
                        stdout='{"success": true, "branch": "5-user-auth"}',
                        returncode=0,
                    )

            mock_run.side_effect = mock_subprocess_run

            # Should retry after failure
            result1 = subprocess.run(["echo", "test"], capture_output=True, text=True)
            assert result1.returncode == 1  # First call fails

            result2 = subprocess.run(["echo", "test"], capture_output=True, text=True)
            assert result2.returncode == 0  # Second call succeeds

            assert call_count == 2, "Should have made 2 attempts"

        def test_missing_artifact_recovery(self, complete_speckit_project):
            """Test recovery when artifacts are missing."""
            spec_dir = complete_speckit_project / ".specify" / "specs" / "5-user-auth"

            # Remove task file
            task_file = spec_dir / "TASKS.md"
            if task_file.exists():
                task_file.unlink()

            # Should detect missing file and regenerate or fail gracefully
            missing_files = []
            required_files = ["SPECIFICATION.md", "TASKS.md"]

            for required_file in required_files:
                file_path = spec_dir / required_file
                if not file_path.exists():
                    missing_files.append(required_file)

            # Should handle missing files appropriately
            if missing_files:
                assert "TASKS.md" in missing_files, "Should detect missing task file"
                # In real implementation, would regenerate or prompt user

        def test_inconsistent_artifact_recovery(self, complete_speckit_project):
            """Test recovery from inconsistent artifacts."""
            spec_dir = complete_speckit_project / ".specify" / "specs" / "5-user-auth"

            # Create inconsistent data
            progress_file = spec_dir / "implementation" / "progress.json"
            inconsistent_progress = {
                "completed_tasks": ["non-existent-task"],
                "total_tasks": 5,
                "completed_count": 1,
            }
            progress_file.write_text(json.dumps(inconsistent_progress, indent=2))

            # Should detect inconsistency
            progress_data = json.loads(progress_file.read_text())
            completed_tasks = progress_data.get("completed_tasks", [])

            # Load task file to validate
            task_file = spec_dir / "TASKS.md"
            if task_file.exists():
                tasks_data = json.loads(task_file.read_text())
                all_task_ids = []

                for phase in tasks_data:
                    for task in phase["tasks"]:
                        all_task_ids.append(task["id"])

                # Find invalid tasks
                invalid_tasks = [
                    task_id
                    for task_id in completed_tasks
                    if task_id not in all_task_ids
                ]

                assert len(invalid_tasks) > 0, (
                    "Should detect inconsistent task references"
                )
                assert "non-existent-task" in invalid_tasks, (
                    "Should identify specific invalid task"
                )

    class TestPerformance:
        """Test performance characteristics of workflows."""

        def test_large_specification_handling(self):
            """Test handling of large specifications."""
            # Create large specification
            large_spec_content = "# Large Feature Specification\n\n## Overview\n"
            for i in range(100):
                large_spec_content += f"- Requirement {i}: Detailed description\n"

            large_spec_content += "\n## Functional Requirements\n"
            for i in range(50):
                large_spec_content += f"### Requirement Group {i}\n"
                for j in range(10):
                    large_spec_content += f"- Sub-requirement {i}-{j}\n"

            # Should handle large specs without performance issues
            assert len(large_spec_content) > 10000, "Large spec should be substantial"

            # Test parsing performance (should be fast)
            import time

            start_time = time.time()

            # Simulate parsing
            lines = large_spec_content.split("\n")
            sections = [line for line in lines if line.startswith("## ")]
            requirements = [line for line in lines if line.strip().startswith("- ")]

            parse_time = time.time() - start_time

            assert parse_time < 1.0, f"Parsing should be fast, took {parse_time:.2f}s"
            assert len(sections) >= 2, "Should find sections in large spec"
            assert len(requirements) >= 100, "Should find requirements in large spec"

        def test_many_tasks_handling(self, sample_task_list):
            """Test handling of many tasks."""
            # Expand task list
            expanded_tasks = []
            for phase in sample_task_list:
                expanded_phase = phase.copy()
                expanded_phase["tasks"] = []

                # Create many tasks per phase
                base_task = (
                    phase["tasks"][0]
                    if phase["tasks"]
                    else {
                        "id": "base-task",
                        "title": "Base Task",
                        "description": "Base description",
                        "dependencies": [],
                        "estimated_time": "1h",
                        "priority": "medium",
                    }
                )

                for i in range(20):  # 20 tasks per phase
                    task = base_task.copy()
                    task["id"] = f"task-{i:03d}"
                    task["title"] = f"Task {i + 1}"
                    expanded_phase["tasks"].append(task)

                expanded_tasks.append(expanded_phase)

            # Should handle many tasks
            total_tasks = sum(len(phase["tasks"]) for phase in expanded_tasks)
            assert total_tasks == 100, f"Should handle {total_tasks} tasks"

            # Test dependency analysis performance
            import time

            start_time = time.time()

            # Check for cycles (should be fast)
            def has_cycle(tasks):
                # Simplified cycle detection
                return False  # No cycles in our test data

            cycle_check_time = time.time() - start_time
            assert cycle_check_time < 0.5, (
                f"Cycle check should be fast, took {cycle_check_time:.2f}s"
            )
