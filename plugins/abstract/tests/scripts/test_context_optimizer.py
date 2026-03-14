"""Tests for context_optimizer.py script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import context_optimizer
from context_optimizer import ContextOptimizer, ContextOptimizerCLI

from abstract.config import AbstractConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_config():
    """Default AbstractConfig with context_optimizer populated."""
    return AbstractConfig()


@pytest.fixture
def optimizer(default_config):
    """ContextOptimizer with default config."""
    return ContextOptimizer(default_config)


@pytest.fixture
def skill_file(tmp_path: Path) -> Path:
    """Create a simple skill file."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-skill\ndescription: A test skill\n---\n\n"
        "# Test Skill\n\n## Overview\n\nContent here.\n"
    )
    return skill_file


# ---------------------------------------------------------------------------
# Tests: ContextOptimizer.__init__
# ---------------------------------------------------------------------------


class TestContextOptimizerInit:
    """Tests for ContextOptimizer initialization."""

    @pytest.mark.unit
    def test_init_with_valid_config(self, default_config) -> None:
        """Initializes with valid config without error."""
        optimizer = ContextOptimizer(default_config)
        assert optimizer is not None
        assert optimizer.config is default_config

    @pytest.mark.unit
    def test_init_without_context_optimizer_raises(self) -> None:
        """Config without context_optimizer sub-config raises ValueError."""
        config = AbstractConfig()
        config.context_optimizer = None
        with pytest.raises(ValueError, match="not initialized"):
            ContextOptimizer(config)


# ---------------------------------------------------------------------------
# Tests: analyze_skill_size
# ---------------------------------------------------------------------------


