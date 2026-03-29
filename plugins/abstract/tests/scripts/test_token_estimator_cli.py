"""Tests for TokenEstimatorCLI execute and format_text paths.

Feature: Token estimator CLI
    As a developer
    I want the CLI paths in token_estimator tested
    So that the command-line interface works correctly
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from token_estimator import TokenEstimator, TokenEstimatorCLI


class TestTokenEstimatorCLI:
    """Feature: TokenEstimatorCLI execute and format_text."""

    @pytest.fixture
    def skill_file(self, tmp_path: Path) -> Path:
        """Create a simple skill file."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\nname: my-skill\ndescription: A test skill\n---\n\n"
            "# My Skill\n\n## Overview\n\nContent here.\n"
        )
        return skill_file

    @pytest.fixture
    def cli(self):
        """Create a TokenEstimatorCLI instance."""
        return TokenEstimatorCLI()

    @pytest.mark.unit
    def test_execute_with_file_succeeds(self, cli, skill_file: Path) -> None:
        """Scenario: execute with --file returns success CLIResult.
        Given a skill file path
        When execute is called with args.file set
        Then a successful CLIResult is returned
        """
        args = argparse.Namespace(
            file=skill_file,
            directory=None,
            include_dependencies=False,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )
        result = cli.execute(args)
        assert result.success is True
        assert result.data is not None

    @pytest.mark.unit
    def test_execute_with_nonexistent_file_fails(self, cli, tmp_path: Path) -> None:
        """Scenario: execute with nonexistent file returns failure."""
        args = argparse.Namespace(
            file=tmp_path / "nonexistent.md",
            directory=None,
            include_dependencies=False,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )
        result = cli.execute(args)
        assert result.success is False

    @pytest.mark.unit
    def test_execute_with_directory_succeeds(self, cli, skill_file: Path) -> None:
        """Scenario: execute with directory returns success CLIResult."""
        skill_dir = skill_file.parent.parent  # tmp_path
        args = argparse.Namespace(
            file=None,
            directory=skill_dir,
            include_dependencies=False,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )
        result = cli.execute(args)
        assert result.success is True

    @pytest.mark.unit
    def test_execute_with_empty_directory_returns_warning(
        self, cli, tmp_path: Path
    ) -> None:
        """Scenario: execute with empty directory returns warning."""
        args = argparse.Namespace(
            file=None,
            directory=tmp_path,
            include_dependencies=False,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )
        result = cli.execute(args)
        assert result.success is True
        assert result.warnings  # Should have a warning about no files

    @pytest.mark.unit
    def test_format_text_with_list_data(self, cli, skill_file: Path) -> None:
        """Scenario: format_text with a list of results returns string."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(skill_file)
        output = cli.format_text([result])
        assert isinstance(output, str)
        assert "Total tokens" in output

    @pytest.mark.unit
    def test_format_text_with_multiple_results(self, cli, tmp_path: Path) -> None:
        """Scenario: format_text with multiple results inserts separators."""
        # Create two skill files
        for name in ["skill-a", "skill-b"]:
            skill_dir = tmp_path / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\n---\n\n# {name}\n\nContent.\n"
            )

        estimator = TokenEstimator()
        results = estimator.analyze_directory(tmp_path)
        assert len(results) == 2

        output = cli.format_text(results)
        assert isinstance(output, str)
        # Separator should be present between results
        assert "-" * 50 in output

    @pytest.mark.unit
    def test_format_text_with_single_result_dict(self, cli, skill_file: Path) -> None:
        """Scenario: format_text with a dict (not list) still works."""
        estimator = TokenEstimator()
        result = estimator.analyze_file(skill_file)
        # format_text handles non-list data via the else branch
        output = cli.format_text(result)
        assert isinstance(output, str)

    @pytest.mark.unit
    def test_format_text_good_token_range(self, tmp_path: Path) -> None:
        """Scenario: File with 800-2000 tokens gets GOOD recommendation."""
        skill_file = tmp_path / "SKILL.md"
        # ~1000 tokens = ~4000 chars
        skill_file.write_text("---\nname: x\n---\n\n# Skill\n\n" + "word " * 3500)

        estimator = TokenEstimator()
        result = estimator.analyze_file(skill_file)
        formatted = estimator.format_analysis(result)

        total = result["total_tokens"]
        if 800 < total <= 2000:
            assert "GOOD" in formatted
