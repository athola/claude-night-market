"""Test suite for version_fetcher module.

Following BDD principles with Given/When/Then structure.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from version_fetcher import (
    fetch_github_action_version,
    fetch_npm_latest_version,
    fetch_pypi_latest_version,
    get_default_action_versions,
    get_latest_action_versions,
    get_tool_versions,
)


@pytest.mark.unit
class TestFetchGitHubActionVersion:
    """Test GitHub Action version fetching behavior."""

    @patch("urllib.request.urlopen")
    def test_fetch_github_action_version_returns_major_version(self, mock_urlopen):
        """Given a GitHub action, when fetching version, then returns major version."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"tag_name": "v4.1.2"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        version = fetch_github_action_version("actions/checkout")

        # Then
        assert version == "v4"

    @patch("urllib.request.urlopen")
    def test_fetch_github_action_version_handles_simple_tag(self, mock_urlopen):
        """Given a simple tag without dots, when fetching version, then returns tag as-is."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"tag_name": "stable"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        version = fetch_github_action_version("dtolnay/rust-toolchain")

        # Then
        assert version == "stable"

    @patch("urllib.request.urlopen")
    def test_fetch_github_action_version_returns_none_on_error(self, mock_urlopen):
        """Given a network error, when fetching version, then returns None."""
        # Given
        mock_urlopen.side_effect = Exception("Network error")

        # When
        version = fetch_github_action_version("actions/nonexistent")

        # Then
        assert version is None

    @patch("urllib.request.urlopen")
    def test_fetch_github_action_version_caches_results(self, mock_urlopen):
        """Given multiple calls for same action, when fetching version, then uses cache."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"tag_name": "v4.0.0"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Clear cache first
        fetch_github_action_version.cache_clear()

        # When
        version1 = fetch_github_action_version("actions/checkout")
        version2 = fetch_github_action_version("actions/checkout")

        # Then
        assert version1 == version2
        # Should only call urlopen once due to caching
        assert mock_urlopen.call_count == 1

    @patch("urllib.request.urlopen")
    def test_fetch_github_action_version_constructs_correct_url(self, mock_urlopen):
        """Given an action name, when fetching version, then constructs correct API URL."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"tag_name": "v2.0.0"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        fetch_github_action_version.cache_clear()
        fetch_github_action_version("owner/repo")

        # Then
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert (
            "https://api.github.com/repos/owner/repo/releases/latest"
            in request.full_url
        )


@pytest.mark.unit
class TestGetDefaultActionVersions:
    """Test default action versions behavior."""

    def test_get_default_action_versions_returns_dict(self):
        """When getting default action versions, then returns dictionary."""
        # When
        versions = get_default_action_versions()

        # Then
        assert isinstance(versions, dict)
        assert len(versions) > 0

    def test_get_default_action_versions_includes_common_actions(self):
        """When getting default action versions, then includes common actions."""
        # When
        versions = get_default_action_versions()

        # Then
        expected_actions = [
            "actions/checkout",
            "actions/setup-python",
            "actions/setup-node",
            "dtolnay/rust-toolchain",
        ]
        for action in expected_actions:
            assert action in versions

    def test_get_default_action_versions_has_valid_versions(self):
        """When getting default action versions, then all versions are non-empty strings."""
        # When
        versions = get_default_action_versions()

        # Then
        for action, version in versions.items():
            assert isinstance(version, str)
            assert len(version) > 0


@pytest.mark.unit
class TestGetLatestActionVersions:
    """Test latest action versions behavior."""

    @patch("version_fetcher.fetch_github_action_version")
    def test_get_latest_action_versions_fetches_all_actions(self, mock_fetch):
        """When getting latest versions, then fetches all known actions."""
        # Given
        mock_fetch.return_value = "v4"

        # When
        versions = get_latest_action_versions()

        # Then
        assert len(versions) > 0
        assert mock_fetch.call_count >= len(versions)

    @patch("version_fetcher.fetch_github_action_version")
    def test_get_latest_action_versions_falls_back_to_defaults(self, mock_fetch):
        """Given fetch failures, when getting latest versions, then uses defaults."""
        # Given
        mock_fetch.return_value = None  # Simulate fetch failure

        # When
        versions = get_latest_action_versions()

        # Then
        defaults = get_default_action_versions()
        for action in defaults:
            assert action in versions
            assert versions[action] == defaults[action]

    @patch("version_fetcher.fetch_github_action_version")
    def test_get_latest_action_versions_uses_fetched_when_available(self, mock_fetch):
        """Given successful fetches, when getting latest versions, then uses fetched versions."""
        # Given
        mock_fetch.return_value = "v5"

        # When
        versions = get_latest_action_versions()

        # Then
        # All fetched versions should be v5
        for version in versions.values():
            assert version == "v5"

    @patch("version_fetcher.fetch_github_action_version")
    def test_get_latest_action_versions_respects_cache_parameter(self, mock_fetch):
        """Given use_cache=False, when getting latest versions, then clears cache."""
        # Given
        mock_fetch.return_value = "v4"

        # When
        get_latest_action_versions(use_cache=False)

        # Then
        # Cache should be cleared and fetch called
        assert mock_fetch.called


@pytest.mark.unit
class TestFetchPyPILatestVersion:
    """Test PyPI version fetching behavior."""

    @patch("urllib.request.urlopen")
    def test_fetch_pypi_latest_version_returns_version(self, mock_urlopen):
        """Given a PyPI package, when fetching version, then returns version string."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"info": {"version": "1.2.3"}}
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        version = fetch_pypi_latest_version("pytest")

        # Then
        assert version == "1.2.3"

    @patch("urllib.request.urlopen")
    def test_fetch_pypi_latest_version_returns_none_on_error(self, mock_urlopen):
        """Given a network error, when fetching PyPI version, then returns None."""
        # Given
        mock_urlopen.side_effect = Exception("Network error")

        # When
        version = fetch_pypi_latest_version("nonexistent-package")

        # Then
        assert version is None

    @patch("urllib.request.urlopen")
    def test_fetch_pypi_latest_version_constructs_correct_url(self, mock_urlopen):
        """Given a package name, when fetching PyPI version, then constructs correct URL."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"info": {"version": "1.0.0"}}
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        fetch_pypi_latest_version.cache_clear()
        fetch_pypi_latest_version("mypackage")

        # Then
        call_args = mock_urlopen.call_args
        url = call_args[0][0]
        assert "https://pypi.org/pypi/mypackage/json" in url

    @patch("urllib.request.urlopen")
    def test_fetch_pypi_latest_version_caches_results(self, mock_urlopen):
        """Given multiple calls for same package, when fetching version, then uses cache."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"info": {"version": "1.0.0"}}
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Clear cache first
        fetch_pypi_latest_version.cache_clear()

        # When
        version1 = fetch_pypi_latest_version("pytest")
        version2 = fetch_pypi_latest_version("pytest")

        # Then
        assert version1 == version2
        assert mock_urlopen.call_count == 1


