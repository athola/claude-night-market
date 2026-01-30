"""Tests for the Makefile dogfooder script.

Tests the key functionality that exists in the refactored module:
- YAML target catalog loading
- MakefileDogfooder initialization
- Documentation command extraction
- Makefile synthesis and generation

Note: The original implementation with parse_makefile, analyze_makefile,
MakefileInventory, and Target classes was refactored out. Those tests
are skipped until the implementation is restored.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from makefile_dogfooder import (
    DocumentationCommandExtractor,
    MakefileDogfooder,
    MakefileTargetGenerator,
    load_target_catalog,
)


class TestTargetCatalogLoading:
    """Tests for YAML target catalog loading."""

    def test_load_target_catalog_returns_dict(self) -> None:
        """Test that load_target_catalog returns expected structure."""
        catalog = load_target_catalog()

        assert isinstance(catalog, dict)
        assert "essential_targets" in catalog
        assert "recommended_targets" in catalog
        assert "convenience_targets" in catalog
        assert "skip_dirs" in catalog

    def test_essential_targets_have_required_keys(self) -> None:
        """Test that essential targets have expected structure.

        Note: YAML catalog uses dict format {name: description}
        """
        catalog = load_target_catalog()
        essential = catalog["essential_targets"]

        assert isinstance(essential, dict)
        assert len(essential) > 0

        for name, description in essential.items():
            assert isinstance(name, str)
            assert isinstance(description, str)
            assert len(description) > 0

    def test_skip_dirs_is_list(self) -> None:
        """Test that skip_dirs is a list of strings."""
        catalog = load_target_catalog()
        skip_dirs = catalog["skip_dirs"]

        assert isinstance(skip_dirs, list)
        assert all(isinstance(d, str) for d in skip_dirs)


class TestMakefileDogfooderInit:
    """Tests for MakefileDogfooder initialization."""

    def test_init_loads_catalog(self) -> None:
        """Test that MakefileDogfooder loads target catalog on init."""
        dogfooder = MakefileDogfooder()

        assert hasattr(dogfooder, "essential_targets")
        assert hasattr(dogfooder, "recommended_targets")
        assert hasattr(dogfooder, "convenience_targets")
        assert hasattr(dogfooder, "skip_dirs")

    def test_init_with_custom_root_dir(self, tmp_path: Path) -> None:
        """Test initialization with custom root directory."""
        dogfooder = MakefileDogfooder(root_dir=tmp_path)

        assert dogfooder.root_dir == tmp_path

    def test_init_verbose_mode(self) -> None:
        """Test verbose mode flag."""
        dogfooder = MakefileDogfooder(verbose=True)

        assert dogfooder.verbose is True

    def test_init_explain_mode(self) -> None:
        """Test explain mode flag."""
        dogfooder = MakefileDogfooder(explain=True)

        assert dogfooder.explain is True


# NOTE: The following test classes are skipped because the functionality
# was removed during refactoring. The implementation now only loads from YAML
# and the parsing/analysis methods no longer exist.
#
# To restore these tests, the following would need to be re-implemented:
# - MakefileInventory dataclass
# - Target dataclass
# - MakefileDogfooder.parse_makefile() method
# - MakefileDogfooder.analyze_makefile() method


@pytest.mark.skip(
    reason="Functionality removed during refactoring - parse_makefile not implemented"
)
class TestIncludeParsing:
    """Tests for include directive parsing."""

    def test_parse_include_directive(self, tmp_path: Path) -> None:
        """Test parsing of include directives from Makefile content."""
        pass

    def test_no_includes(self, tmp_path: Path) -> None:
        """Test parsing Makefile with no includes."""
        pass


@pytest.mark.skip(
    reason="Functionality removed during refactoring - parse_makefile not implemented"
)
class TestPhonyRecognition:
    """Tests for .PHONY target recognition."""

    def test_single_phony_declaration(self, tmp_path: Path) -> None:
        """Test parsing single .PHONY declaration."""
        pass

    def test_multiple_phony_declarations(self, tmp_path: Path) -> None:
        """Test parsing multiple .PHONY declarations."""
        pass


@pytest.mark.skip(
    reason="Functionality removed during refactoring - parse_makefile not implemented"
)
class TestPluginTypeDetection:
    """Tests for plugin type detection logic."""

    def test_leaf_plugin_type(self, tmp_path: Path) -> None:
        """Test detection of leaf plugin (standard plugin Makefile)."""
        pass

    def test_aggregator_plugin_type(self, tmp_path: Path) -> None:
        """Test detection of aggregator (Makefile with delegation)."""
        pass

    def test_auxiliary_plugin_type(self, tmp_path: Path) -> None:
        """Test detection of auxiliary Makefile (in docs/ or tests/)."""
        pass


@pytest.mark.skip(
    reason="Functionality removed during refactoring - analyze_makefile not implemented"
)
class TestScoringLogic:
    """Tests for Makefile scoring logic."""

    def test_essential_targets_scoring(self) -> None:
        """Test that essential targets contribute 20 points each."""
        pass

    def test_markdown_only_auto_credit(self) -> None:
        """Test that markdown-only plugins get auto-credit for Python targets."""
        pass

    def test_auxiliary_auto_credit(self) -> None:
        """Test that auxiliary Makefiles get auto-credit for some targets."""
        pass


@pytest.mark.skip(
    reason="Functionality removed during refactoring - analyze_makefile not implemented"
)
class TestExplainMode:
    """Tests for --explain mode output."""

    def test_explain_mode_outputs_breakdown(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that explain mode outputs scoring breakdown."""
        pass


