"""Structural tests for the bug_review package refactor.

Feature: bug_review is a package with domain submodules

As a developer maintaining pensive,
I want bug_review split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.bug_review as bug_pkg
from pensive.skills.bug_review import BugReviewSkill


@pytest.mark.unit
class TestBugReviewPackageStructure:
    """Verify bug_review is a package with submodules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_bug_review_is_a_package(self) -> None:
        """
        Scenario: bug_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.bug_review
        Then it should be a package (has __path__)
        """
        assert hasattr(bug_pkg, "__path__"), (
            "pensive.skills.bug_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: BugReviewSkill importable from package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.bug_review import BugReviewSkill'
        Then it should succeed and instantiate
        """
        assert BugReviewSkill is not None
        skill = BugReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detection_submodule_exists(self) -> None:
        """
        Scenario: _detection submodule is importable
        Given the package layout
        When we import pensive.skills.bug_review._detection
        Then DetectionMixin should be available
        """
        mod = importlib.import_module("pensive.skills.bug_review._detection")
        assert hasattr(mod, "DetectionMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analysis_submodule_exists(self) -> None:
        """
        Scenario: _analysis submodule is importable
        Given the package layout
        When we import pensive.skills.bug_review._analysis
        Then AnalysisMixin should be available
        """
        mod = importlib.import_module("pensive.skills.bug_review._analysis")
        assert hasattr(mod, "AnalysisMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reporting_submodule_exists(self) -> None:
        """
        Scenario: _reporting submodule is importable
        Given the package layout
        When we import pensive.skills.bug_review._reporting
        Then ReportingMixin should be available
        """
        mod = importlib.import_module("pensive.skills.bug_review._reporting")
        assert hasattr(mod, "ReportingMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_methods_present_on_assembled_class(self) -> None:
        """
        Scenario: assembled BugReviewSkill has all detection/analysis methods
        Given submodule mixins are composed in __init__.py
        When we instantiate BugReviewSkill
        Then all original public methods should be present
        """
        skill = BugReviewSkill()
        expected_methods = [
            "detect_null_pointer_dereference",
            "detect_race_conditions",
            "detect_memory_leaks",
            "detect_sql_injection",
            "detect_off_by_one_errors",
            "detect_integer_overflow",
            "detect_resource_leaks",
            "detect_logical_errors",
            "detect_type_confusion",
            "detect_timing_attacks",
            "categorize_severity",
            "generate_fix_recommendations",
            "analyze_bug_patterns",
            "validate_bug_fixes",
            "detect_false_positives",
            "create_bug_report",
            "check_external_dependencies",
            "analyze",
        ]
        missing = [m for m in expected_methods if not hasattr(skill, m)]
        assert not missing, f"Missing methods after refactor: {missing}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_submodule_line_counts_within_budget(self) -> None:
        """
        Scenario: each submodule stays under 400 lines
        Given the package layout
        When we count lines in each submodule
        Then every file should be <= 400 lines
        """
        pkg_dir = Path(bug_pkg.__path__[0])
        submodules = ["_detection.py", "_analysis.py", "_reporting.py"]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