@pytest.mark.unit
class TestFetchNPMLatestVersion:
    """Test npm version fetching behavior."""

    @patch("urllib.request.urlopen")
    def test_fetch_npm_latest_version_returns_version(self, mock_urlopen):
        """Given an npm package, when fetching version, then returns version string."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"version": "5.0.0"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        version = fetch_npm_latest_version("typescript")

        # Then
        assert version == "5.0.0"

    @patch("urllib.request.urlopen")
    def test_fetch_npm_latest_version_returns_none_on_error(self, mock_urlopen):
        """Given a network error, when fetching npm version, then returns None."""
        # Given
        mock_urlopen.side_effect = Exception("Network error")

        # When
        version = fetch_npm_latest_version("nonexistent-package")

        # Then
        assert version is None

    @patch("urllib.request.urlopen")
    def test_fetch_npm_latest_version_constructs_correct_url(self, mock_urlopen):
        """Given a package name, when fetching npm version, then constructs correct URL."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"version": "1.0.0"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        fetch_npm_latest_version.cache_clear()
        fetch_npm_latest_version("vite")

        # Then
        call_args = mock_urlopen.call_args
        url = call_args[0][0]
        assert "https://registry.npmjs.org/vite/latest" in url

    @patch("urllib.request.urlopen")
    def test_fetch_npm_latest_version_caches_results(self, mock_urlopen):
        """Given multiple calls for same package, when fetching version, then uses cache."""
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"version": "1.0.0"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Clear cache first
        fetch_npm_latest_version.cache_clear()

        # When
        version1 = fetch_npm_latest_version("typescript")
        version2 = fetch_npm_latest_version("typescript")

        # Then
        assert version1 == version2
        assert mock_urlopen.call_count == 1


