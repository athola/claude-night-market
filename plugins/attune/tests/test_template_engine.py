"""Test suite for template_engine module.

Following BDD principles with Given/When/Then structure.
"""

import pytest
from template_engine import TemplateEngine, get_default_variables


@pytest.mark.unit
class TestTemplateEngineInitialization:
    """Test TemplateEngine initialization behavior."""

    def test_initialization_with_variables(self, sample_template_variables):
        """Given template variables, when initializing engine, then stores variables."""
        # When
        engine = TemplateEngine(sample_template_variables)

        # Then
        assert engine.variables == sample_template_variables

    def test_initialization_with_empty_variables(self):
        """Given empty variables dict, when initializing engine, then creates engine."""
        # When
        engine = TemplateEngine({})

        # Then
        assert engine.variables == {}


@pytest.mark.unit
class TestTemplateRendering:
    """Test template string rendering behavior."""

    def test_render_simple_variable(self):
        """Given a template with one variable, when rendering, then substitutes variable."""
        # Given
        engine = TemplateEngine({"PROJECT_NAME": "my-project"})
        template = "# {{PROJECT_NAME}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "# my-project"

    def test_render_multiple_variables(self, sample_template_variables):
        """Given a template with multiple variables, when rendering, then substitutes all."""
        # Given
        engine = TemplateEngine(sample_template_variables)
        template = "{{PROJECT_NAME}} by {{AUTHOR}} <{{EMAIL}}>"

        # When
        result = engine.render(template)

        # Then
        assert result == "test-project by Test Author <test@example.com>"

    def test_render_variable_multiple_times(self):
        """Given a template with repeated variable, when rendering, then substitutes all occurrences."""
        # Given
        engine = TemplateEngine({"VAR": "value"})
        template = "{{VAR}} and {{VAR}} again {{VAR}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "value and value again value"

    def test_render_preserves_unknown_variables(self):
        """Given a template with unknown variable, when rendering, then leaves placeholder."""
        # Given
        engine = TemplateEngine({"KNOWN": "value"})
        template = "{{KNOWN}} but {{UNKNOWN}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "value but {{UNKNOWN}}"

    def test_render_with_underscores_in_variable_name(self):
        """Given a variable with underscores, when rendering, then substitutes correctly."""
        # Given
        engine = TemplateEngine({"PROJECT_MODULE": "my_module"})
        template = "module: {{PROJECT_MODULE}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "module: my_module"

    def test_render_with_numbers_in_variable_name(self):
        """Given a variable with numbers, when rendering, then substitutes correctly."""
        # Given
        engine = TemplateEngine({"PYTHON_VERSION_310": "3.10"})
        template = "Python {{PYTHON_VERSION_310}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "Python 3.10"

    def test_render_ignores_lowercase_variables(self):
        """Given a template with lowercase variable, when rendering, then ignores it."""
        # Given
        engine = TemplateEngine({"VAR": "value"})
        template = "{{VAR}} but not {{var}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "value but not {{var}}"

    def test_render_multiline_template(
        self, sample_template_content, sample_template_variables
    ):
        """Given a multiline template, when rendering, then processes all lines."""
        # Given
        engine = TemplateEngine(sample_template_variables)

        # When
        result = engine.render(sample_template_content)

        # Then
        assert "# test-project" in result
        assert "Test Author <test@example.com>" in result
        assert "MIT - Copyright (c) 2025" in result

    def test_render_empty_template(self):
        """Given an empty template, when rendering, then returns empty string."""
        # Given
        engine = TemplateEngine({"VAR": "value"})
        template = ""

        # When
        result = engine.render(template)

        # Then
        assert result == ""

    def test_render_template_without_variables(self):
        """Given a template without variable placeholders, when rendering, then returns unchanged."""
        # Given
        engine = TemplateEngine({"VAR": "value"})
        template = "No variables here!"

        # When
        result = engine.render(template)

        # Then
        assert result == "No variables here!"

    def test_render_converts_values_to_string(self):
        """Given numeric variable values, when rendering, then converts to strings."""
        # Given
        engine = TemplateEngine({"YEAR": 2025, "VERSION": 3.10})
        template = "Year: {{YEAR}}, Version: {{VERSION}}"

        # When
        result = engine.render(template)

        # Then
        assert result == "Year: 2025, Version: 3.1"


