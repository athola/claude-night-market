"""Structural tests for the makefile_review package refactor.

Feature: makefile_review is a package with domain submodules

As a developer maintaining pensive,
I want makefile_review split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.makefile_review as makefile_pkg
from pensive.skills.makefile_review import MakefileReviewSkill


@pytest.mark.unit
class TestMakefileReviewPackageStructure:
    """Verify makefile_review is a package with submodules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_makefile_review_is_a_package(self) -> None:
        """
        Scenario: makefile_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.makefile_review
        Then it should be a package (has __path__)
        """
        assert hasattr(makefile_pkg, "__path__"), (
            "pensive.skills.makefile_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: MakefileReviewSkill importable from package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.makefile_review import MakefileReviewSkill'
        Then it should succeed and instantiate
        """
        assert MakefileReviewSkill is not None
        skill = MakefileReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_helpers_submodule_exists(self) -> None:
        """
        Scenario: _helpers submodule is importable
        Given the package layout
        When we import pensive.skills.makefile_review._helpers
        Then HelpersMixin should be available
        """
        mod = importlib.import_module("pensive.skills.makefile_review._helpers")
        assert hasattr(mod, "HelpersMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analysis_submodule_exists(self) -> None:
        """
        Scenario: _analysis submodule is importable
        Given the package layout
        When we import pensive.skills.makefile_review._analysis
        Then AnalysisMixin should be available
        """
        mod = importlib.import_module("pensive.skills.makefile_review._analysis")
        assert hasattr(mod, "AnalysisMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_submodule_exists(self) -> None:
        """
        Scenario: _quality submodule is importable
        Given the package layout
        When we import pensive.skills.makefile_review._quality
        Then QualityMixin should be available
        """
        mod = importlib.import_module("pensive.skills.makefile_review._quality")
        assert hasattr(mod, "QualityMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reporting_submodule_exists(self) -> None:
        """
        Scenario: _reporting submodule is importable
        Given the package layout
        When we import pensive.skills.makefile_review._reporting
        Then ReportingMixin should be available
        """
        mod = importlib.import_module("pensive.skills.makefile_review._reporting")
        assert hasattr(mod, "ReportingMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_methods_present_on_assembled_class(self) -> None:
        """
        Scenario: assembled MakefileReviewSkill has all analysis methods
        Given submodule mixins are composed in __init__.py
        When we instantiate MakefileReviewSkill
        Then all original public methods should be present
        """
        skill = MakefileReviewSkill()
        expected_methods = [
            "analyze_makefile_structure",
            "analyze_dependencies",
            "analyze_performance",
            "analyze_portability",
            "analyze_security",
            "analyze_variables",
            "analyze_target_organization",
            "analyze_modernization",
            "generate_makefile_recommendations",
            "create_makefile_quality_report",
            "analyze_multiple_makefiles",
            "analyze_build_system_integration",
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
        pkg_dir = Path(makefile_pkg.__path__[0])
        submodules = ["_helpers.py", "_analysis.py", "_quality.py", "_reporting.py"]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
