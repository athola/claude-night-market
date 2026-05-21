"""Structural tests for the api_review package refactor.

Feature: api_review is a package with domain submodules

As a developer maintaining pensive,
I want api_review split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.api_review as api_pkg
from pensive.skills.api_review import ApiReviewSkill


@pytest.mark.unit
class TestApiReviewPackageStructure:
    """Verify api_review is a package with submodules."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_api_review_is_a_package(self) -> None:
        """
        Scenario: api_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.api_review
        Then it should be a package (has __path__)
        """
        assert hasattr(api_pkg, "__path__"), (
            "pensive.skills.api_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: ApiReviewSkill importable from package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.api_review import ApiReviewSkill'
        Then it should succeed and instantiate
        """
        assert ApiReviewSkill is not None
        skill = ApiReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_language_submodule_exists(self) -> None:
        """
        Scenario: _language submodule is importable
        Given the package layout
        When we import pensive.skills.api_review._language
        Then LanguageMixin should be available
        """
        mod = importlib.import_module("pensive.skills.api_review._language")
        assert hasattr(mod, "LanguageMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_quality_submodule_exists(self) -> None:
        """
        Scenario: _quality submodule is importable
        Given the package layout
        When we import pensive.skills.api_review._quality
        Then QualityMixin should be available
        """
        mod = importlib.import_module("pensive.skills.api_review._quality")
        assert hasattr(mod, "QualityMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reporting_submodule_exists(self) -> None:
        """
        Scenario: _reporting submodule is importable
        Given the package layout
        When we import pensive.skills.api_review._reporting
        Then ReportingMixin should be available
        """
        mod = importlib.import_module("pensive.skills.api_review._reporting")
        assert hasattr(mod, "ReportingMixin")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_methods_present_on_assembled_class(self) -> None:
        """
        Scenario: assembled ApiReviewSkill has all analysis methods
        Given submodule mixins are composed in __init__.py
        When we instantiate ApiReviewSkill
        Then all original public methods should be present
        """
        skill = ApiReviewSkill()
        expected_methods = [
            "analyze_typescript_api",
            "analyze_javascript_api",
            "analyze_python_api",
            "analyze_rust_api",
            "check_documentation",
            "check_naming_consistency",
            "check_error_handling",
            "check_breaking_changes",
            "validate_rest_patterns",
            "check_input_validation",
            "analyze_versioning",
            "check_security_practices",
            "analyze_performance_implications",
            "generate_api_summary",
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
        pkg_dir = Path(api_pkg.__path__[0])
        submodules = ["_language.py", "_quality.py", "_reporting.py"]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