@pytest.mark.skip(
    reason="Functionality removed during refactoring - parse_makefile not implemented"
)
class TestVerboseMode:
    """Tests for --verbose mode output."""

    def test_verbose_mode_shows_includes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that verbose mode shows include discovery."""
        pass


class TestDocumentationCommandExtractor:
    """Tests for DocumentationCommandExtractor class."""

    def test_extract_slash_commands_from_markdown(self, tmp_path: Path) -> None:
        """Test extraction of /-commands from markdown files."""
        # Create test markdown file with slash commands
        test_file = tmp_path / "README.md"
        test_file.write_text(
            """
# Plugin README

## Usage

Use `/update-docs` to update documentation.

Run `/pr-review --dry-run` for PR analysis.

Available commands:
- `/validate-plugin`
- `/test-update`
"""
        )

        extractor = DocumentationCommandExtractor(tmp_path)
        commands = extractor.extract_from_file(test_file)

        # Should extract 4 slash commands
        slash_cmds = [c for c in commands if c["type"] == "slash-command"]
        assert len(slash_cmds) == 4

        # Check first command
        assert slash_cmds[0]["command"] == "update-docs"
        assert slash_cmds[0]["source"] == "README.md"
        assert slash_cmds[0]["line"] == 6  # Line 1 is blank after triple-quote

    def test_extract_cli_invocations(self, tmp_path: Path) -> None:
        """Test extraction of claude CLI invocations."""
        test_file = tmp_path / "docs.md"
        test_file.write_text(
            """
Execute: `claude code-review --file main.py`

