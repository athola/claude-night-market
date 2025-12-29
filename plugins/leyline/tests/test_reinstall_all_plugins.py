"""Tests for reinstall_all_plugins.py script.

Tests the plugin reinstall functionality that uninstalls and reinstalls
all Claude plugins to clear cache corruption or version mismatches.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import the script module
script_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_path))

# ruff: noqa: E402
import reinstall_all_plugins

PluginEntry = dict[str, Any]
PluginList = list[PluginEntry]


class CaptureResult(Protocol):
    """Captured output payload."""

    out: str


class CaptureFixture(Protocol):
    """Protocol for pytest capsys fixture."""

    def readouterr(self) -> CaptureResult:
        """Return captured stdout/stderr."""
        ...


EXPECTED_REINSTALLABLE_COUNT = 2
EXPECTED_SUBPROCESS_CALLS = 2


@pytest.mark.unit
class TestExcludedPlugins:
    """Test the EXCLUDED_PLUGINS constant."""

    def test_hookify_is_excluded(self) -> None:
        """Hookify should be in EXCLUDED_PLUGINS to prevent breaking process."""
        assert "hookify" in reinstall_all_plugins.EXCLUDED_PLUGINS

    def test_excluded_plugins_is_set(self) -> None:
        """EXCLUDED_PLUGINS should be a set for O(1) lookup."""
        assert isinstance(reinstall_all_plugins.EXCLUDED_PLUGINS, set)


@pytest.mark.unit
class TestReadInstalledPlugins:
    """Feature: Configuration file reading for reinstall.

    As a plugin manager
    I want to read plugin configurations
    So that I can determine which plugins need reinstalling.
    """

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_read_valid_config_v2(
        self, mock_exists: MagicMock, mock_file: MagicMock
    ) -> None:
        """Scenario: Reading a valid v2 configuration file.

        Given a v2 configuration file exists with valid plugin data
        When the read_installed_plugins function is called
        Then it should return the parsed plugin dictionary.
        """
        # First call for v2 file - exists
        mock_exists.return_value = True

        expected_data: dict[str, Any] = {
            "plugins": {"test@marketplace": [{"version": "1.0.0", "scope": "user"}]}
        }
        mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            expected_data
        )

        with patch.object(Path, "open", mock_file):
            result = reinstall_all_plugins.read_installed_plugins()

        assert result == {"test@marketplace": [{"version": "1.0.0", "scope": "user"}]}

    @patch("pathlib.Path.exists", return_value=False)
    def test_missing_config_file_exits(self, mock_exists: MagicMock) -> None:
        """Scenario: Handling a missing configuration file.

        Given no configuration file exists (neither v1 nor v2)
        When the read_installed_plugins function is called
        Then it should exit with code 1.
        """
        with pytest.raises(SystemExit) as excinfo:
            reinstall_all_plugins.read_installed_plugins()

        assert excinfo.value.code == 1

    @patch("pathlib.Path.open", new_callable=mock_open, read_data="not json")
    @patch("pathlib.Path.exists", return_value=True)
    def test_invalid_json_exits(
        self, mock_exists: MagicMock, mock_file: MagicMock
    ) -> None:
        """Scenario: Handling invalid JSON in configuration file.

        Given the configuration file contains invalid JSON
        When the read_installed_plugins function is called
        Then it should exit with code 1.
        """
        with pytest.raises(SystemExit) as excinfo:
            reinstall_all_plugins.read_installed_plugins()

        assert excinfo.value.code == 1


@pytest.mark.unit
class TestCategorizePlugins:
    """Feature: Plugin categorization.

    As a plugin manager
    I want to categorize plugins as reinstallable or excluded
    So that I don't break essential plugins during reinstall.
    """

    def test_categorize_normal_plugin(self) -> None:
        """Scenario: Categorizing a normal plugin.

        Given a plugin that is not in EXCLUDED_PLUGINS
        When categorize_plugins is called
        Then it should be in the reinstallable list.
        """
        plugins = {"test-plugin@marketplace": [{"version": "1.0.0", "scope": "user"}]}

        reinstallable, excluded = reinstall_all_plugins.categorize_plugins(plugins)

        assert len(reinstallable) == 1
        assert len(excluded) == 0
        assert reinstallable[0]["name"] == "test-plugin"
        assert reinstallable[0]["marketplace"] == "marketplace"

    def test_categorize_excluded_plugin(self) -> None:
        """Scenario: Categorizing an excluded plugin.

        Given a plugin that is in EXCLUDED_PLUGINS (hookify)
        When categorize_plugins is called
        Then it should be in the excluded list.
        """
        plugins = {"hookify@marketplace": [{"version": "1.0.0", "scope": "user"}]}

        reinstallable, excluded = reinstall_all_plugins.categorize_plugins(plugins)

        assert len(reinstallable) == 0
        assert len(excluded) == 1
        assert excluded[0]["name"] == "hookify"

    def test_categorize_mixed_plugins(self) -> None:
        """Scenario: Categorizing a mix of plugins.

        Given multiple plugins with some excluded
        When categorize_plugins is called
        Then they should be correctly separated.
        """
        plugins = {
            "normal-plugin@marketplace": [{"version": "1.0.0"}],
            "hookify@marketplace": [{"version": "2.0.0"}],
            "another-plugin@different-market": [{"version": "3.0.0"}],
        }

        reinstallable, excluded = reinstall_all_plugins.categorize_plugins(plugins)

        assert len(reinstallable) == EXPECTED_REINSTALLABLE_COUNT
        assert len(excluded) == 1
        reinstallable_names = [p["name"] for p in reinstallable]
        assert "normal-plugin" in reinstallable_names
        assert "another-plugin" in reinstallable_names

    def test_categorize_extracts_marketplace(self) -> None:
        """Scenario: Extracting marketplace from plugin name.

        Given a plugin with @marketplace suffix
        When categorize_plugins is called
        Then the marketplace should be extracted correctly.
        """
        plugins = {"test@claude-night-market": [{"version": "1.0.0"}]}

        reinstallable, _ = reinstall_all_plugins.categorize_plugins(plugins)

        assert reinstallable[0]["marketplace"] == "claude-night-market"

    def test_categorize_handles_no_marketplace(self) -> None:
        """Scenario: Handling plugin name without marketplace.

        Given a plugin name without @ separator
        When categorize_plugins is called
        Then marketplace should be 'unknown'.
        """
        plugins = {"orphan-plugin": [{"version": "1.0.0"}]}

        reinstallable, _ = reinstall_all_plugins.categorize_plugins(plugins)

        assert reinstallable[0]["marketplace"] == "unknown"

    def test_categorize_preserves_local_flag(self) -> None:
        """Scenario: Preserving the isLocal flag.

        Given a plugin with isLocal set to True
        When categorize_plugins is called
        Then is_local should be preserved.
        """
        plugins = {"local-plugin@market": [{"version": "1.0.0", "isLocal": True}]}

        reinstallable, _ = reinstall_all_plugins.categorize_plugins(plugins)

        assert reinstallable[0]["is_local"] is True

    def test_categorize_case_insensitive_exclusion(self) -> None:
        """Scenario: Case-insensitive exclusion check.

        Given a plugin with uppercase name matching excluded
        When categorize_plugins is called
        Then it should be excluded.
        """
        plugins = {"Hookify@market": [{"version": "1.0.0"}]}

        reinstallable, excluded = reinstall_all_plugins.categorize_plugins(plugins)

        assert len(reinstallable) == 0
        assert len(excluded) == 1


@pytest.mark.unit
class TestPrintPluginTable:
    """Test the print_plugin_table function."""

    def test_empty_plugins_prints_nothing(self, capsys: CaptureFixture) -> None:
        """Should print nothing for empty plugin list."""
        reinstall_all_plugins.print_plugin_table([], "Title")

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_prints_formatted_table(self, capsys: CaptureFixture) -> None:
        """Should print a formatted table with plugin info."""
        plugins = [
            {
                "name": "test-plugin",
                "marketplace": "marketplace",
                "is_local": False,
            }
        ]

        reinstall_all_plugins.print_plugin_table(plugins, "Test Title")

        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "test-plugin" in captured.out
        assert "marketplace" in captured.out
        assert "no" in captured.out  # is_local = False


@pytest.mark.unit
class TestGenerateCommands:
    """Test command generation for manual execution."""

    def test_generate_commands_output(self, capsys: CaptureFixture) -> None:
        """Should generate uninstall and install commands."""
        reinstallable = [
            {
                "full_name": "test@market",
                "name": "test",
                "marketplace": "market",
                "is_local": False,
            }
        ]
        excluded: PluginList = []

        reinstall_all_plugins.generate_commands(reinstallable, excluded)

        captured = capsys.readouterr()
        assert "/plugin uninstall test@market" in captured.out
        assert "/plugin install test@market" in captured.out
        assert "UNINSTALL PHASE" in captured.out
        assert "INSTALL PHASE" in captured.out

    def test_generate_commands_shows_excluded(self, capsys: CaptureFixture) -> None:
        """Should show excluded plugins in output."""
        reinstallable: PluginList = []
        excluded: PluginList = [
            {
                "full_name": "hookify@market",
                "name": "hookify",
                "marketplace": "market",
                "is_local": False,
            }
        ]

        reinstall_all_plugins.generate_commands(reinstallable, excluded)

        captured = capsys.readouterr()
        assert "Excluded" in captured.out
        assert "hookify@market" in captured.out


@pytest.mark.unit
class TestGenerateScript:
    """Test bash script generation."""

    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.chmod")
    def test_generate_script_creates_file(
        self,
        mock_chmod: MagicMock,
        mock_write: MagicMock,
        capsys: CaptureFixture,
    ) -> None:
        """Should create a bash script file."""
        reinstallable = [
            {"full_name": "test@market", "name": "test", "marketplace": "market"}
        ]
        excluded: PluginList = []

        reinstall_all_plugins.generate_script(reinstallable, excluded)

        mock_write.assert_called_once()
        script_content = mock_write.call_args[0][0]
        assert "#!/bin/bash" in script_content
        assert "test@market" in script_content
        assert "claude plugin uninstall" in script_content
        assert "claude plugin install" in script_content

    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.chmod")
    def test_generate_script_sets_executable(
        self, mock_chmod: MagicMock, mock_write: MagicMock
    ) -> None:
        """Should set the script as executable (0o755)."""
        reinstallable = [{"full_name": "test@market", "name": "test"}]
        excluded: PluginList = []

        reinstall_all_plugins.generate_script(reinstallable, excluded)

        mock_chmod.assert_called_once_with(0o755)


@pytest.mark.unit
class TestExecuteReinstall:
    """Test the actual reinstall execution."""

    @patch("subprocess.run")
    def test_execute_successful_reinstall(
        self, mock_run: MagicMock, capsys: CaptureFixture
    ) -> None:
        """Scenario: Successful plugin reinstall.

        Given all subprocess calls succeed
        When execute_reinstall is called
        Then all plugins should be reinstalled successfully.
        """
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        reinstallable = [
            {
                "full_name": "test@market",
                "name": "test",
                "marketplace": "market",
            }
        ]
        excluded: PluginList = []

        reinstall_all_plugins.execute_reinstall(reinstallable, excluded)

        # Should have called uninstall and install for each plugin
        assert mock_run.call_count == EXPECTED_SUBPROCESS_CALLS

        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "All plugins reinstalled successfully" in captured.out

    @patch("subprocess.run")
    def test_execute_handles_uninstall_failure(
        self,
        mock_run: MagicMock,
        capsys: CaptureFixture,
    ) -> None:
        """Scenario: Handling uninstall failures gracefully.

        Given an uninstall command fails
        When execute_reinstall is called
        Then it should continue with install phase.
        """
        # First call (uninstall) fails, second (install) succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr=""),
            MagicMock(returncode=0, stderr=""),
        ]

        reinstallable = [{"full_name": "test@market", "name": "test"}]
        excluded: PluginList = []

        reinstall_all_plugins.execute_reinstall(reinstallable, excluded)

        captured = capsys.readouterr()
        assert "[WARN]" in captured.out  # Uninstall warning
        assert "[OK]" in captured.out  # Install success

    @patch("subprocess.run")
    def test_execute_reports_install_failure(
        self, mock_run: MagicMock, capsys: CaptureFixture
    ) -> None:
        """Scenario: Reporting install failures.

        Given an install command fails
        When execute_reinstall is called
        Then it should report the failure and exit with code 1.
        """
        # First call (uninstall) succeeds, second (install) fails
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1, stderr="Install error"),
        ]

        reinstallable = [{"full_name": "test@market", "name": "test"}]
        excluded: PluginList = []

        with pytest.raises(SystemExit) as excinfo:
            reinstall_all_plugins.execute_reinstall(reinstallable, excluded)

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "[FAILED]" in captured.out

    @patch("subprocess.run")
    def test_execute_handles_timeout(
        self,
        mock_run: MagicMock,
        capsys: CaptureFixture,
    ) -> None:
        """Scenario: Handling subprocess timeout.

        Given a subprocess times out
        When execute_reinstall is called
        Then it should handle the timeout gracefully.
        """
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30)

        reinstallable = [{"full_name": "test@market", "name": "test"}]
        excluded: PluginList = []

        with pytest.raises(SystemExit):
            reinstall_all_plugins.execute_reinstall(reinstallable, excluded)

        captured = capsys.readouterr()
        assert "[TIMEOUT]" in captured.out

    @patch("subprocess.run")
    def test_execute_shows_summary(
        self, mock_run: MagicMock, capsys: CaptureFixture
    ) -> None:
        """Scenario: Showing reinstall summary.

        Given the reinstall process completes
        When execute_reinstall is called
        Then it should show a summary of results.
        """
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        reinstallable = [
            {"full_name": "p1@market", "name": "p1"},
            {"full_name": "p2@market", "name": "p2"},
        ]
        excluded: PluginList = [{"full_name": "hookify@market", "name": "hookify"}]

        reinstall_all_plugins.execute_reinstall(reinstallable, excluded)

        captured = capsys.readouterr()
        assert "REINSTALL SUMMARY" in captured.out
        assert "Total plugins: 2" in captured.out
        assert "Excluded: 1" in captured.out


@pytest.mark.unit
class TestMain:
    """Test the main entry point."""

    @patch.object(reinstall_all_plugins, "read_installed_plugins")
    @patch.object(reinstall_all_plugins, "categorize_plugins")
    @patch.object(reinstall_all_plugins, "generate_commands")
    def test_main_list_only_mode(
        self,
        mock_generate: MagicMock,
        mock_categorize: MagicMock,
        mock_read: MagicMock,
    ) -> None:
        """Should generate commands in list-only mode."""
        mock_read.return_value = {"test@market": [{"version": "1.0.0"}]}
        mock_categorize.return_value = (
            [{"full_name": "test@market", "name": "test"}],
            [],
        )

        with patch("sys.argv", ["script", "--list-only"]):
            reinstall_all_plugins.main()

        mock_generate.assert_called_once()

    @patch.object(reinstall_all_plugins, "read_installed_plugins")
    @patch.object(reinstall_all_plugins, "categorize_plugins")
    @patch.object(reinstall_all_plugins, "generate_script")
    def test_main_generate_script_mode(
        self,
        mock_script: MagicMock,
        mock_categorize: MagicMock,
        mock_read: MagicMock,
    ) -> None:
        """Should generate script in generate-script mode."""
        mock_read.return_value = {"test@market": [{"version": "1.0.0"}]}
        mock_categorize.return_value = (
            [{"full_name": "test@market", "name": "test"}],
            [],
        )

        with patch("sys.argv", ["script", "--generate-script"]):
            reinstall_all_plugins.main()

        mock_script.assert_called_once()

    @patch.object(reinstall_all_plugins, "read_installed_plugins")
    @patch.object(reinstall_all_plugins, "categorize_plugins")
    @patch.object(reinstall_all_plugins, "print_plugin_table")
    def test_main_dry_run_mode(
        self,
        mock_print: MagicMock,
        mock_categorize: MagicMock,
        mock_read: MagicMock,
        capsys: CaptureFixture,
    ) -> None:
        """Should show dry run info without executing."""
        mock_read.return_value = {"test@market": [{"version": "1.0.0"}]}
        mock_categorize.return_value = (
            [{"full_name": "test@market", "name": "test"}],
            [],
        )

        with patch("sys.argv", ["script", "--dry-run"]):
            reinstall_all_plugins.main()

        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out

    @patch.object(reinstall_all_plugins, "read_installed_plugins")
    @patch.object(reinstall_all_plugins, "categorize_plugins")
    def test_main_no_reinstallable_plugins(
        self,
        mock_categorize: MagicMock,
        mock_read: MagicMock,
        capsys: CaptureFixture,
    ) -> None:
        """Should handle case when all plugins are excluded."""
        mock_read.return_value = {"hookify@market": [{"version": "1.0.0"}]}
        mock_categorize.return_value = (
            [],
            [{"full_name": "hookify@market", "name": "hookify"}],
        )

        with patch("sys.argv", ["script"]):
            reinstall_all_plugins.main()

        captured = capsys.readouterr()
        assert "No plugins to reinstall" in captured.out

    @patch.object(reinstall_all_plugins, "read_installed_plugins")
    def test_main_no_plugins_exits(self, mock_read: MagicMock) -> None:
        """Should exit when no plugins found."""
        mock_read.return_value = {}

        with patch("sys.argv", ["script"]):
            with pytest.raises(SystemExit) as excinfo:
                reinstall_all_plugins.main()

        assert excinfo.value.code == 1
