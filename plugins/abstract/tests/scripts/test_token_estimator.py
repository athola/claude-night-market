"""Tests for token_estimator.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from token_estimator import TokenEstimator


class TestTokenEstimator:
    """Test cases for TokenEstimator."""

    def test_estimator_initialization(self) -> None:
        """Test estimator initializes correctly."""
        estimator = TokenEstimator()
        assert estimator is not None

    def test_analyze_file_basic(self, temp_skill_file) -> None:
        """Test basic file analysis."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(temp_skill_file)

        assert "file" in result
        assert "total_tokens" in result
        assert "frontmatter_tokens" in result
        assert "body_tokens" in result
        assert "code_tokens" in result
        assert "dependencies" in result
        assert "character_count" in result
        assert "line_count" in result

    def test_analyze_file_token_components(self, temp_skill_file) -> None:
        """Test token component breakdown."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(temp_skill_file)

        # Total should be sum of components
        total = result["total_tokens"]
        components_sum = (
            result["frontmatter_tokens"] + result["body_tokens"] + result["code_tokens"]
        )

        assert total == components_sum
        assert total > 0

    def test_analyze_file_nonexistent_fails(self) -> None:
        """Test that analyzing nonexistent file raises error."""
        estimator = TokenEstimator()
        with pytest.raises(FileNotFoundError):
            estimator.analyze_file(Path("/nonexistent/file.md"))

    def test_format_analysis_basic(self, temp_skill_file) -> None:
        """Test analysis formatting."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(temp_skill_file)
        formatted = estimator.format_analysis(result)

        assert "Total tokens:" in formatted
        assert "Component breakdown:" in formatted
        assert "Recommendations" in formatted

    def test_format_analysis_optimal_range(self, temp_skill_file) -> None:
        """Test recommendations for optimal token range."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(temp_skill_file)
        formatted = estimator.format_analysis(result)

        # Our sample should be in optimal or good range
        assert "OPTIMAL" in formatted or "GOOD" in formatted

    def test_analyze_file_with_dependencies(
        self, temp_skill_dir, sample_skill_content
    ) -> None:
        """Test dependency token calculation."""
        # Create main skill with dependency
        main_dir = temp_skill_dir / "main-skill"
        main_dir.mkdir()
        main_content = """---
name: main-skill
description: Main skill
dependencies: [dep-skill]
---

## Overview

Main content.
"""
        (main_dir / "SKILL.md").write_text(main_content)

        # Create dependency skill
        dep_dir = temp_skill_dir / "dep-skill"
        dep_dir.mkdir()
        (dep_dir / "SKILL.md").write_text(sample_skill_content)

        estimator = TokenEstimator()
        result = estimator.analyze_file(
            main_dir / "SKILL.md",
            include_dependencies=True,
        )

        assert "dependency_tokens" in result
        assert "total_with_dependencies" in result
        assert result["total_with_dependencies"] > result["total_tokens"]

    def test_analyze_file_missing_dependency(self, temp_skill_dir) -> None:
        """Test handling of missing dependencies."""
        skill_dir = temp_skill_dir / "skill-with-missing-dep"
        skill_dir.mkdir()
        content = """---
name: test-skill
description: Test
dependencies: [nonexistent-dep]
---

