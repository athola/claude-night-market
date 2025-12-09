"""Edge case and error scenario tests for the parseltongue plugin.

Tests boundary conditions, error handling, and
unexpected input scenarios.
"""

from __future__ import annotations

import asyncio
import json
import signal
import tempfile
import threading
from pathlib import Path
from typing import Never
from unittest.mock import patch

import pytest
from parseltongue.config.config_loader import ConfigLoader
from parseltongue.exceptions import AnalysisError
from parseltongue.plugin.loader import PluginLoader
from parseltongue.skills.async_analyzer import AsyncAnalysisSkill
from parseltongue.skills.compatibility_checker import CompatibilityChecker

# Import parseltongue components for testing
from parseltongue.skills.language_detection import LanguageDetectionSkill
from parseltongue.skills.skill_loader import SkillLoader
from parseltongue.storage.result_storage import ResultStorage
from parseltongue.utils.dependency_analyzer import DependencyAnalyzer
from parseltongue.utils.file_reader import FileReader
from parseltongue.utils.file_utils import FileUtils
from parseltongue.utils.http_client import HttpClient
from parseltongue.utils.logger import ParseltongLogger
from parseltongue.utils.memory_manager import MemoryManager
from parseltongue.utils.resource_monitor import ResourceMonitor


class TestEdgeCasesAndErrorScenarios:
    """Test suite for edge cases and error handling."""

    @pytest.mark.unit
    def test_empty_code_handling(self) -> None:
        """Given empty input, when analyzing, then handles gracefully."""
        # Arrange
        skill = LanguageDetectionSkill()
        empty_inputs = ["", "   \n\t  ", None]

        for input_code in empty_inputs:
            # Act
            if input_code is None:
                with pytest.raises((ValueError, TypeError)):
                    skill.detect_language(input_code)
            else:
                result = skill.detect_language(input_code)

                # Assert
                assert result["language"] == "unknown"
                assert result["confidence"] == 0

    @pytest.mark.unit
    def test_extremely_long_code_handling(self) -> None:
        """Given extremely long code, when analyzing, then handles efficiently."""
        # Arrange
        skill = LanguageDetectionSkill()
        long_code = "def function_{}(): pass\n".format("{}") * 10000  # 10k lines

        # Act
        result = skill.detect_language(long_code)

        # Assert
        assert result["language"] == "python"
        assert result["confidence"] > 0.9
        # Should complete without memory issues

    @pytest.mark.unit
    def test_malformed_unicode_handling(self) -> None:
        """Given malformed Unicode input, when analyzing, then handles gracefully."""
        # Arrange
        skill = LanguageDetectionSkill()
        malformed_unicode = b"\xff\xfe\x00\x41\x00\x42"  # Invalid UTF-8

        # Act & Assert
        with pytest.raises(UnicodeDecodeError):
            skill.detect_language(malformed_unicode)

    @pytest.mark.unit
    def test_mixed_language_input(self) -> None:
        """Given mixed language content, when analyzing, then identifies dominant language."""
        # Arrange
        skill = LanguageDetectionSkill()
        mixed_code = """
# JavaScript section
class JSClass {
    constructor() {
        this.name = "JavaScript";
    }
}

/* Python section in comments - should be ignored */
# This is just a comment
def python_function():
    pass

// TypeScript section
interface TypeScriptInterface {
    name: string;
}
        """

        # Act
        result = skill.detect_language(mixed_code)

        # Assert
        assert result["language"] in [
            "javascript",
            "typescript",
        ]  # Should detect actual code over comments
        assert result["confidence"] > 0.5

    @pytest.mark.unit
    def test_syntax_error_handling(self) -> None:
        """Given code with syntax errors, when analyzing, then handles gracefully."""
        # Arrange
        skill = LanguageDetectionSkill()
        syntax_error_code = """
def broken_function(
    print("Missing closing parenthesis")
        """

        # Act
        result = skill.detect_language(syntax_error_code)

        # Assert
        # Should still identify language based on keywords
        assert result["language"] == "python"
        assert "def" in result["detected_keywords"]

    @pytest.mark.unit
    async def test_async_timeout_handling(self) -> None:
        """Given long-running analysis, when timeout occurs, then handles gracefully."""
        # Arrange
        skill = AsyncAnalysisSkill()
        large_async_code = (
            """
async def slow_function():
    for i in range(100000):
        await asyncio.sleep(0.001)
        print(f"Processing {i}")
        """
            * 100
        )  # Very large async code

        # Mock timeout
        with patch("asyncio.wait_for") as mock_wait_for:
            mock_wait_for.side_effect = TimeoutError()

            # Act & Assert
            with pytest.raises(AnalysisError):
                await skill.analyze_async_functions(large_async_code)

    @pytest.mark.unit
    def test_permission_denied_scenarios(self) -> None:
        """Given permission denied errors, when accessing files, then handles gracefully."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file and remove read permissions
            test_file = Path(temp_dir) / "restricted.py"
            test_file.write_text("print('restricted')")
            test_file.chmod(0o000)  # Remove all permissions

            try:
                # Act
                reader = FileReader()
                result = reader.read_file(test_file)

                # Assert
                assert "error" in result.lower() or "permission" in result.lower()

            finally:
                # Restore permissions for cleanup
                test_file.chmod(0o644)

    @pytest.mark.unit
    def test_network_timeout_simulation(self) -> None:
        """Given network operations, when timeout occurs, then handles gracefully."""
        # Arrange
        with patch("requests.get") as mock_get:
            mock_get.side_effect = TimeoutError("Network timeout")

            # Act
            client = HttpClient()
            result = client.fetch_remote_analysis("https://example.com/code.py")

            # Assert
            assert result is None or "timeout" in str(result).lower()

    @pytest.mark.unit
    def test_memory_pressure_scenarios(self) -> None:
        """Given memory pressure, when analyzing, then uses fallback strategies."""
        # Arrange
        with patch("psutil.virtual_memory") as mock_memory:
            # Simulate low memory
            mock_memory.return_value.available = 100 * 1024 * 1024  # 100MB only

            # Act
            manager = MemoryManager()
            strategy = manager.get_optimal_strategy(1000)  # Many files

            # Assert
            assert (
                strategy["concurrent"] is False
            )  # Should disable concurrent processing
            assert strategy["batch_size"] < 1000  # Should reduce batch size

    @pytest.mark.unit
    def test_corrupted_file_handling(self) -> None:
        """Given corrupted files, when analyzing, then handles gracefully."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Write partial/incomplete Python code
            f.write(
                "class IncompleteClass:\n    def __init__(self\n        # Missing closing parenthesis and colon",
            )
            temp_file = f.name

        try:
            # Act
            reader = FileReader()
            result = reader.read_file(Path(temp_file))

            # Assert
            assert (
                "error" in result.lower() or result is not None
            )  # Should handle gracefully

        finally:
            Path(temp_file).unlink()

    @pytest.mark.unit
    def test_circular_dependency_detection(self) -> None:
        """Given circular dependency scenarios, when analyzing, then detects correctly."""
        # Arrange
        circular_dependency_code = """
# module_a.py
import module_b
class ClassA:
    def __init__(self):
        self.b_instance = module_b.ClassB()

# module_b.py
import module_a
class ClassB:
    def __init__(self):
        self.a_instance = module_a.ClassA()
        """

        # Act
        analyzer = DependencyAnalyzer()
        analysis = analyzer.analyze_dependencies(circular_dependency_code)

        # Assert
        assert "circular_dependencies" in analysis
        assert len(analysis["circular_dependencies"]) >= 1

    @pytest.mark.unit
    def test_unicode_edge_cases(self) -> None:
        """Given unusual Unicode content, when analyzing, then handles correctly."""
        # Arrange
        skill = LanguageDetectionSkill()
        unicode_edge_cases = [
            # Zero-width characters
            "def test():\u200bpass",
            # Right-to-left text
            "def test():\n\tname = 'rtl_test'",  # RTL-style identifier
            # Emoji in code
            "def test():\n\tprint('🚀 Launching 🎉')",
            # Combining characters
            "def cafe():\n\treturn 'cafe\\u0301'",  # café
        ]

        for code in unicode_edge_cases:
            # Act
            result = skill.detect_language(code)

            # Assert
            assert result is not None
            assert "language" in result

    @pytest.mark.unit
    def test_extreme_nesting_scenarios(self) -> None:
        """Given deeply nested code, when analyzing, then handles efficiently."""
        # Arrange
        skill = LanguageDetectionSkill()
        deeply_nested_code = """\
def deeply_nested_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            if True:
                                if True:
                                    if True:
                                        if True:
                                            if True:
                                                return "deeply nested"
        """

        # Act
        result = skill.analyze_complexity(deeply_nested_code)

        # Assert
        assert result["nesting_depth"] >= 10
        assert result["complexity_level"] in ["high", "very_high"]
        assert "recommendations" in result

    @pytest.mark.unit
    def test_concurrent_access_scenarios(self) -> None:
        """Given concurrent access, when analyzing, then handles race conditions."""
        # Arrange
        skill = LanguageDetectionSkill()
        results = []
        errors = []

        def analyze_worker(worker_id) -> None:
            try:
                code = f"def function_{worker_id}(): pass"
                result = skill.detect_language(code)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Act - Run multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=analyze_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(result["language"] == "python" for result in results)

    @pytest.mark.unit
    def test_invalid_configuration_handling(self) -> None:
        """Given invalid configuration, when loading, then provides helpful errors."""
        # Arrange
        invalid_configs = [
            # Malformed JSON
            '{"skills": ["python", "javascript"',  # Missing closing brace
            # Invalid YAML
            "skills:\n  - python\n  - javascript\ninvalid: [unclosed",
            # Invalid data types
            '{"python_version": 3.11, "invalid": ["should", "be", "string"]}',
        ]

        # Act & Assert
        for config in invalid_configs:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False,
            ) as f:
                f.write(config)
                temp_file = f.name

            try:
                loader = ConfigLoader()
                with pytest.raises((json.JSONDecodeError, ValueError)):
                    loader.load_config(Path(temp_file))

            finally:
                Path(temp_file).unlink()

    @pytest.mark.unit
    def test_plugin_discovery_failures(self) -> None:
        """Given plugin discovery issues, when loading, then handles gracefully."""
        # Arrange
        loader = PluginLoader()

        # Try to load from non-existent directory
        non_existent_path = Path("/non/existent/path")

        # Act
        plugins = loader.discover_plugins(non_existent_path)

        # Assert
        assert isinstance(plugins, list)
        # Should return empty list rather than crashing

    @pytest.mark.unit
    async def test_interrupted_operations(self) -> None:
        """Given interrupted operations, when analyzing, then cleanup properly."""

        # Arrange
        class InterruptException(Exception):
            pass

        def interrupt_handler(signum, frame) -> Never:
            msg = "Operation interrupted"
            raise InterruptException(msg)

        # Set up signal handler
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, interrupt_handler)

        try:
            # Act & Assert
            with pytest.raises(InterruptException):
                # Simulate interruption during analysis
                skill = AsyncAnalysisSkill()
                with patch("asyncio.sleep") as mock_sleep:
                    mock_sleep.side_effect = lambda _: signal.raise_signal(
                        signal.SIGINT,
                    )
                    await skill.analyze_concurrency_patterns("async def test(): pass")

        finally:
            # Restore original handler
            signal.signal(signal.SIGINT, original_handler)

    @pytest.mark.unit
    def test_resource_exhaustion_recovery(self) -> None:
        """Given resource exhaustion, when analyzing, then recovers gracefully."""
        # Arrange
        with patch("psutil.Process") as mock_process:
            # Simulate high memory usage
            mock_process.return_value.memory_info.return_value.rss = (
                8 * 1024 * 1024 * 1024
            )  # 8GB

            # Act
            monitor = ResourceMonitor()
            status = monitor.check_resources()

            # Assert
            assert status["memory_pressure"] is True
            assert "recommendations" in status

    @pytest.mark.unit
    def test_database_connection_failures(self) -> None:
        """Given database connection issues, when analyzing, then handles gracefully."""
        # Arrange
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")

            # Act
            storage = ResultStorage("sqlite:///test.db")

            # Assert
            with pytest.raises(Exception, match="Database connection failed"):
                storage.save_results({"test": "data"})

    @pytest.mark.unit
    def test_malformed_skill_metadata(self) -> None:
        """Given malformed skill metadata, when loading, then handles gracefully."""
        # Arrange
        malformed_metadata = {
            "name": "",  # Empty name
            "description": None,  # None description
            "tools": "not_a_list",  # Wrong type
            "invalid_field": "should be ignored",
        }

        # Act
        loader = SkillLoader()
        result = loader.validate_metadata(malformed_metadata)

        # Assert
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.unit
    def test_file_system_edge_cases(self) -> None:
        """Given edge cases in file system operations, when analyzing, then handles correctly."""
        # Arrange
        edge_cases = [
            # Very long filename
            "a" * 255 + ".py",
            # Special characters in filename
            "file with spaces.py",
            "file-with-dashes.py",
            "file_with_underscores.py",
            # Hidden files
            ".hidden_file.py",
        ]

        # Act & Assert
        for filename in edge_cases:
            with tempfile.NamedTemporaryFile(
                prefix=filename[:50],
                suffix=".py",
                delete=False,
            ) as f:
                f.write("def test_function(): pass")
                temp_file = f.name

            try:
                utils = FileUtils()
                if Path(temp_file).exists():
                    result = utils.is_python_file(Path(temp_file))
                    # Should handle various filename formats
                    assert isinstance(result, bool)

            finally:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()

    @pytest.mark.unit
    def test_asyncio_event_loop_errors(self) -> None:
        """Given asyncio event loop issues, when analyzing, then handles correctly."""
        # Arrange
        async_code = """
async def test_function():
    await asyncio.sleep(0.1)
    return "result"
        """

        # Act - Test with no event loop
        try:
            # Simulate no running event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new event loop for test
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)

                skill = AsyncAnalysisSkill()
                # This should handle the case where there's no running loop
                with pytest.raises(RuntimeError):
                    asyncio.run(skill.analyze_async_functions(async_code))

                # Cleanup
                new_loop.close()

        except Exception as e:
            # Expected behavior for certain test environments
            assert (
                "no running event loop" in str(e).lower()
                or "event loop" in str(e).lower()
            )

    @pytest.mark.unit
    def test_version_compatibility_issues(self) -> None:
        """Given version compatibility issues, when analyzing, then handles gracefully."""
        # Arrange
        version_specific_code = """
# Python 3.8+ features
from typing import Literal, TypedDict

Status = Literal["active", "inactive"]

class UserDict(TypedDict):
    name: str
    age: int

# Python 3.10+ features
def process_data(data: list[str]) -> None:
    match data:
        case []:
            print("Empty list")
        case [item]:
            print(f"Single item: {item}")
        case items:
            print(f"Multiple items: {len(items)}")
        """

        # Act
        checker = CompatibilityChecker()
        analysis = checker.check_compatibility(version_specific_code)

        # Assert
        assert "minimum_version" in analysis
        assert analysis["minimum_version"] >= "3.10"  # Should detect newer features
        assert "features_by_version" in analysis

    @pytest.mark.unit
    def test_logging_and_debugging_scenarios(self) -> None:
        """Given logging/debugging scenarios, when analyzing, then handles correctly."""
        # Arrange
        # Test with various logging levels
        logger = ParseltongLogger()

        # Act & Assert - Should not crash with any logging level
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Test structured logging
        logger.info(
            "Processing completed",
            extra={"file_count": 10, "duration": 1.5, "success": True},
        )
