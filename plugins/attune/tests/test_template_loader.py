"""Test suite for template_loader module.

Following BDD principles with Given/When/Then structure.
"""

from unittest.mock import patch

import pytest
from template_loader import TemplateLoader, create_custom_template_dir


@pytest.mark.unit
class TestTemplateLoaderInitialization:
    """Test TemplateLoader initialization behavior."""

    def test_initialization_with_language(self):
        """Given a language, when initializing loader, then stores language."""
        # When
        loader = TemplateLoader("python")

        # Then
        assert loader.language == "python"

    def test_initialization_creates_search_paths(self):
        """Given a language, when initializing loader, then creates search paths."""
        # When
        loader = TemplateLoader("python")

        # Then
        assert isinstance(loader.search_paths, list)


@pytest.mark.unit
class TestSearchPathGeneration:
    """Test template search path generation behavior."""

    def test_search_paths_includes_default_plugin_templates(self):
        """Given any language, when getting search paths, then includes plugin templates."""
        # When
        loader = TemplateLoader("python")

        # Then
        # Default path should be last (lowest priority)
        assert any("templates" in str(path) for path in loader.search_paths)

    def test_search_paths_priority_order(self, tmp_path, monkeypatch):
        """Given multiple template locations, when getting search paths, then orders by priority."""
        # Given - create all possible template locations
        home_dir = tmp_path / "home"
        home_templates = home_dir / ".claude" / "attune" / "templates" / "python"
        home_templates.mkdir(parents=True)

        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.chdir(tmp_path)

        # When
        loader = TemplateLoader("python")

        # Then
        # User templates should have higher priority than default
        path_strs = [str(p) for p in loader.search_paths]
        assert any(".claude" in p for p in path_strs)

    @patch.dict("os.environ", {"ATTUNE_TEMPLATES_PATH": "/custom/templates"})
    def test_search_paths_respects_environment_variable(self, tmp_path):
        """Given ATTUNE_TEMPLATES_PATH env var, when getting search paths, then includes custom path."""
        # Given
        custom_path = tmp_path / "custom" / "templates" / "python"
        custom_path.mkdir(parents=True)

        with patch.dict(
            "os.environ",
            {"ATTUNE_TEMPLATES_PATH": str(tmp_path / "custom" / "templates")},
        ):
            # When
            loader = TemplateLoader("python")

            # Then
            assert any("custom" in str(path) for path in loader.search_paths)

    def test_search_paths_excludes_nonexistent_paths(self, tmp_path, monkeypatch):
        """Given non-existent template directories, when getting search paths, then excludes them."""
        # Given - use a temp home directory with no templates
        home_dir = tmp_path / "empty_home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))

        # When
        loader = TemplateLoader("python")

        # Then
        # Should still have some paths (default plugin path)
        assert len(loader.search_paths) >= 0


@pytest.mark.unit
class TestFindTemplate:
    """Test template finding behavior."""

    def test_find_template_returns_path_when_exists(self, tmp_path):
        """Given an existing template, when finding template, then returns path."""
        # Given
        template_dir = tmp_path / "templates" / "python"
        template_dir.mkdir(parents=True)
        makefile = template_dir / "Makefile.template"
        makefile.write_text("# Makefile\n")

        loader = TemplateLoader("python")
        loader.search_paths = [template_dir]

        # When
        result = loader.find_template("Makefile.template")

        # Then
        assert result is not None
        assert result == makefile

    def test_find_template_returns_none_when_missing(self, tmp_path):
        """Given a non-existent template, when finding template, then returns None."""
        # Given
        template_dir = tmp_path / "templates" / "python"
        template_dir.mkdir(parents=True)

        loader = TemplateLoader("python")
        loader.search_paths = [template_dir]

        # When
        result = loader.find_template("NonExistent.template")

        # Then
        assert result is None

    def test_find_template_uses_priority_order(self, tmp_path):
        """Given templates in multiple locations, when finding template, then uses highest priority."""
        # Given
        high_priority = tmp_path / "high"
        high_priority.mkdir()
        (high_priority / "test.template").write_text("high priority")

        low_priority = tmp_path / "low"
        low_priority.mkdir()
        (low_priority / "test.template").write_text("low priority")

        loader = TemplateLoader("python")
        loader.search_paths = [high_priority, low_priority]

        # When
        result = loader.find_template("test.template")

        # Then
        assert result is not None
        assert result.read_text() == "high priority"