class TestAnalyzeSkillSize:
    """Tests for analyze_skill_size categorization."""

    @pytest.mark.unit
    def test_small_file_categorized_as_small(self, optimizer, tmp_path: Path) -> None:
        """Tiny file is categorized as 'small'."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n\n# Skill\n\nShort content.\n")

        result = optimizer.analyze_skill_size(skill_file)
        assert result["category"] == "small"
        assert result["bytes"] > 0
        assert result["estimated_tokens"] > 0

    @pytest.mark.unit
    def test_missing_file_raises_file_not_found(
        self, optimizer, tmp_path: Path
    ) -> None:
        """Missing file raises FileNotFoundError."""
        missing = tmp_path / "NONEXISTENT.md"
        with pytest.raises(FileNotFoundError):
            optimizer.analyze_skill_size(missing)

    @pytest.mark.unit
    def test_medium_file_categorized_as_medium(self, optimizer, tmp_path: Path) -> None:
        """File in 2000-5000 byte range is 'medium'."""
        skill_file = tmp_path / "SKILL.md"
        content = "---\nname: x\n---\n\n# Skill\n\n" + "word " * 500
        skill_file.write_text(content)

        result = optimizer.analyze_skill_size(skill_file)
        if result["bytes"] <= 2000:
            assert result["category"] == "small"
        elif result["bytes"] <= 5000:
            assert result["category"] == "medium"

    @pytest.mark.unit
    def test_large_file_categorized_correctly(self, optimizer, tmp_path: Path) -> None:
        """File in 5000-15000 byte range is 'large'."""
        skill_file = tmp_path / "SKILL.md"
        content = "---\nname: x\n---\n\n# Skill\n\n" + "word " * 1400
        skill_file.write_text(content)

        result = optimizer.analyze_skill_size(skill_file)
        if result["bytes"] <= 2000:
            assert result["category"] == "small"
        elif result["bytes"] <= 5000:
            assert result["category"] == "medium"
        elif result["bytes"] <= 15000:
            assert result["category"] == "large"
        else:
            assert result["category"] == "xlarge"

    @pytest.mark.unit
    def test_xlarge_file_categorized_as_xlarge(self, optimizer, tmp_path: Path) -> None:
        """File exceeding 15000 bytes is 'xlarge'."""
        skill_file = tmp_path / "SKILL.md"
        content = "---\nname: x\n---\n\n# Skill\n\n" + "word " * 4000
        skill_file.write_text(content)

        result = optimizer.analyze_skill_size(skill_file)
        if result["bytes"] > 15000:
            assert result["category"] == "xlarge"


# ---------------------------------------------------------------------------
# Tests: extract_content_summary
# ---------------------------------------------------------------------------


class TestExtractContentSummary:
    """Tests for extract_content_summary."""

    @pytest.mark.unit
    def test_returns_string(self, optimizer) -> None:
        """Returns a string from multi-section content."""
        content = (
            "---\nname: test\n---\n\n"
            "# Section 1\n\nFirst line.\nSecond line.\n\n"
            "# Section 2\n\nAnother line.\n"
        )
        result = optimizer.extract_content_summary(content, max_section_lines=2)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_includes_section_headers(self, optimizer) -> None:
        """Headers are included in the summary."""
        content = "# Overview\n\nFirst line.\n\n# Usage\n\nSecond line.\n"
        result = optimizer.extract_content_summary(content, max_section_lines=1)
        assert "# Overview" in result
        assert "# Usage" in result

    @pytest.mark.unit
    def test_limits_lines_per_section(self, optimizer) -> None:
        """Only max_section_lines lines from each section are included."""
        content = "# Section\n\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        result = optimizer.extract_content_summary(content, max_section_lines=2)
        lines_in_result = [
            line for line in result.split("\n") if line.startswith("Line")
        ]
        assert len(lines_in_result) <= 2

    @pytest.mark.unit
    def test_content_with_frontmatter(self, optimizer) -> None:
        """Content with frontmatter is handled."""
        content = (
            "---\nname: test\ndescription: A skill\n---\n\n# Section\n\nContent here.\n"
        )
        result = optimizer.extract_content_summary(content, max_section_lines=5)
        assert isinstance(result, str)
        assert "# Section" in result

    @pytest.mark.unit
    def test_empty_content_returns_string(self, optimizer) -> None:
        """Empty content returns empty string."""
        result = optimizer.extract_content_summary("", max_section_lines=5)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: analyze_directory
# ---------------------------------------------------------------------------


class TestAnalyzeDirectory:
    """Tests for analyze_directory."""

    @pytest.mark.unit
    def test_empty_directory_returns_empty_list(
        self, optimizer, tmp_path: Path
    ) -> None:
        """Directory with no skill files returns empty list."""
        results = optimizer.analyze_directory(tmp_path)
        assert results == []

    @pytest.mark.unit
    def test_directory_with_skills_returns_list(
        self, optimizer, tmp_path: Path
    ) -> None:
        """Directory with SKILL.md files returns results."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\n---\n\n# My Skill\n\nContent.\n"
        )

        results = optimizer.analyze_directory(tmp_path)
        assert len(results) == 1
        assert "path" in results[0]
        assert "bytes" in results[0]
        assert "category" in results[0]
        assert "estimated_tokens" in results[0]

    @pytest.mark.unit
    def test_results_sorted_by_size_descending(self, optimizer, tmp_path: Path) -> None:
        """Results are sorted by size in descending order."""
        small_dir = tmp_path / "small-skill"
        small_dir.mkdir()
        (small_dir / "SKILL.md").write_text("---\nname: small\n---\n\nShort.\n")

        large_dir = tmp_path / "large-skill"
        large_dir.mkdir()
        (large_dir / "SKILL.md").write_text("---\nname: large\n---\n\n" + "word " * 500)

        results = optimizer.analyze_directory(tmp_path)
        assert len(results) == 2
        assert results[0]["bytes"] >= results[1]["bytes"]

    @pytest.mark.unit
    def test_analyze_directory_with_exception_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """analyze_directory skips files that raise exceptions."""
        config = AbstractConfig()
        opt = ContextOptimizer(config)

        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\nname: x\n---\n\n# Skill\n")

        original = opt.analyze_skill_size

        def raising_analyze(path):
            raise OSError("Simulated error")

        opt.analyze_skill_size = raising_analyze
        try:
            results = opt.analyze_directory(tmp_path)
            assert results == []
        finally:
            opt.analyze_skill_size = original


