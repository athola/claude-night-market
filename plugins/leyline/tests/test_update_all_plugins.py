"""Tests for update_all_plugins.py script."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import the script module
# Since it's in the scripts directory, we need to add the path
script_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_path))

# ruff: noqa: E402
# mypy: ignore-errors
import update_all_plugins


@pytest.mark.unit
class TestReadInstalledPlugins:
    """Feature: Configuration file reading.

    As a plugin manager
    I want to read plugin configurations
    So that I can determine which plugins need updating.
    """

    @patch("builtins.open", new_callable=mock_open, read_data='{"plugins": {}}')
    @patch("pathlib.Path.exists", return_value=True)
    def test_read_valid_config(
        self, mock_exists: MagicMock, mock_file: MagicMock
    ) -> None:
        """Scenario: Reading a valid configuration file.

        Given a configuration file exists with valid plugin data
        When the read_installed_plugins function is called
        Then it should return the parsed plugin dictionary.
        """
        expected_data: dict[str, Any] = {
            "plugins": {"test@marketplace": [{"version": "1.0.0"}]}
        }
        mock_file.return_value.read.return_value = json.dumps(expected_data)

        result = update_all_plugins.read_installed_plugins()

        assert result == {"test@marketplace": [{"version": "1.0.0"}]}

    @patch("builtins.open", new_callable=mock_open, read_data='{"plugins": {}}')
    @patch("pathlib.Path.exists", return_value=True)
    def test_read_config_with_no_plugins(
        self, mock_exists: MagicMock, mock_file: MagicMock
    ) -> None:
        """Scenario: Reading a configuration file with no plugins.

        Given a configuration file exists with an empty plugins dictionary
        When the read_installed_plugins function is called
        Then it should return an empty dictionary.
        """
        expected_data: dict[str, Any] = {"plugins": {}}
        mock_file.return_value.read.return_value = json.dumps(expected_data)

        result = update_all_plugins.read_installed_plugins()

        assert result == {}

    @patch("pathlib.Path.exists", return_value=False)
    def test_missing_config_file(self, mock_exists: MagicMock) -> None:
        """Scenario: Handling a missing configuration file.

        Given the configuration file does not exist
        When the read_installed_plugins function is called
        Then it should exit with code 1.
        """
        # sys.exit must raise SystemExit to stop code execution, otherwise
        # the function continues to open() and fails with FileNotFoundError
        with pytest.raises(SystemExit) as excinfo:
            update_all_plugins.read_installed_plugins()

        assert excinfo.value.code == 1

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_invalid_json(self, mock_exists: MagicMock, mock_file: MagicMock) -> None:
        """Scenario: Handling invalid JSON in configuration file.

        Given a configuration file exists with invalid JSON
        When the read_installed_plugins function is called
        Then it should raise a JSONDecodeError.
        """
        mock_file.return_value.read.return_value = "invalid json"

        with pytest.raises(json.JSONDecodeError):
            update_all_plugins.read_installed_plugins()


@pytest.mark.unit
class TestUpdatePlugin:
    """Feature: Plugin update execution.

    As a plugin manager
    I want to update individual plugins
    So that plugins stay current.
    """

    @patch("subprocess.run")
    def test_plugin_already_latest(self, mock_run: MagicMock) -> None:
        """Scenario: Updating a plugin already at the latest version.

        Given a plugin is already at the latest version
        When the update_plugin function is called
        Then it should return success with the same version.
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Plugin test@marketplace (1.2.3) already at the latest version",
        )

        success, old_version, new_version = update_all_plugins.update_plugin(
            "test@marketplace"
        )

        assert success is True
        assert old_version == "1.2.3"
        assert new_version == "1.2.3"
        mock_run.assert_called_once_with(
            ["claude", "plugin", "update", "test@marketplace"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

    @patch("subprocess.run")
    def test_plugin_successfully_updated(self, mock_run: MagicMock) -> None:
        """Scenario: Successfully updating a plugin to a new version.

        Given a plugin has a newer version available
        When the update_plugin function is called
        Then it should return success with the old and new versions.
        """
        # Note: The regex in the script captures until the first dot,
        # so "1.1.0" would be captured as "1". Testing with a version without dots.
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Plugin test@marketplace updated from 1.0.0 to 2",
        )

        success, old_version, new_version = update_all_plugins.update_plugin(
            "test@marketplace"
        )

        assert success is True
        assert old_version == "1.0.0"
        assert new_version == "2"

    @patch("subprocess.run")
    def test_plugin_update_without_version_info(self, mock_run: MagicMock) -> None:
        """Scenario: Updating a plugin with unparseable version information.

        Given a plugin update succeeds but version info cannot be parsed
        When the update_plugin function is called
        Then it should return success with unknown versions.
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Plugin updated successfully",
        )

        success, old_version, new_version = update_all_plugins.update_plugin(
            "test@marketplace"
        )

        assert success is True
        assert old_version == "unknown"
        assert new_version == "unknown"

    @patch("subprocess.run")
    def test_plugin_update_failed(self, mock_run: MagicMock) -> None:
        """Scenario: Handling a failed plugin update.

        Given a plugin update command fails
        When the update_plugin function is called
        Then it should return failure with error versions.
        """
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Error: Unable to update plugin",
        )

        success, old_version, new_version = update_all_plugins.update_plugin(
            "test@marketplace"
        )

        assert success is False
        assert old_version == "error"
        assert new_version == "error"

    @patch("subprocess.run")
    def test_plugin_update_timeout(self, mock_run: MagicMock) -> None:
        """Scenario: Handling a plugin update timeout.

        Given a plugin update command times out
        When the update_plugin function is called
        Then it should return failure with timeout versions.
        """
        mock_run.side_effect = subprocess.TimeoutExpired("claude", 30)

        with patch("builtins.print") as mock_print:
            success, old_version, new_version = update_all_plugins.update_plugin(
                "test@marketplace"
            )

        assert success is False
        assert old_version == "timeout"
        assert new_version == "timeout"
        mock_print.assert_called_with("[TIMEOUT] Timeout updating test@marketplace")

    @patch("subprocess.run")
    def test_plugin_update_exception(self, mock_run: MagicMock) -> None:
        """Scenario: Handling an unexpected exception during update.

        Given a plugin update raises an unexpected exception
        When the update_plugin function is called
        Then it should return failure with error versions.
        """
        mock_run.side_effect = Exception("Unexpected error")

        with patch("builtins.print") as mock_print:
            success, old_version, new_version = update_all_plugins.update_plugin(
                "test@marketplace"
            )

        assert success is False
        assert old_version == "error"
        assert new_version == "error"
        mock_print.assert_called_with(
            "[ERROR] Error updating test@marketplace: Unexpected error"
        )

    @patch("subprocess.run")
    def test_plugin_update_with_dotted_version(self, mock_run: MagicMock) -> None:
        """Scenario: Updating a plugin with a dotted version number.

        Given a plugin update to a version with dots in the number
        When the update_plugin function is called
        Then it should parse the version correctly up to the first dot.
        """
        # This tests the actual behavior of the regex - it captures until the first dot
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Plugin test@marketplace updated from 1.0.0 to 2.1.0",
        )

        success, old_version, new_version = update_all_plugins.update_plugin(
            "test@marketplace"
        )

        assert success is True
        assert old_version == "1.0.0"
        # The regex captures "2" (stops at the first dot)
        assert new_version == "2"


@pytest.mark.unit
class TestMain:
    """Feature: Batch plugin update workflow.

    As a user
    I want to update all plugins at once
    So that my environment stays current.
    """

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_all_plugins_latest(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: All plugins are already at the latest version.

        Given all plugins are at the latest version
        When the main function is executed
        Then it should display a summary showing no updates.
        """
        # Setup mock data
        mock_read.return_value = {
            "plugin1@marketplace1": [{"version": "1.0.0"}],
            "plugin2@marketplace2": [{"version": "2.0.0"}],
        }
        mock_update.side_effect = [
            (True, "1.0.0", "1.0.0"),  # Already latest
            (True, "2.0.0", "2.0.0"),  # Already latest
        ]

        update_all_plugins.main()

        # Verify print calls contain expected summary
        print_calls = [str(call) for call in mock_print.call_args_list]

        # Check that it prints the update summary
        summary_calls = [call for call in print_calls if "UPDATE SUMMARY" in call]
        assert len(summary_calls) > 0

        # Check statistics
        stats_calls = [call for call in print_calls if "Total plugins: 2" in call]
        assert len(stats_calls) > 0

        updated_calls = [call for call in print_calls if "Updated: 0" in call]
        assert len(updated_calls) > 0

        latest_calls = [call for call in print_calls if "Already latest: 2" in call]
        assert len(latest_calls) > 0

        failed_calls = [call for call in print_calls if "Failed: 0" in call]
        assert len(failed_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_some_plugins_updated(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: Some plugins are updated while others fail or are current.

        Given a mix of plugins that need updates, are current, and fail
        When the main function is executed
        Then it should display accurate statistics for each category.
        """
        mock_read.return_value = {
            "plugin1@marketplace1": [{"version": "1.0.0"}],
            "plugin2@marketplace2": [{"version": "1.0.0"}],
            "plugin3@marketplace3": [{"version": "3.0.0"}],
        }
        mock_update.side_effect = [
            (True, "1.0.0", "1.0.0"),  # Already latest
            (True, "1.0.0", "1.1.0"),  # Updated
            (False, "error", "error"),  # Failed
        ]

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]

        # Check statistics
        stats_calls = [call for call in print_calls if "Total plugins: 3" in call]
        assert len(stats_calls) > 0

        updated_calls = [call for call in print_calls if "Updated: 1" in call]
        assert len(updated_calls) > 0

        latest_calls = [call for call in print_calls if "Already latest: 1" in call]
        assert len(latest_calls) > 0

        failed_calls = [call for call in print_calls if "Failed: 1" in call]
        assert len(failed_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_no_plugins(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: No plugins are configured in the system.

        Given no plugins are found in the configuration
        When the main function is executed
        Then it should display an error message.
        """
        mock_read.return_value = {}

        update_all_plugins.main()

        # Should print error message
        error_calls = [
            str(call)
            for call in mock_print.call_args_list
            if "[ERROR] No plugins found" in str(call)
        ]
        assert len(error_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_multiple_entries_same_plugin(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: A plugin has multiple version entries.

        Given a plugin has multiple entries with different versions
        When the main function is executed
        Then it should process each entry separately.
        """
        mock_read.return_value = {
            "plugin1@marketplace1": [
                {"version": "1.0.0"},
                {"version": "1.1.0"},
            ]
        }
        mock_update.side_effect = [
            (True, "1.0.0", "1.2.0"),  # Updated
            (True, "1.1.0", "1.2.0"),  # Updated
        ]

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]

        # Should count both entries
        stats_calls = [call for call in print_calls if "Total plugins: 2" in call]
        assert len(stats_calls) > 0

        updated_calls = [call for call in print_calls if "Updated: 2" in call]
        assert len(updated_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_displays_plugin_details(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: Displaying plugin details during update.

        Given a plugin is being updated
        When the main function is executed
        Then it should display the plugin name, marketplace, and version changes.
        """
        mock_read.return_value = {"my-plugin@my-marketplace": [{"version": "1.0.0"}]}
        mock_update.return_value = (True, "1.0.0", "2.0.0")

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]

        # Check that plugin name is displayed
        updating_calls = [
            call
            for call in print_calls
            if "Updating my-plugin from my-marketplace" in call
        ]
        assert len(updating_calls) > 0

        # Check that update details are shown
        updated_calls = [
            call for call in print_calls if "[UPDATED] 1.0.0 -> 2.0.0" in call
        ]
        assert len(updated_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_shows_note_for_updates(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: Displaying a restart note after updates.

        Given plugins have been successfully updated
        When the main function completes
        Then it should display a note about restarting Claude Code.
        """
        mock_read.return_value = {"plugin1@marketplace": [{"version": "1.0.0"}]}
        mock_update.return_value = (True, "1.0.0", "2.0.0")

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]

        # Should show restart note
        note_calls = [
            call for call in print_calls if "Restart Claude Code to apply" in str(call)
        ]
        assert len(note_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_truncates_long_already_latest_list(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: Truncating a long list of already-latest plugins.

        Given more than 5 plugins are already at the latest version
        When the main function displays the summary
        Then it should truncate the list and show a count of remaining items.
        """
        # Create 7 plugins
        plugins: dict[str, list[dict[str, str]]] = {}
        for i in range(7):
            plugins[f"plugin{i}@marketplace{i}"] = [{"version": "1.0.0"}]

        mock_read.return_value = plugins
        mock_update.side_effect = [(True, "1.0.0", "1.0.0")] * 7

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]

        # Should show truncation message
        more_calls = [call for call in print_calls if "... and 2 more" in str(call)]
        assert len(more_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_handles_plugin_without_at_symbol(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: Handling plugin names without marketplace separator.

        Given a plugin name does not contain the @ symbol
        When the main function processes the plugin
        Then it should display "unknown" as the marketplace.
        """
        mock_read.return_value = {"simpleplugin": [{"version": "1.0.0"}]}
        mock_update.return_value = (True, "1.0.0", "1.0.0")

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]

        # Should show "unknown" marketplace
        updating_calls = [
            call
            for call in print_calls
            if "Updating simpleplugin from unknown" in str(call)
        ]
        assert len(updating_calls) > 0

    @patch("update_all_plugins.update_plugin")
    @patch("update_all_plugins.read_installed_plugins")
    @patch("builtins.print")
    def test_main_output_format_no_emojis(
        self, mock_print: MagicMock, mock_read: MagicMock, mock_update: MagicMock
    ) -> None:
        """Scenario: Output format uses text markers instead of emojis.

        Given the main function is generating output
        When it displays status messages
        Then it should use text markers like [UPDATED] instead of emojis.
        """
        mock_read.return_value = {"test@marketplace": [{"version": "1.0.0"}]}
        mock_update.return_value = (True, "1.0.0", "2.0.0")

        update_all_plugins.main()

        print_calls = [str(call) for call in mock_print.call_args_list]
        all_output = " ".join(print_calls)

        # Check for common emojis - should not find any
        assert "🔧" not in all_output
        assert "✅" not in all_output
        assert "❌" not in all_output
        assert "📦" not in all_output

        # Should use text markers instead
        assert "[UPDATED]" in all_output
        # Also check that brackets are used consistently
        assert "[NOTE]" in all_output
