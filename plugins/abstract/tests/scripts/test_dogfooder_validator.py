"""Tests for scripts/dogfooder/validator.py.

Covers MakefileTargetGenerator, generate_makefile, run_preflight_checks,
and validate_working_directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from dogfooder.validator import (
    MakefileTargetGenerator,
    _generate_python_makefile,
    _generate_rust_makefile,
    _generate_typescript_makefile,
    generate_makefile,
    run_preflight_checks,
    validate_working_directory,
)

# ---------------------------------------------------------------------------
# MakefileTargetGenerator._get_live_command
# ---------------------------------------------------------------------------


class TestGetLiveCommand:
    """_get_live_command returns known plugin commands or None."""

    @pytest.mark.unit
    def test_known_plugin_and_command(self, tmp_path):
        """Returns the live command when plugin+command are in the table."""
        gen = MakefileTargetGenerator(tmp_path)
        cmd = gen._get_live_command("conserve", "bloat-scan")
        assert cmd is not None
        assert "bloat_detector" in cmd

    @pytest.mark.unit
    def test_unknown_plugin_returns_none(self, tmp_path):
        """Returns None for an unknown plugin."""
        gen = MakefileTargetGenerator(tmp_path)
        assert gen._get_live_command("unknown-plugin", "cmd") is None

    @pytest.mark.unit
    def test_unknown_command_in_known_plugin_returns_none(self, tmp_path):
        """Returns None when command not in plugin's table."""
        gen = MakefileTargetGenerator(tmp_path)
        assert gen._get_live_command("conserve", "does-not-exist") is None


# ---------------------------------------------------------------------------
# MakefileTargetGenerator.generate_target
# ---------------------------------------------------------------------------


class TestGenerateTarget:
    """generate_target produces a valid Makefile target string."""

    @pytest.mark.unit
    def test_target_name_prefixed_with_demo(self, tmp_path):
        """Target name starts with 'demo-'."""
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="myplugin",
            command_name="my-command",
            invocation="/my-command",
        )
        assert "demo-my-command:" in result

    @pytest.mark.unit
    def test_live_command_used_when_available(self, tmp_path):
        """When plugin+command has live command, it appears in recipe."""
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="conserve",
            command_name="bloat-scan",
            invocation="/bloat-scan",
        )
        assert "bloat_detector" in result

    @pytest.mark.unit
    def test_fallback_echo_when_no_live_command(self, tmp_path):
        """When no live command, fallback echo instructions are used."""
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="unknown-plugin",
            command_name="my-cmd",
            invocation="/my-cmd",
        )
        assert "Claude Code" in result or "Execute manually" in result

    @pytest.mark.unit
    def test_description_in_target_comment(self, tmp_path):
        """Description appears in ## comment of target."""
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="myplugin",
            command_name="my-cmd",
            invocation="/my-cmd",
            description="My custom description",
        )
        assert "My custom description" in result

    @pytest.mark.unit
    def test_invocation_in_recipe(self, tmp_path):
        """Invocation string appears in the recipe."""
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="myplugin",
            command_name="my-cmd",
            invocation="/my-cmd --flag",
        )
        assert "/my-cmd --flag" in result

    @pytest.mark.unit
    def test_slash_removed_from_target_name(self, tmp_path):
        """Slashes in command_name are stripped from target name."""
        gen = MakefileTargetGenerator(tmp_path)
        result = gen.generate_target(
            plugin="p",
            command_name="sub/command",
            invocation="/sub/command",
        )
        assert "demo-subcommand:" in result


# ---------------------------------------------------------------------------
# MakefileTargetGenerator.generate_demo_targets
# ---------------------------------------------------------------------------


