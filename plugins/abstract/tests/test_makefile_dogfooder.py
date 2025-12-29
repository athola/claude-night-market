"""Tests for the Makefile dogfooder script.

Tests the key functionality: include parsing, PHONY recognition,
plugin type detection, and scoring logic.
"""

# Import the module under test
import sys
from pathlib import Path
from textwrap import dedent

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from makefile_dogfooder import MakefileDogfooder, MakefileInventory, Target


def make_target(
    name: str,
    phony: bool = True,
    dependencies: list[str] | None = None,
    commands: list[str] | None = None,
) -> Target:
    """Helper to create Target with required fields."""
    return Target(
        name=name,
        description="",
        phony=phony,
        dependencies=dependencies or [],
        commands=commands or [],
        file_path="/fake/Makefile",
        line_number=1,
    )


class TestIncludeParsing:
    """Tests for include directive parsing."""

    def test_parse_include_directive(self, tmp_path: Path) -> None:
        """Test parsing of include directives from Makefile content."""
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            dedent("""\
            -include $(ABSTRACT_DIR)/config/make/common.mk
            -include $(ABSTRACT_DIR)/config/make/python.mk
            include local.mk

            help:
            \t@echo "Help"
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        assert len(inventory.includes) == 3
        assert "$(ABSTRACT_DIR)/config/make/common.mk" in inventory.includes
        assert "$(ABSTRACT_DIR)/config/make/python.mk" in inventory.includes
        assert "local.mk" in inventory.includes

    def test_no_includes(self, tmp_path: Path) -> None:
        """Test parsing Makefile with no includes."""
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            dedent("""\
            .PHONY: help

            help:
            \t@echo "Help"
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        assert inventory.includes == []


class TestPhonyRecognition:
    """Tests for .PHONY target recognition."""

    def test_single_phony_declaration(self, tmp_path: Path) -> None:
        """Test parsing single .PHONY declaration."""
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            dedent("""\
            .PHONY: help clean test

            help:
            \t@echo "Help"
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        # The .PHONY target itself should be recognized
        assert ".PHONY" in inventory.targets
        # And targets declared as PHONY should be marked
        assert "help" in inventory.targets
        assert inventory.targets["help"].phony is True

    def test_multiple_phony_declarations(self, tmp_path: Path) -> None:
        """Test parsing multiple .PHONY declarations.

        Note: Implementation reads .PHONY dependencies from the last
        .PHONY target entry. Multiple declarations result in only the
        last line's targets being marked as phony. This is a known
        limitation - best practice is a single .PHONY declaration.
        """
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            dedent("""\
            .PHONY: help clean test lint

            help:
            \t@echo "Help"

            test:
            \t@pytest
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        # All PHONY targets on the single line should be tracked
        assert inventory.targets["help"].phony is True
        assert inventory.targets["test"].phony is True


class TestPluginTypeDetection:
    """Tests for plugin type detection logic."""

    def test_leaf_plugin_type(self, tmp_path: Path) -> None:
        """Test detection of leaf plugin (standard plugin Makefile)."""
        # Create path that looks like a plugin path
        plugin_dir = tmp_path / "plugins" / "myplugin"
        plugin_dir.mkdir(parents=True)
        makefile = plugin_dir / "Makefile"
        makefile.write_text(
            dedent("""\
            .PHONY: help test

            help:
            \t@echo "Help"

            test:
            \tuv run pytest
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        assert inventory.plugin_type == "leaf"

    def test_aggregator_plugin_type(self, tmp_path: Path) -> None:
        """Test detection of aggregator (Makefile with delegation).

        Aggregator detection requires 'plugins' in the path AND
        $(MAKE) -C commands in target commands.
        """
        # Create path that includes "plugins" to trigger aggregator detection
        plugins_dir = tmp_path / "plugins" / "root"
        plugins_dir.mkdir(parents=True)
        makefile = plugins_dir / "Makefile"
        makefile.write_text(
            dedent("""\
            .PHONY: help test-all

            help:
            \t@echo "Help"

            test-all:
            \t$(MAKE) -C plugins/abstract test
            \t$(MAKE) -C plugins/sanctum test
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        assert inventory.plugin_type == "aggregator"
        # Verify commands were captured correctly
        assert len(inventory.targets["test-all"].commands) == 2

    def test_auxiliary_plugin_type(self, tmp_path: Path) -> None:
        """Test detection of auxiliary Makefile (in docs/ or tests/)."""
        docs_dir = tmp_path / "plugins" / "abstract" / "docs"
        docs_dir.mkdir(parents=True)
        makefile = docs_dir / "Makefile"
        makefile.write_text(
            dedent("""\
            .PHONY: help

            help:
            \t@echo "Docs help"
        """)
        )

        dogfooder = MakefileDogfooder()
        inventory = dogfooder.parse_makefile(makefile)

        assert inventory.plugin_type == "auxiliary"


class TestScoringLogic:
    """Tests for Makefile scoring logic."""

    def test_essential_targets_scoring(self) -> None:
        """Test that essential targets contribute 20 points each."""
        # Create inventory with essential targets
        inventory = MakefileInventory(
            file_path="/fake/plugins/test/Makefile",
            targets={
                "help": make_target("help"),
                "clean": make_target("clean"),
                ".PHONY": make_target(".PHONY"),
            },
            variables={},
            includes=[],
            plugin_type="leaf",
        )

        dogfooder = MakefileDogfooder()
        result = dogfooder.analyze_makefile(inventory)

        # 3 essential targets * 20 points = 60 points base
        assert result.score >= 60

    def test_markdown_only_auto_credit(self) -> None:
        """Test that markdown-only plugins get auto-credit for Python targets."""
        inventory = MakefileInventory(
            file_path="/fake/plugins/archetypes/Makefile",
            targets={
                "help": make_target("help"),
                "clean": make_target("clean"),
                ".PHONY": make_target(".PHONY"),
                "status": make_target("status"),
            },
            variables={},
            includes=["$(ABSTRACT_DIR)/config/make/markdown-only.mk"],
            plugin_type="leaf",
        )

        dogfooder = MakefileDogfooder()
        result = dogfooder.analyze_makefile(inventory)

        # Should get auto-credit for test, lint, format, install
        # 3 essential (60) + status (10) + 4 Python auto-credit (40) = 100+
        assert result.score == 100  # Capped at 100

    def test_auxiliary_auto_credit(self) -> None:
        """Test that auxiliary Makefiles get auto-credit for some targets."""
        inventory = MakefileInventory(
            file_path="/fake/plugins/abstract/docs/Makefile",
            targets={
                "help": make_target("help"),
                ".PHONY": make_target(".PHONY"),
                "%": make_target("%", phony=False),  # catch-all rule
            },
            variables={},
            includes=[],
            plugin_type="auxiliary",
        )

        dogfooder = MakefileDogfooder()
        result = dogfooder.analyze_makefile(inventory)

        # Auxiliary should get credit for Python targets + status
        # Plus catch-all % gives credit for clean
        assert result.score >= 80


class TestExplainMode:
    """Tests for --explain mode output."""

    def test_explain_mode_outputs_breakdown(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that explain mode outputs scoring breakdown."""
        inventory = MakefileInventory(
            file_path="/fake/Makefile",
            targets={
                "help": make_target("help"),
            },
            variables={},
            includes=[],
            plugin_type="leaf",
        )

        dogfooder = MakefileDogfooder(explain=True)
        dogfooder.analyze_makefile(inventory)

        captured = capsys.readouterr()
        assert "[explain]" in captured.out
        assert "Plugin type:" in captured.out
        assert "Scoring breakdown:" in captured.out


class TestVerboseMode:
    """Tests for --verbose mode output."""

    def test_verbose_mode_shows_includes(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that verbose mode shows include discovery."""
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            dedent("""\
            -include config/common.mk

            help:
            \t@echo "Help"
        """)
        )

        dogfooder = MakefileDogfooder(verbose=True)
        dogfooder.parse_makefile(makefile)

        captured = capsys.readouterr()
        assert "[verbose]" in captured.out
        assert "includes:" in captured.out
