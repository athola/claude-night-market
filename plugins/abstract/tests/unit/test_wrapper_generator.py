"""Tests for wrapper_generator.py.

Covers generate_wrapper(), auto_detect_wrappers(), and CLI main().
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

# Add scripts directory to path so the module can be imported directly.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import wrapper_generator  # noqa: E402

# ---------------------------------------------------------------------------
# Module import fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def wg():
    """Reload wrapper_generator with a clean module state.

    Reloading ensures monkeypatches on module-level state don't bleed
    between tests.
    """
    return importlib.reload(wrapper_generator)


# ---------------------------------------------------------------------------
# generate_wrapper - return value (parametrized)
# ---------------------------------------------------------------------------


class TestGenerateWrapperReturnValue:
    """generate_wrapper returns syntactically correct Python source."""

    @pytest.mark.unit
    def test_returns_string(self, wg) -> None:
        """Given valid arguments, generate_wrapper returns a string."""
        result = wg.generate_wrapper("sanctum", "pr-review", "CodeReviewer")
        assert isinstance(result, str)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("plugin", "command", "superpower", "expected_class"),
        [
            ("myplugin", "review", "Reviewer", "ReviewWrapper"),
            ("sanctum", "pr-review", "CodeReviewer", "PrReviewWrapper"),
            ("plugin", "do-some-thing", "Doer", "DoSomeThingWrapper"),
        ],
        ids=["single-word", "hyphenated", "three-segment"],
    )
    def test_class_name_derived_from_command(
        self, wg, plugin, command, superpower, expected_class
    ) -> None:
        """Given a command name, generated class name follows PascalCase."""
        result = wg.generate_wrapper(plugin, command, superpower)
        assert expected_class in result

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("plugin", "command", "superpower", "expected_substring"),
        [
            ("myplugin", "cmd", "Super", "myplugin"),
            ("plugin", "my-cmd", "Super", "my-cmd"),
            ("plugin", "cmd", "CodeReviewer", "CodeReviewer"),
            ("plugin", "cmd", "MySuper", "from abstract.superpowers."),
            (
                "plugin",
                "cmd",
                "CodeReviewer",
                "from abstract.superpowers.codereviewer import CodeReviewer",
            ),
            ("plugin", "cmd", "Super", "def execute("),
            ("plugin", "cmd", "Super", "def _map_parameters("),
        ],
        ids=[
            "contains-plugin-name",
            "contains-command-name",
            "contains-superpower-name",
            "contains-import-statement",
            "import-uses-lowercase",
            "contains-execute-method",
            "contains-map-parameters",
        ],
    )
    def test_output_contains_expected_content(
        self, wg, plugin, command, superpower, expected_substring
    ) -> None:
        """Given arguments, generated code contains expected substring."""
        result = wg.generate_wrapper(plugin, command, superpower)
        assert expected_substring in result

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
    @pytest.mark.parametrize(
        ("file_content", "expected_count"),
        [
            ("superpower: BaseSuperpower\n", 1),
            ("This command delegates to a superpower.\n", 1),
            ("This command does its own thing.\n", 0),
            ("SUPERPOWER: SomePower\n", 1),
        ],
        ids=[
            "superpower-keyword",
            "delegates-to-keyword",
            "no-reference-skipped",
            "case-insensitive",
        ],
    )
    def test_detects_superpower_references(
        self, wg, tmp_path, file_content, expected_count
    ) -> None:
        """Given command file content, correct number of results returned."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "do-work.md").write_text(file_content)
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == expected_count

    @pytest.mark.unit
    def test_returns_correct_tuple_structure(self, wg, tmp_path) -> None:
        """Given detected command, tuple has (plugin, command, superpower)."""
        plugins_dir = tmp_path / "plugins"
        cmds = plugins_dir / "myplugin" / "commands"
        cmds.mkdir(parents=True)
        (cmds / "do-it.md").write_text("superpower: something\n")
        result = wg.auto_detect_wrappers(tmp_path)
        assert len(result) == 1
        assert result[0][0] == "myplugin"
        assert result[0][1] == "do-it"
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


# ---------------------------------------------------------------------------
# CLI main() - --auto-detect mode (with mock verification)
# ---------------------------------------------------------------------------


