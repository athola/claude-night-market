"""Structural tests for the test_review package refactor.

Feature: test_review is a package with domain submodules

As a developer maintaining pensive,
I want test_review split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.test_review as test_review_pkg
from pensive.skills.test_review import TestReviewSkill


@pytest.mark.unit
class TestTestReviewPackageStructure:
    """Verify test_review is a package with submodules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_test_review_is_a_package(self) -> None:
        """
        Scenario: test_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.test_review
        Then it should be a package (has __path__)
        """
        assert hasattr(test_review_pkg, "__path__"), (
            "pensive.skills.test_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: TestReviewSkill importable from package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.test_review import TestReviewSkill'
        Then it should succeed and instantiate
        """
        assert TestReviewSkill is not None
        skill = TestReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_coverage_submodule_exists(self) -> None:
        """
        Scenario: _coverage submodule is importable
        Given the package layout
        When we import pensive.skills.test_review._coverage
        Then CoverageMixin should be available
        """
        mod = importlib.import_module("pensive.skills.test_review._coverage")
        assert hasattr(mod, "CoverageMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_submodule_exists(self) -> None:
        """
        Scenario: _structure submodule is importable
        Given the package layout
        When we import pensive.skills.test_review._structure
        Then StructureMixin should be available
        """
        mod = importlib.import_module("pensive.skills.test_review._structure")
        assert hasattr(mod, "StructureMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_patterns_submodule_exists(self) -> None:
        """
        Scenario: _patterns submodule is importable
        Given the package layout
        When we import pensive.skills.test_review._patterns
        Then PatternsMixin should be available
        """
        mod = importlib.import_module("pensive.skills.test_review._patterns")
        assert hasattr(mod, "PatternsMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reporting_submodule_exists(self) -> None:
        """
        Scenario: _reporting submodule is importable
        Given the package layout
        When we import pensive.skills.test_review._reporting
        Then ReportingMixin should be available
        """
        mod = importlib.import_module("pensive.skills.test_review._reporting")
        assert hasattr(mod, "ReportingMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_methods_present_on_assembled_class(self) -> None:
        """
        Scenario: assembled TestReviewSkill has all analysis methods
        Given submodule mixins are composed in __init__.py
        When we instantiate TestReviewSkill
        Then all original public methods should be present
        """
        skill = TestReviewSkill()
        expected_methods = [
            "analyze_test_coverage",
            "analyze_test_structure",
            "evaluate_tdd_compliance",
            "analyze_bdd_patterns",
            "identify_test_anti_patterns",
            "analyze_test_data_management",
            "analyze_mock_usage",
            "analyze_test_performance",
            "analyze_integration_test_coverage",
            "detect_test_flakiness",
            "create_test_quality_report",
            "generate_testing_recommendations",
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
        pkg_dir = Path(test_review_pkg.__path__[0])
        submodules = ["_coverage.py", "_structure.py", "_patterns.py", "_reporting.py"]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
