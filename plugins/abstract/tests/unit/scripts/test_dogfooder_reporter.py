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
    def test_analyze_plugin_coverage_uses_matching_targets(
        self, tmp_path: Path
    ) -> None:
        """Scenario: coverage_percent reflects only matching required targets
        Given a Makefile with 10 unrelated targets and 1 matching demo target
        When analyze_plugin() is called for a command /my-cmd
        Then coverage_percent is 50 (1 of 2 required targets present)
             not inflated by unrelated targets
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "cov-test"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text("Use `/my-cmd` to do things.\n")

        # Makefile has demo-my-cmd but NOT test-my-cmd, plus many unrelated targets
        makefile_lines = [
            ".PHONY: help test lint clean build demo-my-cmd a b c d e",
            "help:",
            "\t@echo help",
            "demo-my-cmd:",
            "\t@echo demo",
        ]
        for t in ["test", "lint", "clean", "build", "a", "b", "c", "d", "e"]:
            makefile_lines.append(f"{t}:")
            makefile_lines.append(f"\t@echo {t}")
        (plugin_dir / "Makefile").write_text("\n".join(makefile_lines) + "\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = dogfooder.analyze_plugin("cov-test")

        # Required: demo-my-cmd + test-my-cmd (2 targets)
        # Present: only demo-my-cmd (1 target)
        # Coverage should be 50%, not inflated by unrelated targets
        assert finding["coverage_percent"] == 50

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


class TestAnalyzePluginEdgeCases:
    """Feature: analyze_plugin handles edge cases

    As a developer
    I want analyze_plugin to handle missing README and Makefile scenarios
    So that analysis degrades gracefully
    """

    @pytest.mark.unit
    def test_no_readme_returns_status(self, tmp_path: Path) -> None:
        """Scenario: Plugin directory has no README.md
        Given a plugin directory without a README.md
        When analyze_plugin() is called
        Then it returns a dict with status 'no-readme'
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "no-readme-plugin"
        plugin_dir.mkdir(parents=True)

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = dogfooder.analyze_plugin("no-readme-plugin")

        assert finding["plugin"] == "no-readme-plugin"
        assert finding["status"] == "no-readme"

    @pytest.mark.unit
    def test_no_makefile_without_generate_returns_status(self, tmp_path: Path) -> None:
        """Scenario: Plugin has README but no Makefile and generate_missing=False
        Given a plugin directory with README but no Makefile
        When analyze_plugin(generate_missing=False) is called
        Then it returns a dict with status 'no-makefile'
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "no-makefile-plugin"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text("Some content.\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = dogfooder.analyze_plugin("no-makefile-plugin", generate_missing=False)

        assert finding["plugin"] == "no-makefile-plugin"
        assert finding["status"] == "no-makefile"


class TestInsertionStrategies:
    """Feature: Makefile content insertion strategies

    As a developer
    I want the dogfooder to insert generated targets at the right location
    So that Makefile structure is preserved
    """

    @pytest.mark.unit
    def test_insert_before_catchall_comment(self, tmp_path: Path) -> None:
        """Scenario: Insert content before the catch-all guard comment
        Given Makefile content with a catch-all guard comment
        When _insert_content_before_catchall() is called
        Then the new content appears before the comment
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        content = (
            ".PHONY: help\n\nhelp:\n\t@echo help\n\n"
            "# Guard against accidental file creation\n%::\n\t@:\n"
        )
        new_content = "new-target: ## New target\n\t@echo new\n"
        catchall_pattern = "\n\n# Guard against accidental file creation"

        result = dogfooder._insert_content_before_catchall(
            content, new_content, catchall_pattern
        )

        assert "new-target:" in result
        assert result.index("new-target:") < result.index(
            "# Guard against accidental file creation"
        )

    @pytest.mark.unit
    def test_insert_before_percent_colon(self, tmp_path: Path) -> None:
        """Scenario: Insert content before %:: rule
        Given Makefile content with a %:: catch-all rule
        When _insert_content_before_percent_colon() is called
        Then the new content appears before %::
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        content = ".PHONY: help\n\nhelp:\n\t@echo help\n\n%::\n\t@:\n"
        new_content = "new-target: ## New target\n\t@echo new\n"

        result = dogfooder._insert_content_before_percent_colon(content, new_content)

        assert "new-target:" in result
        assert result.index("new-target:") < result.index("%::")

    @pytest.mark.unit
    def test_determine_insertion_with_catchall(self, tmp_path: Path) -> None:
        """Scenario: Strategy picks catchall insertion when both markers exist
        Given Makefile content with both guard comment and %:: rule
        When _determine_insertion_strategy() is called
        Then content is inserted before the guard comment
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        content = (
            ".PHONY: help\n\nhelp:\n\t@echo help\n\n"
            "# Guard against accidental file creation\n%::\n\t@:\n"
        )
        new_content = "demo-cmd: ## Demo\n\t@echo demo\n"

        result = dogfooder._determine_insertion_strategy(content, new_content)

        assert "demo-cmd:" in result
        assert result.index("demo-cmd:") < result.index("Guard against")

    @pytest.mark.unit
    def test_determine_insertion_with_percent_only(self, tmp_path: Path) -> None:
        """Scenario: Strategy picks %:: insertion when no guard comment exists
        Given Makefile content with %:: but no guard comment
        When _determine_insertion_strategy() is called
        Then content is inserted before %::
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        content = ".PHONY: help\n\nhelp:\n\t@echo help\n\n%::\n\t@:\n"
        new_content = "demo-cmd: ## Demo\n\t@echo demo\n"

        result = dogfooder._determine_insertion_strategy(content, new_content)

        assert "demo-cmd:" in result
        assert result.index("demo-cmd:") < result.index("%::")

    @pytest.mark.unit
    def test_determine_insertion_appends_when_no_markers(self, tmp_path: Path) -> None:
        """Scenario: Strategy appends when no %:: or guard comment
        Given plain Makefile content with no special markers
        When _determine_insertion_strategy() is called
        Then content is appended at the end
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        content = ".PHONY: help\n\nhelp:\n\t@echo help\n"
        new_content = "demo-cmd: ## Demo\n\t@echo demo\n"

        result = dogfooder._determine_insertion_strategy(content, new_content)

        assert result.endswith("demo-cmd: ## Demo\n\t@echo demo\n\n")


