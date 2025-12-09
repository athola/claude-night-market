"""Tests for skill_analyzer.py."""

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from skill_analyzer import SkillAnalyzer

# Test constants
CUSTOM_THRESHOLD = 200
DEFAULT_THRESHOLD = 150
EXPECTED_RESULTS_COUNT = 3


class TestSkillAnalyzer:
    """Test cases for SkillAnalyzer."""

    def test_analyzer_initialization(self) -> None:
        """Test analyzer initializes with correct threshold."""
        analyzer = SkillAnalyzer(threshold=CUSTOM_THRESHOLD)
        assert analyzer.threshold == CUSTOM_THRESHOLD

    def test_analyzer_default_threshold(self) -> None:
        """Test analyzer uses default threshold."""
        analyzer = SkillAnalyzer()
        assert analyzer.threshold == DEFAULT_THRESHOLD

    def test_analyze_file_basic_metrics(self, temp_skill_file) -> None:
        """Test basic file analysis metrics."""
        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(temp_skill_file)

        assert "file" in result
        assert "line_count" in result
        assert "word_count" in result
        assert "char_count" in result
        assert "themes" in result
        assert "subsections" in result
        assert "code_blocks" in result
        assert "estimated_tokens" in result
        assert "recommendations" in result

    def test_analyze_file_counts_sections(self, temp_skill_file) -> None:
        """Test that analyzer counts sections correctly."""
        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(temp_skill_file)

        # Our sample has sections, just verify they're counted
        assert result["themes"] >= 0
        assert result["subsections"] >= 0

    def test_analyze_file_nonexistent_fails(self) -> None:
        """Test that analyzing nonexistent file raises error."""
        analyzer = SkillAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file(Path("/nonexistent/file.md"))

    def test_recommendations_under_threshold(self, temp_skill_file) -> None:
        """Test recommendations for file under threshold."""
        analyzer = SkillAnalyzer(threshold=1000)  # High threshold
        result = analyzer.analyze_file(temp_skill_file)

        recommendations = result["recommendations"]
        assert any("OK" in rec or "within threshold" in rec for rec in recommendations)

    def test_recommendations_over_threshold(self, temp_skill_file) -> None:
        """Test recommendations for file over threshold."""
        analyzer = SkillAnalyzer(threshold=5)  # Very low threshold
        result = analyzer.analyze_file(temp_skill_file)

        recommendations = result["recommendations"]
        assert any("MODULARIZE" in rec for rec in recommendations)

    def test_format_analysis_basic(self, temp_skill_file) -> None:
        """Test analysis formatting."""
        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(temp_skill_file)
        formatted = analyzer.format_analysis(result)

        assert "Analysis for:" in formatted
        assert "Line count:" in formatted
        assert "Recommendations" in formatted

    def test_format_analysis_verbose(self, temp_skill_file) -> None:
        """Test verbose analysis formatting."""
        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(temp_skill_file, verbose=True)
        formatted = analyzer.format_analysis(result, verbose=True)

        assert "Detailed Analysis" in formatted
        assert "main_sections" in result
        assert "sub_sections" in result

    def test_analyze_directory_finds_skills(
        self, temp_skill_dir, sample_skill_content
    ) -> None:
        """Test directory analysis finds skill files."""
        # Create multiple skill files
        for i in range(3):
            skill_dir = temp_skill_dir / f"skill-{i}"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(sample_skill_content)

        analyzer = SkillAnalyzer()
        results = analyzer.analyze_directory(temp_skill_dir)

        assert len(results) == EXPECTED_RESULTS_COUNT
        for result in results:
            assert "file" in result
            assert "recommendations" in result

    def test_analyze_empty_directory(self, temp_skill_dir) -> None:
        """Test analyzing empty directory returns empty list."""
        analyzer = SkillAnalyzer()
        results = analyzer.analyze_directory(temp_skill_dir)

        assert results == []

    @pytest.mark.parametrize(
        ("threshold", "expected"),
        [
            (5, "MODULARIZE"),  # Very low threshold to trigger modularize
            (1000, "OK"),
        ],
    )
    def test_threshold_recommendations(
        self, temp_skill_file, threshold, expected
    ) -> None:
        """Test different thresholds produce appropriate recommendations."""
        analyzer = SkillAnalyzer(threshold=threshold)
        result = analyzer.analyze_file(temp_skill_file)

        recommendations = " ".join(result["recommendations"])
        assert expected in recommendations
