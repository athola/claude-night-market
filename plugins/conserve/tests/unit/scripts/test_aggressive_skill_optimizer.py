#!/usr/bin/env python3
"""Tests for aggressive_skill_optimizer.py - actual implementation tests."""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the aggressive_skill_optimizer module
scripts_dir = Path(__file__).parent.parent.parent.parent / "scripts"
spec = importlib.util.spec_from_file_location(
    "aggressive_skill_optimizer_module",
    scripts_dir / "aggressive_skill_optimizer.py",
)
assert spec is not None
assert spec.loader is not None
aggressive_skill_optimizer_module = importlib.util.module_from_spec(spec)
sys.modules["aggressive_skill_optimizer_module"] = aggressive_skill_optimizer_module
spec.loader.exec_module(aggressive_skill_optimizer_module)

aggressive_optimize_skill = aggressive_skill_optimizer_module.aggressive_optimize_skill


class TestAggressiveSkillOptimizerImplementation:
    """Feature: Aggressive optimizer removes code blocks and documentation fluff.

    As a skill maintainer
    I want to aggressively optimize large skill files
    So that they remain under size limits
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimizer_replaces_large_code_blocks(self, tmp_path: Path) -> None:
        """Scenario: Optimizer replaces large code blocks with tool references.

        Given a skill with large code blocks
        When optimizing aggressively
        Then large blocks should be replaced with tool references
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        large_code = "\n".join([f"    line_{i}" for i in range(15)])
        content = f"""# Skill

```python
{large_code}
```
"""
        skill_file.write_text(content)

        # Act
        reduction = aggressive_optimize_skill(str(skill_file))

        # Assert
        new_content = skill_file.read_text()
        assert "tools/" in new_content
        assert reduction >= 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimizer_preserves_small_code_blocks(self, tmp_path: Path) -> None:
        """Scenario: Optimizer preserves small code blocks.

        Given a skill with small code blocks
        When optimizing
        Then small blocks should remain unchanged
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = """# Skill

```python
def small():
    pass
```
"""
        skill_file.write_text(content)

        # Act
        aggressive_optimize_skill(str(skill_file))

        # Assert
        new_content = skill_file.read_text()
        assert "def small():" in new_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimizer_removes_documentation_sections(self, tmp_path: Path) -> None:
        """Scenario: Optimizer removes documentation fluff sections.

        Given a skill with detailed implementation sections
        When optimizing
        Then verbose sections should be removed
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = """# Skill

## Overview

Important stuff

## Detailed Implementation

This is verbose documentation that should be removed.

## More Content

Keep this
"""
        skill_file.write_text(content)

        # Act
        reduction = aggressive_optimize_skill(str(skill_file))

        # Assert
        new_content = skill_file.read_text()
        assert "Detailed Implementation" not in new_content
        assert reduction > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimizer_returns_line_reduction(self, tmp_path: Path) -> None:
        """Scenario: Optimizer returns number of lines reduced.

        Given any skill file
        When optimizing
        Then it should return the reduction count
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Simple\n\n" + "Content\n" * 20)

        # Act
        reduction = aggressive_optimize_skill(str(skill_file))

        # Assert
        assert isinstance(reduction, int)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_optimizer_handles_multiple_patterns(self, tmp_path: Path) -> None:
        """Scenario: Optimizer removes multiple documentation sections.

        Given a skill with various verbose sections
        When optimizing
        Then all matching sections should be removed
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        content = """# Skill

## Advanced Usage

Verbose content

## Examples

More verbose content

## Notes

Even more verbose content
"""
        skill_file.write_text(content)

        # Act
        aggressive_optimize_skill(str(skill_file))

        # Assert
        new_content = skill_file.read_text()
        assert "Advanced Usage" not in new_content
        assert "Examples" not in new_content


class TestAggressiveSkillOptimizerEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Scenario: Optimizer handles empty files.

        Given an empty skill file
        When optimizing
        Then it should complete without errors
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("")

        # Act
        reduction = aggressive_optimize_skill(str(skill_file))

        # Assert
        assert reduction >= 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_file_with_no_optimizations_needed(self, tmp_path: Path) -> None:
        """Scenario: Optimizer handles files needing no optimization.

        Given a minimal skill file
        When optimizing
        Then it should return minimal or zero reduction
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("# Minimal Skill\n")

        # Act
        reduction = aggressive_optimize_skill(str(skill_file))

        # Assert
        assert reduction >= 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_file_with_multiple_code_blocks(self, tmp_path: Path) -> None:
        """Scenario: Optimizer handles multiple code blocks correctly.

        Given a skill with multiple large code blocks
        When optimizing
        Then all large blocks should be replaced
        """
        # Arrange
        skill_file = tmp_path / "SKILL.md"
        large_block = "\n".join([f"    code_{i}" for i in range(15)])
        content = f"""# Skill

```python
{large_block}
```

Some text

```python
{large_block}
```
"""
        skill_file.write_text(content)

        # Act
        aggressive_optimize_skill(str(skill_file))

        # Assert
        new_content = skill_file.read_text()
        # Both blocks should reference tools
        assert new_content.count("tools/") >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