@pytest.mark.unit
class TestTemplateFileRendering:
    """Test template file rendering behavior."""

    def test_render_file_creates_output(self, tmp_path):
        """Given a template file, when rendering to output, then creates file."""
        # Given
        template_file = tmp_path / "template.txt.template"
        template_file.write_text("Hello {{NAME}}!")

        output_file = tmp_path / "output.txt"
        engine = TemplateEngine({"NAME": "World"})

        # When
        engine.render_file(template_file, output_file)

        # Then
        assert output_file.exists()
        assert output_file.read_text() == "Hello World!"

    def test_render_file_creates_parent_directories(self, tmp_path):
        """Given output path with non-existent parent, when rendering, then creates directories."""
        # Given
        template_file = tmp_path / "template.txt"
        template_file.write_text("Content: {{VAR}}")

        output_file = tmp_path / "nested" / "deep" / "output.txt"
        engine = TemplateEngine({"VAR": "value"})

        # When
        engine.render_file(template_file, output_file)

        # Then
        assert output_file.exists()
        assert output_file.parent.exists()
        assert output_file.read_text() == "Content: value"

    def test_render_file_overwrites_existing(self, tmp_path):
        """Given an existing output file, when rendering, then overwrites content."""
        # Given
        template_file = tmp_path / "template.txt"
        template_file.write_text("New: {{VAR}}")

        output_file = tmp_path / "output.txt"
        output_file.write_text("Old content")

        engine = TemplateEngine({"VAR": "content"})

        # When
        engine.render_file(template_file, output_file)

        # Then
        assert output_file.read_text() == "New: content"

    def test_render_file_with_complex_template(
        self, tmp_path, sample_template_variables
    ):
        """Given a complex template file, when rendering, then processes correctly."""
        # Given
        template_file = tmp_path / "Makefile.template"
        template_file.write_text("""# {{PROJECT_NAME}} Makefile

.PHONY: help
help:
\t@echo "Project: {{PROJECT_NAME}}"
\t@echo "Author: {{AUTHOR}}"
\t@echo "License: {{LICENSE}}"
""")

        output_file = tmp_path / "Makefile"
        engine = TemplateEngine(sample_template_variables)

        # When
        engine.render_file(template_file, output_file)

        # Then
        content = output_file.read_text()
        assert "# test-project Makefile" in content
        assert 'echo "Project: test-project"' in content
        assert 'echo "Author: Test Author"' in content


@pytest.mark.unit
class TestGetDefaultVariables:
    """Test default template variables generation."""

    def test_get_default_variables_python(self):
        """Given Python project parameters, when getting defaults, then returns Python variables."""
        # When
        variables = get_default_variables("my-project", language="python")

        # Then
        assert variables["PROJECT_NAME"] == "my-project"
        assert variables["PROJECT_MODULE"] == "my_project"
        assert "PYTHON_VERSION" in variables
        assert "PYTHON_VERSION_SHORT" in variables

    def test_get_default_variables_rust(self):
        """Given Rust project parameters, when getting defaults, then returns Rust variables."""
        # When
        variables = get_default_variables("my-project", language="rust")

        # Then
        assert variables["PROJECT_NAME"] == "my-project"
        assert "RUST_EDITION" in variables
        assert variables["RUST_EDITION"] == "2021"

    def test_get_default_variables_typescript(self):
        """Given TypeScript project parameters, when getting defaults, then returns TS variables."""
        # When
        variables = get_default_variables("my-project", language="typescript")

        # Then
        assert variables["PROJECT_NAME"] == "my-project"
        assert "PACKAGE_MANAGER" in variables
        assert variables["PACKAGE_MANAGER"] == "npm"

    def test_project_name_with_hyphens_converts_to_module_name(self):
        """Given a project name with hyphens, when getting defaults, then converts to underscores."""
        # When
        variables = get_default_variables("my-awesome-project")

        # Then
        assert variables["PROJECT_MODULE"] == "my_awesome_project"

    def test_project_name_with_spaces_converts_to_module_name(self):
        """Given a project name with spaces, when getting defaults, then converts to underscores."""
        # When
        variables = get_default_variables("my awesome project")

        # Then
        assert variables["PROJECT_MODULE"] == "my_awesome_project"

    def test_python_version_short_removes_dot(self):
        """Given Python version with dot, when getting defaults, then creates short version."""
        # When
        variables = get_default_variables("test", python_version="3.11")

        # Then
        assert variables["PYTHON_VERSION_SHORT"] == "311"

    def test_includes_current_year(self):
        """Given current time, when getting defaults, then includes current year."""
        # When
        variables = get_default_variables("test")

        # Then
        assert "YEAR" in variables
        # Year should be a string representation of current year (2025 or later)
        assert int(variables["YEAR"]) >= 2025

    def test_includes_author_information(self):
        """Given author details, when getting defaults, then includes in variables."""
        # When
        variables = get_default_variables(
            "test", author="John Doe", email="john@example.com"
        )

        # Then
        assert variables["AUTHOR"] == "John Doe"
        assert variables["EMAIL"] == "john@example.com"

    def test_includes_repository_url(self):
        """Given repository URL, when getting defaults, then includes in variables."""
        # When
        variables = get_default_variables(
            "test", repository="https://github.com/user/repo"
        )

        # Then
        assert variables["REPOSITORY"] == "https://github.com/user/repo"

    def test_includes_license_type(self):
        """Given license type, when getting defaults, then includes in variables."""
        # When
        variables = get_default_variables("test", license_type="Apache-2.0")

        # Then
        assert variables["LICENSE"] == "Apache-2.0"

    def test_includes_description(self):
        """Given project description, when getting defaults, then includes in variables."""
        # When
        variables = get_default_variables("test", description="My awesome project")

        # Then
        assert variables["PROJECT_DESCRIPTION"] == "My awesome project"

    def test_custom_python_version(self):
        """Given custom Python version, when getting defaults, then uses custom version."""
        # When
        variables = get_default_variables("test", python_version="3.12")

        # Then
        assert variables["PYTHON_VERSION"] == "3.12"
        assert variables["PYTHON_VERSION_SHORT"] == "312"

    def test_custom_rust_edition(self):
        """Given custom Rust edition, when getting defaults, then uses custom edition."""
        # When
        variables = get_default_variables("test", language="rust", rust_edition="2024")

        # Then
        assert variables["RUST_EDITION"] == "2024"

    def test_custom_package_manager(self):
        """Given custom package manager, when getting defaults, then uses custom manager."""
        # When
        variables = get_default_variables(
            "test", language="typescript", package_manager="pnpm"
        )

        # Then
        assert variables["PACKAGE_MANAGER"] == "pnpm"