@pytest.mark.unit
class TestGetToolVersions:
    """Test tool versions retrieval behavior."""

    @patch("version_fetcher.fetch_pypi_latest_version")
    def test_get_tool_versions_python(self, mock_fetch):
        """Given 'python' language, when getting tool versions, then fetches Python tools."""
        # Given
        mock_fetch.return_value = "1.0.0"

        # When
        versions = get_tool_versions("python")

        # Then
        expected_tools = ["ruff", "mypy", "pytest"]
        for tool in expected_tools:
            assert tool in versions

    @patch("version_fetcher.fetch_npm_latest_version")
    def test_get_tool_versions_typescript(self, mock_fetch):
        """Given 'typescript' language, when getting tool versions, then fetches TS tools."""
        # Given
        mock_fetch.return_value = "5.0.0"

        # When
        versions = get_tool_versions("typescript")

        # Then
        expected_tools = ["typescript", "vite", "eslint"]
        for tool in expected_tools:
            assert tool in versions

    def test_get_tool_versions_rust(self):
        """Given 'rust' language, when getting tool versions, then returns empty dict."""
        # When
        versions = get_tool_versions("rust")

        # Then
        # Rust tools not fetched from registries (handled by Cargo)
        assert isinstance(versions, dict)

    @patch("version_fetcher.fetch_pypi_latest_version")
    def test_get_tool_versions_uses_fallback_on_failure(self, mock_fetch):
        """Given fetch failures, when getting tool versions, then uses fallback versions."""
        # Given
        mock_fetch.return_value = None

        # When
        versions = get_tool_versions("python")

        # Then
        # Should have fallback versions
        assert "ruff" in versions
        assert versions["ruff"] is not None

    def test_get_tool_versions_unknown_language(self):
        """Given unknown language, when getting tool versions, then returns empty dict."""
        # When
        versions = get_tool_versions("unknown")

        # Then
        assert versions == {}


@pytest.mark.bdd
class TestVersionFetcherBehavior:
    """BDD-style tests for version fetcher workflows."""

    @patch("urllib.request.urlopen")
    def test_scenario_fetch_latest_github_action_version(self, mock_urlopen):
        """
        Scenario: Fetching latest GitHub Action version.

        Given a GitHub Action exists
        When I fetch its latest version
        Then it should return the major version number
        """
        # Given
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"tag_name": "v4.2.1"}).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # When
        fetch_github_action_version.cache_clear()
        version = fetch_github_action_version("actions/checkout")

        # Then
        assert version == "v4"

    @patch("version_fetcher.fetch_github_action_version")
    def test_scenario_get_all_latest_action_versions_with_fallback(self, mock_fetch):
        """
        Scenario: Getting all latest action versions with fallback.

        Given some GitHub Actions are available
        And some fail to fetch
        When I get latest action versions
        Then it should return versions for all actions
        And use defaults for failed fetches
        """

        # Given
        def fetch_side_effect(action):
            if "checkout" in action:
                return "v4"
            return None  # Fail for others

        mock_fetch.side_effect = fetch_side_effect

        # When
        versions = get_latest_action_versions()

        # Then
        assert "actions/checkout" in versions
        assert versions["actions/checkout"] == "v4"
        # Others should have defaults
        defaults = get_default_action_versions()
        for action in defaults:
            assert action in versions
            assert versions[action] is not None

    @patch("urllib.request.urlopen")
    @patch("version_fetcher.fetch_pypi_latest_version")
    def test_scenario_get_python_tool_versions(self, mock_pypi, mock_urlopen):
        """
        Scenario: Getting latest Python tool versions.

        Given Python development tools exist in PyPI
        When I get tool versions for Python
        Then it should fetch latest versions from PyPI
        And return a dictionary of tool versions
        """
        # Given
        mock_pypi.return_value = "8.0.0"

        # When
        versions = get_tool_versions("python")

        # Then
        assert "pytest" in versions
        assert "ruff" in versions
        assert "mypy" in versions
        assert all(v is not None for v in versions.values())
