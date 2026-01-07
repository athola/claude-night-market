"""Integration tests for attune plugin workflows.

Tests complete workflows combining multiple modules.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from project_detector import ProjectDetector
from template_engine import TemplateEngine, get_default_variables
from validate_project import ProjectValidator


@pytest.mark.integration
class TestProjectInitializationWorkflow:
    """Test complete project initialization workflows."""

    def test_python_project_initialization_workflow(self, tmp_path):
        """Integration: Complete Python project initialization.

        Given a new directory
        When I detect the language and initialize the project
        Then all components should work together
        """
        # Given
        project_dir = tmp_path / "test-python-project"
        project_dir.mkdir()

        # Create a basic pyproject.toml to trigger detection
        (project_dir / "pyproject.toml").write_text("""[project]
name = "test-project"
version = "0.1.0"
""")

        # When - Detect language
        detector = ProjectDetector(project_dir)
        language = detector.detect_language()

        # Then - Language detected
        assert language == "python"

        # When - Get template variables
        variables = get_default_variables(
            project_name="test-project",
            language=language,
            author="Test Author",
            email="test@example.com",
        )

        # Then - Variables generated
        assert variables["PROJECT_NAME"] == "test-project"
        assert variables["PROJECT_MODULE"] == "test_project"
        assert "PYTHON_VERSION" in variables

        # When - Render a template
        template_content = "# {{PROJECT_NAME}}\nAuthor: {{AUTHOR}}"
        engine = TemplateEngine(variables)
        rendered = engine.render(template_content)

        # Then - Template rendered correctly
        assert "# test-project" in rendered
        assert "Author: Test Author" in rendered

    def test_rust_project_initialization_workflow(self, tmp_path):
        """Integration: Complete Rust project initialization.

        Given a Rust project
        When I detect and validate it
        Then all tools should recognize it as Rust
        """
        # Given
        project_dir = tmp_path / "test-rust-project"
        project_dir.mkdir()
        (project_dir / "Cargo.toml").write_text("""[package]
name = "test-project"
version = "0.1.0"
edition = "2021"
""")

        # When - Detect language
        detector = ProjectDetector(project_dir)
        language = detector.detect_language()

        # Then
        assert language == "rust"

        # When - Get variables
        variables = get_default_variables(
            project_name="test-project", language="rust", rust_edition="2021"
        )

        # Then
        assert "RUST_EDITION" in variables
        assert variables["RUST_EDITION"] == "2021"

    def test_project_detection_and_validation_workflow(self, tmp_path):
        """Integration: Project detection followed by validation.

        Given a project with some configuration
        When I detect and validate it
        Then validation should use detected information
        """
        # Given - Python project with minimal setup
        project_dir = tmp_path / "validation-test"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (project_dir / "Makefile").write_text("help:\n\t@echo help\n")

        # When - Detect
        detector = ProjectDetector(project_dir)
        language = detector.detect_language()
        missing = detector.get_missing_configurations(language)

        # Then - Should detect Python and identify missing files
        assert language == "python"
        assert ".gitignore" in missing
        assert ".pre-commit-config.yaml" in missing

        # When - Validate
        validator = ProjectValidator(project_dir)
        validator.run_validation(language)

        # Then - Should have validation results
        assert len(validator.results) > 0
        # Makefile should pass
        makefile_results = [r for r in validator.results if r.name == "makefile"]
        assert len(makefile_results) == 1
        assert makefile_results[0].passed is True


@pytest.mark.integration
class TestTemplateRenderingWorkflow:
    """Test template rendering workflows."""

    def test_multi_file_template_rendering(self, tmp_path):
        """Integration: Rendering multiple related templates.

        Given multiple template files
        When I render them with the same variables
        Then all should have consistent values
        """
        # Given
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        templates = {
            "README.md": "# {{PROJECT_NAME}}\n{{PROJECT_DESCRIPTION}}",
            "LICENSE": "Copyright (c) {{YEAR}} {{AUTHOR}}",
            "setup.py": 'name="{{PROJECT_NAME}}"\nauthor="{{AUTHOR}}"',
        }

        for filename, content in templates.items():
            (template_dir / filename).write_text(content)

        variables = get_default_variables(
            "test-project", description="A test project", author="Jane Doe"
        )

        engine = TemplateEngine(variables)

        # When - Render all templates
        rendered = {}
        for filename in templates:
            template_path = template_dir / filename
            content = template_path.read_text()
            rendered[filename] = engine.render(content)

        # Then - All should have consistent variable substitution
        assert "test-project" in rendered["README.md"]
        assert "test-project" in rendered["setup.py"]
        assert "Jane Doe" in rendered["LICENSE"]
        assert "Jane Doe" in rendered["setup.py"]


@pytest.mark.integration
class TestEndToEndProjectSetup:
    """Test end-to-end project setup scenarios."""

    def test_complete_python_project_setup(self, tmp_path):
        """Integration: Complete Python project setup from scratch.

        Given an empty directory
        When I set up a complete Python project
        Then it should have all necessary components
        """
        # Given
        project_dir = tmp_path / "complete-setup"
        project_dir.mkdir()

        # When - Create basic structure
        (project_dir / "pyproject.toml").write_text("""[project]
name = "complete-setup"
version = "0.1.0"

[tool.mypy]
python_version = "3.10"
""")
        (project_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n")
        (project_dir / "Makefile").write_text("help:\n\t@echo help\n")
        (project_dir / ".pre-commit-config.yaml").write_text("repos: []\n")

        src_dir = project_dir / "src" / "complete_setup"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text('__version__ = "0.1.0"\n')

        tests_dir = project_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")

        (project_dir / "README.md").write_text("# complete-setup\n")

        # Then - Detect should work
        detector = ProjectDetector(project_dir)
        assert detector.detect_language() == "python"

        # Then - Validation should mostly pass
        validator = ProjectValidator(project_dir)
        validator.run_validation("python")

        # Check critical validations pass
        pyproject_results = [r for r in validator.results if r.name == "pyproject"]
        assert len(pyproject_results) == 1
        assert pyproject_results[0].passed is True

        makefile_results = [r for r in validator.results if r.name == "makefile"]
        assert len(makefile_results) == 1
        assert makefile_results[0].passed is True
