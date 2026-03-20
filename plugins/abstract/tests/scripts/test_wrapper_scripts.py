"""Tests for thin wrapper scripts.

Feature: CLI wrapper scripts
    As a developer
    I want wrapper scripts importable and instantiable
    So that the module-level code runs and gets covered
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from compliance_checker import ComplianceChecker
from improvement_suggester import ImprovementSuggester
from skills_auditor import SkillsAuditor
from token_usage_tracker import TokenUsageTracker
from tool_performance_analyzer import ToolPerformanceAnalyzer
from update_changelog import main, update_changelog

# ---------------------------------------------------------------------------
# token_usage_tracker.py
# ---------------------------------------------------------------------------


class TestTokenUsageTracker:
    """Feature: TokenUsageTracker script."""

    @pytest.mark.unit
    def test_import_and_instantiate(self, tmp_path: Path) -> None:
        """Scenario: TokenUsageTracker can be imported and instantiated."""
        tracker = TokenUsageTracker(tmp_path)
        assert tracker.skills_dir == tmp_path
        assert tracker.optimal_limit == 2000

    @pytest.mark.unit
    def test_track_usage_empty_dir(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns zeros.
        Given a directory with no SKILL.md files
        When track_usage is called
        Then total_skills is 0
        """
        tracker = TokenUsageTracker(tmp_path)
        result = tracker.track_usage()
        assert result["total_skills"] == 0
        assert result["total_tokens"] == 0

    @pytest.mark.unit
    def test_track_usage_with_skill_files(self, tmp_path: Path) -> None:
        """Scenario: Skill files are counted and tokens estimated.
        Given two SKILL.md files with known content sizes
        When track_usage is called
        Then total_skills is 2
        """
        skill_dir1 = tmp_path / "skill1"
        skill_dir1.mkdir()
        (skill_dir1 / "SKILL.md").write_text("x" * 800)  # 200 tokens

        skill_dir2 = tmp_path / "skill2"
        skill_dir2.mkdir()
        (skill_dir2 / "SKILL.md").write_text("y" * 400)  # 100 tokens

        tracker = TokenUsageTracker(tmp_path)
        result = tracker.track_usage()
        assert result["total_skills"] == 2
        assert result["total_tokens"] > 0

    @pytest.mark.unit
    def test_track_usage_optimal_vs_over_limit(self, tmp_path: Path) -> None:
        """Scenario: Files classified as optimal or over-limit correctly."""
        # Small file (under optimal_limit of 2000 tokens)
        skill_dir = tmp_path / "small-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("x" * 100)  # 25 tokens

        tracker = TokenUsageTracker(tmp_path, optimal_limit=2000)
        result = tracker.track_usage()
        assert result["optimal_usage_count"] == 1
        assert result["skills_over_limit"] == 0

    @pytest.mark.unit
    def test_get_usage_report_returns_string(self, tmp_path: Path) -> None:
        """Scenario: get_usage_report returns a formatted string."""
        tracker = TokenUsageTracker(tmp_path)
        report = tracker.get_usage_report()
        assert isinstance(report, str)
        assert "Token Usage Report" in report

    @pytest.mark.unit
    def test_custom_optimal_limit(self, tmp_path: Path) -> None:
        """Scenario: Custom optimal_limit is stored correctly."""
        tracker = TokenUsageTracker(tmp_path, optimal_limit=500, max_limit=1000)
        assert tracker.optimal_limit == 500
        assert tracker.max_limit == 1000


# ---------------------------------------------------------------------------
# tool_performance_analyzer.py
# ---------------------------------------------------------------------------


class TestToolPerformanceAnalyzer:
    """Feature: ToolPerformanceAnalyzer script."""

    @pytest.mark.unit
    def test_import_and_instantiate(self, tmp_path: Path) -> None:
        """Scenario: ToolPerformanceAnalyzer can be imported and instantiated."""
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        assert analyzer.skills_dir == tmp_path

    @pytest.mark.unit
    def test_analyze_tools_empty_dir(self, tmp_path: Path) -> None:
        """Scenario: Empty directory returns zero tools."""
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 0
        assert result["tools"] == {}

    @pytest.mark.unit
    def test_get_performance_report_returns_string(self, tmp_path: Path) -> None:
        """Scenario: get_performance_report returns a string."""
        analyzer = ToolPerformanceAnalyzer(tmp_path)
        report = analyzer.get_performance_report()
        assert isinstance(report, str)
        assert "Tool Performance Report" in report


