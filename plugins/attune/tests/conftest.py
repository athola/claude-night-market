"""Shared fixtures and configuration for attune plugin testing.

This module provides common test fixtures, mocks, and utilities for testing
the attune plugin's project initialization and template rendering capabilities.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# Add the scripts directory to Python path for importing attune scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Add root scripts directory for shared modules (e.g., tasks_manager)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))


@pytest.fixture
def attune_plugin_root():
    """Return the attune plugin root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def mock_project_path(tmp_path):
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def python_project(tmp_path):
    """Create a minimal Python project structure."""
    project_dir = tmp_path / "python-project"
    project_dir.mkdir()

    # Create pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("""[project]
name = "test-project"
version = "0.1.0"
description = "A test project"
""")

    # Create src directory
    src_dir = project_dir / "src" / "test_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text(
        '"""Test project package."""\n\n__version__ = "0.1.0"\n'
    )

    return project_dir


@pytest.fixture
def rust_project(tmp_path):
    """Create a minimal Rust project structure."""
    project_dir = tmp_path / "rust-project"
    project_dir.mkdir()

    # Create Cargo.toml
    cargo = project_dir / "Cargo.toml"
    cargo.write_text("""[package]
name = "test-project"
version = "0.1.0"
edition = "2021"

[dependencies]
""")

    # Create src/main.rs
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.rs").write_text('fn main() {\n    println!("Hello, world!");\n}\n')

    return project_dir


@pytest.fixture
def typescript_project(tmp_path):
    """Create a minimal TypeScript project structure."""
    project_dir = tmp_path / "typescript-project"
    project_dir.mkdir()

    # Create package.json
    package_json = project_dir / "package.json"
    package_json.write_text("""{
  "name": "test-project",
  "version": "0.1.0",
  "description": "A test project"
}
""")

    # Create tsconfig.json
    tsconfig = project_dir / "tsconfig.json"
    tsconfig.write_text("""{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true
  }
}
""")

    # Create src/index.ts
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "index.ts").write_text(
        'export function hello(): string {\n  return "Hello, TypeScript!";\n}\n'
    )

    return project_dir


@pytest.fixture
def git_project(tmp_path):
    """Create a project with git initialized."""
    project_dir = tmp_path / "git-project"
    project_dir.mkdir()

    # Create .git directory
    git_dir = project_dir / ".git"
    git_dir.mkdir()

    return project_dir


@pytest.fixture
def sample_template_variables() -> dict[str, str]:
    """Sample template variables for rendering."""
    return {
        "PROJECT_NAME": "test-project",
        "PROJECT_MODULE": "test_project",
        "PROJECT_DESCRIPTION": "A test project for unit testing",
        "AUTHOR": "Test Author",
        "EMAIL": "test@example.com",
        "LICENSE": "MIT",
        "YEAR": "2025",
        "REPOSITORY": "https://github.com/test/test-project",
        "PYTHON_VERSION": "3.10",
        "PYTHON_VERSION_SHORT": "310",
    }


@pytest.fixture
def sample_template_content() -> str:
    """Sample template file content with variable placeholders."""
    return """# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

## Author

{{AUTHOR}} <{{EMAIL}}>

## License

{{LICENSE}} - Copyright (c) {{YEAR}}

## Repository

{{REPOSITORY}}
"""


@pytest.fixture
def python_template_dir(tmp_path):
    """Create a directory with Python templates."""
    template_root = tmp_path / "templates"
    python_dir = template_root / "python"
    python_dir.mkdir(parents=True)

    # Create Makefile template
    makefile = python_dir / "Makefile.template"
    makefile.write_text("""# {{PROJECT_NAME}} Makefile

.PHONY: help
help:
\t@echo "{{PROJECT_NAME}} - {{PROJECT_DESCRIPTION}}"
\t@echo "Author: {{AUTHOR}}"
""")

    # Create pyproject.toml template
    pyproject = python_dir / "pyproject.toml.template"
    pyproject.write_text("""[project]
name = "{{PROJECT_NAME}}"
version = "0.1.0"
description = "{{PROJECT_DESCRIPTION}}"
authors = [{name = "{{AUTHOR}}", email = "{{EMAIL}}"}]
requires-python = ">=3.{{PYTHON_VERSION}}"
""")

    # Create workflow template
    workflows_dir = python_dir / "workflows"
    workflows_dir.mkdir()
    test_workflow = workflows_dir / "test.yml.template"
    test_workflow.write_text("""name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: make test
""")

    return template_root


@pytest.fixture
def mock_subprocess():
    """Mock subprocess module for testing git operations."""
    mock = Mock()
    mock.run = Mock()
    mock.run.return_value = Mock(returncode=0, stdout=b"", stderr=b"")
    return mock


@pytest.fixture
def mock_validation_result():
    """Create a mock ValidationResult for testing."""
    from validate_project import ValidationResult

    def create_result(name: str, passed: bool, message: str, category: str):
        return ValidationResult(name, passed, message, category)

    return create_result


@pytest.fixture
def sample_project_info() -> dict[str, Any]:
    """Sample project information from detector."""
    return {
        "path": "/path/to/project",
        "language": "python",
        "git_initialized": True,
        "existing_files": {
            ".gitignore": True,
            "Makefile": True,
            ".pre-commit-config.yaml": False,
            "pyproject.toml": True,
        },
    }


@pytest.fixture
def sample_missing_configs() -> list:
    """Sample list of missing configuration files."""
    return [
        ".pre-commit-config.yaml",
        ".github/workflows/test.yml",
        ".github/workflows/lint.yml",
    ]


# Test markers for pytest configuration
def pytest_configure(config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests for workflow orchestration"
    )
    config.addinivalue_line("markers", "performance: Performance and scalability tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to execute")
    config.addinivalue_line("markers", "bdd: Behavior-driven development style tests")


def pytest_collection_modifyitems(config, items) -> None:
    """Add custom markers to items based on their content."""
    for item in items:
        # Add performance marker
        if "performance" in item.nodeid or any(
            keyword in item.nodeid
            for keyword in ["performance", "scalability", "benchmark"]
        ):
            item.add_marker(pytest.mark.performance)

        # Add bdd marker
        if "bdd" in item.nodeid or any(
            keyword in item.nodeid
            for keyword in ["bdd", "behavior", "feature", "scenario"]
        ):
            item.add_marker(pytest.mark.bdd)


# Helper functions for test data
def create_mock_detector_result(language: str, git_init: bool = True) -> dict[str, Any]:
    """Create a mock project detector result."""
    return {
        "path": "/test/project",
        "language": language,
        "git_initialized": git_init,
        "existing_files": {},
    }


def create_mock_template_variables(
    project_name: str = "test-project",
    language: str = "python",
) -> dict[str, str]:
    """Create mock template variables."""
    module_name = project_name.replace("-", "_")
    return {
        "PROJECT_NAME": project_name,
        "PROJECT_MODULE": module_name,
        "PROJECT_DESCRIPTION": f"A {language} test project",
        "AUTHOR": "Test Author",
        "EMAIL": "test@example.com",
        "LICENSE": "MIT",
        "YEAR": "2025",
        "REPOSITORY": f"https://github.com/test/{project_name}",
    }