class TestGenerateDemoTargets:
    """generate_demo_targets creates targets for all documented commands."""

    @pytest.mark.unit
    def test_generates_individual_demo_targets(self, tmp_path):
        """Each slash command gets a demo-* target."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [
            {"type": "slash-command", "command": "update-docs"},
            {"type": "slash-command", "command": "pr-review"},
        ]
        result = gen.generate_demo_targets("myplugin", commands)
        assert "demo-update-docs:" in result
        assert "demo-pr-review:" in result

    @pytest.mark.unit
    def test_generates_aggregate_target(self, tmp_path):
        """An aggregate demo-{plugin}-commands target is generated."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [{"type": "slash-command", "command": "do-thing"}]
        result = gen.generate_demo_targets("myplugin", commands)
        assert "demo-myplugin-commands:" in result

    @pytest.mark.unit
    def test_generates_test_targets(self, tmp_path):
        """test-* targets are generated for slash commands."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [{"type": "slash-command", "command": "verify"}]
        result = gen.generate_demo_targets("myplugin", commands)
        assert "test-verify:" in result

    @pytest.mark.unit
    def test_cli_invocation_targets_generated(self, tmp_path):
        """CLI invocation commands get demo-cli-* targets."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [{"type": "cli-invocation", "invocation": "pytest --cov"}]
        result = gen.generate_demo_targets("myplugin", commands)
        assert "demo-cli-pytest:" in result

    @pytest.mark.unit
    def test_no_aggregate_when_no_slash_commands(self, tmp_path):
        """When no slash commands, no aggregate target is generated."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [{"type": "cli-invocation", "invocation": "make test"}]
        result = gen.generate_demo_targets("myplugin", commands)
        assert "demo-myplugin-commands:" not in result

    @pytest.mark.unit
    def test_limits_slash_commands_to_10(self, tmp_path):
        """Only first 10 slash commands get demo and test targets (20 total)."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [{"type": "slash-command", "command": f"cmd-{i}"} for i in range(15)]
        result = gen.generate_demo_targets("myplugin", commands)
        # Each of the 10 commands generates 1 demo-* and 1 test-* = 20 total
        demo_count = result.count("demo-cmd-")
        assert demo_count <= 20  # 10 demo + 10 test targets


# ---------------------------------------------------------------------------
# generate_makefile
# ---------------------------------------------------------------------------


class TestGenerateMakefile:
    """generate_makefile creates a language-appropriate Makefile."""

    @pytest.mark.unit
    def test_python_makefile_when_pyproject_toml(self, tmp_path):
        """Generates Python Makefile when pyproject.toml exists."""
        (tmp_path / "pyproject.toml").touch()
        result = generate_makefile(tmp_path, "myplugin", dry_run=True)
        assert result is True

    @pytest.mark.unit
    def test_rust_makefile_when_cargo_toml(self, tmp_path):
        """Generates Rust Makefile when Cargo.toml exists."""
        (tmp_path / "Cargo.toml").touch()
        result = generate_makefile(tmp_path, "myplugin", dry_run=True)
        assert result is True

    @pytest.mark.unit
    def test_typescript_makefile_when_package_json(self, tmp_path):
        """Generates TypeScript Makefile when package.json exists."""
        (tmp_path / "package.json").touch()
        result = generate_makefile(tmp_path, "myplugin", dry_run=True)
        assert result is True

    @pytest.mark.unit
    def test_default_python_when_no_language_file(self, tmp_path, capsys):
        """Defaults to Python when no language file found."""
        result = generate_makefile(tmp_path, "myplugin", dry_run=True)
        assert result is True

    @pytest.mark.unit
    def test_dry_run_does_not_write_file(self, tmp_path):
        """In dry_run mode, Makefile is not written."""
        generate_makefile(tmp_path, "myplugin", dry_run=True)
        assert not (tmp_path / "Makefile").exists()

    @pytest.mark.unit
    def test_writes_file_when_not_dry_run(self, tmp_path):
        """When not dry_run, Makefile is written."""
        (tmp_path / "pyproject.toml").touch()
        generate_makefile(tmp_path, "myplugin", dry_run=False)
        assert (tmp_path / "Makefile").exists()


# ---------------------------------------------------------------------------
# _generate_*_makefile helpers
# ---------------------------------------------------------------------------


class TestMakefileTemplates:
    """The template generators produce valid Makefile stubs."""

    @pytest.mark.unit
    def test_python_template_contains_standard_targets(self):
        """Python template has install, lint, test, and build targets."""
        content = _generate_python_makefile("myplugin")
        for target in ("install:", "lint:", "test:", "build:"):
            assert target in content

    @pytest.mark.unit
    def test_rust_template_contains_cargo_targets(self):
        """Rust template has fmt, test, build targets."""
        content = _generate_rust_makefile("myplugin")
        for target in ("fmt:", "test:", "build:"):
            assert target in content

    @pytest.mark.unit
    def test_typescript_template_contains_npm_targets(self):
        """TypeScript template has install, typecheck, test targets."""
        content = _generate_typescript_makefile("myplugin")
        for target in ("install:", "typecheck:", "test:"):
            assert target in content

    @pytest.mark.unit
    def test_plugin_name_capitalized_in_header(self):
        """Plugin name appears capitalized in file header comment."""
        content = _generate_python_makefile("mytest")
        assert "Mytest" in content


