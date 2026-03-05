"""Unit tests for the dogfooder.reporter module.

Feature: Dogfooder package reporter module
  As a developer modularizing makefile_dogfooder.py
  I want the MakefileDogfooder orchestrator in a dedicated reporter module
  So that report generation and plugin analysis are independently testable
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))


class TestDogfooderReporterImports:
    """Feature: dogfooder.reporter module exports correct symbols

    As a developer using the dogfooder package
    I want to import MakefileDogfooder directly from dogfooder.reporter
    So that the main orchestrator is independently usable
    """

    @pytest.mark.unit
    def test_makefile_dogfooder_importable_from_reporter(self) -> None:
        """Scenario: MakefileDogfooder is importable from dogfooder.reporter
        Given the dogfooder package exists
        When I import MakefileDogfooder from dogfooder.reporter
        Then the import succeeds and the symbol is a class
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        assert isinstance(MakefileDogfooder, type)

    @pytest.mark.unit
    def test_processing_config_importable_from_reporter(self) -> None:
        """Scenario: ProcessingConfig is importable from dogfooder.reporter
        Given the dogfooder package exists
        When I import ProcessingConfig from dogfooder.reporter
        Then the import succeeds and the symbol is a class
        """
        from dogfooder.reporter import ProcessingConfig  # noqa: PLC0415

        assert isinstance(ProcessingConfig, type)


