#!/usr/bin/env python3
"""Tests for quick_skill_optimizer.py - actual implementation tests.

This module tests the quick skill optimizer following TDD/BDD principles.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the quick_skill_optimizer module
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "quick_skill_optimizer_module", scripts_dir / "quick_skill_optimizer.py"
)
assert spec is not None
assert spec.loader is not None
quick_skill_optimizer_module = importlib.util.module_from_spec(spec)
sys.modules["quick_skill_optimizer_module"] = quick_skill_optimizer_module
spec.loader.exec_module(quick_skill_optimizer_module)

extract_python_blocks = quick_skill_optimizer_module.extract_python_blocks
create_tool_reference = quick_skill_optimizer_module.create_tool_reference
quick_optimize_skill = quick_skill_optimizer_module.quick_optimize_skill


class TestQuickSkillOptimizerImplementation:
    """Feature: Quick skill optimizer extracts large code blocks to tools.

    As a skill maintainer
    I want to extract large Python blocks to external tools
    So that skills remain focused and readable
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_finds_python_blocks(self, tmp_path: Path) -> None:
        """Scenario: Extractor finds Python code blocks in skill file.

        Given a skill file with Python code blocks
        When extracting blocks
        Then it should find all Python blocks
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = """# Skill

```python
def long_function():
    # Line 1
    # Line 2
    # Line 3
    # Line 4
    # Line 5
    # Line 6
    # Line 7
    # Line 8
    # Line 9
    # Line 10
    # Line 11
    # Line 12
    # Line 13
    # Line 14
    # Line 15
    # Line 16
    pass
```
"""
        skill_file.write_text(content)

        # Act
        blocks = extract_python_blocks(str(skill_file))

        # Assert
        assert len(blocks) > 0
        assert blocks[0]["lines"] > 15

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extract_ignores_small_blocks(self, tmp_path: Path) -> None:
        """Scenario: Extractor ignores small code blocks.

        Given a skill file with small Python blocks
        When extracting blocks
        Then small blocks should be ignored
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = """# Skill

```python
def small_function():
    pass
```
"""
        skill_file.write_text(content)

        # Act
        blocks = extract_python_blocks(str(skill_file))

        # Assert
        assert len(blocks) == 0  # Should ignore small blocks

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_create_tool_reference_formats_correctly(self) -> None:
        """Scenario: Tool reference creator generates standardized format.

        Given a function name and tool name
        When creating a reference
        Then it should include usage examples
        """
        # Act
        result = create_tool_reference("process_data", "data_processor")

        # Assert
        assert "tools/data_processor.py" in result
        assert "process data" in result
        assert "```bash" in result
        assert "--input" in result

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quick_optimize_creates_tools_directory(self, tmp_path: Path) -> None:
        """Scenario: Optimizer creates tools directory if needed.

        Given a skill file without tools directory
        When optimizing
        Then it should create the tools directory
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = (
            """# Skill

```python
def very_long_function():
    # Many lines to trigger extraction
"""
            + "\n    # Line\n" * 20
            + """    pass
```
"""
        )
        skill_file.write_text(content)

        # Act
        quick_optimize_skill(str(skill_file))

        # Assert
        tools_dir = tmp_path / "tools"
        assert tools_dir.exists()
        assert tools_dir.is_dir()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quick_optimize_extracts_large_functions(self, tmp_path: Path) -> None:
        """Scenario: Optimizer extracts large functions to tool files.

        Given a skill with large code blocks
        When optimizing
        Then it should create tool files
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = (
            """# Skill

```python
def large_function():
    # Generate 20 lines
"""
            + "\n    pass\n" * 20
            + """
```
"""
        )
        skill_file.write_text(content)

        # Act
        count = quick_optimize_skill(str(skill_file))

        # Assert
        assert count > 0
        tools_dir = tmp_path / "tools"
        tool_files = list(tools_dir.glob("*.py"))
        assert len(tool_files) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quick_optimize_returns_count(self, tmp_path: Path) -> None:
        """Scenario: Optimizer returns count of extracted functions.

        Given a skill file
        When optimizing
        Then it should return the number of extractions
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Simple skill\n")

        # Act
        count = quick_optimize_skill(str(skill_file))

        # Assert
        assert isinstance(count, int)
        assert count >= 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_extracted_tool_is_executable(self, tmp_path: Path) -> None:
        """Scenario: Extracted tool files are executable.

        Given extracted tool files
        When checking permissions
        Then files should be executable
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = (
            """# Skill

```python
def function_to_extract():
"""
            + "\n    pass\n" * 20
            + """
```
"""
        )
        skill_file.write_text(content)

        # Act
        quick_optimize_skill(str(skill_file))

        # Assert
        tools_dir = tmp_path / "tools"
        tool_files = list(tools_dir.glob("*.py"))
        if tool_files:
            import os

            assert os.access(tool_files[0], os.X_OK)


class TestQuickSkillOptimizerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_skill_without_code_blocks(self, tmp_path: Path) -> None:
        """Scenario: Optimizer handles skills without code blocks.

        Given a skill file with no Python blocks
        When optimizing
        Then it should complete without errors
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Simple skill with no code\n")

        # Act
        count = quick_optimize_skill(str(skill_file))

        # Assert
        assert count == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_multiple_large_blocks(self, tmp_path: Path) -> None:
        """Scenario: Optimizer handles multiple large code blocks.

        Given a skill with multiple large blocks
        When optimizing
        Then it should extract all large blocks
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = (
            """# Skill

```python
def function1():
"""
            + "\n    pass\n" * 20
            + """
```

```python
def function2():
"""
            + "\n    pass\n" * 20
            + """
```
"""
        )
        skill_file.write_text(content)

        # Act
        count = quick_optimize_skill(str(skill_file))

        # Assert
        assert count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
