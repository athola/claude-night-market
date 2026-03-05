"""Unit tests for the dogfooder.validator module.

Feature: Dogfooder package validator module
  As a developer modularizing makefile_dogfooder.py
  I want recipe/target generation logic in a dedicated module
  So that it can be tested and extended independently
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))


class TestDogfooderValidatorImports:
    """Feature: dogfooder.validator module exports correct symbols

    As a developer using the dogfooder package
    I want to import validator classes directly from dogfooder.validator
    So that recipe generation and preflight checks are independently usable
    """

    @pytest.mark.unit
    def test_makefile_target_generator_importable(self) -> None:
        """Scenario: MakefileTargetGenerator is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import MakefileTargetGenerator from dogfooder.validator
        Then the import succeeds and the symbol is a class
        """
        from dogfooder.validator import MakefileTargetGenerator  # noqa: PLC0415

        assert isinstance(MakefileTargetGenerator, type)

    @pytest.mark.unit
    def test_generate_makefile_importable(self) -> None:
        """Scenario: generate_makefile is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import generate_makefile from dogfooder.validator
        Then the import succeeds and the symbol is callable
        """
        from dogfooder.validator import generate_makefile  # noqa: PLC0415

        assert callable(generate_makefile)

    @pytest.mark.unit
    def test_run_preflight_checks_importable(self) -> None:
        """Scenario: run_preflight_checks is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import run_preflight_checks from dogfooder.validator
        Then the import succeeds and the symbol is callable
        """
        from dogfooder.validator import run_preflight_checks  # noqa: PLC0415

        assert callable(run_preflight_checks)

    @pytest.mark.unit
    def test_validate_working_directory_importable(self) -> None:
        """Scenario: validate_working_directory is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import validate_working_directory from dogfooder.validator
        Then the import succeeds and the symbol is callable
        """
        from dogfooder.validator import validate_working_directory  # noqa: PLC0415

        assert callable(validate_working_directory)


class TestMakefileTargetGeneratorFromValidator:
    """Feature: MakefileTargetGenerator works from dogfooder.validator

    As a developer
    I want MakefileTargetGenerator imported from the validator module
    So that target generation works identically to the monolithic script
    """

    @pytest.mark.unit
    def test_generate_target_produces_make_syntax(self, tmp_path: Path) -> None:
        """Scenario: generate_target returns valid Makefile target syntax
        Given a plugin name, command name, and invocation
        When generate_target() is called
        Then the result contains a properly formatted Makefile target
        """
        from dogfooder.validator import MakefileTargetGenerator  # noqa: PLC0415

        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="myplugin",
            command_name="my-cmd",
            invocation="/my-cmd",
            description="Demo my-cmd",
        )

        assert "demo-my-cmd:" in result
        assert "## Demo my-cmd" in result

    @pytest.mark.unit
    def test_generate_demo_targets_includes_test_target(self, tmp_path: Path) -> None:
        """Scenario: generate_demo_targets produces test-* targets for slash commands
        Given a list of slash-command entries
        When generate_demo_targets() is called
        Then a test-<name> target is generated for each command
        """
        from dogfooder.validator import MakefileTargetGenerator  # noqa: PLC0415

        gen = MakefileTargetGenerator(tmp_path)
        commands = [{"type": "slash-command", "command": "check", "args": ""}]

        result = gen.generate_demo_targets("testplugin", commands)

        assert "test-check:" in result
        assert "## Test check command workflow" in result

    @pytest.mark.unit
    def test_generate_demo_targets_includes_aggregate(self, tmp_path: Path) -> None:
        """Scenario: generate_demo_targets includes an aggregate target
        Given multiple slash-command entries
        When generate_demo_targets() is called
        Then a demo-<plugin>-commands aggregate target is generated
        """
        from dogfooder.validator import MakefileTargetGenerator  # noqa: PLC0415

        gen = MakefileTargetGenerator(tmp_path)
        commands = [
            {"type": "slash-command", "command": "cmd-one", "args": ""},
            {"type": "slash-command", "command": "cmd-two", "args": ""},
        ]

        result = gen.generate_demo_targets("myplugin", commands)

        assert "demo-myplugin-commands:" in result

    @pytest.mark.unit
    def test_get_live_command_returns_none_for_unknown(self, tmp_path: Path) -> None:
        """Scenario: _get_live_command returns None for an unknown plugin/command pair
        Given a plugin and command name not in PLUGIN_TOOLS
        When _get_live_command() is called
        Then None is returned
        """
        from dogfooder.validator import MakefileTargetGenerator  # noqa: PLC0415

        gen = MakefileTargetGenerator(tmp_path)
        result = gen._get_live_command("nonexistent-plugin", "nonexistent-cmd")

        assert result is None

    @pytest.mark.unit
    def test_get_live_command_returns_script_for_known(self, tmp_path: Path) -> None:
        """Scenario: _get_live_command returns a shell command for a known pair
        Given the conserve plugin and bloat-scan command (which is in PLUGIN_TOOLS)
        When _get_live_command() is called
        Then a non-empty string is returned
        """
        from dogfooder.validator import MakefileTargetGenerator  # noqa: PLC0415

        gen = MakefileTargetGenerator(tmp_path)
        result = gen._get_live_command("conserve", "bloat-scan")

        assert result is not None
        assert "bloat_detector.py" in result


class TestRunPreflightChecks:
    """Feature: run_preflight_checks validates the environment

    As a developer
    I want preflight checks imported from dogfooder.validator
    So that pre-execution validation is independently usable
    """

    @pytest.mark.unit
    def test_preflight_passes_for_valid_directory(self, tmp_path: Path) -> None:
        """Scenario: preflight succeeds when root and plugins dirs exist
        Given a root_dir with a plugins/ subdirectory
        When run_preflight_checks() is called
        Then True is returned
        """
        from dogfooder.validator import run_preflight_checks  # noqa: PLC0415

        plugins = tmp_path / "plugins"
        plugins.mkdir()

        assert run_preflight_checks(tmp_path, "plugins") is True

    @pytest.mark.unit
    def test_preflight_fails_for_missing_root(self, tmp_path: Path) -> None:
        """Scenario: preflight fails when root_dir does not exist
        Given a root_dir path that does not exist
        When run_preflight_checks() is called
        Then False is returned
        """
        from dogfooder.validator import run_preflight_checks  # noqa: PLC0415

        nonexistent = tmp_path / "ghost"

        assert run_preflight_checks(nonexistent, "plugins") is False

    @pytest.mark.unit
    def test_preflight_fails_for_missing_plugins_dir(self, tmp_path: Path) -> None:
        """Scenario: preflight fails when the plugins sub-directory is absent
        Given a root_dir that exists but has no plugins/ sub-directory
        When run_preflight_checks() is called
        Then False is returned
        """
        from dogfooder.validator import run_preflight_checks  # noqa: PLC0415

        # tmp_path exists but has no plugins/ child
        assert run_preflight_checks(tmp_path, "plugins") is False


class TestGenerateMakefile:
    """Feature: generate_makefile creates Makefiles for plugins

    As a developer
    I want generate_makefile imported from dogfooder.validator
    So that Makefile generation is independently usable
    """

    @pytest.mark.unit
    def test_generate_makefile_python_writes_file(self, tmp_path: Path) -> None:
        """Scenario: generate_makefile writes a Makefile for a Python plugin
        Given a plugin directory with a pyproject.toml
        When generate_makefile() is called without dry_run
        Then a Makefile is created in the plugin directory
        """
        from dogfooder.validator import generate_makefile  # noqa: PLC0415

        plugin_dir = tmp_path / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "pyproject.toml").write_text("[project]\nname = 'myplugin'\n")

        result = generate_makefile(plugin_dir, "myplugin", dry_run=False)

        assert result is True
        assert (plugin_dir / "Makefile").exists()

    @pytest.mark.unit
    def test_generate_makefile_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """Scenario: generate_makefile with dry_run=True does not write a file
        Given a plugin directory with a pyproject.toml
        When generate_makefile() is called with dry_run=True
        Then True is returned but no Makefile is written
        """
        from dogfooder.validator import generate_makefile  # noqa: PLC0415

        plugin_dir = tmp_path / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "pyproject.toml").write_text("[project]\nname = 'myplugin'\n")

        result = generate_makefile(plugin_dir, "myplugin", dry_run=True)

        assert result is True
        assert not (plugin_dir / "Makefile").exists()
