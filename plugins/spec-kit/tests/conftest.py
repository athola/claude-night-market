"""Pytest configuration and shared fixtures for spec-kit testing."""

from unittest.mock import Mock

import pytest


@pytest.fixture
def sample_spec_content():
    """Sample valid specification content."""
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
def sample_task_list():
    """Sample task list from task planning."""
    return [
        {
            "phase": "0 - Setup",
            "tasks": [
                {
                    "id": "setup-001",
                    "title": "Initialize project structure",
                    "description": "Create directory structure for authentication module",
                    "dependencies": [],
                    "estimated_time": "30m",
                    "priority": "high"
                },
                {
                    "id": "setup-002",
                    "title": "Install authentication dependencies",
                    "description": "Install bcrypt, jwt, and related packages",
                    "dependencies": ["setup-001"],
                    "estimated_time": "15m",
                    "priority": "high"
                }
            ]
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
                    "priority": "high"
                },
                {
                    "id": "found-002",
                    "title": "Implement password hashing utilities",
                    "description": "Create secure password hashing and verification functions",
                    "dependencies": ["setup-002"],
                    "estimated_time": "30m",
                    "priority": "high"
                }
            ]
        }
    ]


@pytest.fixture
def sample_plugin_manifest():
    """Sample spec-kit plugin manifest."""
    return {
        "name": "spec-kit",
        "version": "2.0.0",
        "description": "Spec Driven Development toolkit",
        "commands": [
            "./commands/speckit.specify.md",
            "./commands/speckit.plan.md",
            "./commands/speckit.implement.md"
        ],
        "skills": [
            "./skills/speckit-orchestrator",
            "./skills/spec-writing",
            "./skills/task-planning"
        ],
        "agents": [
            "./agents/spec-analyzer.md",
            "./agents/task-generator.md",
            "./agents/implementation-executor.md"
        ],
        "dependencies": {
            "abstract": ">=2.0.0",
            "superpowers": ">=1.0.0"
        }
    }


@pytest.fixture
def temp_speckit_project(tmp_path):
    """Create a temporary speckit-enabled project structure."""
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
def temp_skill_files(tmp_path):
    """Create temporary skill files for testing."""
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
def mock_git_repo(tmp_path):
    """Create a mock git repository with branches."""
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


@pytest.fixture
def sample_feature_description():
    """Sample natural language feature description."""
    return "I want to add user authentication with email and password login, including role-based access control for admin and regular users"


@pytest.fixture
def mock_todowrite():
    """Mock TodoWrite tool for testing."""
    mock = Mock()
    mock.return_value = {"success": True}
    return mock


@pytest.fixture
def mock_skill_loader():
    """Mock skill loading functionality."""
    def load_skill(skill_name):
        skills = {
            "spec-writing": {
                "name": "spec-writing",
                "description": "Create clear specifications",
                "category": "specification"
            },
            "task-planning": {
                "name": "task-planning",
                "description": "Generate implementation tasks",
                "category": "planning"
            },
            "speckit-orchestrator": {
                "name": "speckit-orchestrator",
                "description": "Workflow orchestration",
                "category": "workflow"
            }
        }
        return skills.get(skill_name)

    return load_skill


@pytest.fixture
def workflow_progress_items():
    """Standard workflow progress tracking items."""
    return [
        "Repository context verified",
        "Prerequisites validated",
        "Command-specific skills loaded",
        "Artifacts created/updated",
        "Verification completed"
    ]


class MockAgentResponse:
    """Mock agent response for testing."""

    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data or {}
        self.error = error


@pytest.fixture
def mock_agent_responses():
    """Collection of mock agent responses."""
    return {
        "spec_analyzer": MockAgentResponse(
            success=True,
            data={
                "complexity": "medium",
                "estimated_effort": "2-3 days",
                "key_components": ["authentication", "authorization", "session management"]
            }
        ),
        "task_generator": MockAgentResponse(
            success=True,
            data={
                "total_tasks": 12,
                "phases": ["setup", "foundation", "implementation", "integration"],
                "estimated_duration": "2-3 days"
            }
        ),
        "implementation_executor": MockAgentResponse(
            success=True,
            data={
                "implementation_status": "ready",
                "prerequisites_met": True,
                "blocking_issues": []
            }
        )
    }