# ---------------------------------------------------------------------------
# Tests: report_statistics
# ---------------------------------------------------------------------------


class TestReportStatistics:
    """Tests for report_statistics."""

    @pytest.mark.unit
    def test_empty_results_no_crash(self, optimizer) -> None:
        """Empty results list returns without crash."""
        optimizer.report_statistics([])

    @pytest.mark.unit
    def test_results_with_xlarge_skill_no_crash(
        self, optimizer, tmp_path: Path
    ) -> None:
        """Results with xlarge skill does not crash report."""
        results = [
            {
                "path": "large-skill/SKILL.md",
                "absolute_path": str(tmp_path / "large-skill" / "SKILL.md"),
                "bytes": 20000,
                "category": "xlarge",
                "estimated_tokens": 5000,
            }
        ]
        optimizer.report_statistics(results)

    @pytest.mark.unit
    def test_results_with_normal_skills(self, optimizer) -> None:
        """Normal results processed without crash."""
        results = [
            {
                "path": "skill1/SKILL.md",
                "absolute_path": "/tmp/skill1/SKILL.md",
                "bytes": 500,
                "category": "small",
                "estimated_tokens": 100,
            },
            {
                "path": "skill2/SKILL.md",
                "absolute_path": "/tmp/skill2/SKILL.md",
                "bytes": 1500,
                "category": "small",
                "estimated_tokens": 300,
            },
        ]
        optimizer.report_statistics(results)


# ---------------------------------------------------------------------------
# Tests: ContextOptimizerCLI
# ---------------------------------------------------------------------------


class TestContextOptimizerCLI:
    """Tests for ContextOptimizerCLI instantiation and format_text."""

    @pytest.mark.unit
    def test_cli_can_be_instantiated(self) -> None:
        """ContextOptimizerCLI instantiates without crash."""
        cli = ContextOptimizerCLI()
        assert cli is not None

    @pytest.mark.unit
    def test_cli_format_text_analyze_command(self, tmp_path: Path) -> None:
        """format_text for analyze command returns string."""
        cli = ContextOptimizerCLI()
        data = {
            "command": "analyze",
            "path": str(tmp_path / "SKILL.md"),
            "bytes": 500,
            "category": "small",
            "estimated_tokens": 100,
        }
        result = cli.format_text(data)
        assert isinstance(result, str)
        assert "Skill File" in result or "bytes" in result.lower() or "small" in result

    @pytest.mark.unit
    def test_cli_format_text_report_command(self, tmp_path: Path) -> None:
        """format_text for report command with empty results."""
        cli = ContextOptimizerCLI()
        config = AbstractConfig()
        opt = ContextOptimizer(config)

        data = {
            "command": "report",
            "results": [],
            "optimizer": opt,
        }
        result = cli.format_text(data)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_cli_format_text_stats_command(self, tmp_path: Path) -> None:
        """format_text for stats command."""
        cli = ContextOptimizerCLI()
        config = AbstractConfig()
        opt = ContextOptimizer(config)

        data = {
            "command": "stats",
            "results": [],
            "optimizer": opt,
        }
        result = cli.format_text(data)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_format_text_report_with_results(self, tmp_path: Path) -> None:
        """format_text for report with actual results shows detail."""
        cli = ContextOptimizerCLI()
        config = AbstractConfig()
        opt = ContextOptimizer(config)

        data = {
            "command": "report",
            "results": [
                {
                    "path": "my-skill/SKILL.md",
                    "bytes": 1500,
                    "category": "small",
                    "estimated_tokens": 300,
                }
            ],
            "optimizer": opt,
        }
        result = cli.format_text(data)
        assert isinstance(result, str)
        assert "my-skill/SKILL.md" in result or "Detailed" in result


# ---------------------------------------------------------------------------
# Tests: ContextOptimizerCLI.execute
# ---------------------------------------------------------------------------


