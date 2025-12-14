"""Pytest configuration and shared fixtures for spec-kit testing.

This module provides reusable test fixtures following TDD/BDD principles:
- Focused fixtures that do one thing well
- Clear docstrings describing the "Given" state
- Type hints for better IDE support
- Edge case fixtures for boundary testing
- Factory fixtures for generating variations
"""

from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import Mock

import pytest


# ============================================================================
# Specification Content Fixtures
# ============================================================================


@pytest.fixture
def valid_authentication_spec_content() -> str:
    """Given a complete, valid authentication specification.

    Provides a realistic spec with all standard sections:
    - Overview, User Scenarios, Functional Requirements
    - Success Criteria, Assumptions, Open Questions

    Use this for testing happy path spec processing.
    """
    return """# Feature Specification: User Authentication

## Overview
Implement user authentication to allow secure access to the application.

## User Scenarios

### As a user
I want to log in with my email and password
So that I can access my personalized content

### As an administrator
I want to manage user accounts
So that I can maintain system security

## Functional Requirements

### Authentication
- Users can register with email and password
- Users can log in with existing credentials
- Sessions expire after 24 hours
- Password reset functionality available

### Authorization
- Role-based access control (admin, user)
- Protected routes require authentication
- Resource ownership validation

## Success Criteria

- Users can successfully register and log in
- Password security meets industry standards
- Session management works correctly
- Authorization prevents unauthorized access

## Assumptions

- Email delivery service is available
- Password complexity requirements follow OWASP guidelines
- User data is stored securely

## Open Questions

[CLARIFY] What specific roles are needed beyond admin/user?
[CLARIFY] Should we implement multi-factor authentication initially?
[CLARIFY] What are the session timeout requirements for different user types?
"""


@pytest.fixture
def minimal_spec_content() -> str:
    """Given a minimal but valid specification.

    Contains only required sections with minimal content.
    Use this for testing spec processors that should work with sparse input.
    """
    return """# Feature Specification: Basic Feature

## Overview
A simple feature implementation.

## Functional Requirements
- Must do something useful
"""


@pytest.fixture
def empty_spec_content() -> str:
    """Given an empty specification.

    Use this for testing validation that catches missing content.
    """
    return ""


@pytest.fixture
def malformed_spec_content() -> str:
    """Given a malformed specification with invalid markdown.

    Contains broken syntax and inconsistent formatting.
    Use this for testing error handling in spec parsers.
    """
    return """# Feature Specification: Broken Feature

## Overview
Missing closing markdown

## Functional Requirements
- Item 1
- Item 2
### Unexpected subheading in list

[CLARIFY Broken tag syntax
More broken content...
"""


@pytest.fixture
def spec_without_requirements() -> str:
    """Given a spec missing the functional requirements section.

    Use this for testing validation that enforces required sections.
    """
    return """# Feature Specification: Incomplete Feature

## Overview
This spec is missing functional requirements.

## Success Criteria
- Should not validate
"""


@pytest.fixture
def spec_with_only_questions() -> str:
    """Given a spec that contains only open questions.

    Represents an underspecified feature awaiting clarification.
    Use this for testing clarification workflows.
    """
    return """# Feature Specification: Unclear Feature

## Overview
Feature needs clarification.

## Open Questions
[CLARIFY] What should this feature do?
[CLARIFY] Who are the users?
[CLARIFY] What are the requirements?
"""


@pytest.fixture
def spec_content_factory() -> Callable[[str, str, List[str]], str]:
    """Given a factory for generating spec variations.

    Returns a function that creates spec content with customizable:
    - Feature name
    - Overview description
    - List of functional requirements

    Use this for parametric testing across multiple scenarios.
    """

    def create_spec(
        feature_name: str,
        overview: str,
        requirements: List[str],
    ) -> str:
        reqs = "\n".join(f"- {req}" for req in requirements)
        return f"""# Feature Specification: {feature_name}

## Overview
{overview}

## Functional Requirements
{reqs}

## Success Criteria
- All requirements implemented
"""

    return create_spec


# ============================================================================
# Task and Planning Fixtures
# ============================================================================


