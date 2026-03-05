"""Tests for wrapper_generator.py.

Covers generate_wrapper(), auto_detect_wrappers(), and CLI main().
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path so the module can be imported directly.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# ---------------------------------------------------------------------------
# Module import fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def wg(monkeypatch: pytest.MonkeyPatch):
    """Import wrapper_generator with a clean module state.

    Re-importing ensures monkeypatches on module-level state don't bleed
    between tests.
    """
    if "wrapper_generator" in sys.modules:
        del sys.modules["wrapper_generator"]

    import wrapper_generator  # noqa: PLC0415

    return wrapper_generator


# ---------------------------------------------------------------------------
# generate_wrapper - return value
# ---------------------------------------------------------------------------


class TestGenerateWrapperReturnValue:
    """generate_wrapper returns syntactically correct Python source."""

    @pytest.mark.unit
    def test_returns_string(self, wg) -> None:
        """Given valid arguments, generate_wrapper returns a string."""
        result = wg.generate_wrapper("sanctum", "pr-review", "CodeReviewer")
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_class_name_single_word_command(self, wg) -> None:
        """Given a single-word command, class name is capitalised correctly."""
        result = wg.generate_wrapper("myplugin", "review", "Reviewer")
        assert "ReviewWrapper" in result

    @pytest.mark.unit
    def test_class_name_hyphenated_command(self, wg) -> None:
        """Given a hyphenated command, class name joins words in PascalCase."""
        result = wg.generate_wrapper("sanctum", "pr-review", "CodeReviewer")
        assert "PrReviewWrapper" in result

    @pytest.mark.unit
    def test_class_name_multi_segment_command(self, wg) -> None:
        """Given three-segment command, class name has three capitalised words."""
        result = wg.generate_wrapper("plugin", "do-some-thing", "Doer")
        assert "DoSomeThingWrapper" in result

    @pytest.mark.unit
    def test_output_contains_plugin_name(self, wg) -> None:
        """Given plugin_name='myplugin', generated code references it."""
        result = wg.generate_wrapper("myplugin", "cmd", "Super")
        assert "myplugin" in result

    @pytest.mark.unit
    def test_output_contains_command_name(self, wg) -> None:
        """Given command_name='my-cmd', generated code references it."""
        result = wg.generate_wrapper("plugin", "my-cmd", "Super")
        assert "my-cmd" in result

    @pytest.mark.unit
    def test_output_contains_superpower_name(self, wg) -> None:
        """Given target_superpower='CodeReviewer', generated code imports it."""
        result = wg.generate_wrapper("plugin", "cmd", "CodeReviewer")
        assert "CodeReviewer" in result

    @pytest.mark.unit
    def test_output_contains_import_statement(self, wg) -> None:
        """Given any superpower, generated code has an import from abstract."""
        result = wg.generate_wrapper("plugin", "cmd", "MySuper")
        assert "from abstract.superpowers." in result

    @pytest.mark.unit
    def test_import_uses_lowercase_superpower(self, wg) -> None:
        """Given superpower='CodeReviewer', import path uses lowercase name."""
        result = wg.generate_wrapper("plugin", "cmd", "CodeReviewer")
        assert "from abstract.superpowers.codereviewer import CodeReviewer" in result

    @pytest.mark.unit
    def test_output_contains_execute_method(self, wg) -> None:
        """Generated code always contains an execute() method."""
        result = wg.generate_wrapper("plugin", "cmd", "Super")
        assert "def execute(" in result

    @pytest.mark.unit
    def test_output_contains_map_parameters_method(self, wg) -> None:
        """Generated code always contains a _map_parameters() method."""
        result = wg.generate_wrapper("plugin", "cmd", "Super")
        assert "def _map_parameters(" in result

    @pytest.mark.unit
    def test_output_no_file_written_when_no_output_path(self, wg, tmp_path) -> None:
        """Given output_path=None, no file is written to disk."""
        wg.generate_wrapper("plugin", "cmd", "Super", output_path=None)
        # tmp_path should remain empty - nothing was written
        assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# generate_wrapper - file creation
# ---------------------------------------------------------------------------


class TestGenerateWrapperFileCreation:
    """generate_wrapper creates the output file when output_path is given."""

    @pytest.mark.unit
    def test_creates_file_at_output_path(self, wg, tmp_path) -> None:
        """Given output_path inside tmp_path, file is created."""
        out = tmp_path / "my_wrapper.py"
        wg.generate_wrapper("plugin", "cmd", "Super", output_path=out)
        assert out.exists()

    @pytest.mark.unit
    def test_file_content_matches_return_value(self, wg, tmp_path) -> None:
        """Given output_path, file content equals the returned string."""
        out = tmp_path / "wrapper.py"
        code = wg.generate_wrapper("plugin", "cmd", "Super", output_path=out)
        assert out.read_text() == code

    @pytest.mark.unit
    def test_creates_parent_directories(self, wg, tmp_path) -> None:
        """Given output_path with non-existent parents, dirs are created."""
        out = tmp_path / "deep" / "nested" / "dir" / "wrapper.py"
        wg.generate_wrapper("plugin", "cmd", "Super", output_path=out)
        assert out.exists()
        assert out.parent.is_dir()

    @pytest.mark.unit
    def test_overwrites_existing_file(self, wg, tmp_path) -> None:
        """Given an existing file at output_path, it is overwritten."""
        out = tmp_path / "wrapper.py"
        out.write_text("old content")
        wg.generate_wrapper("plugin", "cmd", "Super", output_path=out)
        assert out.read_text() != "old content"

    @pytest.mark.unit
    def test_prints_confirmation_message(self, wg, tmp_path, capsys) -> None:
        """Given output_path, a confirmation line is printed to stdout."""
        out = tmp_path / "wrapper.py"
        wg.generate_wrapper("plugin", "cmd", "Super", output_path=out)
        captured = capsys.readouterr()
        assert str(out) in captured.out


# ---------------------------------------------------------------------------
# auto_detect_wrappers - missing plugins dir
# ---------------------------------------------------------------------------


class TestAutoDetectWrappersMissingPluginsDir:
    """auto_detect_wrappers handles missing plugins directory gracefully."""

    @pytest.mark.unit
    def test_returns_empty_list_when_plugins_dir_missing(self, wg, tmp_path) -> None:
        """Given repo_root with no plugins/ dir, returns empty list."""
        result = wg.auto_detect_wrappers(tmp_path)
        assert result == []

    @pytest.mark.unit
    def test_prints_error_when_plugins_dir_missing(self, wg, tmp_path, capsys) -> None:
        """Given missing plugins/ dir, error message is printed to stderr."""
        wg.auto_detect_wrappers(tmp_path)
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower() or "plugins" in captured.err


# ---------------------------------------------------------------------------
# auto_detect_wrappers - plugins without commands
# ---------------------------------------------------------------------------


class TestAutoDetectWrappersNoCommands:
    """auto_detect_wrappers skips plugins that have no commands/ directory."""

    @pytest.mark.unit
    def test_returns_empty_when_no_commands_dirs(self, wg, tmp_path) -> None:
        """Given plugins with no commands/ subdirectory, returns empty list."""
        plugins_dir = tmp_path / "plugins"
        (plugins_dir / "myplugin").mkdir(parents=True)
        result = wg.auto_detect_wrappers(tmp_path)
        assert result == []

    @pytest.mark.unit
    def test_skips_hidden_directories(self, wg, tmp_path) -> None:
        """Given a .hidden plugin directory, it is skipped."""
        plugins_dir = tmp_path / "plugins"
        hidden = plugins_dir / ".hidden-plugin"
        hidden.mkdir(parents=True)
        (hidden / "commands").mkdir()
        result = wg.auto_detect_wrappers(tmp_path)
        assert result == []

    @pytest.mark.unit
    def test_returns_empty_when_commands_dir_has_no_md_files(
        self, wg, tmp_path
    ) -> None:
        """Given commands/ dir with no .md files, returns empty list."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "readme.txt").write_text("not a markdown file")
        result = wg.auto_detect_wrappers(tmp_path)
        assert result == []


