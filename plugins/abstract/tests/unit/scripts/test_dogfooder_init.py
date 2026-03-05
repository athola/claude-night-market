"""Unit tests for the dogfooder package __init__.py re-exports.

Feature: Dogfooder package top-level exports
  As a developer who already imports from makefile_dogfooder
  I want the dogfooder package __init__.py to re-export all public symbols
  So that downstream code can also import from 'dogfooder' directly
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))


class TestDogfooderPackageExports:
    """Feature: dogfooder package exports all public symbols

    As a developer
    I want to import every public name from the dogfooder package
    So that 'from dogfooder import X' always works without knowing
    which sub-module X lives in
    """

    @pytest.mark.unit
    def test_load_target_catalog_exported_from_package(self) -> None:
        """Scenario: load_target_catalog is importable from the package root
        Given the dogfooder/__init__.py re-exports parser symbols
        When I run 'from dogfooder import load_target_catalog'
        Then the import succeeds
        """
        from dogfooder import load_target_catalog  # noqa: PLC0415

        assert callable(load_target_catalog)

    @pytest.mark.unit
    def test_documentation_command_extractor_exported(self) -> None:
        """Scenario: DocumentationCommandExtractor is importable from the package root
        Given the dogfooder/__init__.py re-exports parser symbols
        When I run 'from dogfooder import DocumentationCommandExtractor'
        Then the import succeeds
        """
        from dogfooder import DocumentationCommandExtractor  # noqa: PLC0415

        assert isinstance(DocumentationCommandExtractor, type)

    @pytest.mark.unit
    def test_makefile_analyzer_exported(self) -> None:
        """Scenario: MakefileAnalyzer is importable from the package root
        Given the dogfooder/__init__.py re-exports parser symbols
        When I run 'from dogfooder import MakefileAnalyzer'
        Then the import succeeds
        """
        from dogfooder import MakefileAnalyzer  # noqa: PLC0415

        assert isinstance(MakefileAnalyzer, type)

    @pytest.mark.unit
    def test_makefile_target_generator_exported(self) -> None:
        """Scenario: MakefileTargetGenerator is importable from the package root
        Given the dogfooder/__init__.py re-exports validator symbols
        When I run 'from dogfooder import MakefileTargetGenerator'
        Then the import succeeds
        """
        from dogfooder import MakefileTargetGenerator  # noqa: PLC0415

        assert isinstance(MakefileTargetGenerator, type)

    @pytest.mark.unit
    def test_makefile_dogfooder_exported(self) -> None:
        """Scenario: MakefileDogfooder is importable from the package root
        Given the dogfooder/__init__.py re-exports reporter symbols
        When I run 'from dogfooder import MakefileDogfooder'
        Then the import succeeds
        """
        from dogfooder import MakefileDogfooder  # noqa: PLC0415

        assert isinstance(MakefileDogfooder, type)

    @pytest.mark.unit
    def test_generate_makefile_exported(self) -> None:
        """Scenario: generate_makefile is importable from the package root
        Given the dogfooder/__init__.py re-exports validator symbols
        When I run 'from dogfooder import generate_makefile'
        Then the import succeeds
        """
        from dogfooder import generate_makefile  # noqa: PLC0415

        assert callable(generate_makefile)

    @pytest.mark.unit
    def test_run_preflight_checks_exported(self) -> None:
        """Scenario: run_preflight_checks is importable from the package root
        Given the dogfooder/__init__.py re-exports validator symbols
        When I run 'from dogfooder import run_preflight_checks'
        Then the import succeeds
        """
        from dogfooder import run_preflight_checks  # noqa: PLC0415

        assert callable(run_preflight_checks)

    @pytest.mark.unit
    def test_validate_working_directory_exported(self) -> None:
        """Scenario: validate_working_directory is importable from the package root
        Given the dogfooder/__init__.py re-exports validator symbols
        When I run 'from dogfooder import validate_working_directory'
        Then the import succeeds
        """
        from dogfooder import validate_working_directory  # noqa: PLC0415

        assert callable(validate_working_directory)

    @pytest.mark.unit
    def test_processing_config_exported(self) -> None:
        """Scenario: ProcessingConfig is importable from the package root
        Given the dogfooder/__init__.py re-exports reporter symbols
        When I run 'from dogfooder import ProcessingConfig'
        Then the import succeeds
        """
        from dogfooder import ProcessingConfig  # noqa: PLC0415

        assert isinstance(ProcessingConfig, type)

    @pytest.mark.unit
    def test_all_list_contains_expected_names(self) -> None:
        """Scenario: __all__ in dogfooder/__init__.py lists every public symbol
        Given the dogfooder package is imported
        When __all__ is inspected
        Then it contains every name the tests expect to import
        """
        import dogfooder  # noqa: PLC0415

        expected = {
            "load_target_catalog",
            "DocumentationCommandExtractor",
            "MakefileAnalyzer",
            "MakefileTargetGenerator",
            "MakefileDogfooder",
            "ProcessingConfig",
            "generate_makefile",
            "run_preflight_checks",
            "validate_working_directory",
        }
        assert expected.issubset(set(dogfooder.__all__))
