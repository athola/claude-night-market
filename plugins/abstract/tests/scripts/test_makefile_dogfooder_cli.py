"""Tests for makefile_dogfooder.py CLI wrapper functions.

Feature: Makefile dogfooder CLI
    As a developer
    I want the CLI entry point tested
    So that main(), _process_single_plugin, and _process_all_plugins work

This file covers the thin CLI wrapper in makefile_dogfooder.py (the
``main``, ``_process_single_plugin``, and ``_process_all_plugins``
functions) which sit at 12% coverage.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from makefile_dogfooder import (
    MakefileDogfooder,
    ProcessingConfig,
    _process_all_plugins,
    _process_single_plugin,
    main,
)


def _make_plugin_tree(tmp_path: Path, name: str = "testplugin") -> Path:
    """Create a minimal plugin directory tree for dogfooder tests."""
    plugin_dir = tmp_path / "plugins" / name
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "README.md").write_text("Use `/my-cmd` here.\n")
    (plugin_dir / "Makefile").write_text(".PHONY: help\nhelp:\n\t@echo help\n")
    return tmp_path


# ---------------------------------------------------------------------------
# _process_single_plugin
# ---------------------------------------------------------------------------


class TestProcessSinglePlugin:
    """Feature: _process_single_plugin processes one plugin.

    As a developer
    I want single-plugin processing logic tested
    So that --plugin mode works correctly
    """

    @pytest.mark.unit
    def test_analyze_only_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Analyze mode returns 0 with no generation.
        Given a plugin with documented commands
        When config.mode is 'analyze'
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        dogfooder = MakefileDogfooder(root_dir=root)
        config = ProcessingConfig(
            mode="analyze",
            generate_missing=False,
            dry_run=False,
            verbose=False,
        )
        rc = _process_single_plugin(dogfooder, "testplugin", config)
        assert rc == 0

    @pytest.mark.unit
    def test_verbose_analyze_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Verbose analyze mode prints JSON and returns 0.
        Given a plugin with documented commands
        When config.mode is 'analyze' and verbose is True
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        dogfooder = MakefileDogfooder(root_dir=root)
        config = ProcessingConfig(
            mode="analyze",
            generate_missing=False,
            dry_run=False,
            verbose=True,
        )
        rc = _process_single_plugin(dogfooder, "testplugin", config)
        assert rc == 0

    @pytest.mark.unit
    def test_generate_mode_prints_targets(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: Generate mode prints generated targets.
        Given a plugin with missing targets
        When config.mode is 'generate'
        Then generated targets are printed and return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        dogfooder = MakefileDogfooder(root_dir=root)
        config = ProcessingConfig(
            mode="generate",
            generate_missing=False,
            dry_run=False,
            verbose=False,
        )
        rc = _process_single_plugin(dogfooder, "testplugin", config)
        assert rc == 0
        captured = capsys.readouterr()
        assert "Generated targets" in captured.out or "testplugin" in captured.out

    @pytest.mark.unit
    def test_generate_mode_no_missing_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: Generate mode with no missing targets returns 0 silently.
        Given a plugin with all targets present
        When config.mode is 'generate'
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path, "complete")
        plugin_dir = root / "plugins" / "complete"
        (plugin_dir / "README.md").write_text("- `/single-cmd`\n")
        (plugin_dir / "Makefile").write_text(
            ".PHONY: help demo-single-cmd test-single-cmd\n"
            "help:\n\t@echo help\n"
            "demo-single-cmd:\n\t@echo demo\n"
            "test-single-cmd:\n\t@echo test\n"
        )
        dogfooder = MakefileDogfooder(root_dir=root)
        config = ProcessingConfig(
            mode="generate",
            generate_missing=False,
            dry_run=False,
            verbose=False,
        )
        rc = _process_single_plugin(dogfooder, "complete", config)
        assert rc == 0


# ---------------------------------------------------------------------------
# _process_all_plugins
# ---------------------------------------------------------------------------


class TestProcessAllPlugins:
    """Feature: _process_all_plugins processes every plugin.

    As a developer
    I want all-plugins processing tested
    So that the full scan works correctly
    """

    @pytest.mark.unit
    def test_analyze_all_runs_without_error(self, tmp_path: Path) -> None:
        """Scenario: Analyze mode over all plugins completes.
        Given multiple plugins in the tree
        When config.mode is 'analyze'
        Then no exception is raised
        """
        root = _make_plugin_tree(tmp_path, "alpha")
        beta = root / "plugins" / "beta"
        beta.mkdir(parents=True)
        (beta / "README.md").write_text("# Beta\n")
        (beta / "Makefile").write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        dogfooder = MakefileDogfooder(root_dir=root)
        config = ProcessingConfig(
            mode="analyze",
            generate_missing=False,
            dry_run=False,
            verbose=False,
        )
        # Should not raise
        _process_all_plugins(dogfooder, config)

    @pytest.mark.unit
    def test_generate_all_produces_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Scenario: Generate mode over all plugins produces output.
        Given a plugin with missing targets
        When config.mode is 'generate'
        Then output contains 'Generating targets'
        """
        root = _make_plugin_tree(tmp_path)
        dogfooder = MakefileDogfooder(root_dir=root)
        config = ProcessingConfig(
            mode="generate",
            generate_missing=False,
            dry_run=False,
            verbose=False,
        )
        _process_all_plugins(dogfooder, config)
        captured = capsys.readouterr()
        assert "Generating targets" in captured.out


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------