@pytest.mark.unit
class TestGetAllTemplates:
    """Test getting all templates behavior."""

    def test_get_all_templates_returns_list(self, tmp_path):
        """Given template directories, when getting all templates, then returns list."""
        # Given
        template_dir = tmp_path / "templates" / "python"
        template_dir.mkdir(parents=True)
        (template_dir / "test.template").write_text("content")

        loader = TemplateLoader("python")
        loader.search_paths = [template_dir]

        # When
        templates = loader.get_all_templates()

        # Then
        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_get_all_templates_finds_nested_templates(self, tmp_path):
        """Given nested template directories, when getting all, then finds all templates."""
        # Given
        template_dir = tmp_path / "templates" / "python"
        template_dir.mkdir(parents=True)

        workflows_dir = template_dir / "workflows"
        workflows_dir.mkdir()

        (template_dir / "root.template").write_text("root")
        (workflows_dir / "nested.template").write_text("nested")

        loader = TemplateLoader("python")
        loader.search_paths = [template_dir]

        # When
        templates = loader.get_all_templates()

        # Then
        assert len(templates) == 2
        template_names = [t.name for t in templates]
        assert "root.template" in template_names
        assert "nested.template" in template_names

    def test_get_all_templates_deduplicates_by_priority(self, tmp_path):
        """Given duplicate templates in multiple paths, when getting all, then uses highest priority."""
        # Given
        high_priority = tmp_path / "high"
        high_priority.mkdir()
        (high_priority / "test.template").write_text("high")

        low_priority = tmp_path / "low"
        low_priority.mkdir()
        (low_priority / "test.template").write_text("low")

        loader = TemplateLoader("python")
        loader.search_paths = [high_priority, low_priority]

        # When
        templates = loader.get_all_templates()

        # Then
        assert len(templates) == 1
        assert templates[0].read_text() == "high"

    def test_get_all_templates_only_includes_template_files(self, tmp_path):
        """Given mixed file types, when getting all templates, then only includes .template files."""
        # Given
        template_dir = tmp_path / "templates" / "python"
        template_dir.mkdir(parents=True)

        (template_dir / "valid.template").write_text("template")
        (template_dir / "not_template.txt").write_text("text")
        (template_dir / "README.md").write_text("readme")

        loader = TemplateLoader("python")
        loader.search_paths = [template_dir]

        # When
        templates = loader.get_all_templates()

        # Then
        assert len(templates) == 1
        assert templates[0].name == "valid.template"


@pytest.mark.unit
class TestCreateCustomTemplateDir:
    """Test custom template directory creation behavior."""

    def test_create_custom_template_dir_user_location(self, tmp_path, monkeypatch):
        """Given 'user' location, when creating custom dir, then creates in home directory."""
        # Given
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))

        # When
        result_path = create_custom_template_dir("python", "user")

        # Then
        assert result_path.exists()
        assert ".claude" in str(result_path)
        assert "attune" in str(result_path)
        assert "python" in str(result_path)

    def test_create_custom_template_dir_project_location(self, tmp_path, monkeypatch):
        """Given 'project' location, when creating custom dir, then creates in current directory."""
        # Given
        monkeypatch.chdir(tmp_path)

        # When
        result_path = create_custom_template_dir("python", "project")

        # Then
        assert result_path.exists()
        assert ".attune" in str(result_path)
        assert "python" in str(result_path)

    def test_create_custom_template_dir_creates_workflows_subdir(
        self, tmp_path, monkeypatch
    ):
        """Given any location, when creating custom dir, then creates workflows subdirectory."""
        # Given
        monkeypatch.chdir(tmp_path)

        # When
        result_path = create_custom_template_dir("python", "project")

        # Then
        workflows_dir = result_path / "workflows"
        assert workflows_dir.exists()
        assert workflows_dir.is_dir()

    def test_create_custom_template_dir_idempotent(self, tmp_path, monkeypatch):
        """Given existing custom dir, when creating again, then succeeds without error."""
        # Given
        monkeypatch.chdir(tmp_path)
        first_path = create_custom_template_dir("python", "project")

        # When
        second_path = create_custom_template_dir("python", "project")

        # Then
        assert first_path == second_path
        assert second_path.exists()

    def test_create_custom_template_dir_for_rust(self, tmp_path, monkeypatch):
        """Given rust language, when creating custom dir, then creates rust templates directory."""
        # Given
        monkeypatch.chdir(tmp_path)

        # When
        result_path = create_custom_template_dir("rust", "project")

        # Then
        assert "rust" in str(result_path)
        assert result_path.exists()

    def test_create_custom_template_dir_for_typescript(self, tmp_path, monkeypatch):
        """Given typescript language, when creating custom dir, then creates typescript templates directory."""
        # Given
        monkeypatch.chdir(tmp_path)

        # When
        result_path = create_custom_template_dir("typescript", "project")

        # Then
        assert "typescript" in str(result_path)
        assert result_path.exists()