@pytest.fixture
def valid_task_list() -> List[Dict[str, Any]]:
    """Given a valid, well-structured task list with dependencies.

    Contains multiple phases with properly linked tasks.
    Use this for testing task processing and dependency resolution.
    """
    return [
        {
            "phase": "0 - Setup",
            "tasks": [
                {
                    "id": "setup-001",
                    "title": "Initialize project structure",
                    "description": (
                        "Create directory structure for authentication module"
                    ),
                    "dependencies": [],
                    "estimated_time": "30m",
                    "priority": "high",
                },
                {
                    "id": "setup-002",
                    "title": "Install authentication dependencies",
                    "description": "Install bcrypt, jwt, and related packages",
                    "dependencies": ["setup-001"],
                    "estimated_time": "15m",
                    "priority": "high",
                },
            ],
        },
        {
            "phase": "1 - Foundation",
            "tasks": [
                {
                    "id": "found-001",
                    "title": "Create user model and schema",
                    "description": "Define User entity with authentication fields",
                    "dependencies": ["setup-002"],
                    "estimated_time": "45m",
                    "priority": "high",
                },
                {
                    "id": "found-002",
                    "title": "Implement password hashing utilities",
                    "description": (
                        "Create secure password hashing and verification functions"
                    ),
                    "dependencies": ["setup-002"],
                    "estimated_time": "30m",
                    "priority": "high",
                },
            ],
        },
    ]


@pytest.fixture
def empty_task_list() -> List[Dict[str, Any]]:
    """Given an empty task list.

    Use this for testing edge cases in task processing.
    """
    return []


@pytest.fixture
def task_with_circular_dependency() -> List[Dict[str, Any]]:
    """Given a task list with circular dependencies.

    Task A depends on B, B depends on C, C depends on A.
    Use this for testing dependency validation.
    """
    return [
        {
            "phase": "1 - Problematic",
            "tasks": [
                {
                    "id": "task-a",
                    "title": "Task A",
                    "description": "Depends on B",
                    "dependencies": ["task-b"],
                    "estimated_time": "30m",
                    "priority": "high",
                },
                {
                    "id": "task-b",
                    "title": "Task B",
                    "description": "Depends on C",
                    "dependencies": ["task-c"],
                    "estimated_time": "30m",
                    "priority": "high",
                },
                {
                    "id": "task-c",
                    "title": "Task C",
                    "description": "Depends on A",
                    "dependencies": ["task-a"],
                    "estimated_time": "30m",
                    "priority": "high",
                },
            ],
        },
    ]


@pytest.fixture
def task_with_missing_dependency() -> List[Dict[str, Any]]:
    """Given a task list referencing non-existent dependencies.

    Use this for testing dependency validation.
    """
    return [
        {
            "phase": "1 - Invalid",
            "tasks": [
                {
                    "id": "task-001",
                    "title": "Task with missing dep",
                    "description": "References non-existent dependency",
                    "dependencies": ["nonexistent-task"],
                    "estimated_time": "30m",
                    "priority": "high",
                },
            ],
        },
    ]


