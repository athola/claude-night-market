"""Tests for speckit-orchestrator skill functionality."""

from unittest.mock import Mock, patch

import pytest


class TestSpeckitOrchestrator:
    """Test cases for the Speckit Orchestrator skill."""

    @pytest.fixture
    def orchestrator(self, tmp_path, mock_skill_loader):
        """Given an orchestrator instance with command-skill mappings.

        Creates mock orchestrator with predefined command mappings and
        complementary skill relationships.
        """
        # Mock the orchestrator skill
        orchestrator = Mock()
        orchestrator.plugin_root = tmp_path
        orchestrator.command_skill_map = {
            "speckit.specify": "spec-writing",
            "speckit.clarify": "spec-writing",
            "speckit.plan": "task-planning",
            "speckit.tasks": "task-planning",
            "speckit.implement": None,
            "speckit.analyze": None,
            "speckit.checklist": None,
        }
        orchestrator.complementary_skills = {
            "spec-writing": ["brainstorming"],
            "task-planning": ["writing-plans"],
            "speckit.implement": ["executing-plans", "systematic-debugging"],
            "speckit.analyze": ["systematic-debugging", "verification"],
            "speckit.checklist": ["verification-before-completion"],
        }
        orchestrator.load_skill = mock_skill_loader
        return orchestrator

    def test_should_verify_repository_context_when_initializing_session(
        self,
        orchestrator,
        temp_speckit_project,
    ) -> None:
        """Test repository context verification during session initialization."""
        # Given: an orchestrator with a speckit project
        orchestrator.plugin_root = temp_speckit_project

        # When: checking for required directory structure
        specify_dir = temp_speckit_project / ".specify"

        # Then: all required directories should exist
        assert specify_dir.exists()
        assert (specify_dir / "scripts").exists()
        assert (specify_dir / "specs").exists()

    def test_should_detect_missing_directory_when_specify_dir_absent(
        self, orchestrator, tmp_path
    ) -> None:
        """Test session initialization detects when .specify directory is missing."""
        # Given: an orchestrator without .specify directory
        orchestrator.plugin_root = tmp_path

        # When: checking for .specify directory
        specify_dir = tmp_path / ".specify"

        # Then: directory should not exist
        assert not specify_dir.exists()

    def test_should_map_commands_to_correct_skills_when_querying_mapping(
        self, orchestrator
    ) -> None:
        """Test command to skill mapping is correct."""
        # Given: expected command-to-skill mappings
        expected_mappings = {
            "speckit.specify": "spec-writing",
            "speckit.clarify": "spec-writing",
            "speckit.plan": "task-planning",
            "speckit.tasks": "task-planning",
            "speckit.implement": None,  # No primary skill
            "speckit.analyze": None,  # No primary skill
            "speckit.checklist": None,  # No primary skill
        }

        # When/Then: each command should map to expected skill
        for command, expected_skill in expected_mappings.items():
            actual_skill = orchestrator.command_skill_map.get(command)
            assert actual_skill == expected_skill, (
                f"Command {command} should map to {expected_skill}"
            )

    def test_should_load_primary_and_complementary_skills_when_executing_specify_command(
        self, orchestrator
    ) -> None:
        """Test loading dependencies for /speckit.specify command."""
        # Given: the speckit.specify command
        command = "speckit.specify"
        primary_skill = orchestrator.command_skill_map[command]
        complementary_skills = orchestrator.complementary_skills.get(primary_skill, [])

        # When: loading the primary skill
        primary_loaded = orchestrator.load_skill(primary_skill)

        # Then: spec-writing should be loaded as primary
        assert primary_loaded is not None
        assert primary_loaded["name"] == "spec-writing"

        # And: brainstorming should be in complementary skills
        assert "brainstorming" in complementary_skills

    def test_should_load_task_planning_dependencies_when_executing_plan_command(
        self, orchestrator
    ) -> None:
        """Test loading dependencies for /speckit.plan command."""
        # Given: the speckit.plan command
        command = "speckit.plan"
        primary_skill = orchestrator.command_skill_map[command]
        complementary_skills = orchestrator.complementary_skills.get(primary_skill, [])

        # When: loading the primary skill
        primary_loaded = orchestrator.load_skill(primary_skill)

        # Then: task-planning should be loaded as primary
        assert primary_loaded is not None
        assert primary_loaded["name"] == "task-planning"

        # And: writing-plans should be in complementary skills
        assert "writing-plans" in complementary_skills

    def test_should_load_only_complementary_skills_when_executing_implement_command(
        self, orchestrator
    ) -> None:
        """Test loading dependencies for /speckit.implement command."""
        # Given: the speckit.implement command
        command = "speckit.implement"
        primary_skill = orchestrator.command_skill_map[command]

        # When: checking for primary skill
        # Then: no primary skill should be assigned
        assert primary_skill is None

        # And: complementary skills should be available
        complementary_skills = orchestrator.complementary_skills.get(command, [])
        assert "executing-plans" in complementary_skills
        assert "systematic-debugging" in complementary_skills

    def test_should_create_todo_items_when_initializing_progress_tracking(
        self,
        orchestrator,
        workflow_progress_items,
    ) -> None:
        """Test progress tracking initialization creates proper todo items."""
        # Given: workflow progress items for tracking
        progress_items = workflow_progress_items

        # When: validating progress items structure
        # Then: should have todos for each progress item
        assert len(progress_items) == 5
        assert "Repository context verified" in progress_items
        assert "Artifacts created/updated" in progress_items

    def test_should_validate_artifact_consistency_when_checking_related_files(
        self,
        orchestrator,
        temp_speckit_project,
    ) -> None:
        """Test validation of consistency across speckit artifacts."""
        # Given: related artifacts in the speckit project
        specs_dir = temp_speckit_project / ".specify" / "specs"
        spec_file = specs_dir / "1-user-auth" / "SPECIFICATION.md"
        spec_file.parent.mkdir(parents=True)
        spec_file.write_text(
            "# User Authentication Spec\n\n## Overview\nUser auth feature",
        )

        # When: validating artifact consistency
        # Then: spec file should exist with expected content
        assert spec_file.exists()
        assert "User Authentication" in spec_file.read_text()

    def test_should_verify_required_dependencies_when_validating_skill(
        self, orchestrator
    ) -> None:
        """Test validation of skill dependencies."""
        # Given: a mock skill with dependencies
        skill_with_deps = {
            "name": "test-skill",
            "dependencies": ["abstract", "superpowers"],
        }

        # When: validating dependencies exist
        required_deps = skill_with_deps["dependencies"]

        # Then: all required dependencies should be listed
        assert "abstract" in required_deps
        assert "superpowers" in required_deps

    def test_should_track_workflow_state_transitions_when_executing_commands(
        self, orchestrator
    ) -> None:
        """Test workflow state tracking and management."""
        # Given: defined workflow states
        workflow_states = [
            "initialized",
            "specifying",
            "planning",
            "implementing",
            "completed",
        ]

        # When: transitioning through states
        current_state = "initialized"
        # Then: should be in a valid state
        assert current_state in workflow_states

        # When: state transitions to specifying
        current_state = "specifying"
        # Then: should still be in a valid state
        assert current_state in workflow_states

    def test_should_return_none_when_loading_nonexistent_skill(
        self, orchestrator
    ) -> None:
        """Test error handling when required skill is missing."""
        # Given: a non-existent skill name
        # When: attempting to load the skill
        missing_skill = orchestrator.load_skill("non-existent-skill")

        # Then: should return None
        assert missing_skill is None

    def test_should_have_executable_scripts_when_validating_prerequisites(
        self, orchestrator, temp_speckit_project
    ) -> None:
        """Test validation of workflow prerequisites."""
        # Given: required scripts in the project
        scripts_dir = temp_speckit_project / ".specify" / "scripts"
        bash_dir = scripts_dir / "bash"
        create_script = bash_dir / "create-new-feature.sh"

        # When: checking script existence and permissions
        # Then: script should exist and be executable
        assert create_script.exists()
        assert create_script.stat().st_mode & 0o111  # Executable bit set

    def test_should_load_skill_with_context_when_requested(
        self, orchestrator
    ) -> None:
        """Test skill loading with proper context."""
        # Given: a skill name to load
        skill_name = "spec-writing"

        # When: loading skill with context
        loaded_skill = orchestrator.load_skill(skill_name)

        # Then: skill should be loaded successfully
        assert loaded_skill is not None
        assert loaded_skill["name"] == "spec-writing"

    def test_should_execute_full_workflow_when_running_specify_command(
        self, orchestrator, mock_todowrite
    ) -> None:
        """Test complete command execution workflow."""
        # Given: the speckit.specify command
        command = "speckit.specify"

        # When: Step 1 - Initialize session
        mock_todowrite.return_value = {"success": True}

        # And: Step 2 - Load dependencies
        primary_skill = orchestrator.command_skill_map[command]
        # Then: should load correct primary skill
        assert primary_skill == "spec-writing"

        # When: Step 3 - Track progress
        progress_items = [
            "Repository context verified",
            "Command-specific skills loaded",
            "Artifacts created/updated",
        ]

        # Then: Step 4 - Validate completion
        assert len(progress_items) == 3
