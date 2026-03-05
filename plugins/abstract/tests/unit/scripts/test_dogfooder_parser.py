"""Unit tests for the dogfooder.parser module.

Feature: Dogfooder package parser module
  As a developer modularizing makefile_dogfooder.py
  I want parser functionality in a dedicated module
  So that the codebase is easier to maintain and test in isolation
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow importing from the scripts directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))


class TestDogfooderParserImports:
    """Feature: dogfooder.parser module exports correct symbols

    As a developer using the dogfooder package
    I want to import parser classes directly from dogfooder.parser
    So that I can use them independently of the monolithic script
    """

    @pytest.mark.unit
    def test_load_target_catalog_importable_from_parser(self) -> None:
        """Scenario: load_target_catalog is importable from dogfooder.parser
        Given the dogfooder package exists
        When I import load_target_catalog from dogfooder.parser
        Then the import succeeds and the symbol is callable
        """
        from dogfooder.parser import load_target_catalog  # noqa: PLC0415

        assert callable(load_target_catalog)

    @pytest.mark.unit
    def test_documentation_command_extractor_importable(self) -> None:
        """Scenario: DocumentationCommandExtractor is importable from dogfooder.parser
        Given the dogfooder package exists
        When I import DocumentationCommandExtractor from dogfooder.parser
        Then the import succeeds and the symbol is a class
        """
        from dogfooder.parser import DocumentationCommandExtractor  # noqa: PLC0415

        assert isinstance(DocumentationCommandExtractor, type)

    @pytest.mark.unit
    def test_makefile_analyzer_importable(self) -> None:
        """Scenario: MakefileAnalyzer is importable from dogfooder.parser
        Given the dogfooder package exists
        When I import MakefileAnalyzer from dogfooder.parser
        Then the import succeeds and the symbol is a class
        """
        from dogfooder.parser import MakefileAnalyzer  # noqa: PLC0415

        assert isinstance(MakefileAnalyzer, type)


class TestLoadTargetCatalogFromParser:
    """Feature: load_target_catalog works when called from the parser module

    As a developer using dogfooder.parser
    I want load_target_catalog to resolve the YAML path correctly
    So that the catalog loads regardless of how the module is imported
    """

    @pytest.mark.unit
    def test_catalog_returns_dict(self) -> None:
        """Scenario: catalog loads successfully from the parser module
        Given the data/makefile_target_catalog.yaml file exists
        When load_target_catalog() is called from dogfooder.parser
        Then it returns a dict with the expected top-level keys
        """
        from dogfooder.parser import load_target_catalog  # noqa: PLC0415

        catalog = load_target_catalog()

        assert isinstance(catalog, dict)
        assert "essential_targets" in catalog
        assert "recommended_targets" in catalog
        assert "convenience_targets" in catalog
        assert "skip_dirs" in catalog

    @pytest.mark.unit
    def test_catalog_path_resolves_via_parser_file(self) -> None:
        """Scenario: YAML path resolves relative to parser.py, not the script root
        Given parser.py lives inside the dogfooder/ sub-package
        When load_target_catalog() is called
        Then it resolves ../../data/makefile_target_catalog.yaml correctly
        """
        from dogfooder.parser import load_target_catalog  # noqa: PLC0415

        # Verify no exception is raised and result is non-empty
        catalog = load_target_catalog()
        assert len(catalog) > 0


class TestDocumentationCommandExtractorFromParser:
    """Feature: DocumentationCommandExtractor works from dogfooder.parser

    As a developer
    I want DocumentationCommandExtractor imported from the parser module
    So that it behaves identically to the version in the monolithic script
    """

    @pytest.mark.unit
    def test_extract_slash_commands_from_readme(self, tmp_path: Path) -> None:
        """Scenario: slash commands are extracted from a README
        Given a README.md containing backtick-wrapped /commands
        When extract_from_file() is called
        Then the slash commands are returned with correct metadata
        """
        from dogfooder.parser import DocumentationCommandExtractor  # noqa: PLC0415

        readme = tmp_path / "README.md"
        readme.write_text("Use `/my-command` to do things.\n")

        extractor = DocumentationCommandExtractor(tmp_path)
        commands = extractor.extract_from_file(readme)

        slash_cmds = [c for c in commands if c["type"] == "slash-command"]
        assert len(slash_cmds) == 1
        assert slash_cmds[0]["command"] == "my-command"

    @pytest.mark.unit
    def test_extract_all_groups_by_file(self, tmp_path: Path) -> None:
        """Scenario: extract_all groups commands by relative file path
        Given two plugin READMEs each containing a slash command
        When extract_all() is called
        Then results are keyed by relative file path
        """
        from dogfooder.parser import DocumentationCommandExtractor  # noqa: PLC0415

        plugin_a = tmp_path / "plugins" / "alpha"
        plugin_a.mkdir(parents=True)
        (plugin_a / "README.md").write_text("Use `/cmd-a`.\n")

        plugin_b = tmp_path / "plugins" / "beta"
        plugin_b.mkdir(parents=True)
        (plugin_b / "README.md").write_text("Use `/cmd-b`.\n")

        extractor = DocumentationCommandExtractor(tmp_path)
        result = extractor.extract_all()

        assert "plugins/alpha/README.md" in result
        assert "plugins/beta/README.md" in result

    @pytest.mark.unit
    def test_empty_file_returns_no_commands(self, tmp_path: Path) -> None:
        """Scenario: a file with no commands returns an empty list
        Given a markdown file with no slash or CLI commands
        When extract_from_file() is called
        Then an empty list is returned
        """
        from dogfooder.parser import DocumentationCommandExtractor  # noqa: PLC0415

        doc = tmp_path / "doc.md"
        doc.write_text("# Just a heading\n\nNo commands here.\n")

        extractor = DocumentationCommandExtractor(tmp_path)
        assert extractor.extract_from_file(doc) == []


class TestMakefileAnalyzerFromParser:
    """Feature: MakefileAnalyzer works from dogfooder.parser

    As a developer
    I want MakefileAnalyzer imported from the parser module
    So that it behaves identically to the version in the monolithic script
    """

    @pytest.mark.unit
    def test_has_target_returns_true_when_present(self, tmp_path: Path) -> None:
        """Scenario: has_target returns True for a defined target
        Given a Makefile with a 'help' target
        When has_target('help') is called
        Then True is returned
        """
        from dogfooder.parser import MakefileAnalyzer  # noqa: PLC0415

        mf = tmp_path / "Makefile"
        mf.write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        analyzer = MakefileAnalyzer(mf)
        assert analyzer.has_target("help") is True

    @pytest.mark.unit
    def test_has_target_returns_false_when_absent(self, tmp_path: Path) -> None:
        """Scenario: has_target returns False for a missing target
        Given a Makefile with no 'demo-foo' target
        When has_target('demo-foo') is called
        Then False is returned
        """
        from dogfooder.parser import MakefileAnalyzer  # noqa: PLC0415

        mf = tmp_path / "Makefile"
        mf.write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        analyzer = MakefileAnalyzer(mf)
        assert analyzer.has_target("demo-foo") is False

    @pytest.mark.unit
    def test_get_missing_targets_identifies_gaps(self, tmp_path: Path) -> None:
        """Scenario: get_missing_targets returns targets not in the Makefile
        Given a Makefile with 'help' and a required set {'help', 'demo-foo'}
        When get_missing_targets() is called
        Then only 'demo-foo' is returned as missing
        """
        from dogfooder.parser import MakefileAnalyzer  # noqa: PLC0415

        mf = tmp_path / "Makefile"
        mf.write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        analyzer = MakefileAnalyzer(mf)
        missing = analyzer.get_missing_targets({"help", "demo-foo"})
        assert missing == {"demo-foo"}

    @pytest.mark.unit
    def test_missing_makefile_returns_empty_targets(self, tmp_path: Path) -> None:
        """Scenario: a non-existent Makefile yields empty targets dict
        Given a path to a Makefile that does not exist
        When MakefileAnalyzer is constructed
        Then targets is an empty dict and has_target always returns False
        """
        from dogfooder.parser import MakefileAnalyzer  # noqa: PLC0415

        mf = tmp_path / "Makefile"  # not created

        analyzer = MakefileAnalyzer(mf)
        assert analyzer.targets == {}
        assert analyzer.has_target("help") is False