class TestMainCLI:
    """Feature: main() CLI entry point.

    As a developer
    I want the CLI main function tested
    So that argument parsing and dispatch work
    """

    @pytest.mark.unit
    def test_main_analyze_mode(self, tmp_path: Path) -> None:
        """Scenario: main() in analyze mode returns 0.
        Given a valid plugin tree
        When main is invoked with --mode analyze
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "analyze",
            ],
        ):
            rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_with_plugin_flag(self, tmp_path: Path) -> None:
        """Scenario: main() with --plugin processes single plugin.
        Given a valid plugin tree
        When main is invoked with --plugin testplugin
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "analyze",
                "--plugin",
                "testplugin",
            ],
        ):
            rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_nonexistent_root_returns_one(self, tmp_path: Path) -> None:
        """Scenario: main() with non-existent root returns 1.
        Given a root path that does not exist
        When main is invoked
        Then return code is 1
        """
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(tmp_path / "nonexistent"),
                "--mode",
                "analyze",
            ],
        ):
            rc = main()
        assert rc == 1

    @pytest.mark.unit
    def test_main_dry_run_mode(self, tmp_path: Path) -> None:
        """Scenario: main() with --dry-run completes without writing.
        Given a valid plugin tree
        When main is invoked with --mode analyze --dry-run
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "analyze",
                "--dry-run",
            ],
        ):
            rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_verbose_mode(self, tmp_path: Path) -> None:
        """Scenario: main() with --verbose completes successfully.
        Given a valid plugin tree
        When main is invoked with --verbose
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "analyze",
                "--verbose",
            ],
        ):
            rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_json_output(self, tmp_path: Path) -> None:
        """Scenario: main() with --output json produces JSON report.
        Given a valid plugin tree
        When main is invoked with --output json
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "analyze",
                "--output",
                "json",
            ],
        ):
            rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_generate_mode(self, tmp_path: Path) -> None:
        """Scenario: main() with --mode generate works.
        Given a valid plugin tree with missing targets
        When main is invoked with --mode generate
        Then return code is 0
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "generate",
            ],
        ):
            rc = main()
        assert rc == 0

    @pytest.mark.unit
    def test_main_nonexistent_plugin_returns_one(self, tmp_path: Path) -> None:
        """Scenario: main() with --plugin for non-existent plugin returns 1.
        Given a valid root but non-existent plugin name
        When main is invoked
        Then return code is 1
        """
        root = _make_plugin_tree(tmp_path)
        with patch(
            "sys.argv",
            [
                "makefile_dogfooder.py",
                "--root",
                str(root),
                "--mode",
                "analyze",
                "--plugin",
                "nonexistent",
            ],
        ):
            rc = main()
        assert rc == 1
