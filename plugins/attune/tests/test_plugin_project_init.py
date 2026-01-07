"""Test suite for plugin_project_init module.

Following BDD principles with Given/When/Then structure.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import functions from plugin_project_init
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from plugin_project_init import (
    create_plugin_structure,
    initialize_plugin_project,
    main,
)


@pytest.mark.unit
class TestCreatePluginStructure:
    """Test create_plugin_structure function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Given empty path, when creating structure, then creates all directories."""
        # Given
        project_path = tmp_path / "test-plugin"
        project_path.mkdir()
        plugin_name = "test-plugin"

        # When
        create_plugin_structure(project_path, plugin_name)

        # Then
        expected_dirs = [
            ".claude-plugin",
            "commands",
            "skills",
            "agents",
            "hooks",
            "scripts",
            "tests",
            "docs",
        ]
        for dir_name in expected_dirs:
            assert (project_path / dir_name).exists(), f"{dir_name} not created"

    def test_creates_valid_plugin_json(self, tmp_path):
        """Given empty path, when creating structure, then creates valid plugin.json."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        plugin_name = "my-plugin"

        # When
        create_plugin_structure(project_path, plugin_name)

        # Then
        plugin_json = project_path / ".claude-plugin" / "plugin.json"
        assert plugin_json.exists()

        data = json.loads(plugin_json.read_text())
        assert data["name"] == plugin_name
        assert data["version"] == "0.1.0"
        assert "commands" in data
        assert "skills" in data
        assert "agents" in data

    def test_creates_valid_metadata_json(self, tmp_path):
        """Given empty path, when creating structure, then creates valid metadata.json."""
        # Given
        project_path = tmp_path / "test-plugin"
        project_path.mkdir()
        plugin_name = "test-plugin"

        # When
        create_plugin_structure(project_path, plugin_name)

        # Then
        metadata_json = project_path / ".claude-plugin" / "metadata.json"
        assert metadata_json.exists()

        data = json.loads(metadata_json.read_text())
        assert data["name"] == plugin_name
        assert data["category"] == "development-tools"
        assert "compatibility" in data

    def test_creates_readme_with_plugin_name(self, tmp_path):
        """Given empty path, when creating structure, then creates README with plugin name."""
        # Given
        project_path = tmp_path / "awesome-plugin"
        project_path.mkdir()
        plugin_name = "awesome-plugin"

        # When
        create_plugin_structure(project_path, plugin_name)

        # Then
        readme = project_path / "README.md"
        assert readme.exists()
        content = readme.read_text()
        assert plugin_name in content
        assert "Installation" in content
        assert "Commands" in content

    def test_prints_creation_messages(self, tmp_path, capsys):
        """Given empty path, when creating structure, then prints progress."""
        # Given
        project_path = tmp_path / "test-plugin"
        project_path.mkdir()
        plugin_name = "test-plugin"

        # When
        create_plugin_structure(project_path, plugin_name)

        # Then
        captured = capsys.readouterr()
        assert "Created" in captured.out


