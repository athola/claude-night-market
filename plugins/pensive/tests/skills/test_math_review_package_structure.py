"""Structural tests for the math_review package refactor.

Feature: math_review is a package with domain submodules

As a developer maintaining pensive,
I want math_review to be split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.math_review as math_review_pkg
from pensive.skills.math_review import MathReviewSkill


@pytest.mark.unit
class TestMathReviewPackageStructure:
    """Verify math_review is a package with submodules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_math_review_is_a_package(self) -> None:
        """
        Scenario: math_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.math_review
        Then it should be a package (has __path__)
        """
        assert hasattr(math_review_pkg, "__path__"), (
            "pensive.skills.math_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: MathReviewSkill importable from package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.math_review import MathReviewSkill'
        Then it should succeed and return the class
        """
        assert MathReviewSkill is not None
        skill = MathReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_numerical_submodule_exists(self) -> None:
        """
        Scenario: _numerical submodule is importable
        Given the package layout
        When we import pensive.skills.math_review._numerical
        Then NumericalMixin should be available
        """
        mod = importlib.import_module("pensive.skills.math_review._numerical")
        assert hasattr(mod, "NumericalMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_statistics_submodule_exists(self) -> None:
        """
        Scenario: _statistics submodule is importable
        Given the package layout
        When we import pensive.skills.math_review._statistics
        Then StatisticsMixin should be available
        """
        mod = importlib.import_module("pensive.skills.math_review._statistics")
        assert hasattr(mod, "StatisticsMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_algorithms_submodule_exists(self) -> None:
        """
        Scenario: _algorithms submodule is importable
        Given the package layout
        When we import pensive.skills.math_review._algorithms
        Then AlgorithmsMixin should be available
        """
        mod = importlib.import_module("pensive.skills.math_review._algorithms")
        assert hasattr(mod, "AlgorithmsMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reporting_submodule_exists(self) -> None:
        """
        Scenario: _reporting submodule is importable
        Given the package layout
        When we import pensive.skills.math_review._reporting
        Then ReportingMixin should be available
        """
        mod = importlib.import_module("pensive.skills.math_review._reporting")
        assert hasattr(mod, "ReportingMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_methods_present_on_assembled_class(self) -> None:
        """
        Scenario: assembled MathReviewSkill has all analysis methods
        Given submodule mixins are composed in __init__.py
        When we instantiate MathReviewSkill
        Then all original public methods should be present
        """
        skill = MathReviewSkill()
        expected_methods = [
            "analyze_numerical_precision",
            "analyze_integer_overflow",
            "analyze_matrix_stability",
            "analyze_statistical_fallacies",
            "analyze_probability_distributions",
            "analyze_optimization_algorithms",
            "analyze_calculus_implementations",
            "analyze_geometry_trigonometry",
            "analyze_computational_complexity",
            "analyze_mathematical_proofs",
            "create_math_correctness_report",
            "generate_mathematical_recommendations",
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
        pkg_dir = Path(math_review_pkg.__path__[0])
        submodules = [
            "_numerical.py",
            "_statistics.py",
            "_algorithms.py",
            "_reporting.py",
        ]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
