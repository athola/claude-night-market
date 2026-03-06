"""Tests for the migration_analyzer script.

Feature: Plugin migration analysis
    As a developer
    I want migration paths analyzed
    So that overlapping functionality with superpowers is identified
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from migration_analyzer import (  # noqa: E402
    MigrationAnalyzer,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analyzer(tmp_path: Path) -> MigrationAnalyzer:
    """Given a MigrationAnalyzer operating in tmp_path."""
    import os  # noqa: PLC0415

    original = os.getcwd()
    os.chdir(tmp_path)
    yield MigrationAnalyzer("test-plugin")
    os.chdir(original)


@pytest.fixture
def analyzer_with_commands(tmp_path: Path) -> tuple[MigrationAnalyzer, Path]:
    """Given an analyzer with a commands/ directory."""
    import os  # noqa: PLC0415

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    original = os.getcwd()
    os.chdir(tmp_path)
    yield MigrationAnalyzer("test-plugin"), commands_dir
    os.chdir(original)


# ---------------------------------------------------------------------------
# Tests: MigrationAnalyzer.__init__
# ---------------------------------------------------------------------------


class TestMigrationAnalyzerInit:
    """Feature: MigrationAnalyzer initialization."""

    @pytest.mark.unit
    def test_plugin_name_stored(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: plugin_name is stored on initialization."""
        assert analyzer.plugin_name == "test-plugin"

    @pytest.mark.unit
    def test_overlap_mappings_populated(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Default overlap mappings are loaded."""
        assert len(analyzer.overlap_mappings) > 0
        assert "test-driven-development" in analyzer.overlap_mappings

    @pytest.mark.unit
    def test_compatibility_validator_created(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Compatibility validator instance is created."""
        assert analyzer.compatibility_validator is not None


# ---------------------------------------------------------------------------
# Tests: analyze_plugin
# ---------------------------------------------------------------------------


class TestAnalyzePlugin:
    """Feature: Analyze plugin commands for overlap."""

    @pytest.mark.unit
    def test_no_command_file_returns_empty(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Missing command file returns empty overlaps.
        Given no commands directory
        When analyze_plugin is called
        Then empty dict is returned
        """
        result = analyzer.analyze_plugin("nonexistent-command")
        assert result == {}

    @pytest.mark.unit
    def test_command_with_tdd_patterns(
        self, analyzer_with_commands: tuple[MigrationAnalyzer, Path]
    ) -> None:
        """Scenario: Command with TDD patterns shows TDD overlap.
        Given a command file with RED phase, GREEN phase, REFACTOR phase
        When analyze_plugin is called
        Then test-driven-development overlap is detected
        """
        mgr, commands_dir = analyzer_with_commands
        cmd_file = commands_dir / "my-command.md"
        cmd_file.write_text(
            "# TDD Command\n"
            "RED phase: write failing test\n"
            "GREEN phase: minimal code\n"
            "REFACTOR phase: improve code\n"
            "write failing test first\n"
            "watch it fail\n"
            "minimal code to pass\n"
            "test-first approach\n"
        )
        overlaps = mgr.analyze_plugin("my-command")
        assert "test-driven-development" in overlaps
        assert overlaps["test-driven-development"]["confidence"] > 0.5

    @pytest.mark.unit
    def test_command_with_no_patterns_returns_empty(
        self, analyzer_with_commands: tuple[MigrationAnalyzer, Path]
    ) -> None:
        """Scenario: Command with no known patterns returns empty overlaps."""
        mgr, commands_dir = analyzer_with_commands
        cmd_file = commands_dir / "unrelated.md"
        cmd_file.write_text("# Unrelated\nDoes something completely unrelated.\n")
        overlaps = mgr.analyze_plugin("unrelated")
        assert overlaps == {}


# ---------------------------------------------------------------------------
# Tests: _calculate_overlap
# ---------------------------------------------------------------------------


class TestCalculateOverlap:
    """Feature: Overlap confidence calculation."""

    @pytest.mark.unit
    def test_full_pattern_match_returns_one(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: All patterns matched returns 1.0 confidence."""
        patterns = ["hello", "world"]
        result = analyzer._calculate_overlap("hello world", patterns)
        assert result == 1.0

    @pytest.mark.unit
    def test_partial_match_returns_fraction(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Half patterns matched returns 0.5 confidence."""
        patterns = ["hello", "world"]
        result = analyzer._calculate_overlap("hello there", patterns)
        assert result == 0.5

    @pytest.mark.unit
    def test_no_match_returns_zero(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: No patterns matched returns 0.0 confidence."""
        patterns = ["hello", "world"]
        result = analyzer._calculate_overlap("something else", patterns)
        assert result == 0.0

    @pytest.mark.unit
    def test_empty_patterns_returns_zero(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Empty patterns list returns 0.0."""
        result = analyzer._calculate_overlap("hello world", [])
        assert result == 0.0

    @pytest.mark.unit
    def test_case_insensitive_matching(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Pattern matching is case-insensitive."""
        patterns = ["RED phase"]
        result = analyzer._calculate_overlap("red phase is first", patterns)
        assert result == 1.0


# ---------------------------------------------------------------------------
# Tests: _get_matched_patterns
# ---------------------------------------------------------------------------


class TestGetMatchedPatterns:
    """Feature: Get list of matched patterns."""

    @pytest.mark.unit
    def test_returns_matching_patterns(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Returns only matched patterns."""
        patterns = ["hello", "world", "foo"]
        result = analyzer._get_matched_patterns("hello world", patterns)
        assert "hello" in result
        assert "world" in result
        assert "foo" not in result

    @pytest.mark.unit
    def test_returns_empty_when_no_match(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Returns empty list when no patterns match."""
        patterns = ["hello", "world"]
        result = analyzer._get_matched_patterns("something else", patterns)
        assert result == []


# ---------------------------------------------------------------------------
# Tests: _calculate_migration_priority
# ---------------------------------------------------------------------------


class TestCalculateMigrationPriority:
    """Feature: Migration priority calculation from overlaps."""

    @pytest.mark.unit
    def test_empty_overlaps_returns_zero(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: No overlaps returns 0.0 priority."""
        result = analyzer._calculate_migration_priority({})
        assert result == 0.0

    @pytest.mark.unit
    def test_single_overlap_uses_confidence(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Single overlap returns its confidence as priority."""
        overlaps = {"tdd": {"confidence": 0.75, "patterns_matched": []}}
        result = analyzer._calculate_migration_priority(overlaps)
        assert result == 0.75

    @pytest.mark.unit
    def test_multiple_overlaps_boosts_priority(
        self, analyzer: MigrationAnalyzer
    ) -> None:
        """Scenario: Multiple overlaps boost priority by 0.1."""
        overlaps = {
            "tdd": {"confidence": 0.75, "patterns_matched": []},
            "debugging": {"confidence": 0.60, "patterns_matched": []},
        }
        result = analyzer._calculate_migration_priority(overlaps)
        assert result == 0.85  # 0.75 + 0.1

    @pytest.mark.unit
    def test_multiple_overlaps_capped_at_one(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Priority is capped at 1.0."""
        overlaps = {
            "tdd": {"confidence": 0.95, "patterns_matched": []},
            "debugging": {"confidence": 0.90, "patterns_matched": []},
        }
        result = analyzer._calculate_migration_priority(overlaps)
        assert result <= 1.0


# ---------------------------------------------------------------------------
# Tests: _suggest_best_superpower
# ---------------------------------------------------------------------------


class TestSuggestBestSuperpower:
    """Feature: Best superpower suggestion."""

    @pytest.mark.unit
    def test_empty_overlaps_returns_none(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: No overlaps returns None."""
        result = analyzer._suggest_best_superpower({})
        assert result is None

    @pytest.mark.unit
    def test_returns_highest_confidence_superpower(
        self, analyzer: MigrationAnalyzer
    ) -> None:
        """Scenario: Returns superpower with highest confidence."""
        overlaps = {
            "tdd": {"confidence": 0.75, "patterns_matched": []},
            "debugging": {"confidence": 0.90, "patterns_matched": []},
        }
        result = analyzer._suggest_best_superpower(overlaps)
        assert result == "debugging"


# ---------------------------------------------------------------------------
# Tests: _load_overlap_mappings
# ---------------------------------------------------------------------------


class TestLoadOverlapMappings:
    """Feature: Overlap mappings loaded from file or defaults."""

    @pytest.mark.unit
    def test_default_mappings_when_no_file(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Default mappings returned when no yaml file."""
        mappings = analyzer._load_overlap_mappings()
        assert "test-driven-development" in mappings
        assert isinstance(mappings["test-driven-development"], list)

    @pytest.mark.unit
    def test_custom_yaml_mappings_loaded(self, tmp_path: Path) -> None:
        """Scenario: Custom yaml mappings file is loaded.
        Given a data/overlap_mappings.yaml file
        When _load_overlap_mappings is called
        Then custom mappings are returned
        """
        import os  # noqa: PLC0415

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        mapping_file = data_dir / "overlap_mappings.yaml"
        mapping_file.write_text(
            "custom-skill:\n  - custom pattern\n  - another pattern\n"
        )
        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            a = MigrationAnalyzer("test-plugin")
            assert "custom-skill" in a.overlap_mappings
            assert "custom pattern" in a.overlap_mappings["custom-skill"]
        finally:
            os.chdir(original)


# ---------------------------------------------------------------------------
# Tests: analyze_migration_path
# ---------------------------------------------------------------------------


class TestAnalyzeMigrationPath:
    """Feature: Full migration path analysis."""

    @pytest.mark.unit
    def test_returns_migration_path_structure(
        self, analyzer: MigrationAnalyzer
    ) -> None:
        """Scenario: analyze_migration_path returns expected keys."""
        result = analyzer.analyze_migration_path("nonexistent-command")
        assert "command" in result
        assert "overlaps" in result
        assert "migration_priority" in result
        assert "suggested_superpower" in result
        assert "wrapper_status" in result
        assert "compatibility" in result

    @pytest.mark.unit
    def test_command_name_in_result(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: command field matches the input."""
        result = analyzer.analyze_migration_path("my-command")
        assert result["command"] == "my-command"


# ---------------------------------------------------------------------------
# Tests: generate_migration_report
# ---------------------------------------------------------------------------


class TestGenerateMigrationReport:
    """Feature: Full migration report generation."""

    @pytest.mark.unit
    def test_no_commands_dir_returns_error(self, analyzer: MigrationAnalyzer) -> None:
        """Scenario: Missing commands/ directory returns error dict."""
        result = analyzer.generate_migration_report()
        assert "error" in result

    @pytest.mark.unit
    def test_empty_commands_dir_returns_empty_report(
        self, analyzer_with_commands: tuple[MigrationAnalyzer, Path]
    ) -> None:
        """Scenario: Empty commands/ directory returns report with 0 commands."""
        mgr, _ = analyzer_with_commands
        result = mgr.generate_migration_report()
        assert result["plugin"] == "test-plugin"
        assert result["summary"]["total_commands"] == 0

    @pytest.mark.unit
    def test_commands_in_report(
        self, analyzer_with_commands: tuple[MigrationAnalyzer, Path]
    ) -> None:
        """Scenario: Commands in directory appear in the report."""
        mgr, commands_dir = analyzer_with_commands
        (commands_dir / "cmd-one.md").write_text("# Cmd One\nSome content.\n")
        (commands_dir / "cmd-two.md").write_text("# Cmd Two\nOther content.\n")
        result = mgr.generate_migration_report()
        assert result["summary"]["total_commands"] == 2
        assert "cmd-one" in result["commands"]
        assert "cmd-two" in result["commands"]

    @pytest.mark.unit
    def test_high_priority_migration_counted(
        self, analyzer_with_commands: tuple[MigrationAnalyzer, Path]
    ) -> None:
        """Scenario: High-confidence overlap adds to high_priority count."""
        mgr, commands_dir = analyzer_with_commands
        # Write a file that matches many TDD patterns
        cmd_file = commands_dir / "tdd-cmd.md"
        cmd_file.write_text(
            "RED phase: write failing test\n"
            "GREEN phase: minimal code\n"
            "REFACTOR phase: improve code\n"
            "write failing test\n"
            "watch it fail\n"
            "minimal code\n"
            "test-first\n"
        )
        result = mgr.generate_migration_report()
        # Count totals
        total = result["summary"]["total_commands"]
        assert total == 1