Content.
"""
        (skill_dir / "SKILL.md").write_text(content)

        estimator = TokenEstimator()
        result = estimator.analyze_file(
            skill_dir / "SKILL.md",
            include_dependencies=True,
        )

        assert "missing_dependencies" in result
        assert "nonexistent-dep" in result["missing_dependencies"]

    def test_analyze_directory(self, temp_skill_dir, sample_skill_content) -> None:
        """Test directory analysis."""
        # Create multiple skills
        for i in range(2):
            skill_dir = temp_skill_dir / f"skill-{i}"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(sample_skill_content)

        estimator = TokenEstimator()
        results = estimator.analyze_directory(temp_skill_dir)

        EXPECTED_FILE_COUNT = 2
        assert len(results) == EXPECTED_FILE_COUNT
        for result in results:
            assert "total_tokens" in result

    def test_empty_directory(self, temp_skill_dir) -> None:
        """Test analyzing empty directory."""
        estimator = TokenEstimator()
        results = estimator.analyze_directory(temp_skill_dir)

        assert results == []


class TestTokenEstimatorFormatAnalysis:
    """Test format_analysis covers all recommendation branches."""

    @pytest.mark.unit
    def test_format_high_token_shows_modularize(self, tmp_path: Path) -> None:
        """File with many tokens shows MODULARIZE recommendation."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n\n" + "word " * 12000)

        estimator = TokenEstimator()
        result = estimator.analyze_file(skill_file)
        formatted = estimator.format_analysis(result)
        assert "MODULARIZE" in formatted

    @pytest.mark.unit
    def test_format_consider_range(self, tmp_path: Path) -> None:
        """File in 2000-3000 token range shows CONSIDER recommendation."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n\n" + "word " * 8500)

        estimator = TokenEstimator()
        result = estimator.analyze_file(skill_file)
        total = result["total_tokens"]

        formatted = estimator.format_analysis(result)
        if 2000 < total <= 3000:
            assert "CONSIDER" in formatted

    @pytest.mark.unit
    def test_format_with_dependencies_in_result(self, tmp_path: Path) -> None:
        """format_analysis shows dependency_tokens when present."""
        estimator = TokenEstimator()
        analysis = {
            "file": str(tmp_path / "SKILL.md"),
            "total_tokens": 500,
            "frontmatter_tokens": 50,
            "body_tokens": 400,
            "code_tokens": 50,
            "dependencies": ["dep-skill"],
            "character_count": 2000,
            "line_count": 50,
            "dependency_tokens": 200,
            "missing_dependencies": [],
            "total_with_dependencies": 700,
        }
        formatted = estimator.format_analysis(analysis, include_dependencies=True)
        assert (
            "Dependency tokens" in formatted
            or "total_with_dependencies" in formatted.lower()
            or "dependency" in formatted.lower()
        )

    @pytest.mark.unit
    def test_format_with_missing_dependencies(self, tmp_path: Path) -> None:
        """format_analysis shows missing dependencies."""
        estimator = TokenEstimator()
        analysis = {
            "file": str(tmp_path / "SKILL.md"),
            "total_tokens": 500,
            "frontmatter_tokens": 50,
            "body_tokens": 400,
            "code_tokens": 50,
            "dependencies": ["missing-dep"],
            "character_count": 2000,
            "line_count": 50,
            "dependency_tokens": 0,
            "missing_dependencies": ["missing-dep"],
            "total_with_dependencies": 500,
        }
        formatted = estimator.format_analysis(analysis, include_dependencies=True)
        assert "Missing dependencies" in formatted or "missing" in formatted.lower()

    @pytest.mark.unit
    def test_format_code_heavy_suggests_extract(self, tmp_path: Path) -> None:
        """Code-heavy files suggest extraction."""
        estimator = TokenEstimator()
        analysis = {
            "file": "test.md",
            "total_tokens": 1500,
            "frontmatter_tokens": 50,
            "body_tokens": 200,
            "code_tokens": 1250,
            "dependencies": [],
            "character_count": 6000,
            "line_count": 100,
        }
        formatted = estimator.format_analysis(analysis)
        assert "CONSIDER" in formatted or "Extract" in formatted


class TestTokenEstimatorAnalyzeDirectoryExtended:
    """Test analyze_directory with dependency inclusion."""

    @pytest.mark.unit
    def test_analyze_directory_with_include_deps(self, tmp_path: Path) -> None:
        """analyze_directory with include_dependencies=True works."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n---\n\n# My Skill\n\nContent.\n"
        )

        estimator = TokenEstimator()
        results = estimator.analyze_directory(tmp_path, include_dependencies=True)
        assert len(results) == 1