@pytest.mark.unit
class TestInitializePluginProject:
    """Test initialize_plugin_project function."""

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_initializes_git_repository(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given project path, when initializing, then initializes git."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        mock_init_git.assert_called_once_with(project_path, force=False)

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_creates_plugin_structure(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given project path, when initializing, then creates plugin structure."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        assert (project_path / ".claude-plugin" / "plugin.json").exists()
        assert (project_path / "commands").exists()
        assert (project_path / "skills").exists()

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_copies_python_templates(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given project path, when initializing, then copies Python templates."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        mock_copy_templates.assert_called_once()
        call_kwargs = mock_copy_templates.call_args[1]
        assert call_kwargs["language"] == "python"
        assert call_kwargs["project_path"] == project_path

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_creates_scripts_init_file(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given project path, when initializing, then creates scripts/__init__.py."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        assert (project_path / "scripts" / "__init__.py").exists()

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_creates_tests_init_file(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given project path, when initializing, then creates tests/__init__.py."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        assert (project_path / "tests" / "__init__.py").exists()

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_creates_example_skill(self, mock_init_git, mock_copy_templates, tmp_path):
        """Given project path, when initializing, then creates example skill."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        skill_path = project_path / "skills" / "example-skill" / "SKILL.md"
        assert skill_path.exists()
        content = skill_path.read_text()
        assert "name: example-skill" in content
        assert "my-plugin" in content

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_creates_example_command(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given project path, when initializing, then creates example command."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        command_path = project_path / "commands" / "example.md"
        assert command_path.exists()
        content = command_path.read_text()
        assert "name: example" in content

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_creates_structure_test(self, mock_init_git, mock_copy_templates, tmp_path):
        """Given project path, when initializing, then creates plugin structure test."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        test_path = project_path / "tests" / "test_plugin_structure.py"
        assert test_path.exists()
        content = test_path.read_text()
        assert "def test_plugin_json_exists" in content

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_prints_success_message(
        self, mock_init_git, mock_copy_templates, tmp_path, capsys
    ):
        """Given project path, when initializing, then prints success and next steps."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "my-plugin")

        # Then
        captured = capsys.readouterr()
        assert "initialized successfully" in captured.out
        assert "Next steps" in captured.out

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_uses_custom_author_info(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given custom author info, when initializing, then uses it in templates."""
        # Given
        project_path = tmp_path / "my-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(
            project_path,
            "my-plugin",
            author="Test Author",
            email="test@example.com",
        )

        # Then
        call_kwargs = mock_copy_templates.call_args[1]
        variables = call_kwargs["variables"]
        assert variables["AUTHOR"] == "Test Author"


@pytest.mark.unit
class TestMain:
    """Test the main() CLI entry point."""

    @patch("plugin_project_init.initialize_plugin_project")
    def test_main_creates_default_path(self, mock_init):
        """Given plugin name, when running main, then uses default path."""
        # Given
        with patch("sys.argv", ["plugin_project_init.py", "test-plugin"]):
            # When
            main()

            # Then
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["plugin_name"] == "test-plugin"
            assert "plugins/test-plugin" in str(call_kwargs["project_path"])

    @patch("plugin_project_init.initialize_plugin_project")
    def test_main_uses_custom_path(self, mock_init, tmp_path):
        """Given --path argument, when running main, then uses custom path."""
        # Given
        custom_path = tmp_path / "custom-location"
        with patch(
            "sys.argv",
            ["plugin_project_init.py", "my-plugin", "--path", str(custom_path)],
        ):
            # When
            main()

            # Then
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert str(custom_path) in str(call_kwargs["project_path"])

    @patch("plugin_project_init.initialize_plugin_project")
    def test_main_passes_author_info(self, mock_init):
        """Given author arguments, when running main, then passes them."""
        # Given
        with patch(
            "sys.argv",
            [
                "plugin_project_init.py",
                "my-plugin",
                "--author",
                "John Doe",
                "--email",
                "john@example.com",
            ],
        ):
            # When
            main()

            # Then
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["author"] == "John Doe"
            assert call_kwargs["email"] == "john@example.com"

    @patch("plugin_project_init.initialize_plugin_project")
    def test_main_passes_force_flag(self, mock_init):
        """Given --force flag, when running main, then passes force=True."""
        # Given
        with patch("sys.argv", ["plugin_project_init.py", "my-plugin", "--force"]):
            # When
            main()

            # Then
            mock_init.assert_called_once()
            call_kwargs = mock_init.call_args[1]
            assert call_kwargs["force"] is True

    @patch("plugin_project_init.initialize_plugin_project")
    def test_main_creates_directory_if_not_exists(self, mock_init, tmp_path):
        """Given non-existent path, when running main, then creates directory."""
        # Given
        new_path = tmp_path / "new" / "path" / "plugin"
        with patch(
            "sys.argv",
            ["plugin_project_init.py", "my-plugin", "--path", str(new_path)],
        ):
            # When
            main()

            # Then
            assert new_path.exists()


@pytest.mark.unit
class TestPluginProjectInitBehavior:
    """BDD-style tests for plugin project initialization behavior."""

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_scenario_initialize_new_plugin_project(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given a new plugin name
        When initializing plugin project
        Then creates complete plugin structure with all required files
        """
        # Given
        project_path = tmp_path / "new-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "new-plugin")

        # Then - Plugin structure exists
        assert (project_path / ".claude-plugin" / "plugin.json").exists()
        assert (project_path / ".claude-plugin" / "metadata.json").exists()
        assert (project_path / "README.md").exists()

        # Then - Directory structure exists
        assert (project_path / "commands").is_dir()
        assert (project_path / "skills").is_dir()
        assert (project_path / "agents").is_dir()
        assert (project_path / "hooks").is_dir()
        assert (project_path / "scripts").is_dir()
        assert (project_path / "tests").is_dir()
        assert (project_path / "docs").is_dir()

        # Then - Example files exist
        assert (project_path / "skills" / "example-skill" / "SKILL.md").exists()
        assert (project_path / "commands" / "example.md").exists()
        assert (project_path / "tests" / "test_plugin_structure.py").exists()

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_scenario_plugin_json_is_valid_json(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given a new plugin project
        When plugin.json is created
        Then it contains valid JSON with required fields
        """
        # Given
        project_path = tmp_path / "json-test-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "json-test-plugin")

        # Then
        plugin_json = project_path / ".claude-plugin" / "plugin.json"
        data = json.loads(plugin_json.read_text())

        assert data["name"] == "json-test-plugin"
        assert data["version"] == "0.1.0"
        assert isinstance(data["commands"], list)
        assert isinstance(data["skills"], list)
        assert isinstance(data["agents"], list)
        assert isinstance(data["keywords"], list)
        assert "author" in data
        assert data["license"] == "MIT"

    @patch("plugin_project_init.copy_templates")
    @patch("plugin_project_init.initialize_git")
    def test_scenario_generated_test_is_executable(
        self, mock_init_git, mock_copy_templates, tmp_path
    ):
        """Given a new plugin project
        When test file is created
        Then it is syntactically valid Python
        """
        # Given
        project_path = tmp_path / "test-plugin"
        project_path.mkdir()
        mock_init_git.return_value = True
        mock_copy_templates.return_value = []

        # When
        initialize_plugin_project(project_path, "test-plugin")

        # Then - Test file is valid Python
        test_file = project_path / "tests" / "test_plugin_structure.py"
        content = test_file.read_text()

        # Compile to check syntax
        compile(content, str(test_file), "exec")

        # Verify test functions exist
        assert "def test_plugin_json_exists" in content
        assert "def test_metadata_json_exists" in content
        assert "def test_readme_exists" in content
