"""Structural tests for the performance_review package refactor.

Feature: performance_review is a package with domain submodules

As a developer maintaining pensive,
I want performance_review split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.performance_review as perf_pkg
from pensive.skills.performance_review import PerformanceReviewSkill


@pytest.mark.unit
class TestPerformanceReviewPackageStructure:
    """Verify performance_review is a package with submodules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_performance_review_is_a_package(self) -> None:
        """
        Scenario: performance_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.performance_review
        Then it should be a package (has __path__)
        """
        assert hasattr(perf_pkg, "__path__"), (
            "pensive.skills.performance_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: PerformanceReviewSkill importable from package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.performance_review import PerformanceReviewSkill'
        Then it should succeed and instantiate
        """
        assert PerformanceReviewSkill is not None
        skill = PerformanceReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_helpers_submodule_exists(self) -> None:
        """
        Scenario: _helpers submodule is importable
        Given the package layout
        When we import pensive.skills.performance_review._helpers
        Then key helper functions should be available
        """
        mod = importlib.import_module("pensive.skills.performance_review._helpers")
        assert hasattr(mod, "_collect_non_list_names")
        assert hasattr(mod, "_MEMOIZATION_DECORATORS")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_visitor_submodule_exists(self) -> None:
        """
        Scenario: _visitor submodule is importable
        Given the package layout
        When we import pensive.skills.performance_review._visitor
        Then _PerfVisitor should be available
        """
        mod = importlib.import_module("pensive.skills.performance_review._visitor")
        assert hasattr(mod, "_PerfVisitor")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_analyze_method_present(self) -> None:
        """
        Scenario: assembled PerformanceReviewSkill has analyze method
        Given submodules composed in __init__.py
        When we instantiate PerformanceReviewSkill
        Then analyze method should be present
        """
        skill = PerformanceReviewSkill()
        assert hasattr(skill, "analyze")
        assert callable(skill.analyze)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_submodule_line_counts_within_budget(self) -> None:
        """
        Scenario: each submodule stays under 400 lines
        Given the package layout
        When we count lines in each submodule
        Then every file should be <= 400 lines
        """
        pkg_dir = Path(perf_pkg.__path__[0])
        submodules = ["_helpers.py", "_visitor.py"]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
