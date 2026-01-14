#!/usr/bin/env python3
"""Fetch latest versions for dependencies and GitHub Actions."""

import json
import urllib.request
from functools import lru_cache
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

# Common network/parsing exceptions for URL fetching
_FETCH_ERRORS = (
    HTTPError,
    URLError,
    JSONDecodeError,
    TimeoutError,
    ValueError,
    KeyError,
)


def _validate_https_url(url: str) -> None:
    """Validate that URL uses HTTPS scheme only.

    Args:
        url: URL to validate

    Raises:
        ValueError: If URL doesn't use HTTPS scheme

    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Only HTTPS URLs allowed, got: {parsed.scheme}")


@lru_cache(maxsize=128)
def fetch_github_action_version(action: str) -> str | None:
    """Fetch latest version tag for a GitHub Action.

    Args:
        action: GitHub action in format "owner/repo"

    Returns:
        Latest version tag (e.g., "v4") or None if fetch fails

    """
    try:
        url = f"https://api.github.com/repos/{action}/releases/latest"
        _validate_https_url(url)
        req = urllib.request.Request(
            url, headers={"Accept": "application/vnd.github.v3+json"}
        )
        # URL validated above via _validate_https_url()
        with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310
            data = json.loads(response.read().decode())
            tag_name = data.get("tag_name", "")

            # Return major version (v4.1.2 -> v4)
            if tag_name.startswith("v"):
                major_version: str = tag_name.split(".")[0]
                return major_version

            return str(tag_name)

    except _FETCH_ERRORS as e:
        print(f"Warning: Could not fetch version for {action}: {e}")
        return None


def get_default_action_versions() -> dict[str, str]:
    """Get default GitHub Action versions.

    Returns:
        Dictionary mapping action names to versions

    """
    return {
        "actions/checkout": "v4",
        "actions/setup-python": "v5",
        "actions/setup-node": "v4",
        "dtolnay/rust-toolchain": "stable",
        "Swatinem/rust-cache": "v2",
        "astral-sh/setup-uv": "v2",
        "codecov/codecov-action": "v4",
    }


def get_latest_action_versions(use_cache: bool = True) -> dict[str, str]:
    """Get latest GitHub Action versions with defaults for missing values.

    Args:
        use_cache: Whether to use cached results

    Returns:
        Dictionary mapping action names to latest versions

    """
    if not use_cache:
        fetch_github_action_version.cache_clear()

    default_versions = get_default_action_versions()
    latest_versions = {}

    for action, default_version in default_versions.items():
        version = fetch_github_action_version(action)
        latest_versions[action] = version or default_version

    return latest_versions


@lru_cache(maxsize=32)
def fetch_pypi_latest_version(package: str) -> str | None:
    """Fetch latest version from PyPI.

    Args:
        package: PyPI package name

    Returns:
        Latest version string or None

    """
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        _validate_https_url(url)
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310
            data = json.loads(resp.read().decode())
            return str(data["info"]["version"])
    except _FETCH_ERRORS as e:
        print(f"Warning: Could not fetch PyPI version for {package}: {e}")
        return None


@lru_cache(maxsize=32)
def fetch_npm_latest_version(package: str) -> str | None:
    """Fetch latest version from npm registry.

    Args:
        package: npm package name

    Returns:
        Latest version string or None

    """
    try:
        url = f"https://registry.npmjs.org/{package}/latest"
        _validate_https_url(url)
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310
            data = json.loads(resp.read().decode())
            return str(data["version"])
    except _FETCH_ERRORS as e:
        print(f"Warning: Could not fetch npm version for {package}: {e}")
        return None


def get_tool_versions(language: str) -> dict[str, str]:
    """Get latest tool versions for a language.

    Args:
        language: Programming language (python, rust, typescript)

    Returns:
        Dictionary of tool versions

    """
    versions = {}

    if language == "python":
        versions.update(
            {
                "ruff": fetch_pypi_latest_version("ruff") or "0.14.0",
                "mypy": fetch_pypi_latest_version("mypy") or "1.18.0",
                "pytest": fetch_pypi_latest_version("pytest") or "8.3.0",
            }
        )
    elif language == "typescript":
        versions.update(
            {
                "typescript": fetch_npm_latest_version("typescript") or "5.5.0",
                "vite": fetch_npm_latest_version("vite") or "5.3.0",
                "eslint": fetch_npm_latest_version("eslint") or "8.57.0",
            }
        )

    return versions


if __name__ == "__main__":
    # Example usage
    print("Fetching latest GitHub Action versions...")
    actions = get_latest_action_versions()
    for action, version in actions.items():
        print(f"  {action}: {version}")

    print("\nFetching latest Python tool versions...")
    python_versions = get_tool_versions("python")
    for tool, version in python_versions.items():
        print(f"  {tool}: {version}")