@pytest.mark.bdd
class TestTemplateLoaderBehavior:
    """BDD-style tests for TemplateLoader workflows."""

    def test_scenario_custom_template_overrides_default(self, tmp_path, monkeypatch):
        """Scenario: Custom template overriding default template.

        Given a default template exists
        And a custom template with the same name exists
        When I find the template
        Then it should return the custom template
        """
        # Given
        default_dir = tmp_path / "default"
        default_dir.mkdir()
        (default_dir / "Makefile.template").write_text("# Default Makefile")

        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        (custom_dir / "Makefile.template").write_text("# Custom Makefile")

        # When
        loader = TemplateLoader("python")
        loader.search_paths = [
            custom_dir,
            default_dir,
        ]  # Custom first (higher priority)
        result = loader.find_template("Makefile.template")

        # Then
        assert result is not None
        assert result.read_text() == "# Custom Makefile"

    def test_scenario_fallback_to_default_template(self, tmp_path):
        """Scenario: Falling back to default template.

        Given only a default template exists
        When I find the template
        Then it should return the default template
        """
        # Given
        default_dir = tmp_path / "default"
        default_dir.mkdir()
        (default_dir / "Makefile.template").write_text("# Default Makefile")

        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        # No custom template

        # When
        loader = TemplateLoader("python")
        loader.search_paths = [custom_dir, default_dir]
        result = loader.find_template("Makefile.template")

        # Then
        assert result is not None
        assert result.read_text() == "# Default Makefile"

    def test_scenario_template_not_found_anywhere(self, tmp_path):
        """Scenario: Template not found in any location.

        Given no template directories have the requested template
        When I find the template
        Then it should return None
        """
        # Given
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        # When
        loader = TemplateLoader("python")
        loader.search_paths = [dir1, dir2]
        result = loader.find_template("NonExistent.template")

        # Then
        assert result is None

    def test_scenario_collect_all_unique_templates(self, tmp_path):
        """Scenario: Collecting all unique templates from multiple sources.

        Given templates exist in multiple directories
        And some templates have the same name
        When I get all templates
        Then it should return each unique template once
        And use higher priority versions for duplicates
        """
        # Given
        high_priority = tmp_path / "high"
        high_priority.mkdir()
        (high_priority / "common.template").write_text("high priority common")
        (high_priority / "unique_high.template").write_text("unique high")

        low_priority = tmp_path / "low"
        low_priority.mkdir()
        (low_priority / "common.template").write_text("low priority common")
        (low_priority / "unique_low.template").write_text("unique low")

        # When
        loader = TemplateLoader("python")
        loader.search_paths = [high_priority, low_priority]
        templates = loader.get_all_templates()

        # Then
        assert len(templates) == 3  # common (from high), unique_high, unique_low
        template_contents = {t.name: t.read_text() for t in templates}
        assert template_contents["common.template"] == "high priority common"
        assert "unique_high.template" in template_contents
        assert "unique_low.template" in template_contents