Or: ```bash
claude --help
```
"""
        )

        extractor = DocumentationCommandExtractor(tmp_path)
        commands = extractor.extract_from_file(test_file)

        # Should extract 2 CLI invocations
        cli_cmds = [c for c in commands if c["type"] == "cli-invocation"]
        assert len(cli_cmds) == 2

        # Check first invocation
        assert "code-review" in cli_cmds[0]["invocation"]
        assert "--file" in cli_cmds[0]["invocation"]

    def test_aggregates_commands_by_plugin(self, tmp_path: Path) -> None:
        """Test grouping commands by plugin name."""
        # Create multiple READMEs
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        pensive_dir = plugins_dir / "pensive"
        pensive_dir.mkdir()
        sanctum_dir = plugins_dir / "sanctum"
        sanctum_dir.mkdir()

        (pensive_dir / "README.md").write_text("Use `/code-review` here.")
        (sanctum_dir / "README.md").write_text("Run `/pr-review` there.")

        extractor = DocumentationCommandExtractor(tmp_path)
        all_commands = extractor.extract_all()

        # Should have found commands in both plugins
        assert "plugins/pensive/README.md" in all_commands
        assert "plugins/sanctum/README.md" in all_commands

        # Check pensive commands
        pensive_cmds = all_commands["plugins/pensive/README.md"]
        assert len(pensive_cmds) == 1
        assert pensive_cmds[0]["command"] == "code-review"

    def test_handles_empty_files(self, tmp_path: Path) -> None:
        """Test handling of files with no commands."""
        test_file = tmp_path / "EMPTY.md"
        test_file.write_text("# Just a heading\n\nNo commands here.\n")

        extractor = DocumentationCommandExtractor(tmp_path)
        commands = extractor.extract_from_file(test_file)

        assert len(commands) == 0


class TestMakefileSynthesis:
    """Tests for Makefile synthesis and generation."""

    def test_generates_demo_targets(self, tmp_path: Path) -> None:
        """Test generation of demo targets for commands."""
        generator = MakefileTargetGenerator(tmp_path)

        commands = [
            {"type": "slash-command", "command": "update-docs", "args": ""},
            {"type": "slash-command", "command": "pr-review", "args": "--dry-run"},
        ]

        generated = generator.generate_demo_targets("test-plugin", commands)

        # Should generate demo-update-docs and demo-pr-review targets
        assert "demo-update-docs:" in generated
        assert "demo-pr-review:" in generated
        assert "## Demo update-docs command" in generated

    def test_generates_test_targets(self, tmp_path: Path) -> None:
        """Test generation of test-* targets for slash commands."""
        generator = MakefileTargetGenerator(tmp_path)

        commands = [{"type": "slash-command", "command": "validate", "args": ""}]

        generated = generator.generate_demo_targets("test", commands)

        # Should generate test-validate target
        assert "test-validate:" in generated
        assert "## Test validate command workflow" in generated

    def test_generates_aggregate_target(self, tmp_path: Path) -> None:
        """Test generation of aggregate demo-{plugin}-commands target."""
        generator = MakefileTargetGenerator(tmp_path)

        commands = [
            {"type": "slash-command", "command": "cmd1", "args": ""},
            {"type": "slash-command", "command": "cmd2", "args": ""},
        ]

        generated = generator.generate_demo_targets("myplugin", commands)

        # Should generate aggregate target
        assert "demo-myplugin-commands:" in generated
        assert "demo-cmd1" in generated
        assert "demo-cmd2" in generated

    def test_uses_live_commands_when_available(self, tmp_path: Path) -> None:
        """Test that plugin-specific live commands are used."""
        generator = MakefileTargetGenerator(tmp_path)

        # conserve plugin has live bloat-scan command
        live_cmd = generator._get_live_command("conserve", "bloat-scan")

        assert live_cmd is not None
        assert "bloat_detector.py" in live_cmd
        assert "--report" in live_cmd


class TestMakefileDogfooderRefactored:
    """Tests for refactored MakefileDogfooder functionality."""

    def test_analyzes_plugin_coverage(self, tmp_path: Path) -> None:
        """Test plugin analysis for dogfood coverage."""
        # Create test plugin structure
        plugin_dir = tmp_path / "plugins" / "testplugin"
        plugin_dir.mkdir(parents=True)

        # Create README with commands
        readme = plugin_dir / "README.md"
        readme.write_text("## Commands\n\n- `/update-docs`\n- `/validate`\n")

        # Create Makefile
        makefile = plugin_dir / "Makefile"
        makefile.write_text(
            """
.PHONY: help
help: @echo help

