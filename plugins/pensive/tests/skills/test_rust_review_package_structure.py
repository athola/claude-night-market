"""Structural tests for the rust_review package refactor.

Feature: rust_review is a package with domain submodules

As a developer maintaining pensive,
I want rust_review to be split into focused submodules,
So that each file has a single responsibility and stays
under 400 lines.

All existing import paths must continue to work via
__init__.py re-exports.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import pensive.skills.rust_review as rust_review_pkg
from pensive.skills.rust_review import RustReviewSkill


@pytest.mark.unit
class TestRustReviewPackageStructure:
    """
    Verify that rust_review is a package with submodules
    and that all public names are re-exported from __init__.py.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_rust_review_is_a_package(self) -> None:
        """
        Scenario: rust_review is importable as a package
        Given the refactored layout
        When we import pensive.skills.rust_review
        Then it should be a package (has __path__)
        """
        pkg = rust_review_pkg

        assert hasattr(pkg, "__path__"), (
            "pensive.skills.rust_review should be a package, not a module"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_main_class_importable_from_package(self) -> None:
        """
        Scenario: RustReviewSkill is importable from the package root
        Given the __init__.py re-exports
        When we do 'from pensive.skills.rust_review import RustReviewSkill'
        Then it should succeed and return the class
        """
        assert RustReviewSkill is not None
        skill = RustReviewSkill()
        assert skill is not None

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_safety_submodule_exists(self) -> None:
        """
        Scenario: safety submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.safety
        Then SafetyMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.safety")
        assert hasattr(mod, "SafetyMixin")
        assert hasattr(mod, "__all__")
        assert "SafetyMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ownership_submodule_exists(self) -> None:
        """
        Scenario: ownership submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.ownership
        Then OwnershipMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.ownership")
        assert hasattr(mod, "OwnershipMixin")
        assert hasattr(mod, "__all__")
        assert "OwnershipMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_cargo_submodule_exists(self) -> None:
        """
        Scenario: cargo submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.cargo
        Then CargoBuildMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.cargo")
        assert hasattr(mod, "CargoBuildMixin")
        assert hasattr(mod, "__all__")
        assert "CargoBuildMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_patterns_submodule_exists(self) -> None:
        """
        Scenario: patterns submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.patterns
        Then PatternsMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.patterns")
        assert hasattr(mod, "PatternsMixin")
        assert hasattr(mod, "__all__")
        assert "PatternsMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reporting_submodule_exists(self) -> None:
        """
        Scenario: reporting submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.reporting
        Then ReportingMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.reporting")
        assert hasattr(mod, "ReportingMixin")
        assert hasattr(mod, "__all__")
        assert "ReportingMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_structure_submodule_exists(self) -> None:
        """
        Scenario: structure submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.structure
        Then StructureMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.structure")
        assert hasattr(mod, "StructureMixin")
        assert hasattr(mod, "__all__")
        assert "StructureMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_builtins_submodule_exists(self) -> None:
        """
        Scenario: builtins submodule is importable
        Given the package layout
        When we import pensive.skills.rust_review.builtins
        Then BuiltinsMixin should be available
        """
        mod = importlib.import_module("pensive.skills.rust_review.builtins")
        assert hasattr(mod, "BuiltinsMixin")
        assert hasattr(mod, "__all__")
        assert "BuiltinsMixin" in mod.__all__

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_all_methods_present_on_assembled_class(self, mock_skill_context) -> None:
        """
        Scenario: assembled RustReviewSkill has all analysis methods
        Given submodule mixins are composed in __init__.py
        When we instantiate RustReviewSkill
        Then all original public methods should be present
        """
        skill = RustReviewSkill()
        expected_methods = [
            "analyze_unsafe_code",
            "analyze_ownership",
            "analyze_data_races",
            "analyze_memory_safety",
            "analyze_panic_propagation",
            "analyze_async_patterns",
            "analyze_dependencies",
            "analyze_macros",
            "analyze_traits",
            "analyze_const_generics",
            "analyze_build_configuration",
            "analyze_silent_returns",
            "analyze_collection_types",
            "analyze_sql_injection",
            "analyze_cfg_test_misuse",
            "analyze_error_messages",
            "analyze_duplicate_validators",
            "analyze_builtin_preference",
            "analyze",
            "create_rust_security_report",
            "categorize_rust_severity",
            "generate_rust_recommendations",
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
        pkg_dir = Path(rust_review_pkg.__path__[0])
        submodules = [
            "safety.py",
            "ownership.py",
            "cargo.py",
            "structure.py",
            "patterns.py",
            "builtins.py",
            "reporting.py",
        ]
        oversized = {}
        for name in submodules:
            path = pkg_dir / name
            if path.exists():
                lines = path.read_text().splitlines()
                if len(lines) > 400:
                    oversized[name] = len(lines)

        assert not oversized, f"Submodules exceed 400-line budget: {oversized}"
