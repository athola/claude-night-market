# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,E501,PLC0415
"""Tests for auto-star-repo.sh safety guarantees.

Feature: Auto-Star Repository on Session Start

    As a project maintainer
    I want sessions to auto-star anthropics/claude-code if not already starred
    So that contributors naturally support the upstream project

    CRITICAL SAFETY INVARIANT:
    The script must NEVER unstar (DELETE) the repository.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "auto-star-repo.sh"


@pytest.fixture
def hook_source() -> str:
    """Load the auto-star hook source code."""
    return HOOK_PATH.read_text()


def _non_comment_lines(source: str) -> list[str]:
    """Return non-comment, non-empty lines from shell source."""
    return [
        line.strip()
        for line in source.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]


class TestAutoStarNeverUnstars:
    """CRITICAL: Verify the script cannot unstar a repository."""

    @pytest.mark.unit
    def test_no_delete_method_in_script(self, hook_source: str) -> None:
        """
        GIVEN the auto-star hook script
        WHEN scanning for HTTP DELETE operations
        THEN none exist anywhere in non-comment source.
        """
        delete_lines = [
            line for line in _non_comment_lines(hook_source) if "delete" in line.lower()
        ]
        assert delete_lines == [], (
            f"SAFETY VIOLATION: DELETE found in auto-star hook: {delete_lines}"
        )

    @pytest.mark.unit
    def test_no_dash_x_delete_in_script(self, hook_source: str) -> None:
        """
        GIVEN the auto-star hook script
        WHEN scanning for -X DELETE patterns (gh or curl)
        THEN none exist.
        """
        assert "-X DELETE" not in hook_source, (
            "SAFETY VIOLATION: -X DELETE found in auto-star hook"
        )

    @pytest.mark.unit
    def test_no_method_delete_in_script(self, hook_source: str) -> None:
        """
        GIVEN the auto-star hook script
        WHEN scanning for --method DELETE or --request DELETE
        THEN none exist.
        """
        assert "--method DELETE" not in hook_source, (
            "SAFETY VIOLATION: --method DELETE found in auto-star hook"
        )
        assert "--request DELETE" not in hook_source, (
            "SAFETY VIOLATION: --request DELETE found in auto-star hook"
        )


class TestAutoStarIdempotency:
    """Verify both code paths (gh and curl) check before starring."""

    @pytest.mark.unit
    def test_gh_path_checks_before_put(self, hook_source: str) -> None:
        """
        GIVEN the try_gh function
        WHEN examining its logic
        THEN it checks star status before any PUT.
        """
        # Extract try_gh function body
        match = re.search(r"try_gh\(\)\s*\{(.+?)\n\}", hook_source, re.DOTALL)
        assert match, "try_gh function must exist"
        gh_body = match.group(1)

        assert "/user/starred/" in gh_body, "try_gh must check star status"
        assert "-X PUT" in gh_body, "try_gh must PUT to star"
        assert '"404"' in gh_body, "try_gh must gate PUT on 404 status"

    @pytest.mark.unit
    def test_curl_path_checks_before_put(self, hook_source: str) -> None:
        """
        GIVEN the try_curl function
        WHEN examining its logic
        THEN it checks star status before any PUT.
        """
        match = re.search(r"try_curl\(\)\s*\{(.+?)\n\}", hook_source, re.DOTALL)
        assert match, "try_curl function must exist"
        curl_body = match.group(1)

        assert "http_code" in curl_body or "status" in curl_body, (
            "try_curl must capture HTTP status"
        )
        assert "-X PUT" in curl_body, "try_curl must PUT to star"
        assert '"404"' in curl_body, "try_curl must gate PUT on 404 status"

    @pytest.mark.unit
    def test_curl_path_never_unstars(self, hook_source: str) -> None:
        """
        GIVEN the try_curl function
        WHEN scanning for DELETE operations
        THEN none exist in the curl path.
        """
        match = re.search(r"try_curl\(\)\s*\{(.+?)\n\}", hook_source, re.DOTALL)
        assert match, "try_curl function must exist"
        curl_body = match.group(1)

        assert "-X DELETE" not in curl_body, (
            "SAFETY VIOLATION: curl path contains -X DELETE"
        )


class TestAutoStarCurlFallback:
    """Verify curl fallback is properly implemented."""

    @pytest.mark.unit
    def test_curl_checks_availability(self, hook_source: str) -> None:
        """
        GIVEN the try_curl function
        WHEN checking preconditions
        THEN it verifies curl is installed.
        """
        assert "command -v curl" in hook_source, (
            "Script must check for curl availability"
        )

    @pytest.mark.unit
    def test_curl_requires_token(self, hook_source: str) -> None:
        """
        GIVEN the try_curl function
        WHEN no token is available
        THEN it exits without making API calls.
        """
        assert "GITHUB_TOKEN" in hook_source, "Script must check GITHUB_TOKEN"
        assert "GH_TOKEN" in hook_source, "Script must check GH_TOKEN as fallback"

    @pytest.mark.unit
    def test_curl_uses_bearer_auth(self, hook_source: str) -> None:
        """
        GIVEN the try_curl function
        WHEN making API calls
        THEN it uses Bearer token authentication.
        """
        assert "Authorization: Bearer" in hook_source, "curl must use Bearer token auth"

    @pytest.mark.unit
    def test_curl_sets_api_version(self, hook_source: str) -> None:
        """
        GIVEN the try_curl function
        WHEN making API calls
        THEN it sets the GitHub API version header.
        """
        assert "X-GitHub-Api-Version" in hook_source, "curl must set API version header"

    @pytest.mark.unit
    def test_gh_tried_before_curl(self, hook_source: str) -> None:
        """
        GIVEN the main execution flow
        WHEN choosing auth method
        THEN gh is tried first, curl is the fallback.
        """
        assert "try_gh" in hook_source, "Script must have try_gh"
        assert "try_curl" in hook_source, "Script must have try_curl"
        # In the main flow, try_gh should appear before try_curl
        main_section = hook_source[hook_source.rfind("# --- Main") :]
        gh_pos = main_section.find("try_gh")
        curl_pos = main_section.find("try_curl")
        assert gh_pos < curl_pos, "try_gh must be attempted before try_curl"


class TestAutoStarOptOut:
    """Verify the opt-out mechanism works."""

    @pytest.mark.unit
    def test_opt_out_env_var_exits_early(self, hook_source: str) -> None:
        """
        GIVEN the auto-star hook script
        WHEN CLAUDE_NIGHT_MARKET_NO_AUTO_STAR=1 is set
        THEN the script exits before any API calls.
        """
        lines = hook_source.split("\n")
        opt_out_idx = None
        first_api_idx = None
        for i, line in enumerate(lines):
            if "CLAUDE_NIGHT_MARKET_NO_AUTO_STAR" in line:
                opt_out_idx = i
            if first_api_idx is None and "api.github.com" in line:
                first_api_idx = i
        assert opt_out_idx is not None, (
            "Script must check CLAUDE_NIGHT_MARKET_NO_AUTO_STAR"
        )
        assert first_api_idx is not None, "Script must have API calls"
        assert opt_out_idx < first_api_idx, (
            "Opt-out check must come before any API calls"
        )

    @pytest.mark.unit
    def test_opt_out_exits_with_zero(self, hook_source: str) -> None:
        """
        GIVEN the opt-out block
        WHEN the env var is set to 1
        THEN it exits 0 (not an error).
        """
        # Find the opt-out block and verify it exits 0
        assert "exit 0" in hook_source, "Opt-out must exit cleanly"


class TestAutoStarFailSafety:
    """Verify the script fails silently on errors."""

    @pytest.mark.unit
    def test_gh_guard_checks_cli(self, hook_source: str) -> None:
        """
        GIVEN the try_gh function
        WHEN gh CLI is not available
        THEN it returns non-zero to trigger fallback.
        """
        assert "command -v gh" in hook_source, (
            "Script must check for gh CLI availability"
        )

    @pytest.mark.unit
    def test_gh_guard_checks_auth(self, hook_source: str) -> None:
        """
        GIVEN the try_gh function
        WHEN gh is not authenticated
        THEN it returns non-zero to trigger fallback.
        """
        assert "gh auth status" in hook_source, "Script must verify gh authentication"

    @pytest.mark.unit
    def test_main_flow_swallows_all_errors(self, hook_source: str) -> None:
        """
        GIVEN the main execution flow
        WHEN both methods fail
        THEN the script exits 0 (silent failure).
        """
        main_section = hook_source[hook_source.rfind("# --- Main") :]
        assert "|| true" in main_section, "Main flow must swallow errors with || true"
        assert "exit 0" in hook_source, "Script must exit 0 at the end"

    @pytest.mark.unit
    def test_script_is_executable(self) -> None:
        """
        GIVEN the auto-star hook file
        WHEN checking file permissions
        THEN it is executable.
        """
        import os
        import stat

        mode = os.stat(HOOK_PATH).st_mode
        assert mode & stat.S_IXUSR, "Hook must be executable"

    @pytest.mark.unit
    def test_script_has_bash_shebang(self, hook_source: str) -> None:
        """
        GIVEN the auto-star hook script
        WHEN checking the shebang line
        THEN it uses bash.
        """
        assert hook_source.startswith("#!/usr/bin/env bash"), (
            "Hook must have bash shebang"
        )

    @pytest.mark.unit
    def test_script_uses_strict_mode(self, hook_source: str) -> None:
        """
        GIVEN the auto-star hook script
        WHEN checking shell options
        THEN it uses set -euo pipefail.
        """
        assert "set -euo pipefail" in hook_source, "Hook must use strict shell mode"
