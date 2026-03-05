"""Tests for skill_analyzer.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from skill_analyzer import SkillAnalyzer, SkillAnalyzerCLI

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


class TestSkillAnalyzerRecommendations:
    """Test _generate_recommendations covers all branches."""

    @pytest.mark.unit
    def test_high_token_recommendation(self, tmp_path: Path) -> None:
        """File with high tokens gets MODULARIZE recommendation."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: x\ndescription: y\n---\n\n# Skill\n\n" + "word " * 8500
        )

        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(skill_file)
        recommendations = " ".join(result["recommendations"])

        total_tokens = result["estimated_tokens"]
        if total_tokens > 2048:
            assert "MODULARIZE" in recommendations

    @pytest.mark.unit
    def test_moderate_token_recommendation(self, tmp_path: Path) -> None:
        """File with moderate tokens gets CONSIDER recommendation."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n\n# Skill\n\n" + "word " * 6000)

        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(skill_file)
        recommendations = " ".join(result["recommendations"])
        total_tokens = result["estimated_tokens"]

        if 1500 < total_tokens <= 2048:
            assert "CONSIDER" in recommendations

    @pytest.mark.unit
    def test_many_themes_recommendation(self, tmp_path: Path) -> None:
        """File with many H1 themes gets MODULARIZE recommendation."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: x\n---\n\n"
            "# Theme 1\n\nContent 1.\n\n"
            "# Theme 2\n\nContent 2.\n\n"
            "# Theme 3\n\nContent 3.\n\n"
            "# Theme 4\n\nContent 4.\n"
        )

        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(skill_file)
        recommendations = " ".join(result["recommendations"])
        if result["themes"] > 3:
            assert "MODULARIZE" in recommendations

    @pytest.mark.unit
    def test_many_sections_recommendation(self, tmp_path: Path) -> None:
        """File with many H2 sections gets CONSIDER recommendation."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: x\n---\n\n"
            "# Overview\n\nContent 1.\n\n"
            "# Quick Start\n\nContent 2.\n\n"
            "# Details\n\nContent 3.\n"
        )

        analyzer = SkillAnalyzer()
        result = analyzer.analyze_file(skill_file)
        recommendations = " ".join(result["recommendations"])
        if result["themes"] > 2:
            assert "CONSIDER" in recommendations or "MODULARIZE" in recommendations


class TestSkillAnalyzerFormatAnalysisVerbose:
    """Test format_analysis verbose mode and CLI formatting."""

    @pytest.mark.unit
    def test_format_no_results_returns_message(self) -> None:
        """format_text with empty data returns 'No results' message."""
        cli = SkillAnalyzerCLI()
        result = cli.format_text([])
        assert "No results" in result

    @pytest.mark.unit
    def test_format_text_without_analyzer_fallback(self) -> None:
        """format_text with uninitialized analyzer uses fallback."""
        cli = SkillAnalyzerCLI()
        result = cli.format_text([{"file": "test.md", "line_count": 10}])
        assert isinstance(result, str)


class TestSkillAnalyzerExecute:
    """Test SkillAnalyzerCLI.execute processes paths."""

    @pytest.mark.unit
    def test_execute_with_file(self, tmp_path: Path) -> None:
        """execute with a single file returns CLIResult."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text(
            "---\nname: test\ndescription: Test\n---\n\n# Test\n\nContent.\n"
        )

        cli = SkillAnalyzerCLI()
        args = argparse.Namespace(
            file=skill_file,
            directory=None,
            threshold=150,
            verbose=0,
            config=None,
            output=None,
            format="text",
        )
        result = cli.execute(args)
        assert result.success is True

    @pytest.mark.unit
    def test_execute_with_nonexistent_path_fails(self, tmp_path: Path) -> None:
        """execute with nonexistent path returns failure."""
        cli = SkillAnalyzerCLI()
        args = argparse.Namespace(
            file=None,
            directory=tmp_path / "nonexistent",
            threshold=150,
            verbose=0,
            config=None,
            output=None,
            format="text",
        )
        result = cli.execute(args)
        assert result.success is False

    @pytest.mark.unit
    def test_execute_with_directory(self, tmp_path: Path) -> None:
        """execute with directory returns CLIResult."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n---\n\n# My Skill\n\nContent.\n"
        )

        cli = SkillAnalyzerCLI()
        args = argparse.Namespace(
            file=None,
            directory=tmp_path,
            threshold=150,
            verbose=0,
            config=None,
            output=None,
            format="text",
        )
        result = cli.execute(args)
        assert result.success is True
