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

from dogfooder.validator import (
    MakefileTargetGenerator,
    generate_makefile,
    run_preflight_checks,
    validate_working_directory,
)


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
        assert isinstance(MakefileTargetGenerator, type)

    @pytest.mark.unit
    def test_generate_makefile_importable(self) -> None:
        """Scenario: generate_makefile is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import generate_makefile from dogfooder.validator
        Then the import succeeds and the symbol is callable
        """
        assert callable(generate_makefile)

    @pytest.mark.unit
    def test_run_preflight_checks_importable(self) -> None:
        """Scenario: run_preflight_checks is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import run_preflight_checks from dogfooder.validator
        Then the import succeeds and the symbol is callable
        """
        assert callable(run_preflight_checks)

    @pytest.mark.unit
    def test_validate_working_directory_importable(self) -> None:
        """Scenario: validate_working_directory is importable from dogfooder.validator
        Given the dogfooder package exists
        When I import validate_working_directory from dogfooder.validator
        Then the import succeeds and the symbol is callable
        """
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
        gen = MakefileTargetGenerator(tmp_path)
        result = gen._get_live_command("conserve", "bloat-scan")

        assert result is not None
        assert "bloat_detector.py" in result


class TestGenerateDemoTargetsNoDuplicate:
    """Feature: generate_demo_targets produces exactly one aggregate target

    Regression test for C3: the aggregate demo-{plugin}-commands target
    must not be appended twice.
    """

    @pytest.mark.unit
    def test_aggregate_target_appears_exactly_once(self, tmp_path: Path) -> None:
        """Scenario: Aggregate target is not duplicated
        Given multiple slash-command entries
        When generate_demo_targets() is called
        Then demo-{plugin}-commands: appears exactly once
        """
        gen = MakefileTargetGenerator(tmp_path)
        commands = [
            {"type": "slash-command", "command": "cmd-one", "args": ""},
            {"type": "slash-command", "command": "cmd-two", "args": ""},
        ]

        result = gen.generate_demo_targets("myplugin", commands)

        assert result.count("demo-myplugin-commands:") == 1


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
        nonexistent = tmp_path / "ghost"

        assert run_preflight_checks(nonexistent, "plugins") is False

    @pytest.mark.unit
    def test_preflight_fails_for_missing_plugins_dir(self, tmp_path: Path) -> None:
        """Scenario: preflight fails when the plugins sub-directory is absent
        Given a root_dir that exists but has no plugins/ sub-directory
        When run_preflight_checks() is called
        Then False is returned
        """
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
        plugin_dir = tmp_path / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "pyproject.toml").write_text("[project]\nname = 'myplugin'\n")

        result = generate_makefile(plugin_dir, "myplugin", dry_run=True)

        assert result is True
        assert not (plugin_dir / "Makefile").exists()


class TestGenerateTargetLiveCommand:
    """Feature: generate_target uses live commands when available

    As a developer
    I want generate_target to embed actual script invocations
    So that demo targets run real tools instead of placeholders
    """

    @pytest.mark.unit
    def test_live_command_branch_includes_running_message(self, tmp_path: Path) -> None:
        """Scenario: Known plugin/command pair generates a live recipe
        Given a plugin/command pair that exists in PLUGIN_TOOLS
        When generate_target() is called
        Then the recipe includes 'Running' and the actual command
        """
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="conserve",
            command_name="bloat-scan",
            invocation="/bloat-scan",
            description="Demo bloat-scan (LIVE)",
        )

        assert "Running bloat-scan" in result
        assert "bloat_detector.py" in result


class TestGenerateDemoTargetsCliInvocation:
    """Feature: generate_demo_targets handles CLI invocations

    As a developer
    I want CLI invocations to produce demo targets
    So that all documented command types are covered
    """

    @pytest.mark.unit
    def test_cli_invocation_generates_target(self, tmp_path: Path) -> None:
        """Scenario: CLI invocation type generates cli-* targets
        Given a command entry with type 'cli-invocation'
        When generate_demo_targets() is called
        Then a demo target for the CLI invocation is generated
        """
        gen = MakefileTargetGenerator(tmp_path)
        commands = [
            {
                "type": "cli-invocation",
                "invocation": "python scripts/analyze.py --scan",
                "command": "analyze",
            }
        ]

        result = gen.generate_demo_targets("myplugin", commands)

        assert "demo-cli-python:" in result


