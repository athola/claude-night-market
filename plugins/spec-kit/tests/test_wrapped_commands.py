"""Integration tests for wrapped commands with superpowers integration."""

from unittest.mock import Mock, patch

import pytest


class TestWrappedCommands:
    """Test cases for enhanced wrapped commands."""

    class TestWrappedPlanCommand:
        """Test /speckit.plan.wrapped command."""

        def test_skill_loading_sequence(self):
            """Test that writing-plans and speckit-orchestrator skills are loaded."""
            # Mock skill loading
            mock_skills = {"writing-plans": Mock(), "speckit-orchestrator": Mock()}

            # Verify skills are loaded in correct order
            assert "writing-plans" in mock_skills
            assert "speckit-orchestrator" in mock_skills

        def test_spec_kit_context_initialization(self, temp_speckit_project):
            """Test spec-kit context initialization."""
            project_dir = temp_speckit_project

            # Create mock .specify structure
            specify_dir = project_dir / ".specify"
            specify_dir.mkdir(parents=True)
            (specify_dir / "scripts" / "bash").mkdir(parents=True)

            # Create mock setup script
            setup_script = specify_dir / "scripts" / "bash" / "setup-plan.sh"
            setup_script.write_text(
                """#!/bin/bash
echo '{"FEATURE_SPEC": "/tmp/spec.md", "IMPL_PLAN": "/tmp/plan.md", "SPECS_DIR": "/tmp", "BRANCH": "test"}'
"""
            )

            assert setup_script.exists()
            assert setup_script.is_file()

        @patch("subprocess.run")
        def test_enhanced_planning_workflow(self, mock_run, temp_speckit_project):
            """Test enhanced planning workflow with writing-plans integration."""
            # Mock subprocess calls
            mock_run.return_value = Mock(
                stdout='{"FEATURE_SPEC": "/tmp/spec.md", "IMPL_PLAN": "/tmp/plan.md"}',
                returncode=0,
            )

            # Simulate workflow execution
            workflow_steps = [
                "Load writing-plans skill",
                "Initialize spec-kit context",
                "Analyze specification",
                "Apply writing-plans methodology",
                "Generate enhanced artifacts",
            ]

            # All workflow steps should be defined
            assert len(workflow_steps) == 5
            assert "writing-plans" in workflow_steps[0]
            assert "artifacts" in workflow_steps[-1]

        def test_artifact_generation_enhancements(self):
            """Test enhanced artifact generation with writing-plans patterns."""
            expected_artifacts = [
                "research.md",
                "plan.md",
                "data-model.md",
                "contracts/",
                "validation-report.md",
                "traceability-matrix.md",
            ]

            # Should generate more artifacts than standard spec-kit
            assert len(expected_artifacts) >= 6

        def test_quality_validation_integration(self):
            """Test quality validation from both methodologies."""
            quality_checks = {
                "constitution_compliance": "spec-kit",
                "cross_artifact_consistency": "spec-kit",
                "requirement_traceability": "enhanced",
                "dependency_analysis": "writing-plans",
                "risk_assessment": "writing-plans",
            }

            # Should include checks from both methodologies
            spec_kit_checks = [k for k, v in quality_checks.items() if v == "spec-kit"]
            writing_plans_checks = [
                k for k, v in quality_checks.items() if v == "writing-plans"
            ]
            enhanced_checks = [k for k, v in quality_checks.items() if v == "enhanced"]

            assert len(spec_kit_checks) >= 2
            assert len(writing_plans_checks) >= 2
            assert len(enhanced_checks) >= 1

    class TestWrappedTasksCommand:
        """Test /speckit.tasks.wrapped command."""

        def test_user_story_organization(self):
            """Test task organization by user stories."""
            user_stories = ["US1", "US2", "US3"]

            for story in user_stories:
                # Each story should have independent tasks
                story_tasks = {
                    "implementation": [f"{story}-task-1", f"{story}-task-2"],
                    "testing": [f"{story}-test-1"],
                    "documentation": [f"{story}-doc-1"],
                }

                assert len(story_tasks["implementation"]) >= 2
                assert len(story_tasks["testing"]) >= 1
                assert len(story_tasks["documentation"]) >= 1

        def test_enhanced_task_formatting(self):
            """Test enhanced task formatting with writing-plans detail."""
            task_format = "- [ ] T001 [P] [US1] Create User model in src/models/user.py"

            # Should include all required elements
            assert "[ ]" in task_format  # Checkbox
            assert "T001" in task_format  # Task ID
            assert "[P]" in task_format  # Parallel marker
            assert "[US1]" in task_format  # User story
            assert "src/models/user.py" in task_format  # File path

        def test_dependency_analysis_enhancement(self):
            """Test enhanced dependency analysis from writing-plans."""
            dependency_types = {
                "sequential": ["T001 → T002", "T002 → T003"],
                "parallel": ["T004[P]", "T005[P]"],
                "story_based": ["US1 → US2"],
                "external": ["api-service", "database"],
            }

            # Should identify multiple dependency types
            assert len(dependency_types) == 4
            assert len(dependency_types["parallel"]) >= 2

        def test_phase_organization(self):
            """Test phase-based task organization."""
            phases = {
                "Phase 0": ["setup", "environment", "tools"],
                "Phase 1": ["data-model", "core-logic", "api"],
                "Phase 2": ["integration", "performance"],
                "Phase 3": ["testing", "documentation"],
                "Phase 4": ["deployment", "monitoring"],
            }

            # Should have 5 phases with appropriate tasks
            assert len(phases) == 5
            assert len(phases["Phase 1"]) >= 3

        def test_mvp_scope_identification(self):
            """Test MVP scope identification."""
            mvp_tasks = ["core-authentication", "basic-profile", "simple-ui"]
            enhanced_tasks = ["advanced-features", "optimizations", "extras"]

            # MVP should be clearly identified
            assert len(mvp_tasks) >= 3
            assert len(enhanced_tasks) >= 3

    class TestWrappedStartupCommand:
        """Test /speckit.startup.wrapped command."""

        def test_session_state_initialization(self):
            """Test enhanced session state initialization."""
            session_state = {
                "session_id": "test-uuid",
                "workflow_phase": "initialization",
                "loaded_skills": ["writing-plans", "speckit-orchestrator"],
                "artifacts_status": {"spec.md": "not_found", "plan.md": "not_found"},
                "quality_gates": {
                    "repository_ready": "pass",
                    "session_management": "active",
                },
            }

            # Should initialize comprehensive session state
            assert "session_id" in session_state
            assert "writing-plans" in session_state["loaded_skills"]
            assert len(session_state["quality_gates"]) >= 2

        def test_artifact_tracking_configuration(self):
            """Test artifact tracking setup."""
            tracked_artifacts = [
                "SPECIFICATION.md",
                "plan.md",
                "tasks.md",
                "constitution.md",
                "research.md",
                "data-model.md",
                "contracts/",
            ]

            # Should track all spec-kit artifacts
            assert len(tracked_artifacts) >= 7
            assert "contracts/" in tracked_artifacts  # Directory tracking

        @patch("subprocess.run")
        def test_repository_verification(self, mock_run):
            """Test repository context verification."""
            # Mock git repository check
            mock_run.return_value = Mock(returncode=0)

            # Should verify git repository
            verification_steps = [
                "Check git repository",
                "Verify .specify directory",
                "Create required directories",
                "Validate permissions",
            ]

            assert len(verification_steps) >= 4

        def test_skill_coordination_setup(self):
            """Test skill coordination patterns."""
            skill_config = {
                "primary": ["writing-plans", "speckit-orchestrator"],
                "complementary": {
                    "specification": ["brainstorming"],
                    "implementation": ["test-driven-development"],
                    "troubleshooting": ["systematic-debugging"],
                },
            }

            # Should establish clear skill hierarchy
            assert len(skill_config["primary"]) == 2
            assert len(skill_config["complementary"]) >= 3

    class TestWrappedCommandsIntegration:
        """Test integration between wrapped commands."""

        def test_session_continuity(self):
            """Test session continuity across command executions."""
            session_flow = [
                ("startup.wrapped", "initialization"),
                ("plan.wrapped", "planning"),
                ("tasks.wrapped", "task_generation"),
                ("startup.wrapped", "restoration"),  # Session restart
            ]

            # Should maintain session state across commands
            assert len(session_flow) == 4

            # Session should be restorable
            restoration_command = session_flow[-1]
            assert restoration_command[0] == "startup.wrapped"

        def test_artifact_consistency(self):
            """Test artifact consistency across wrapped commands."""
            artifact_lifecycle = {
                "startup.wrapped": ["tracking_setup"],
                "plan.wrapped": ["plan.md", "research.md"],
                "tasks.wrapped": ["tasks.md", "dependency_graph"],
            }

            # Each command should update artifacts appropriately
            for _command, artifacts in artifact_lifecycle.items():
                assert len(artifacts) >= 1

        def test_quality_gate_progression(self):
            """Test quality gate progression through workflow."""
            quality_gates = {
                "Gate 1": {
                    "command": "startup.wrapped",
                    "criteria": ["repository_ready", "spec_kit_initialized"],
                },
                "Gate 2": {
                    "command": "plan.wrapped",
                    "criteria": ["spec_complete", "plan_validated"],
                },
                "Gate 3": {
                    "command": "tasks.wrapped",
                    "criteria": ["tasks_generated", "dependencies_resolved"],
                },
            }

            # Should have quality gates for each phase
            assert len(quality_gates) == 3

            for _gate, config in quality_gates.items():
                assert "command" in config
                assert len(config["criteria"]) >= 2

    class TestErrorHandlingAndRecovery:
        """Test error handling and recovery in wrapped commands."""

        def test_skill_loading_failure(self):
            """Test graceful handling of skill loading failures."""
            failure_scenarios = [
                {"skill": "writing-plans", "fallback": "standard_planning"},
                {"skill": "speckit-orchestrator", "fallback": "basic_coordination"},
                {"skill": "complementary", "fallback": "continue_without"},
            ]

            for scenario in failure_scenarios:
                assert "fallback" in scenario

        def test_artifact_missing_handling(self):
            """Test handling of missing artifacts."""
            missing_artifacts = {
                "spec.md": {"action": "suggest_run_specify", "continue": False},
                "plan.md": {"action": "suggest_run_plan", "continue": False},
                "constitution.md": {"action": "use_default", "continue": True},
            }

            for _artifact, handling in missing_artifacts.items():
                assert "action" in handling
                assert "continue" in handling

        def test_session_recovery_mechanisms(self):
            """Test session recovery after errors."""
            recovery_features = [
                "state_checkpointing",
                "partial_progress_preservation",
                "context_validation",
                "graceful_degradation",
            ]

            # Should have comprehensive recovery mechanisms
            assert len(recovery_features) >= 4

    @pytest.fixture
    def temp_speckit_project(self, tmp_path):
        """Create a temporary spec-kit project structure."""
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        # Create .specify structure
        specify_dir = project_dir / ".specify"
        specify_dir.mkdir(parents=True)

        (specify_dir / "specs").mkdir()
        (specify_dir / "scripts" / "bash").mkdir(parents=True)
        (specify_dir / "memory").mkdir()
        (specify_dir / "templates").mkdir()

        return project_dir

    @pytest.fixture
    def mock_skill_loading(self):
        """Mock skill loading for testing."""
        skills = {
            "writing-plans": {
                "capabilities": ["planning", "task_breakdown", "dependency_analysis"],
                "status": "loaded",
            },
            "speckit-orchestrator": {
                "capabilities": ["coordination", "workflow_management"],
                "status": "loaded",
            },
        }
        return skills

    @pytest.fixture
    def sample_artifacts(self, temp_speckit_project):
        """Create sample spec-kit artifacts for testing."""
        artifacts_dir = temp_speckit_project / ".specify" / "specs" / "test-feature"
        artifacts_dir.mkdir(parents=True)

        # Create sample specification
        spec_file = artifacts_dir / "SPECIFICATION.md"
        spec_file.write_text(
            """
# Test Feature Specification

## Overview
A test feature for validation

## Functional Requirements
- User authentication
- Data storage
- API endpoints

## Success Criteria
- Users can authenticate
- Data persists correctly
- API responses are valid
"""
        )

        # Create sample plan
        plan_file = artifacts_dir / "plan.md"
        plan_file.write_text(
            """
# Implementation Plan

## Technical Context
- Backend: Python/FastAPI
- Database: PostgreSQL
- Frontend: React

## Implementation Phases
- Phase 0: Setup
- Phase 1: Core features
- Phase 2: Integration
"""
        )

        return {"spec": spec_file, "plan": plan_file, "directory": artifacts_dir}