# ---------------------------------------------------------------------------
# run_preflight_checks
# ---------------------------------------------------------------------------


class TestRunPreflightChecks:
    """run_preflight_checks validates preconditions."""

    @pytest.mark.unit
    def test_returns_true_when_valid(self, tmp_path):
        """Returns True when root_dir and plugins_dir exist with write access."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        result = run_preflight_checks(tmp_path, "plugins")
        assert result is True

    @pytest.mark.unit
    def test_returns_false_when_root_missing(self, tmp_path):
        """Returns False when root_dir does not exist."""
        missing = tmp_path / "nonexistent"
        result = run_preflight_checks(missing, "plugins")
        assert result is False

    @pytest.mark.unit
    def test_returns_false_when_plugins_dir_missing(self, tmp_path):
        """Returns False when plugins_dir doesn't exist."""
        result = run_preflight_checks(tmp_path, "plugins")
        assert result is False

    @pytest.mark.unit
    def test_warns_when_no_git_dir(self, tmp_path, capsys):
        """Prints a warning when .git directory is absent."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        run_preflight_checks(tmp_path, "plugins")
        out = capsys.readouterr().out
        assert "git" in out.lower() or "rollback" in out.lower()


# ---------------------------------------------------------------------------
# validate_working_directory
# ---------------------------------------------------------------------------


class TestValidateWorkingDirectory:
    """validate_working_directory checks cwd and optional plugin Makefile."""

    @pytest.mark.unit
    def test_returns_true_when_cwd_matches(self, tmp_path):
        """Returns True when current dir matches root_dir."""
        import os

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = validate_working_directory(tmp_path, "plugins")
        finally:
            os.chdir(original_cwd)
        assert result is True

    @pytest.mark.unit
    def test_returns_false_when_plugin_makefile_missing(self, tmp_path):
        """Returns False when plugin_name specified but Makefile missing."""
        import os

        plugins = tmp_path / "plugins"
        plugins.mkdir()
        plugin_dir = plugins / "myplugin"
        plugin_dir.mkdir()

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = validate_working_directory(
                tmp_path, "plugins", plugin_name="myplugin"
            )
        finally:
            os.chdir(original_cwd)
        assert result is False

    @pytest.mark.unit
    def test_returns_true_when_plugin_makefile_exists(self, tmp_path):
        """Returns True when plugin Makefile exists."""
        import os

        plugins = tmp_path / "plugins"
        plugins.mkdir()
        plugin_dir = plugins / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "Makefile").write_text("# Makefile\n")

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            result = validate_working_directory(
                tmp_path, "plugins", plugin_name="myplugin"
            )
        finally:
            os.chdir(original_cwd)
        assert result is True

    @pytest.mark.unit
    def test_chdir_failure_returns_false(self, tmp_path, monkeypatch):
        """Returns False when os.chdir raises an exception."""
        import os

        # Current dir is different from tmp_path
        original_cwd = Path.cwd()

        def failing_chdir(path):
            raise OSError("permission denied")

        monkeypatch.setattr(os, "chdir", failing_chdir)

        # Make sure cwd != root_dir by using a different path
        result = validate_working_directory(tmp_path / "nonexistent_target", "plugins")
        assert result is False


# ---------------------------------------------------------------------------
# Additional generate_demo_targets: args in slash command
# ---------------------------------------------------------------------------


class TestGenerateDemoTargetsWithArgs:
    """generate_demo_targets includes args in invocation when present."""

    @pytest.mark.unit
    def test_args_appended_to_invocation(self, tmp_path):
        """When slash command has args, they appear in the invocation."""
        gen = MakefileTargetGenerator(tmp_path)
        commands = [
            {"type": "slash-command", "command": "update-docs", "args": "--dry-run"}
        ]
        result = gen.generate_demo_targets("myplugin", commands)
        assert "/update-docs --dry-run" in result


# ---------------------------------------------------------------------------
# run_preflight_checks: write permission failure
# ---------------------------------------------------------------------------


class TestRunPreflightChecksWritePermission:
    """run_preflight_checks returns False when write permission denied."""

    @pytest.mark.unit
    def test_returns_false_on_write_permission_error(self, tmp_path, monkeypatch):
        """Returns False when .write_test file cannot be created."""
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()

        original_touch = Path.touch

        def failing_touch(self, *args, **kwargs):
            if ".write_test" in str(self):
                raise PermissionError("no write access")
            return original_touch(self, *args, **kwargs)

        monkeypatch.setattr(Path, "touch", failing_touch)
        result = run_preflight_checks(tmp_path, "plugins")
        assert result is False