# ---------------------------------------------------------------------------
# auto_detect_wrappers - commands with superpower references
# ---------------------------------------------------------------------------


class TestAutoDetectWrappersSuperpowerRef:
    """auto_detect_wrappers detects commands that reference superpowers."""

    @pytest.mark.unit
    def test_detects_superpower_keyword(self, wg, tmp_path) -> None:
        """Given a command file containing 'superpower:', it is detected."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "do-work.md").write_text("superpower: BaseSuperpower\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == 1
        assert result[0][0] == "myplugin"
        assert result[0][1] == "do-work"

    @pytest.mark.unit
    def test_detects_delegates_to_keyword(self, wg, tmp_path) -> None:
        """Given a command file containing 'delegates to', it is detected."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "run-task.md").write_text("This command delegates to a superpower.\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == 1

    @pytest.mark.unit
    def test_command_without_reference_is_skipped(self, wg, tmp_path) -> None:
        """Given a command file with no superpower reference, it is skipped."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "standalone.md").write_text("This command does its own thing.\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert result == []

    @pytest.mark.unit
    def test_returns_base_superpower_placeholder(self, wg, tmp_path) -> None:
        """Given detected command, third tuple element is 'BaseSuperpower'."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "do-it.md").write_text("superpower: something\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert result[0][2] == "BaseSuperpower"

    @pytest.mark.unit
    def test_multiple_commands_multiple_results(self, wg, tmp_path) -> None:
        """Given two commands with references, two tuples are returned."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "cmd-a.md").write_text("superpower: X\n")
        (cmds / "cmd-b.md").write_text("delegates to a superpower\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == 2

    @pytest.mark.unit
    def test_multiple_plugins_multiple_results(self, wg, tmp_path) -> None:
        """Given two plugins each with one matching command, two tuples returned."""
        plugins_dir = tmp_path / "plugins"
        for plugin in ("alpha", "beta"):
            cmds = plugins_dir / plugin / "commands"
            cmds.mkdir(parents=True)
            (cmds / "work.md").write_text("superpower: Thing\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == 2
        plugin_names = {r[0] for r in result}
        assert plugin_names == {"alpha", "beta"}

    @pytest.mark.unit
    def test_superpower_keyword_case_insensitive(self, wg, tmp_path) -> None:
        """Given 'SUPERPOWER:' in uppercase, it is still detected."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "cmd.md").write_text("SUPERPOWER: SomePower\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# CLI main() - --auto-detect mode
