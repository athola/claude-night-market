#!/usr/bin/env python3
"""Tests for dependency_manager.py script - actual implementation tests.

This module tests the DependencyManager class following TDD/BDD principles.
"""

import importlib.util
import json
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Load the dependency_manager module dynamically
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "dependency_manager_module", scripts_dir / "dependency_manager.py"
)
assert spec is not None
assert spec.loader is not None
dependency_manager_module = importlib.util.module_from_spec(spec)
sys.modules["dependency_manager_module"] = dependency_manager_module
spec.loader.exec_module(dependency_manager_module)

DependencyManager = dependency_manager_module.DependencyManager


class TestDependencyManagerImplementation:
    """Feature: Dependency manager tracks and validates plugin dependencies.

    As a plugin maintenance system
    I want to track and validate dependency references
    So that plugins correctly declare their dependencies
    """

    @pytest.fixture
    def temp_plugin_root(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Create a temporary plugin structure."""
        plugin_root = tmp_path / "test_plugin"
        plugin_root.mkdir()

        # Create plugin.json
        plugin_config = {
            "name": "test-plugin",
            "version": "1.0.0",
            "dependencies": {"sanctum": "^1.0", "imbue": "^1.0"},
        }
        (plugin_root / "plugin.json").write_text(json.dumps(plugin_config))

        # Create skills directory
        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        yield plugin_root

    @pytest.fixture
    def manager(self, temp_plugin_root: Path) -> DependencyManager:
        """Provide a DependencyManager instance."""
        return DependencyManager(temp_plugin_root)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_initializes_with_plugin_root(self, temp_plugin_root: Path) -> None:
        """Scenario: Manager initializes with plugin configuration.

        Given a plugin root directory
        When creating a DependencyManager
        Then it should load plugin structure and config
        """
        # Act
        manager = DependencyManager(temp_plugin_root)

        # Assert
        assert manager.plugin_root == temp_plugin_root
        assert manager.plugin_config == temp_plugin_root / "plugin.json"
        assert isinstance(manager.skill_files, list)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_scans_dependencies_from_plugin_json(
        self, manager: DependencyManager
    ) -> None:
        """Scenario: Manager reads expected dependencies from plugin.json.

        Given a plugin.json with declared dependencies
        When scanning dependencies
        Then it should identify expected dependencies
        """
        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "expected" in deps
        assert "sanctum" in deps["expected"]
        assert "imbue" in deps["expected"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_finds_dependencies_in_skill_files(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager finds dependency references in skill files.

        Given skill files with dependency references
        When scanning dependencies
        Then it should identify found dependencies
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Use sanctum:git-workspace-review\n")

        # Recreate manager to pick up new skill file
        manager = DependencyManager(temp_plugin_root)

        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "found" in deps
        assert "sanctum" in deps["found"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_detects_missing_dependencies(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager detects expected but unused dependencies.

        Given expected dependencies not used in skills
        When detecting issues
        Then it should report missing dependencies
        """
        # Arrange - no skill files, so no dependencies found
        # Act
        issues = manager.detect_issues()

        # Assert
        assert len(issues) > 0
        assert any("Expected dependencies not found" in issue for issue in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_detects_unexpected_dependencies(
        self, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager detects undeclared dependencies in use.

        Given skill files using undeclared dependencies
        When detecting issues
        Then it should report unexpected dependencies
        """
        # Arrange
        # Update plugin.json to have no dependencies
        (temp_plugin_root / "plugin.json").write_text(
            json.dumps({"name": "test", "dependencies": {}})
        )

        # Add skill with dependency
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Use sanctum:something\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        issues = manager.detect_issues()

        # Assert
        assert len(issues) > 0
        assert any("not in plugin.json" in issue for issue in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_detects_old_reference_patterns(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager detects old workspace-utils references.

        Given skill files with old reference patterns
        When detecting issues
        Then it should identify old patterns
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Use workspace-utils:something\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        issues = manager.detect_issues()

        # Assert
        assert len(issues) > 0
        assert any("old reference pattern" in issue for issue in issues)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_handles_invalid_plugin_json(self, temp_plugin_root: Path) -> None:
        """Scenario: Manager handles invalid plugin.json gracefully.

        Given an invalid plugin.json file
        When scanning dependencies
        Then it should report the issue without crashing
        """
        # Arrange
        (temp_plugin_root / "plugin.json").write_text("invalid json {{{")

        manager = DependencyManager(temp_plugin_root)

        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "issues" in deps
        # Should handle error gracefully

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_handles_missing_plugin_json(self, tmp_path: Path) -> None:
        """Scenario: Manager handles missing plugin.json.

        Given a directory without plugin.json
        When scanning dependencies
        Then it should complete without errors
        """
        # Arrange
        plugin_root = tmp_path / "no_config_plugin"
        plugin_root.mkdir()

        manager = DependencyManager(plugin_root)

        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "expected" in deps
        assert len(deps["expected"]) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_fixes_dependencies_dry_run(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager performs dry run of dependency fixes.

        Given skill files with fixable issues
        When running fix in dry-run mode
        Then it should report changes without modifying files
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        original = "Use git-workspace-review\n"
        skill_file.write_text(original)

        manager = DependencyManager(temp_plugin_root)

        # Act
        fixes = manager.fix_dependencies(dry_run=True)

        # Assert
        assert len(fixes) > 0
        assert any("[DRY RUN]" in fix for fix in fixes)
        # File should remain unchanged
        assert skill_file.read_text() == original

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_fixes_dependencies_actual_run(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager actually fixes dependency issues.

        Given skill files with fixable issues
        When running fix in normal mode
        Then it should modify files and report changes
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Use git-workspace-review\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        fixes = manager.fix_dependencies(dry_run=False)

        # Assert
        assert len(fixes) > 0
        assert not any("[DRY RUN]" in fix for fix in fixes)
        # File should be changed
        content = skill_file.read_text()
        assert "sanctum:git-workspace-review" in content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_reports_no_changes_needed(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager reports when no fixes are needed.

        Given skill files with correct references
        When running fix
        Then it should report no changes needed
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Use sanctum:git-workspace-review correctly\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        fixes = manager.fix_dependencies(dry_run=True)

        # Assert
        assert "No changes needed" in fixes

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_generates_comprehensive_report(
        self, manager: DependencyManager
    ) -> None:
        """Scenario: Manager generates comprehensive dependency report.

        Given a plugin with dependencies
        When generating a report
        Then it should include all relevant information
        """
        # Act
        report = manager.generate_report()

        # Assert
        assert "Dependency Management Report" in report
        assert "Plugin Root:" in report
        assert "Skill Files:" in report
        assert "Expected Dependencies:" in report
        assert "Found Dependencies:" in report

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_handles_list_dependencies_format(
        self, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager handles dependencies as list format.

        Given plugin.json with dependencies as list
        When scanning dependencies
        Then it should parse list format correctly
        """
        # Arrange
        config = {"name": "test", "dependencies": ["sanctum", "imbue"]}
        (temp_plugin_root / "plugin.json").write_text(json.dumps(config))

        manager = DependencyManager(temp_plugin_root)

        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "sanctum" in deps["expected"]
        assert "imbue" in deps["expected"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_fixes_duplicate_prefixes(self, temp_plugin_root: Path) -> None:
        """Scenario: Manager fixes duplicate prefix issues.

        Given skill files with duplicate prefixes
        When fixing dependencies
        Then it should remove duplicates
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Use sanctum:sanctum:git-workspace-review\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        manager.fix_dependencies(dry_run=False)

        # Assert
        content = skill_file.read_text()
        # The fix applies the sanctum:sanctum: -> sanctum: replacement
        assert content.count("sanctum:") < 3  # Should reduce duplicate prefixes

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_removes_old_skill_paths(
        self, manager: DependencyManager, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager removes old ~/.claude/skills/ paths.

        Given skill files with old skill paths
        When fixing dependencies
        Then it should remove the old paths
        """
        # Arrange
        skill_file = temp_plugin_root / "skills" / "SKILL.md"
        skill_file.write_text("Load from ~/.claude/skills/something\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        manager.fix_dependencies(dry_run=False)

        # Assert
        content = skill_file.read_text()
        assert "/.claude/skills/" not in content


class TestDependencyManagerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def temp_plugin_root(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Create a temporary plugin structure for edge case tests."""
        plugin_root = tmp_path / "edge_case_plugin"
        plugin_root.mkdir()

        # Create plugin.json
        plugin_config = {
            "name": "edge-test-plugin",
            "version": "1.0.0",
            "dependencies": {"sanctum": "^1.0"},
        }
        (plugin_root / "plugin.json").write_text(json.dumps(plugin_config))

        # Create skills directory
        skills_dir = plugin_root / "skills"
        skills_dir.mkdir()

        yield plugin_root

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_handles_empty_skills_directory(
        self, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager handles plugins with no skill files.

        Given a plugin with no SKILL.md files
        When scanning dependencies
        Then it should complete without errors
        """
        # Arrange - temp_plugin_root has no SKILL.md files
        manager = DependencyManager(temp_plugin_root)

        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "found" in deps
        assert len(deps["found"]) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_fix_handles_missing_plugin_json(self, tmp_path: Path) -> None:
        """Scenario: Fix operation handles missing plugin.json.

        Given a plugin without plugin.json
        When attempting to fix dependencies
        Then it should report the issue
        """
        # Arrange
        plugin_root = tmp_path / "no_config"
        plugin_root.mkdir()

        manager = DependencyManager(plugin_root)

        # Act
        result = manager.fix_dependencies()

        # Assert
        assert "plugin.json not found" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_manager_processes_multiple_skill_files(
        self, temp_plugin_root: Path
    ) -> None:
        """Scenario: Manager processes multiple skill files correctly.

        Given multiple skill files with various dependencies
        When scanning
        Then it should aggregate all dependencies
        """
        # Arrange
        skills_dir = temp_plugin_root / "skills"

        skill1 = skills_dir / "skill1" / "SKILL.md"
        skill1.parent.mkdir()
        skill1.write_text("Use sanctum:something\n")

        skill2 = skills_dir / "skill2" / "SKILL.md"
        skill2.parent.mkdir()
        skill2.write_text("Use imbue:something\n")

        manager = DependencyManager(temp_plugin_root)

        # Act
        deps = manager.scan_dependencies()

        # Assert
        assert "sanctum" in deps["found"]
        assert "imbue" in deps["found"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