# ---------------------------------------------------------------------------
# compliance_checker.py
# ---------------------------------------------------------------------------


class TestComplianceCheckerWrapper:
    """Feature: ComplianceChecker wrapper script."""

    @pytest.mark.unit
    def test_import_compliance_checker(self, tmp_path: Path) -> None:
        """Scenario: ComplianceChecker can be imported."""
        checker = ComplianceChecker(tmp_path)
        assert checker is not None

    @pytest.mark.unit
    def test_check_compliance_empty_dir(self, tmp_path: Path) -> None:
        """Scenario: check_compliance on empty dir returns results dict."""
        checker = ComplianceChecker(tmp_path)
        results = checker.check_compliance()
        assert isinstance(results, dict)


# ---------------------------------------------------------------------------
# improvement_suggester.py
# ---------------------------------------------------------------------------


class TestImprovementSuggesterWrapper:
    """Feature: ImprovementSuggester wrapper script."""

    @pytest.mark.unit
    def test_import_improvement_suggester(self, tmp_path: Path) -> None:
        """Scenario: ImprovementSuggester can be imported."""
        suggester = ImprovementSuggester(tmp_path)
        assert suggester is not None


# ---------------------------------------------------------------------------
# skills_auditor.py
# ---------------------------------------------------------------------------


class TestSkillsAuditorWrapper:
    """Feature: SkillsAuditor wrapper script."""

    @pytest.mark.unit
    def test_import_skills_auditor(self, tmp_path: Path) -> None:
        """Scenario: SkillsAuditor can be imported."""
        auditor = SkillsAuditor(tmp_path)
        assert auditor is not None

    @pytest.mark.unit
    def test_audit_skills_empty_dir(self, tmp_path: Path) -> None:
        """Scenario: audit_skills on empty dir returns results."""
        auditor = SkillsAuditor(tmp_path)
        results = auditor.audit_skills()
        assert isinstance(results, dict)
        assert "total_skills" in results


# ---------------------------------------------------------------------------
# update_changelog.py: update_changelog and main()
# ---------------------------------------------------------------------------


class TestUpdateChangelog:
    """Feature: update_changelog function and main() entry point."""

    @pytest.mark.unit
    def test_update_changelog_no_file(self, tmp_path: Path) -> None:
        """Scenario: update_changelog silently exits when no CHANGELOG.md.
        Given no CHANGELOG.md in cwd
        When update_changelog is called
        Then no crash and no output
        """
        entries = {"Added": ["New feature."]}
        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            update_changelog(entries)  # Should not crash
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_update_changelog_no_unreleased_section(self, tmp_path: Path) -> None:
        """Scenario: update_changelog silently exits when no Unreleased section."""
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\n## [1.0.0] - 2024-01-01\n\nContent.\n")

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            update_changelog({"Added": ["New feature."]})
            # File should remain unchanged (no insertion)
            content = changelog.read_text()
            assert "## [Unreleased]" not in content
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_update_changelog_inserts_entry(self, tmp_path: Path) -> None:
        """Scenario: update_changelog inserts new entries after Unreleased section."""
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2024-01-01\n\nContent.\n"
        )

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            update_changelog({"Added": ["Feature X."], "Fixed": ["Bug Y."]})
            content = changelog.read_text()
            assert "Feature X." in content
            assert "Bug Y." in content
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_update_changelog_with_version(self, tmp_path: Path) -> None:
        """Scenario: update_changelog uses provided version in entry header."""
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2024-01-01\n\nContent.\n"
        )

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            update_changelog({"Changed": ["Update something."]}, version="2.0.0")
            content = changelog.read_text()
            assert "2.0.0" in content
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_update_changelog_deduplicates_entries(self, tmp_path: Path) -> None:
        """Scenario: Duplicate changelog entries are removed."""
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2024-01-01\n\nContent.\n"
        )

        original = os.getcwd()
        os.chdir(tmp_path)
        try:
            # Duplicate entry
            update_changelog({"Added": ["Same feature.", "Same feature."]})
            content = changelog.read_text()
            # Count occurrences of "Same feature."
            assert content.count("Same feature.") == 1
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_main_validate_only_valid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: main --validate-only with valid changelog exits 0."""
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2024-01-01\n\nContent.\n"
        )

        original = os.getcwd()
        os.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["update_changelog.py", "--validate-only"])
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_main_validate_only_invalid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: main --validate-only with no changelog exits 1."""
        original = os.getcwd()
        os.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", ["update_changelog.py", "--validate-only"])
        try:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        finally:
            os.chdir(original)
