"""Edge case and error scenario tests for the pensive plugin.

Tests boundary conditions, error handling, and
unexpected input scenarios.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pensive.config.configuration import Configuration
from pensive.exceptions import ConfigurationError
from pensive.plugin.loader import PluginLoader

# Import pensive components for testing
from pensive.skills.architecture_review import ArchitectureReviewSkill
from pensive.skills.bug_review import BugReviewSkill
from pensive.skills.rust_review import RustReviewSkill
from pensive.skills.unified_review import UnifiedReviewSkill
from pensive.workflows.code_review import CodeReviewWorkflow
from pensive.workflows.memory_manager import MemoryManager


class TestEdgeCasesAndErrorScenarios:
    """Test suite for edge cases and error handling."""

    @pytest.mark.unit
    def test_empty_repository_handling(self) -> None:
        """Given an empty repository, when analyzing, then handles gracefully."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_repo = Path(temp_dir)
            # Initialize empty git repository
            git_executable = shutil.which("git") or "git"
            # nosec: S607 - git_executable is from shutil.which, commands are safe
            subprocess.run(
                [git_executable, "init"],
                check=False,
                cwd=empty_repo,
                capture_output=True,
            )
            # nosec: S607 - git_executable is from shutil.which, commands are safe
            subprocess.run(
                [git_executable, "config", "user.email", "test@example.com"],
                check=False,
                cwd=empty_repo,
                capture_output=True,
            )
            # nosec: S607 - git_executable is from shutil.which, commands are safe
            subprocess.run(
                [git_executable, "config", "user.name", "Test"],
                check=False,
                cwd=empty_repo,
                capture_output=True,
            )

            skill = UnifiedReviewSkill()
            context = Mock()
            context.repo_path = empty_repo
            context.get_files.return_value = []

            # Act
            result = skill.analyze(context)

            # Assert
            assert result is not None
            assert "no code files" in result.lower() or "empty" in result.lower()
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.unit
    def test_malformed_file_handling(self) -> None:
        """Given malformed files, when analyzing, then doesn't crash."""
        # Arrange
        skill = UnifiedReviewSkill()
        context = Mock()
        context.repo_path = Path(tempfile.gettempdir())

        # Test with non-UTF-8 content
        malformed_content = b"\xff\xfe\x00\x41\x00\x42\x00\x43"  # Invalid UTF-8
        context.get_file_content.return_value = malformed_content
        context.get_files.return_value = ["broken_file.txt"]

        # Act & Assert - Should not raise exception
        try:
            result = skill.analyze(context)
            assert result is not None
        except UnicodeDecodeError:
            pytest.fail("Should handle non-UTF-8 content gracefully")

    @pytest.mark.unit
    def test_extremely_large_file_handling(self) -> None:
        """Given huge files, analyzer handles memory efficiently."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            # Create a 10MB file
            for i in range(100000):
                f.write(f"fn function_{i}() -> i32 {{ {i} }}\n")
            large_file_path = f.name

        try:
            skill = UnifiedReviewSkill()
            context = Mock()
            context.get_files.return_value = [large_file_path]

            # Mock file reading with size limit
            def mock_read_content(path) -> str:
                if path == large_file_path:
                    return "/* Large file content truncated for analysis */"
                return ""

            context.get_file_content.side_effect = mock_read_content

            # Act
            result = skill.analyze(context)

            # Assert
            assert result is not None
            assert isinstance(result, str)

        finally:
            Path(large_file_path).unlink()

    @pytest.mark.unit
    def test_missing_dependencies_handling(self) -> None:
        """Given missing Cargo.toml, analyzer returns empty results gracefully."""
        # Arrange
        skill = RustReviewSkill()

        context = Mock()
        context.repo_path = Path(tempfile.gettempdir())
        context.get_files.return_value = ["Cargo.toml", "src/main.rs"]
        # Simulate Cargo.toml not being readable
        context.get_file_content.side_effect = FileNotFoundError("Cargo.toml not found")

        # Act
        result = skill.analyze_dependencies(context)

        # Assert - should return empty results dict without crashing
        assert result is not None
        assert isinstance(result, dict)
        assert "dependencies" in result
        assert result["dependencies"] == []

    @pytest.mark.unit
    def test_circular_dependency_detection(self) -> None:
        """Given layering violations, when analyzing, then detects and reports."""
        # Arrange
        skill = ArchitectureReviewSkill()
        context = Mock()

        # Mock dependencies with layering violations
        # (controller directly accessing repository/database)
        dependencies = [
            {"from": "user_controller.py", "to": "user_service.py"},
            {"from": "user_controller.py", "to": "user_repository.py"},  # Violation!
            {"from": "user_service.py", "to": "user_repository.py"},
        ]
        context.analyze_dependencies.return_value = dependencies

        # Act
        coupling_analysis = skill.analyze_coupling(context)

        # Assert - should detect the layering violation
        assert "violations" in coupling_analysis
        assert "coupling_score" in coupling_analysis
        # Should detect controller -> repository violation
        layering_violations = [
            v
            for v in coupling_analysis["violations"]
            if "layering" in v.get("type", "").lower()
        ]
        assert len(layering_violations) > 0

    @pytest.mark.unit
    def test_permission_denied_scenarios(self) -> None:
        """Given permission errors, analyzer handles gracefully."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file and remove read permissions
            test_file = Path(temp_dir) / "restricted.txt"
            test_file.write_text("secret content")
            test_file.chmod(0o000)  # Remove all permissions

            try:
                skill = UnifiedReviewSkill()
                context = Mock()
                context.get_files.return_value = [str(test_file)]

                def mock_read_content(path) -> str:
                    if str(test_file) in path:
                        msg = f"Permission denied: {path}"
                        raise PermissionError(msg)
                    return ""

                context.get_file_content.side_effect = mock_read_content

                # Act
                result = skill.analyze(context)

                # Assert
                assert result is not None
                # Should continue analysis despite permission error

            finally:
                # Restore permissions for cleanup
                test_file.chmod(0o644)

    @pytest.mark.unit
    def test_network_timeout_scenarios(self) -> None:
        """Given network operations, when timeout occurs, then handles gracefully."""
        # Arrange
        skill = BugReviewSkill()
        context = Mock()

        with patch("requests.get") as mock_get:
            # Simulate network timeout
            mock_get.side_effect = TimeoutError("Network timeout")

            # Act
            result = skill.check_external_dependencies(context)

            # Assert
            assert result is not None
            # Should handle timeout without crashing

    @pytest.mark.unit
    def test_memory_pressure_scenarios(self) -> None:
        """Given low memory, analyzer uses fallback strategies."""
        # Arrange
        memory_manager = MemoryManager()

        with patch("psutil.virtual_memory") as mock_memory:
            # Simulate low memory
            mock_memory.return_value.available = 100 * 1024 * 1024  # 100MB only

            # Act
            strategy = memory_manager.get_optimal_strategy(1000)  # Many files

            # Assert
            assert not strategy["concurrent"]  # Should disable concurrent processing
            assert strategy["batch_size"] < 1000  # Should reduce batch size

    @pytest.mark.unit
    def test_configuration_errors(self) -> None:
        """Given invalid config, loader provides helpful errors."""
        # Arrange
        # Test malformed YAML
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yml",
            delete=False,
        ) as malformed_config:
            malformed_config.write("""
pensive:
  skills:
    - unified-review
  invalid_yaml: [unclosed_bracket
            """)
            config_path = Path(malformed_config.name)

        try:
            # Act & Assert
            with pytest.raises(ConfigurationError) as exc_info:
                Configuration.load_from_file(config_path)

            assert (
                "yaml" in str(exc_info.value).lower()
                or "syntax" in str(exc_info.value).lower()
            )

        finally:
            Path(config_path).unlink()

    @pytest.mark.unit
    def test_unicode_and_special_characters(self) -> None:
        """Given unicode/special chars, analyzer handles correctly."""
        # Arrange
        unicode_content = """
// File with unicode and special characters
pub struct 用户 {
    id: u64,
    name: String,  // 名前
    description: String,  // descripción
}

fn résumé() -> String {
    "café résumé naïve façade".to_string()
}

const EMOJI: &str = "🦀 Rust 🚀";
        """

        skill = UnifiedReviewSkill()
        context = Mock()
        context.get_file_content.return_value = unicode_content
        context.get_files.return_value = ["unicode.rs"]

        # Act
        result = skill.analyze(context)

        # Assert
        assert result is not None
        # Should handle unicode without crashing
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_symlink_handling(self) -> None:
        """Given symlinks in repo, analyzer handles correctly."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create real file
            real_file = repo_path / "real.rs"
            real_file.write_text("pub fn real_function() {}")

            # Create symlink
            symlink_file = repo_path / "linked.rs"
            if os.name != "nt":  # Skip on Windows
                symlink_file.symlink_to(real_file)

                skill = UnifiedReviewSkill()
                context = Mock()
                context.get_files.return_value = [str(real_file), str(symlink_file)]
                context.get_file_content.return_value = "pub fn real_function() {}"

                # Act
                result = skill.analyze(context)

                # Assert
                assert result is not None
                # Should handle symlinks without infinite loops

    @pytest.mark.unit
    def test_deep_directory_structures(self) -> None:
        """Given deep directories, analyzer handles efficiently."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create deep nesting
            current_path = repo_path
            for i in range(20):  # 20 levels deep
                current_path = current_path / f"level_{i}"
                current_path.mkdir()

            # Create file at deepest level
            deep_file = current_path / "deep.rs"
            deep_file.write_text("pub fn deep_function() {}")

            skill = UnifiedReviewSkill()
            context = Mock()
            context.get_files.return_value = [str(deep_file)]
            context.get_file_content.return_value = "pub fn deep_function() {}"

            # Act
            result = skill.analyze(context)

            # Assert
            assert result is not None
            # Should handle deep paths without path length issues

    @pytest.mark.unit
    def test_invalid_file_formats(self) -> None:
        """Given invalid formats, analyzer handles gracefully."""
        # Arrange
        invalid_files = {
            "empty_file.txt": "",  # Empty file
            "only_whitespace.py": "   \n\t  \n  ",  # Only whitespace
            "very_long_line.rs": "x" * 10000,  # Very long line
            "special_chars.sql": "SELECT '😀' FROM table",  # SQL with emoji
        }

        skill = UnifiedReviewSkill()

        for filename, content in invalid_files.items():
            context = Mock()
            context.get_files.return_value = [filename]
            context.get_file_content.return_value = content

            # Act & Assert - Should not crash
            try:
                result = skill.analyze(context)
                assert result is not None
            except Exception as e:
                pytest.fail(f"Analysis failed for {filename}: {e}")

    @pytest.mark.unit
    def test_partial_failure_scenarios(self) -> None:
        """Given partial failures, analyzer continues gracefully."""
        # Arrange
        workflow = CodeReviewWorkflow()

        with (
            patch(
                "pensive.skills.rust_review.RustReviewSkill.analyze",
            ) as mock_rust,
            patch(
                "pensive.skills.api_review.ApiReviewSkill.analyze",
            ) as mock_api,
        ):
            # Make one skill fail, another succeed
            mock_rust.side_effect = Exception("Rust analysis failed")
            mock_api.return_value = "API review completed successfully"

            context = Mock()
            context.repo_path = Path(tempfile.gettempdir())
            context.get_files.return_value = ["src/main.rs"]

            # Act
            result = workflow.execute_skills(["rust-review", "api-review"], context)

            # Assert
            assert result is not None
            assert len(result) == 2
            assert (
                result[0] is None or "error" in str(result[0]).lower()
            )  # Failed skill
            assert result[1] is not None  # Successful skill

    @pytest.mark.unit
    def test_plugin_discovery_failures(self) -> None:
        """Given plugin discovery issues, loader handles gracefully."""
        # Arrange
        loader = PluginLoader()

        # Try to load from non-existent directory
        non_existent_path = Path("/non/existent/path")

        # Act
        plugins = loader.discover_plugins(non_existent_path)

        # Assert
        assert isinstance(plugins, list)
        # Should return empty list rather than crashing