@pytest.fixture
def sample_task_list(valid_task_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Alias for valid_task_list for backward compatibility.

    Use this when test names reference 'sample' instead of 'valid'.
    """
    return valid_task_list


# ============================================================================
# Plugin and Manifest Fixtures
# ============================================================================


@pytest.fixture
def valid_plugin_manifest() -> Dict[str, Any]:
    """Given a valid spec-kit plugin manifest.

    Contains all required plugin metadata fields.
    Use this for testing plugin configuration loading.
    """
    return {
        "name": "spec-kit",
        "version": "2.0.0",
        "description": "Spec Driven Development toolkit",
        "commands": [
            "./commands/speckit.specify.md",
            "./commands/speckit.plan.md",
            "./commands/speckit.implement.md",
        ],
        "skills": [
            "./skills/speckit-orchestrator",
            "./skills/spec-writing",
            "./skills/task-planning",
        ],
        "agents": [
            "./agents/spec-analyzer.md",
            "./agents/task-generator.md",
            "./agents/implementation-executor.md",
        ],
        "dependencies": {"abstract": ">=2.0.0", "superpowers": ">=1.0.0"},
    }


@pytest.fixture
def minimal_plugin_manifest() -> Dict[str, Any]:
    """Given a minimal plugin manifest with only required fields.

    Use this for testing minimal configuration scenarios.
    """
    return {
        "name": "minimal-plugin",
        "version": "1.0.0",
        "description": "Minimal plugin",
    }


@pytest.fixture
def plugin_manifest_missing_version() -> Dict[str, Any]:
    """Given an invalid plugin manifest missing version field.

    Use this for testing manifest validation.
    """
    return {
        "name": "invalid-plugin",
        "description": "Missing version field",
    }


# ============================================================================
# Temporary Directory and File Structure Fixtures
# ============================================================================


@pytest.fixture
def temp_speckit_project(tmp_path: Path) -> Path:
    """Given a complete speckit-enabled project structure.

    Creates a temporary project with:
    - .specify/ directory with scripts and specs subdirectories
    - Mock bash scripts with proper permissions
    - Git repository initialized

    Use this for integration tests requiring full project context.
    """
    project_root = tmp_path / "test-project"
    project_root.mkdir()

    # Create .specify directory
    specify_dir = project_root / ".specify"
    specify_dir.mkdir()

    # Create scripts structure
    scripts_dir = specify_dir / "scripts"
    scripts_dir.mkdir()

    bash_dir = scripts_dir / "bash"
    bash_dir.mkdir()

    # Create a mock create-new-feature.sh script
    create_script = bash_dir / "create-new-feature.sh"
    create_script.write_text("""#!/bin/bash
# Mock script for testing
echo "Mock feature creation script"
""")
    create_script.chmod(0o755)

    # Create specs directory
    specs_dir = specify_dir / "specs"
    specs_dir.mkdir()

    # Create initial git repo
    git_dir = project_root / ".git"
    git_dir.mkdir()

    return project_root


@pytest.fixture
def temp_speckit_project_without_git(tmp_path: Path) -> Path:
    """Given a speckit project structure without git initialization.

    Use this for testing error handling when git is not available.
    """
    project_root = tmp_path / "test-project-no-git"
    project_root.mkdir()

    specify_dir = project_root / ".specify"
    specify_dir.mkdir()

    return project_root


@pytest.fixture
def temp_skill_files(tmp_path: Path) -> Path:
    """Given a complete set of skill files for testing.

    Creates skill directories with SKILL.md metadata files.
    Use this for testing skill discovery and loading.
    """
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Create spec-writing skill
    spec_writing = skills_dir / "spec-writing"
    spec_writing.mkdir()
    (spec_writing / "SKILL.md").write_text("""---
name: spec-writing
description: Create clear specifications
category: specification
---
# Spec Writing Skill
""")

    # Create task-planning skill
    task_planning = skills_dir / "task-planning"
    task_planning.mkdir()
    (task_planning / "SKILL.md").write_text("""---
name: task-planning
description: Generate implementation tasks
category: planning
---
# Task Planning Skill
""")

    # Create orchestrator skill
    orchestrator = skills_dir / "speckit-orchestrator"
    orchestrator.mkdir()
    (orchestrator / "SKILL.md").write_text("""---
name: speckit-orchestrator
description: Workflow orchestration
category: workflow
---
# Orchestrator Skill
""")

    return skills_dir


@pytest.fixture
def temp_skill_files_with_invalid_metadata(tmp_path: Path) -> Path:
    """Given skill files with invalid or malformed metadata.

    Use this for testing error handling in skill loading.
    """
    skills_dir = tmp_path / "invalid-skills"
    skills_dir.mkdir()

    broken_skill = skills_dir / "broken-skill"
    broken_skill.mkdir()
    (broken_skill / "SKILL.md").write_text("""---
name: broken-skill
# Missing description and closing ---
# Broken Skill
""")

    return skills_dir


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Path:
    """Given a mock git repository with multiple branches.

    Creates a minimal git structure with:
    - main branch
    - Feature branches with numeric prefixes

    Use this for testing branch-based workflows.
    """
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    git_dir = repo_dir / ".git"
    git_dir.mkdir()

    # Create mock branch structure
    heads_dir = git_dir / "refs" / "heads"
    heads_dir.mkdir(parents=True)

    # Create some mock branches
    (heads_dir / "main").write_text("commit-main")
    (heads_dir / "1-user-auth").write_text("commit-feature-1")
    (heads_dir / "2-api-integration").write_text("commit-feature-2")

    return repo_dir


# ============================================================================
# Feature Description Fixtures
# ============================================================================


@pytest.fixture
def detailed_feature_description() -> str:
    """Given a detailed natural language feature description.

    Contains clear user intent with specific requirements.
    Use this for testing spec generation from natural language.
    """
    return "I want to add user authentication with email and password login, including role-based access control for admin and regular users"


@pytest.fixture
def vague_feature_description() -> str:
    """Given a vague, underspecified feature description.

    Lacks detail and clarity.
    Use this for testing clarification workflows.
    """
    return "Make the app better"


@pytest.fixture
def empty_feature_description() -> str:
    """Given an empty feature description.

    Use this for testing validation of user input.
    """
    return ""


# ============================================================================
# Mock Tool and Service Fixtures
# ============================================================================


@pytest.fixture
def mock_todowrite() -> Mock:
    """Given a mock TodoWrite tool that always succeeds.

    Use this for testing workflows that use TodoWrite without side effects.
    """
    mock = Mock()
    mock.return_value = {"success": True}
    return mock


@pytest.fixture
def mock_todowrite_failure() -> Mock:
    """Given a mock TodoWrite tool that fails.

    Use this for testing error handling in TodoWrite operations.
    """
    mock = Mock()
    mock.return_value = {"success": False, "error": "TodoWrite failed"}
    return mock


@pytest.fixture
def mock_skill_loader() -> Callable[[str], Dict[str, Any] | None]:
    """Given a mock skill loader function.

    Returns skill metadata for known skills, None for unknown.
    Use this for testing skill-based workflows without file I/O.
    """

    def load_skill(skill_name: str) -> Dict[str, Any] | None:
        skills = {
            "spec-writing": {
                "name": "spec-writing",
                "description": "Create clear specifications",
                "category": "specification",
            },
            "task-planning": {
                "name": "task-planning",
                "description": "Generate implementation tasks",
                "category": "planning",
            },
            "speckit-orchestrator": {
                "name": "speckit-orchestrator",
                "description": "Workflow orchestration",
                "category": "workflow",
            },
        }
        return skills.get(skill_name)

    return load_skill


@pytest.fixture
def workflow_progress_items() -> List[str]:
    """Given standard workflow progress tracking items.

    Use this for asserting on workflow completion steps.
    """
    return [
        "Repository context verified",
        "Prerequisites validated",
        "Command-specific skills loaded",
        "Artifacts created/updated",
        "Verification completed",
    ]


# ============================================================================
# Mock Agent Response Fixtures
# ============================================================================


class MockAgentResponse:
    """Mock agent response for testing agent interactions."""

    def __init__(
        self,
        success: bool = True,
        data: Dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Initialize the mock agent response.

        Args:
            success: Whether the agent call succeeded
            data: Response data payload
            error: Error message if failed
        """
        self.success = success
        self.data = data or {}
        self.error = error


@pytest.fixture
def successful_agent_responses() -> Dict[str, MockAgentResponse]:
    """Given successful responses from all agents.

    Use this for testing happy path agent workflows.
    """
    return {
        "spec_analyzer": MockAgentResponse(
            success=True,
            data={
                "complexity": "medium",
                "estimated_effort": "2-3 days",
                "key_components": [
                    "authentication",
                    "authorization",
                    "session management",
                ],
            },
        ),
        "task_generator": MockAgentResponse(
            success=True,
            data={
                "total_tasks": 12,
                "phases": ["setup", "foundation", "implementation", "integration"],
                "estimated_duration": "2-3 days",
            },
        ),
        "implementation_executor": MockAgentResponse(
            success=True,
            data={
                "implementation_status": "ready",
                "prerequisites_met": True,
                "blocking_issues": [],
            },
        ),
    }


@pytest.fixture
def failed_agent_response() -> MockAgentResponse:
    """Given a failed agent response.

    Use this for testing error handling in agent workflows.
    """
    return MockAgentResponse(
        success=False,
        error="Agent execution failed: timeout",
    )


@pytest.fixture
def agent_response_with_blocking_issues() -> MockAgentResponse:
    """Given an agent response indicating blocking issues.

    Use this for testing workflow handling of prerequisites.
    """
    return MockAgentResponse(
        success=True,
        data={
            "implementation_status": "blocked",
            "prerequisites_met": False,
            "blocking_issues": [
                "Missing authentication library",
                "Database schema not defined",
            ],
        },
    )