# ---------------------------------------------------------------------------


class TestMainAutoDetect:
    """main() --auto-detect scans the repo and generates wrappers."""

    @pytest.mark.unit
    def test_auto_detect_no_wrappers_found_prints_message(
        self, wg, tmp_path, capsys
    ) -> None:
        """Given --auto-detect and no wrappers found, prints informational msg."""
        with patch.object(wg, "auto_detect_wrappers", return_value=[]):
            with patch(
                "sys.argv",
                ["wrapper_generator.py", "--auto-detect", "--repo-root", str(tmp_path)],
            ):
                wg.main()

        captured = capsys.readouterr()
        assert "No wrappers detected" in captured.out

    @pytest.mark.unit
    def test_auto_detect_with_wrappers_calls_generate(
        self, wg, tmp_path, capsys
    ) -> None:
        """Given --auto-detect with detected wrappers, generate_wrapper is called."""
        detected = [("myplugin", "do-work", "BaseSuperpower")]

        calls = []

        def fake_generate(plugin, cmd, sp, output_path=None):
            calls.append((plugin, cmd, sp, output_path))
            return "# generated code"

        with patch.object(wg, "auto_detect_wrappers", return_value=detected):
            with patch.object(wg, "generate_wrapper", side_effect=fake_generate):
                with patch(
                    "sys.argv",
                    [
                        "wrapper_generator.py",
                        "--auto-detect",
                        "--repo-root",
                        str(tmp_path),
                    ],
                ):
                    wg.main()

        assert len(calls) == 1
        assert calls[0][0] == "myplugin"
        assert calls[0][1] == "do-work"

    @pytest.mark.unit
    def test_auto_detect_output_path_uses_repo_root(self, wg, tmp_path, capsys) -> None:
        """Given --auto-detect, output files are written under repo_root/plugins."""
        detected = [("alpha", "my-cmd", "BaseSuperpower")]

        captured_paths = []

        def fake_generate(plugin, cmd, sp, output_path=None):
            captured_paths.append(output_path)
            return "# code"

        with patch.object(wg, "auto_detect_wrappers", return_value=detected):
            with patch.object(wg, "generate_wrapper", side_effect=fake_generate):
                with patch(
                    "sys.argv",
                    [
                        "wrapper_generator.py",
                        "--auto-detect",
                        "--repo-root",
                        str(tmp_path),
                    ],
                ):
                    wg.main()

        assert len(captured_paths) == 1
        assert "alpha" in str(captured_paths[0])
        assert "my_cmd_wrapper.py" in str(captured_paths[0])

    @pytest.mark.unit
    def test_auto_detect_prints_scanning_message(self, wg, tmp_path, capsys) -> None:
        """Given --auto-detect, a 'Scanning' message is printed."""
        with patch.object(wg, "auto_detect_wrappers", return_value=[]):
            with patch(
                "sys.argv",
                ["wrapper_generator.py", "--auto-detect", "--repo-root", str(tmp_path)],
            ):
                wg.main()

        captured = capsys.readouterr()
        assert "Scanning" in captured.out or "scanning" in captured.out.lower()


# ---------------------------------------------------------------------------
# CLI main() - manual mode
# ---------------------------------------------------------------------------