class TestApplyTargetsToMakefile:
    """Feature: apply_targets_to_makefile writes filtered targets

    As a developer
    I want apply_targets_to_makefile to handle all edge cases
    So that Makefile updates are safe and predictable
    """

    @pytest.mark.unit
    def test_missing_makefile_returns_false(self, tmp_path: Path) -> None:
        """Scenario: Makefile path does not exist
        Given a finding with a nonexistent Makefile path
        When apply_targets_to_makefile() is called
        Then False is returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {"makefile": "plugins/ghost/Makefile"}

        result = dogfooder.apply_targets_to_makefile(
            "ghost", finding, "target: ## desc\n\t@echo ok\n"
        )

        assert result is False

    @pytest.mark.unit
    def test_all_duplicates_returns_true(self, tmp_path: Path) -> None:
        """Scenario: All generated targets already exist
        Given a Makefile that already has the generated target
        When apply_targets_to_makefile() is called
        Then True is returned without writing
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "dup" / "Makefile"
        makefile.parent.mkdir(parents=True)
        makefile.write_text(".PHONY: help\n\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {"makefile": "plugins/dup/Makefile"}

        result = dogfooder.apply_targets_to_makefile(
            "dup", finding, "help: ## already exists\n\t@echo help\n"
        )

        assert result is True

    @pytest.mark.unit
    def test_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """Scenario: Dry run prints message without modifying Makefile
        Given a valid Makefile with new targets to add
        When apply_targets_to_makefile(dry_run=True) is called
        Then True is returned and Makefile is unchanged
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "dry" / "Makefile"
        makefile.parent.mkdir(parents=True)
        original = ".PHONY: help\n\nhelp:\n\t@echo help\n"
        makefile.write_text(original)

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {"makefile": "plugins/dry/Makefile"}

        result = dogfooder.apply_targets_to_makefile(
            "dry", finding, "new-target: ## New\n\t@echo new\n", dry_run=True
        )

        assert result is True
        assert makefile.read_text() == original


class TestBuildPhonyBlock:
    """Feature: _build_phony_block formats .PHONY with line wrapping

    As a developer
    I want .PHONY lines to wrap at the length limit
    So that Makefiles stay readable
    """

    @pytest.mark.unit
    def test_short_targets_fit_on_one_line(self, tmp_path: Path) -> None:
        """Scenario: Few short targets stay on one line
        Given 3 short target names
        When _build_phony_block() is called
        Then all targets appear on a single .PHONY line
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        targets = ["help", "test", "lint"]
        result = dogfooder._build_phony_block(targets)

        joined = "\n".join(result)
        assert ".PHONY:" in joined
        assert "help" in joined
        assert "\\" not in joined

    @pytest.mark.unit
    def test_many_long_targets_wrap(self, tmp_path: Path) -> None:
        """Scenario: Many targets cause line wrapping
        Given enough targets to exceed the PHONY_LINE_LENGTH_LIMIT
        When _build_phony_block() is called
        Then backslash continuations appear in the output
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        targets = [f"very-long-target-name-{i}" for i in range(15)]
        result = dogfooder._build_phony_block(targets)

        joined = "\n".join(result)
        assert "\\" in joined


class TestFixMakefilePronouce:
    """Feature: fix_makefile_pronounce updates .PHONY declarations

    As a developer
    I want .PHONY to be updated when new targets are added
    So that make tab-completion works for all targets
    """

    @pytest.mark.unit
    def test_missing_makefile_returns_false(self, tmp_path: Path) -> None:
        """Scenario: Makefile doesn't exist
        Given a finding pointing to a nonexistent Makefile
        When fix_makefile_pronounce() is called
        Then False is returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {"makefile": "plugins/ghost/Makefile", "missing_targets": ["test"]}

        result = dogfooder.fix_makefile_pronounce("ghost", finding)

        assert result is False

    @pytest.mark.unit
    def test_no_missing_targets_returns_true(self, tmp_path: Path) -> None:
        """Scenario: No missing targets
        Given a finding with an empty missing_targets list
        When fix_makefile_pronounce() is called
        Then True is returned (nothing to do)
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "ok" / "Makefile"
        makefile.parent.mkdir(parents=True)
        makefile.write_text(".PHONY: help\n\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {"makefile": "plugins/ok/Makefile", "missing_targets": []}

        assert dogfooder.fix_makefile_pronounce("ok", finding) is True

    @pytest.mark.unit
    def test_no_phony_block_returns_false(self, tmp_path: Path) -> None:
        """Scenario: Makefile has no .PHONY declaration
        Given a Makefile without a .PHONY line
        When fix_makefile_pronounce() is called
        Then False is returned
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "nophony" / "Makefile"
        makefile.parent.mkdir(parents=True)
        makefile.write_text("help:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {
            "makefile": "plugins/nophony/Makefile",
            "missing_targets": ["test"],
        }

        assert dogfooder.fix_makefile_pronounce("nophony", finding) is False

    @pytest.mark.unit
    def test_adds_new_targets_to_phony(self, tmp_path: Path) -> None:
        """Scenario: New targets are added to .PHONY
        Given a Makefile with .PHONY: help and a missing target 'test'
        When fix_makefile_pronounce(dry_run=False) is called
        Then the Makefile .PHONY line includes 'test'
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "addme" / "Makefile"
        makefile.parent.mkdir(parents=True)
        makefile.write_text(".PHONY: help\n\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {
            "makefile": "plugins/addme/Makefile",
            "missing_targets": ["test"],
        }

        result = dogfooder.fix_makefile_pronounce("addme", finding, dry_run=False)

        assert result is True
        updated = makefile.read_text()
        assert "test" in updated
        assert ".PHONY:" in updated

    @pytest.mark.unit
    def test_dry_run_does_not_modify(self, tmp_path: Path) -> None:
        """Scenario: Dry run leaves Makefile unchanged
        Given a Makefile with a missing target
        When fix_makefile_pronounce(dry_run=True) is called
        Then True is returned but Makefile content is unchanged
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "dryfix" / "Makefile"
        makefile.parent.mkdir(parents=True)
        original = ".PHONY: help\n\nhelp:\n\t@echo help\n"
        makefile.write_text(original)

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {
            "makefile": "plugins/dryfix/Makefile",
            "missing_targets": ["lint"],
        }

        result = dogfooder.fix_makefile_pronounce("dryfix", finding, dry_run=True)

        assert result is True
        assert makefile.read_text() == original

    @pytest.mark.unit
    def test_targets_already_in_phony_returns_true(self, tmp_path: Path) -> None:
        """Scenario: Missing targets are already in .PHONY
        Given a Makefile where .PHONY already lists the 'missing' targets
        When fix_makefile_pronounce() is called
        Then True is returned without modification
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        makefile = tmp_path / "plugins" / "already" / "Makefile"
        makefile.parent.mkdir(parents=True)
        makefile.write_text(".PHONY: help test\n\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = {
            "makefile": "plugins/already/Makefile",
            "missing_targets": ["test"],
        }

        assert dogfooder.fix_makefile_pronounce("already", finding) is True


class TestBuildPhonyBlockNoSpuriousLine:
    """Feature: _build_phony_block does not emit a bare .PHONY: line

    Regression test for C2: when all targets fit on one line,
    the result should NOT start with a bare '.PHONY:' line.
    """

    @pytest.mark.unit
    def test_no_bare_phony_line_when_targets_fit(self, tmp_path: Path) -> None:
        """Scenario: Short targets produce no spurious bare .PHONY: line
        Given 3 short target names that fit on one line
        When _build_phony_block() is called
        Then the first line is NOT a bare '.PHONY:' without targets
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        targets = ["help", "test", "lint"]
        result = dogfooder._build_phony_block(targets)

        assert result[0] != ".PHONY:"
        assert result[0].startswith(".PHONY:")
        assert "help" in result[0]


class TestFilterDuplicateTargetsOrphanedRecipes:
    """Feature: _filter_duplicate_targets skips orphaned recipe lines

    Regression test for C4: when a duplicate target header is filtered,
    its recipe lines (tab-indented) must also be filtered.
    """

    @pytest.mark.unit
    def test_duplicate_target_recipes_are_skipped(self, tmp_path: Path) -> None:
        """Scenario: Recipe lines for duplicate targets are excluded
        Given generated content with a duplicate target and its recipes
        When _filter_duplicate_targets() is called
        Then neither the target header nor its recipe lines appear
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        existing = {"old-target"}
        generated = (
            "old-target: ## already here\n"
            "\t@echo old\n"
            "\t@echo old-recipe-2\n"
            "\n"
            "new-target: ## brand new\n"
            "\t@echo new\n"
        )

        filtered_lines = dogfooder._filter_duplicate_targets(generated, existing)
        filtered_text = "\n".join(filtered_lines)

        assert "new-target:" in filtered_text
        assert "old-target:" not in filtered_text
        assert "@echo old" not in filtered_text
        assert "old-recipe-2" not in filtered_text


class TestAnalyzeAllVerboseNoReadme:
    """Feature: analyze_all verbose mode handles no-readme plugins

    Regression test for C5: verbose mode must not crash with KeyError
    when a plugin returns a minimal dict without 'commands_documented'.
    """

    @pytest.mark.unit
    def test_verbose_skips_no_readme_plugin(self, tmp_path: Path) -> None:
        """Scenario: Plugin without README does not crash verbose output
        Given a plugin directory without a README.md
        When analyze_all() is called with verbose=True
        Then no KeyError is raised
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "no-readme"
        plugin_dir.mkdir(parents=True)

        dogfooder = MakefileDogfooder(root_dir=tmp_path, verbose=True)
        # Should not raise KeyError
        report = dogfooder.analyze_all()

        assert isinstance(report, dict)


class TestAnalyzeAllVerbose:
    """Feature: analyze_all with verbose flag prints details

    As a developer
    I want verbose output during analysis
    So that I can see per-plugin progress
    """

    @pytest.mark.unit
    def test_verbose_prints_plugin_details(self, tmp_path: Path, capsys) -> None:
        """Scenario: verbose=True causes per-plugin output
        Given a plugin directory with README and Makefile
        When analyze_all() is called on a verbose MakefileDogfooder
        Then plugin details are printed to stdout
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "verbose-test"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "README.md").write_text("Use `/do-thing`.\n")
        (plugin_dir / "Makefile").write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path, verbose=True)
        dogfooder.analyze_all()

        captured = capsys.readouterr()
        assert "verbose-test:" in captured.out
        assert "Commands documented:" in captured.out


class TestGenerateReportTruncation:
    """Feature: generate_report truncates long missing target lists

    As a developer
    I want reports to stay readable even with many missing targets
    So that output doesn't overwhelm
    """

    @pytest.mark.unit
    def test_more_than_five_missing_shows_truncation(self, tmp_path: Path) -> None:
        """Scenario: More than MAX_MISSING_DISPLAY targets triggers '... and N more'
        Given a finding with 8 missing targets
        When generate_report() is called
        Then the report contains '... and 3 more'
        """
        from dogfooder.reporter import MakefileDogfooder  # noqa: PLC0415

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        dogfooder.report["findings"].append(
            {
                "plugin": "many-missing",
                "coverage_percent": 20,
                "commands_documented": 8,
                "targets_missing": 8,
                "missing_targets": [f"target-{i}" for i in range(8)],
            }
        )
        dogfooder.report["plugins_analyzed"] = 1
        dogfooder.report["commands_found"] = 8
        dogfooder.report["targets_missing"] = 8

        report = dogfooder.generate_report()

        assert "... and 3 more" in report