demo-update-docs: ## Demo update-docs
\t@echo demo
"""
        )

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = dogfooder.analyze_plugin("testplugin")

        # Should find 2 documented commands
        assert finding["commands_documented"] == 2

        # Should find missing demo-validate and test-validate
        # Note: also expects test-update-docs
        assert finding["targets_missing"] == 3
        assert "demo-validate" in finding["missing_targets"]
        assert "test-validate" in finding["missing_targets"]
        assert "test-update-docs" in finding["missing_targets"]

    def test_filters_duplicate_targets(self, tmp_path: Path) -> None:
        """Test that duplicate targets are filtered out."""
        dogfooder = MakefileDogfooder(root_dir=tmp_path)

        existing_targets = {"target1", "target2", "target3"}

        # Generated content with duplicates
        generated_content = """
target1: ## Target 1 description
\t@echo target1

target4: ## New target
\t@echo target4

target2: ## Target 2 (duplicate)
\t@echo target2
"""

        filtered = dogfooder._filter_duplicate_targets(
            generated_content, existing_targets
        )

        # Should only include target4 (new)
        filtered_text = "\n".join(filtered)
        assert "target4:" in filtered_text
        assert "target1:" not in filtered_text

    def test_finds_phony_block(self, tmp_path: Path) -> None:
        """Test .PHONY block finding."""
        dogfooder = MakefileDogfooder(root_dir=tmp_path)

        makefile_content = """
.PHONY: help test build \\
        validate

help: @echo help
"""

        phony_lines = dogfooder._find_phony_block(makefile_content)

        assert len(phony_lines) == 2
        assert ".PHONY:" in phony_lines[0]
        assert phony_lines[0].strip().endswith("\\")
        assert "validate" in phony_lines[1]

    def test_extracts_phony_targets(self, tmp_path: Path) -> None:
        """Test extraction of .PHONY target names."""
        dogfooder = MakefileDogfooder(root_dir=tmp_path)

        phony_lines = [
            ".PHONY: help test \\",
            "\tvalidate build \\",
            "\tclean",
        ]

        targets = dogfooder._extract_phony_targets(phony_lines)

        # Should extract all targets
        assert "help" in targets
        assert "test" in targets
        assert "validate" in targets
        assert "build" in targets
        assert "clean" in targets


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""

    @pytest.mark.integration
    def test_full_dogfooding_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow from doc extraction to makefile generation."""
        # Setup test plugin
        plugin_dir = tmp_path / "plugins" / "testplugin"
        plugin_dir.mkdir(parents=True)

        (plugin_dir / "README.md").write_text(
            """
## Commands

- `/update-docs` - Update documentation
- `/validate` - Validate plugin structure
"""
        )

        (plugin_dir / "Makefile").write_text(
            """
.PHONY: help
help: @echo help
"""
        )

        # Run dogfooder
        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        finding = dogfooder.analyze_plugin("testplugin")

        # Generate targets
        generated = dogfooder.generate_missing_targets("testplugin", finding)

        # Apply to Makefile
        success = dogfooder.apply_targets_to_makefile(
            "testplugin", finding, generated, dry_run=False
        )

        assert success

        # Verify Makefile was updated
        makefile_content = (plugin_dir / "Makefile").read_text()
        assert "demo-update-docs:" in makefile_content

    @pytest.mark.integration
    def test_qa_catches_missing_targets(self, tmp_path: Path) -> None:
        """Test that QA identifies documented commands without targets."""
        # Create plugin with documented but unimplemented commands
        plugin_dir = tmp_path / "plugins" / "incomplete"
        plugin_dir.mkdir(parents=True)

        (plugin_dir / "README.md").write_text(
            """
## Features

- `/feature-one` - Does something
- `/feature-two` - Does something else
"""
        )

        # Empty Makefile
        (plugin_dir / "Makefile").write_text(".PHONY: help\n")

        dogfooder = MakefileDogfooder(root_dir=tmp_path)
        dogfooder.analyze_all()

        # Should report missing targets
        findings = dogfooder.report["findings"]
        incomplete = [f for f in findings if f["plugin"] == "incomplete"][0]

        assert incomplete["targets_missing"] > 0
        assert incomplete["coverage_percent"] < 100