class TestMainManualMode:
    """main() manual mode generates a wrapper from explicit --plugin/--command/--superpower."""

    @pytest.mark.unit
    def test_manual_mode_calls_generate_wrapper(self, wg, capsys) -> None:
        """Given --plugin/--command/--superpower, generate_wrapper is called."""
        calls = []

        def fake_generate(plugin, cmd, sp, output_path=None):
            calls.append((plugin, cmd, sp, output_path))
            return "# code"

        with patch.object(wg, "generate_wrapper", side_effect=fake_generate):
            with patch(
                "sys.argv",
                [
                    "wrapper_generator.py",
                    "--plugin",
                    "sanctum",
                    "--command",
                    "pr-review",
                    "--superpower",
                    "CodeReviewer",
                ],
            ):
                wg.main()

        assert len(calls) == 1
        assert calls[0] == ("sanctum", "pr-review", "CodeReviewer", None)

    @pytest.mark.unit
    def test_manual_mode_prints_code_to_stdout(self, wg, capsys) -> None:
        """Given no --output flag, generated code is printed to stdout."""
        with patch.object(wg, "generate_wrapper", return_value="# generated"):
            with patch(
                "sys.argv",
                [
                    "wrapper_generator.py",
                    "--plugin",
                    "sanctum",
                    "--command",
                    "cmd",
                    "--superpower",
                    "Super",
                ],
            ):
                wg.main()

        captured = capsys.readouterr()
        assert "# generated" in captured.out

    @pytest.mark.unit
    def test_manual_mode_with_output_flag_writes_file(self, wg, tmp_path) -> None:
        """Given --output, generate_wrapper receives the output path."""
        out_file = tmp_path / "wrapper.py"
        calls = []

        def fake_generate(plugin, cmd, sp, output_path=None):
            calls.append(output_path)
            return "# code"

        with patch.object(wg, "generate_wrapper", side_effect=fake_generate):
            with patch(
                "sys.argv",
                [
                    "wrapper_generator.py",
                    "--plugin",
                    "sanctum",
                    "--command",
                    "cmd",
                    "--superpower",
                    "Super",
                    "--output",
                    str(out_file),
                ],
            ):
                wg.main()

        assert len(calls) == 1
        assert calls[0] == out_file

    @pytest.mark.unit
    def test_manual_mode_with_output_flag_suppresses_stdout(
        self, wg, tmp_path, capsys
    ) -> None:
        """Given --output, generated code is NOT printed to stdout."""
        out_file = tmp_path / "wrapper.py"

        with patch.object(wg, "generate_wrapper", return_value="# code"):
            with patch(
                "sys.argv",
                [
                    "wrapper_generator.py",
                    "--plugin",
                    "sanctum",
                    "--command",
                    "cmd",
                    "--superpower",
                    "Super",
                    "--output",
                    str(out_file),
                ],
            ):
                wg.main()

        captured = capsys.readouterr()
        assert "# code" not in captured.out


# ---------------------------------------------------------------------------
# CLI main() - error handling
# ---------------------------------------------------------------------------


class TestMainErrorHandling:
    """main() raises SystemExit when required arguments are missing."""

    @pytest.mark.unit
    def test_no_args_raises_system_exit(self, wg) -> None:
        """Given no arguments, main() calls parser.error() -> SystemExit."""
        with patch("sys.argv", ["wrapper_generator.py"]):
            with pytest.raises(SystemExit) as exc_info:
                wg.main()
        assert exc_info.value.code != 0

    @pytest.mark.unit
    def test_missing_command_raises_system_exit(self, wg) -> None:
        """Given --plugin without --command or --superpower, SystemExit raised."""
        with patch(
            "sys.argv",
            [
                "wrapper_generator.py",
                "--plugin",
                "sanctum",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                wg.main()
        assert exc_info.value.code != 0

    @pytest.mark.unit
    def test_missing_superpower_raises_system_exit(self, wg) -> None:
        """Given --plugin and --command but no --superpower, SystemExit raised."""
        with patch(
            "sys.argv",
            [
                "wrapper_generator.py",
                "--plugin",
                "sanctum",
                "--command",
                "cmd",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                wg.main()
        assert exc_info.value.code != 0

    @pytest.mark.unit
    def test_missing_plugin_raises_system_exit(self, wg) -> None:
        """Given --command and --superpower but no --plugin, SystemExit raised."""
        with patch(
            "sys.argv",
            [
                "wrapper_generator.py",
                "--command",
                "cmd",
                "--superpower",
                "Super",
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                wg.main()
        assert exc_info.value.code != 0