class TestMakefileDogfooderFromReporter:
    """Feature: MakefileDogfooder works correctly from dogfooder.reporter

    As a developer
    I want MakefileDogfooder imported from the reporter module
    So that analysis, scoring, and reporting work identically
    to the monolithic script version
    """

    @pytest.mark.unit
    def test_init_loads_catalog(self) -> None:
        """Scenario: MakefileDogfooder loads target catalog on init
        Given no arguments beyond defaults
        When MakefileDogfooder() is instantiated
        Then essential_targets, recommended_targets, convenience_targets,
        and skip_dirs attributes are set
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder()

        assert hasattr(dogfooder, "essential_targets")
        assert hasattr(dogfooder, "recommended_targets")
        assert hasattr(dogfooder, "convenience_targets")
        assert hasattr(dogfooder, "skip_dirs")

    @pytest.mark.unit
    def test_init_with_custom_root_dir(self, tmp_path: Path) -> None:
        """Scenario: MakefileDogfooder accepts a custom root directory
        Given tmp_path as root_dir
        When MakefileDogfooder(root_dir=tmp_path) is instantiated
        Then dogfooder.root_dir equals tmp_path
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)

        assert dogfooder.root_dir == tmp_path

    @pytest.mark.unit
    def test_verbose_flag(self) -> None:
        """Scenario: verbose flag is stored on the instance
        Given verbose=True
        When MakefileDogfooder(verbose=True) is instantiated
        Then dogfooder.verbose is True
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(verbose=True)

        assert dogfooder.verbose is True

    @pytest.mark.unit
    def test_explain_flag(self) -> None:
        """Scenario: explain flag is stored on the instance
        Given explain=True
        When MakefileDogfooder(explain=True) is instantiated
        Then dogfooder.explain is True
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(explain=True)

        assert dogfooder.explain is True

    @pytest.mark.unit
    def test_analyze_plugin_returns_finding(self, tmp_path: Path) -> None:
        """Scenario: analyze_plugin returns a dict with coverage data
        Given a plugin directory with a README and Makefile
        When analyze_plugin() is called
        Then a dict containing commands_documented and coverage_percent is returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "sample"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text("Use `/do-thing` here.\n")
        (plugin_dir / "Makefile").write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = dogfooder.analyze_plugin("sample")

        assert "commands_documented" in finding
        assert "coverage_percent" in finding
        assert finding["commands_documented"] == 1

    @pytest.mark.unit
    def test_generate_report_contains_findings_header(self, tmp_path: Path) -> None:
        """Scenario: generate_report produces a text report with Findings header
        Given a plugin analyzed by MakefileDogfooder
        When generate_report() is called
        Then the result contains 'Findings by Plugin'
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "reported"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text("Use `/report-cmd`.\n")
        (plugin_dir / "Makefile").write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        dogfooder.analyze_plugin("reported")
        report = dogfooder.generate_report()

        assert "Findings by Plugin" in report

    @pytest.mark.unit
    def test_generate_report_json_format(self, tmp_path: Path) -> None:
        """Scenario: generate_report with output_format='json' returns valid JSON
        Given a MakefileDogfooder with no plugins analyzed
        When generate_report(output_format='json') is called
        Then the result is a valid JSON string
        """
        import json  # noqa: PLC0415

        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        report_json = dogfooder.generate_report(output_format="json")

        parsed = json.loads(report_json)
        assert isinstance(parsed, dict)
        assert "findings" in parsed

    @pytest.mark.unit
    def test_calc_coverage_zero_required_returns_100(self) -> None:
        """Scenario: _calc_coverage returns 100 when no targets are required
        Given required=0 and exist=0
        When _calc_coverage() is called
        Then 100 is returned (no commands = full coverage by convention)
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder()

        assert dogfooder._calc_coverage(0, 0) == 100

    @pytest.mark.unit
    def test_calc_coverage_partial(self) -> None:
        """Scenario: _calc_coverage returns proportional value for partial coverage
        Given required=4 and exist=2
        When _calc_coverage() is called
        Then 50 is returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder()

        assert dogfooder._calc_coverage(4, 2) == 50

    @pytest.mark.unit
    def test_find_phony_block_single_line(self, tmp_path: Path) -> None:
        """Scenario: _find_phony_block detects a single-line .PHONY declaration
        Given Makefile content with '.PHONY: help test'
        When _find_phony_block() is called
        Then a list containing that line is returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        content = ".PHONY: help test\n\nhelp:\n\t@echo help\n"
        phony_lines = dogfooder._find_phony_block(content)

        assert len(phony_lines) >= 1
        assert ".PHONY:" in phony_lines[0]

    @pytest.mark.unit
    def test_extract_phony_targets_returns_all_names(self, tmp_path: Path) -> None:
        """Scenario: _extract_phony_targets extracts every name from a .PHONY block
        Given a multi-line .PHONY block with backslash continuation
        When _extract_phony_targets() is called
        Then all target names are returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        phony_lines = [
            ".PHONY: help test \\",
            "\tvalidate clean",
        ]

        targets = dogfooder._extract_phony_targets(phony_lines)

        assert "help" in targets
        assert "test" in targets
        assert "validate" in targets
        assert "clean" in targets

    @pytest.mark.unit
    def test_filter_duplicate_targets_excludes_existing(self, tmp_path: Path) -> None:
        """Scenario: _filter_duplicate_targets removes targets already in the Makefile
        Given generated content with a mix of existing and new targets
        When _filter_duplicate_targets() is called with the existing set
        Then only new targets remain in the output
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        existing = {"old-target"}
        generated = (
            "old-target: ## already here\n\t@echo old\n\n"
            "new-target: ## brand new\n\t@echo new\n"
        )

        filtered_lines = dogfooder._filter_duplicate_targets(generated, existing)
        filtered_text = "\n".join(filtered_lines)

        assert "new-target:" in filtered_text
        assert "old-target:" not in filtered_text


class TestProcessingConfigFromReporter:
    """Feature: ProcessingConfig dataclass from dogfooder.reporter

    As a developer
    I want ProcessingConfig importable from dogfooder.reporter
    So that CLI configuration is accessible from the package
    """

    @pytest.mark.unit
    def test_processing_config_fields(self) -> None:
        """Scenario: ProcessingConfig stores all four CLI configuration fields
        Given mode, generate_missing, dry_run, and verbose values
        When ProcessingConfig is instantiated
        Then all four attributes are set correctly
        """
        from dogfooder.reporter import ProcessingConfig  # noqa: PLC0415

        cfg = ProcessingConfig(
            mode="analyze",
            generate_missing=False,
            dry_run=True,
            verbose=False,
        )

        assert cfg.mode == "analyze"
        assert cfg.generate_missing is False
        assert cfg.dry_run is True
        assert cfg.verbose is False