@pytest.mark.bdd
class TestTemplateEngineBehavior:
    """BDD-style tests for TemplateEngine workflows."""

    def test_scenario_render_python_makefile(self, tmp_path):
        """Scenario: Rendering a Python Makefile template.

        Given a Makefile template with project variables
        When I render it with Python project variables
        Then it should create a valid Makefile
        And it should contain the project name
        And it should contain the author information
        """
        # Given
        template_file = tmp_path / "Makefile.template"
        template_file.write_text("""# {{PROJECT_NAME}}

.PHONY: help
help:
\t@echo "{{PROJECT_DESCRIPTION}}"
\t@echo "By {{AUTHOR}}"

.PHONY: test
test:
\tpytest
""")

        variables = get_default_variables(
            "my-project", author="Jane Doe", description="A test project"
        )

        # When
        engine = TemplateEngine(variables)
        output_file = tmp_path / "Makefile"
        engine.render_file(template_file, output_file)

        # Then
        content = output_file.read_text()
        assert "# my-project" in content
        assert '"A test project"' in content
        assert '"By Jane Doe"' in content

    def test_scenario_render_pyproject_toml(self, tmp_path):
        """Scenario: Rendering a pyproject.toml template.

        Given a pyproject.toml template
        When I render it with project metadata
        Then it should create a valid pyproject.toml
        And it should include all metadata fields
        """
        # Given
        template_file = tmp_path / "pyproject.toml.template"
        template_file.write_text("""[project]
name = "{{PROJECT_NAME}}"
version = "0.1.0"
description = "{{PROJECT_DESCRIPTION}}"
authors = [{name = "{{AUTHOR}}", email = "{{EMAIL}}"}]
license = {text = "{{LICENSE}}"}
requires-python = ">=3.{{PYTHON_VERSION}}"
""")

        variables = get_default_variables(
            "awesome-lib",
            author="John Smith",
            email="john@example.com",
            python_version="3.10",
            description="An awesome library",
            license_type="MIT",
        )

        # When
        engine = TemplateEngine(variables)
        output_file = tmp_path / "pyproject.toml"
        engine.render_file(template_file, output_file)

        # Then
        content = output_file.read_text()
        assert 'name = "awesome-lib"' in content
        assert 'description = "An awesome library"' in content
        assert 'name = "John Smith"' in content
        assert 'email = "john@example.com"' in content
        assert 'license = {text = "MIT"}' in content

    def test_scenario_multiple_template_rendering(self, tmp_path):
        """Scenario: Rendering multiple templates with same variables.

        Given multiple template files
        When I render them all with the same variables
        Then all files should be created
        And all should have consistent variable substitution
        """
        # Given
        templates = {
            "README.md.template": "# {{PROJECT_NAME}}\n\n{{PROJECT_DESCRIPTION}}",
            ".gitignore.template": "# {{PROJECT_NAME}} gitignore\n__pycache__/",
            "Makefile.template": "# {{PROJECT_NAME}} build\nhelp:\n\t@echo help",
        }

        for filename, content in templates.items():
            (tmp_path / filename).write_text(content)

        variables = get_default_variables(
            "multi-project", description="Multi template test"
        )
        engine = TemplateEngine(variables)

        # When
        for template_name in templates:
            template_path = tmp_path / template_name
            output_path = tmp_path / template_name.replace(".template", "")
            engine.render_file(template_path, output_path)

        # Then
        for output_name in ["README.md", ".gitignore", "Makefile"]:
            output_file = tmp_path / output_name
            assert output_file.exists()
            content = output_file.read_text()
            assert "multi-project" in content
