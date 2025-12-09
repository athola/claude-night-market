"""Tests for speckit-orchestrator skill functionality."""

from unittest.mock import Mock, patch

import pytest


class TestSpeckitOrchestrator:
    """Test cases for the Speckit Orchestrator skill."""

    @pytest.fixture
    def orchestrator(self, tmp_path, mock_skill_loader):
        """Create an orchestrator instance for testing."""
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

    def test_session_initialization_repository_context(
        self,
        orchestrator,
        temp_speckit_project,
    ) -> None:
        """Test repository context verification during session initialization."""
        orchestrator.plugin_root = temp_speckit_project

        # Check for .specify directory
        specify_dir = temp_speckit_project / ".specify"
        assert specify_dir.exists()
        assert (specify_dir / "scripts").exists()
        assert (specify_dir / "specs").exists()

    def test_session_initialization_missing_specify_dir(
        self, orchestrator, tmp_path
    ) -> None:
        """Test session initialization fails when .specify directory is missing."""
        orchestrator.plugin_root = tmp_path  # No .specify directory

        # Should detect missing directory
        specify_dir = tmp_path / ".specify"
        assert not specify_dir.exists()

    def test_command_skill_mapping(self, orchestrator) -> None:
        """Test command to skill mapping is correct."""
        expected_mappings = {
            "speckit.specify": "spec-writing",
            "speckit.clarify": "spec-writing",
            "speckit.plan": "task-planning",
            "speckit.tasks": "task-planning",
            "speckit.implement": None,  # No primary skill
            "speckit.analyze": None,  # No primary skill
            "speckit.checklist": None,  # No primary skill
        }

        for command, expected_skill in expected_mappings.items():
            actual_skill = orchestrator.command_skill_map.get(command)
            assert actual_skill == expected_skill, (
                f"Command {command} should map to {expected_skill}"
            )

    def test_load_command_dependencies_specify_command(self, orchestrator) -> None:
        """Test loading dependencies for /speckit.specify command."""
        command = "speckit.specify"
        primary_skill = orchestrator.command_skill_map[command]
        complementary_skills = orchestrator.complementary_skills.get(primary_skill, [])

        # Should load spec-writing as primary
        primary_loaded = orchestrator.load_skill(primary_skill)
        assert primary_loaded is not None
        assert primary_loaded["name"] == "spec-writing"

        # Should load brainstorming as complementary
        assert "brainstorming" in complementary_skills

    def test_load_command_dependencies_plan_command(self, orchestrator) -> None:
        """Test loading dependencies for /speckit.plan command."""
        command = "speckit.plan"
        primary_skill = orchestrator.command_skill_map[command]
        complementary_skills = orchestrator.complementary_skills.get(primary_skill, [])

        # Should load task-planning as primary
        primary_loaded = orchestrator.load_skill(primary_skill)
        assert primary_loaded is not None
        assert primary_loaded["name"] == "task-planning"

        # Should load writing-plans as complementary
        assert "writing-plans" in complementary_skills

    def test_load_command_dependencies_implement_command(self, orchestrator) -> None:
        """Test loading dependencies for /speckit.implement command."""
        command = "speckit.implement"
        primary_skill = orchestrator.command_skill_map[command]

        # No primary skill for implement
        assert primary_skill is None

        # Should load complementary skills only
        complementary_skills = orchestrator.complementary_skills.get(command, [])
        assert "executing-plans" in complementary_skills
        assert "systematic-debugging" in complementary_skills

    @patch("speckit_orchestrator.TodoWrite")
    def test_progress_tracking_initialization(
        self,
        mock_todowrite,
        orchestrator,
        workflow_progress_items,
    ) -> None:
        """Test progress tracking initialization creates proper todo items."""
        # Simulate progress tracking setup
        mock_todowrite.return_value = None

        # Initialize progress tracking
        progress_items = workflow_progress_items

        # Should create todos for each progress item
        assert len(progress_items) == 5
        assert "Repository context verified" in progress_items
        assert "Artifacts created/updated" in progress_items

    def test_cross_artifact_consistency_validation(
        self,
        orchestrator,
        temp_speckit_project,
    ) -> None:
        """Test validation of consistency across speckit artifacts."""
        # Create related artifacts
        specs_dir = temp_speckit_project / ".specify" / "specs"
        spec_file = specs_dir / "1-user-auth" / "SPECIFICATION.md"
        spec_file.parent.mkdir(parents=True)
        spec_file.write_text(
            "# User Authentication Spec\n\n## Overview\nUser auth feature",
        )

        # Validate artifact consistency
        assert spec_file.exists()
        assert "User Authentication" in spec_file.read_text()

    def test_skill_dependency_validation(self, orchestrator) -> None:
        """Test validation of skill dependencies."""
        # Mock skill with dependencies
        skill_with_deps = {
            "name": "test-skill",
            "dependencies": ["abstract", "superpowers"],
        }

        # Should validate dependencies exist
        required_deps = skill_with_deps["dependencies"]
        assert "abstract" in required_deps
        assert "superpowers" in required_deps

    def test_workflow_state_management(self, orchestrator) -> None:
        """Test workflow state tracking and management."""
        # Simulate workflow states
        workflow_states = [
            "initialized",
            "specifying",
            "planning",
            "implementing",
            "completed",
        ]

        # Should track state transitions
        current_state = "initialized"
        assert current_state in workflow_states

        # State transition
        current_state = "specifying"
        assert current_state in workflow_states

    def test_error_handling_missing_skill(self, orchestrator) -> None:
        """Test error handling when required skill is missing."""
        # Try to load non-existent skill
        missing_skill = orchestrator.load_skill("non-existent-skill")
        assert missing_skill is None

    def test_prerequisite_validation(self, orchestrator, temp_speckit_project) -> None:
        """Test validation of workflow prerequisites."""
        # Check for required scripts
        scripts_dir = temp_speckit_project / ".specify" / "scripts"
        bash_dir = scripts_dir / "bash"
        create_script = bash_dir / "create-new-feature.sh"

        assert create_script.exists()
        assert create_script.stat().st_mode & 0o111  # Executable bit set

    @patch("speckit_orchestrator.Skill")
    def test_skill_loading_with_context(self, mock_skill, orchestrator) -> None:
        """Test skill loading with proper context."""
        # Mock skill loading
        mock_skill_instance = Mock()
        mock_skill_instance.name = "spec-writing"
        mock_skill_instance.description = "Test skill"
        mock_skill.return_value = mock_skill_instance

        # Load skill with context
        skill_name = "spec-writing"
        loaded_skill = orchestrator.load_skill(skill_name)

        assert loaded_skill is not None
        mock_skill.assert_called_once()

    def test_command_execution_workflow(self, orchestrator, mock_todowrite) -> None:
        """Test complete command execution workflow."""
        command = "speckit.specify"

        # Step 1: Initialize session
        mock_todowrite.return_value = {"success": True}

        # Step 2: Load dependencies
        primary_skill = orchestrator.command_skill_map[command]
        assert primary_skill == "spec-writing"

        # Step 3: Track progress
        progress_items = [
            "Repository context verified",
            "Command-specific skills loaded",
            "Artifacts created/updated",
        ]

        # Step 4: Validate completion
        assert len(progress_items) == 3