class TestMainAutoDetect:
    """main() --auto-detect scans the repo and generates wrappers."""

    @pytest.mark.unit
    def test_auto_detect_no_wrappers_found_prints_message(
        self, wg, tmp_path, capsys
    ) -> None:
        """Given --auto-detect and no wrappers found, prints informational msg."""
        mock_detect = Mock(return_value=[])
        with patch.object(wg, "auto_detect_wrappers", mock_detect):
            with patch(
                "sys.argv",
                ["wrapper_generator.py", "--auto-detect", "--repo-root", str(tmp_path)],
            ):
                wg.main()

        mock_detect.assert_called_once()
        captured = capsys.readouterr()
        assert "No wrappers detected" in captured.out

    @pytest.mark.unit
    def test_auto_detect_with_wrappers_calls_generate(
        self, wg, tmp_path, capsys
    ) -> None:
        """Given --auto-detect with detected wrappers, generate_wrapper is called."""
        detected = [("myplugin", "do-work", "BaseSuperpower")]

        mock_detect = Mock(return_value=detected)
        mock_generate = Mock(return_value="# generated code")

        with patch.object(wg, "auto_detect_wrappers", mock_detect):
            with patch.object(wg, "generate_wrapper", mock_generate):
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

        mock_detect.assert_called_once()
        mock_generate.assert_called_once()
        gen_args = mock_generate.call_args
        assert gen_args[0][0] == "myplugin"
        assert gen_args[0][1] == "do-work"
        assert gen_args[0][2] == "BaseSuperpower"

    @pytest.mark.unit
    def test_auto_detect_output_path_uses_repo_root(self, wg, tmp_path, capsys) -> None:
        """Given --auto-detect, output files are written under repo_root/plugins."""
        detected = [("alpha", "my-cmd", "BaseSuperpower")]

        mock_detect = Mock(return_value=detected)
        mock_generate = Mock(return_value="# code")

        with patch.object(wg, "auto_detect_wrappers", mock_detect):
            with patch.object(wg, "generate_wrapper", mock_generate):
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

        mock_generate.assert_called_once()
        output_path = mock_generate.call_args[0][3]
        assert "alpha" in str(output_path)
        assert "my_cmd_wrapper.py" in str(output_path)

    @pytest.mark.unit
    def test_auto_detect_prints_scanning_message(self, wg, tmp_path, capsys) -> None:
        """Given --auto-detect, a 'Scanning' message is printed."""
        mock_detect = Mock(return_value=[])
        with patch.object(wg, "auto_detect_wrappers", mock_detect):
            with patch(
                "sys.argv",
                ["wrapper_generator.py", "--auto-detect", "--repo-root", str(tmp_path)],
            ):
                wg.main()

        mock_detect.assert_called_once()
        captured = capsys.readouterr()
        assert "Scanning" in captured.out or "scanning" in captured.out.lower()


# ---------------------------------------------------------------------------
# CLI main() - manual mode (with mock verification)
# ---------------------------------------------------------------------------


class TestMainManualMode:
    """main() manual mode generates a wrapper from explicit --plugin/--command/--superpower."""

    @pytest.mark.unit
    def test_manual_mode_calls_generate_wrapper(self, wg, capsys) -> None:
        """Given --plugin/--command/--superpower, generate_wrapper is called."""
        mock_generate = Mock(return_value="# code")

        with patch.object(wg, "generate_wrapper", mock_generate):
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

        mock_generate.assert_called_once_with(
            "sanctum", "pr-review", "CodeReviewer", None, dry_run=False
        )

    @pytest.mark.unit
    def test_manual_mode_prints_code_to_stdout(self, wg, capsys) -> None:
        """Given no --output flag, generated code is printed to stdout."""
        mock_generate = Mock(return_value="# generated")
        with patch.object(wg, "generate_wrapper", mock_generate):
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

        mock_generate.assert_called_once()
        captured = capsys.readouterr()
        assert "# generated" in captured.out

    @pytest.mark.unit
    def test_manual_mode_with_output_flag_writes_file(self, wg, tmp_path) -> None:
        """Given --output, generate_wrapper receives the output path."""
        out_file = tmp_path / "wrapper.py"
        mock_generate = Mock(return_value="# code")

        with patch.object(wg, "generate_wrapper", mock_generate):
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

        mock_generate.assert_called_once()
        assert mock_generate.call_args[0][3] == out_file

    @pytest.mark.unit
    def test_manual_mode_with_output_flag_suppresses_stdout(
        self, wg, tmp_path, capsys
    ) -> None:
        """Given --output, generated code is NOT printed to stdout."""
        out_file = tmp_path / "wrapper.py"

        mock_generate = Mock(return_value="# code")
        with patch.object(wg, "generate_wrapper", mock_generate):
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

        mock_generate.assert_called_once()
        captured = capsys.readouterr()
        assert "# code" not in captured.out


# ---------------------------------------------------------------------------
# CLI main() - error handling (parametrized)
# ---------------------------------------------------------------------------


class TestMainErrorHandling:
    """main() raises SystemExit when required arguments are missing."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "argv",
        [
            ["wrapper_generator.py"],
            ["wrapper_generator.py", "--plugin", "sanctum"],
            ["wrapper_generator.py", "--plugin", "sanctum", "--command", "cmd"],
            [
                "wrapper_generator.py",
                "--command",
                "cmd",
                "--superpower",
                "Super",
            ],
        ],
        ids=[
            "no-args",
            "missing-command-and-superpower",
            "missing-superpower",
            "missing-plugin",
        ],
    )
    def test_missing_args_raises_system_exit(self, wg, argv) -> None:
        """Given incomplete arguments, main() raises SystemExit != 0."""
        with patch("sys.argv", argv):
            with pytest.raises(SystemExit) as exc_info:
                wg.main()
        assert exc_info.value.code != 0