class TestGenerateMakefileLanguages:
    """Feature: generate_makefile supports Rust and TypeScript

    As a developer
    I want Makefile generation for multiple languages
    So that non-Python plugins get proper build targets
    """

    @pytest.mark.unit
    def test_rust_makefile_generation(self, tmp_path: Path) -> None:
        """Scenario: Plugin with Cargo.toml gets a Rust Makefile
        Given a plugin directory with Cargo.toml
        When generate_makefile() is called
        Then a Makefile with cargo targets is created
        """
        plugin_dir = tmp_path / "rust-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "Cargo.toml").write_text('[package]\nname = "rust-plugin"\n')

        result = generate_makefile(plugin_dir, "rust-plugin", dry_run=False)

        assert result is True
        content = (plugin_dir / "Makefile").read_text()
        assert "cargo test" in content
        assert "cargo clippy" in content

    @pytest.mark.unit
    def test_typescript_makefile_generation(self, tmp_path: Path) -> None:
        """Scenario: Plugin with package.json gets a TypeScript Makefile
        Given a plugin directory with package.json
        When generate_makefile() is called
        Then a Makefile with npm targets is created
        """
        plugin_dir = tmp_path / "ts-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "package.json").write_text('{"name": "ts-plugin"}')

        result = generate_makefile(plugin_dir, "ts-plugin", dry_run=False)

        assert result is True
        content = (plugin_dir / "Makefile").read_text()
        assert "npm" in content or "npx" in content

    @pytest.mark.unit
    def test_no_language_file_defaults_python(self, tmp_path: Path) -> None:
        """Scenario: Plugin with no language files defaults to Python
        Given a plugin directory with no pyproject.toml, Cargo.toml, or package.json
        When generate_makefile() is called
        Then a Python-style Makefile is created
        """
        plugin_dir = tmp_path / "unknown-plugin"
        plugin_dir.mkdir()

        result = generate_makefile(plugin_dir, "unknown-plugin", dry_run=False)

        assert result is True
        content = (plugin_dir / "Makefile").read_text()
        assert "uv run" in content or "pytest" in content


class TestValidateWorkingDirectory:
    """Feature: validate_working_directory ensures correct context

    As a developer
    I want to validate the working directory before file operations
    So that operations target the right location
    """

    @pytest.mark.unit
    def test_matching_directory_returns_true(self, tmp_path: Path) -> None:
        """Scenario: Working directory matches root_dir
        Given cwd equals root_dir
        When validate_working_directory() is called
        Then True is returned
        """
        import os  # noqa: PLC0415

        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = validate_working_directory(tmp_path, "plugins")
            assert result is True
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_missing_plugin_makefile_returns_false(self, tmp_path: Path) -> None:
        """Scenario: Specified plugin has no Makefile
        Given a valid root_dir but plugin directory has no Makefile
        When validate_working_directory(plugin_name='ghost') is called
        Then False is returned
        """
        import os  # noqa: PLC0415

        plugins = tmp_path / "plugins" / "ghost"
        plugins.mkdir(parents=True)

        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = validate_working_directory(tmp_path, "plugins", "ghost")
            assert result is False
        finally:
            os.chdir(original)

    @pytest.mark.unit
    def test_valid_plugin_makefile_returns_true(self, tmp_path: Path) -> None:
        """Scenario: Plugin with Makefile passes validation
        Given a plugin directory containing a Makefile
        When validate_working_directory(plugin_name='good') is called
        Then True is returned
        """
        import os  # noqa: PLC0415

        plugin_dir = tmp_path / "plugins" / "good"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "Makefile").write_text(".PHONY: help\nhelp:\n\t@echo help\n")

        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = validate_working_directory(tmp_path, "plugins", "good")
            assert result is True
        finally:
            os.chdir(original)