class TestContextOptimizerCLIExecute:
    """Tests for ContextOptimizerCLI.execute across all commands."""

    @pytest.mark.unit
    def test_execute_analyze_command(self, tmp_path: Path, skill_file: Path) -> None:
        """Execute with analyze command returns size info."""
        cli = ContextOptimizerCLI()
        args = argparse.Namespace(
            command="analyze",
            path=skill_file,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )

        original_load = context_optimizer.load_config_with_defaults
        original_root = context_optimizer.find_project_root

        def mock_config(root):
            return AbstractConfig()

        def mock_root(path):
            return tmp_path

        context_optimizer.load_config_with_defaults = mock_config
        context_optimizer.find_project_root = mock_root
        try:
            result = cli.execute(args)
        finally:
            context_optimizer.load_config_with_defaults = original_load
            context_optimizer.find_project_root = original_root

        assert result.success is True
        assert result.data is not None
        assert result.data["command"] == "analyze"

    @pytest.mark.unit
    def test_execute_report_command(self, tmp_path: Path, skill_file: Path) -> None:
        """Execute with report command returns directory analysis."""
        cli = ContextOptimizerCLI()
        args = argparse.Namespace(
            command="report",
            path=tmp_path,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )

        original_load = context_optimizer.load_config_with_defaults
        original_root = context_optimizer.find_project_root

        def mock_config(root):
            return AbstractConfig()

        def mock_root(path):
            return tmp_path

        context_optimizer.load_config_with_defaults = mock_config
        context_optimizer.find_project_root = mock_root
        try:
            result = cli.execute(args)
        finally:
            context_optimizer.load_config_with_defaults = original_load
            context_optimizer.find_project_root = original_root

        assert result.success is True
        assert result.data["command"] == "report"

    @pytest.mark.unit
    def test_execute_stats_command(self, tmp_path: Path) -> None:
        """Execute with stats command returns directory analysis."""
        cli = ContextOptimizerCLI()
        args = argparse.Namespace(
            command="stats",
            path=tmp_path,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )

        original_load = context_optimizer.load_config_with_defaults
        original_root = context_optimizer.find_project_root

        def mock_config(root):
            return AbstractConfig()

        def mock_root(path):
            return tmp_path

        context_optimizer.load_config_with_defaults = mock_config
        context_optimizer.find_project_root = mock_root
        try:
            result = cli.execute(args)
        finally:
            context_optimizer.load_config_with_defaults = original_load
            context_optimizer.find_project_root = original_root

        assert result.success is True
        assert result.data["command"] == "stats"

    @pytest.mark.unit
    def test_execute_analyze_nonexistent_file(self, tmp_path: Path) -> None:
        """Execute with analyze on nonexistent file returns failure."""
        cli = ContextOptimizerCLI()
        nonexistent = tmp_path / "nonexistent.md"
        args = argparse.Namespace(
            command="analyze",
            path=nonexistent,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )

        original_load = context_optimizer.load_config_with_defaults
        original_root = context_optimizer.find_project_root

        def mock_config(root):
            return AbstractConfig()

        def mock_root(path):
            return tmp_path

        context_optimizer.load_config_with_defaults = mock_config
        context_optimizer.find_project_root = mock_root
        try:
            result = cli.execute(args)
        finally:
            context_optimizer.load_config_with_defaults = original_load
            context_optimizer.find_project_root = original_root

        assert result.success is False

    @pytest.mark.unit
    def test_execute_analyze_exception_returns_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Execute when analyze_skill_size raises returns failure."""
        cli = ContextOptimizerCLI()
        sf = tmp_path / "SKILL.md"
        sf.write_text("---\nname: x\n---\n\n# Skill\n")

        args = argparse.Namespace(
            command="analyze",
            path=sf,
            config=None,
            output=None,
            format="text",
            verbose=0,
        )

        monkeypatch.setattr(
            context_optimizer,
            "load_config_with_defaults",
            lambda root: AbstractConfig(),
        )
        monkeypatch.setattr(
            context_optimizer, "find_project_root", lambda path: tmp_path
        )
        monkeypatch.setattr(
            ContextOptimizer,
            "analyze_skill_size",
            lambda self, path: (_ for _ in ()).throw(RuntimeError("Simulated error")),
        )

        result = cli.execute(args)
        assert result.success is False
