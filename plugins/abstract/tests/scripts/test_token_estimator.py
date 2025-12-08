"""Tests for token_estimator.py."""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from token_estimator import TokenEstimator


class TestTokenEstimator:
    """Test cases for TokenEstimator."""

    def test_estimator_initialization(self):
        """Test estimator initializes correctly."""
        estimator = TokenEstimator()
        assert estimator is not None

    def test_analyze_file_basic(self, temp_skill_file):
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

    def test_analyze_file_token_components(self, temp_skill_file):
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

    def test_analyze_file_nonexistent_fails(self):
        """Test that analyzing nonexistent file raises error."""
        estimator = TokenEstimator()
        with pytest.raises(FileNotFoundError):
            estimator.analyze_file(Path("/nonexistent/file.md"))

    def test_format_analysis_basic(self, temp_skill_file):
        """Test analysis formatting."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(temp_skill_file)
        formatted = estimator.format_analysis(result)

        assert "Total tokens:" in formatted
        assert "Component breakdown:" in formatted
        assert "Recommendations" in formatted

    def test_format_analysis_optimal_range(self, temp_skill_file):
        """Test recommendations for optimal token range."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(temp_skill_file)
        formatted = estimator.format_analysis(result)

        # Our sample should be in optimal or good range
        assert "OPTIMAL" in formatted or "GOOD" in formatted

    def test_analyze_file_with_dependencies(self, temp_skill_dir, sample_skill_content):
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
            main_dir / "SKILL.md", include_dependencies=True
        )

        assert "dependency_tokens" in result
        assert "total_with_dependencies" in result
        assert result["total_with_dependencies"] > result["total_tokens"]

    def test_analyze_file_missing_dependency(self, temp_skill_dir):
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
            skill_dir / "SKILL.md", include_dependencies=True
        )

        assert "missing_dependencies" in result
        assert "nonexistent-dep" in result["missing_dependencies"]

    def test_analyze_directory(self, temp_skill_dir, sample_skill_content):
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

    def test_empty_directory(self, temp_skill_dir):
        """Test analyzing empty directory."""
        estimator = TokenEstimator()
        results = estimator.analyze_directory(temp_skill_dir)

        assert results == []
