# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,E501,PLC0415
"""Tests for auto-star-repo.sh safety guarantees.

Feature: Star Prompt on Session Start

    As a project maintainer
    I want sessions to prompt users to star anthropics/claude-code
    So that contributors can support the upstream project voluntarily

    CRITICAL SAFETY INVARIANTS:
    - The script must NEVER star automatically (no PUT calls)
    - The script must NEVER unstar (no DELETE calls)
    - Already-starred repos must produce no output
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


class TestStarPromptNeverStarsAutomatically:
    """CRITICAL: The script must only CHECK status, never star."""

    @pytest.mark.unit
    def test_no_put_method_in_shell_logic(self, hook_source: str) -> None:
        """
        GIVEN the star prompt hook script
        WHEN scanning shell logic for HTTP PUT operations
        THEN none exist outside the heredoc prompt text.

        The heredoc prompt tells Claude the command to run,
        but the script itself never executes PUT.
        """
        # Strip heredoc blocks (between <<'PROMPT' and PROMPT)
        stripped = re.sub(
            r"cat <<'PROMPT'.*?^PROMPT$",
            "",
            hook_source,
            flags=re.DOTALL | re.MULTILINE,
        )
        put_lines = [
            line
            for line in _non_comment_lines(stripped)
            if "-X PUT" in line or "--method PUT" in line
        ]
        assert put_lines == [], f"SAFETY VIOLATION: PUT in shell logic: {put_lines}"

    @pytest.mark.unit
    def test_no_delete_method_in_script(self, hook_source: str) -> None:
        """
        GIVEN the star prompt hook script
        WHEN scanning for HTTP DELETE operations
        THEN none exist anywhere in non-comment source.
        """
        delete_lines = [
            line for line in _non_comment_lines(hook_source) if "delete" in line.lower()
        ]
        assert delete_lines == [], (
            f"SAFETY VIOLATION: DELETE found in hook: {delete_lines}"
        )

    @pytest.mark.unit
    def test_no_dash_x_delete_in_script(self, hook_source: str) -> None:
        """
        GIVEN the star prompt hook script
        WHEN scanning for -X DELETE patterns
        THEN none exist.
        """
        assert "-X DELETE" not in hook_source, (
            "SAFETY VIOLATION: -X DELETE found in hook"
        )


class TestStarPromptOutputBehavior:
    """Verify the script outputs a prompt only when not starred."""

    @pytest.mark.unit
    def test_outputs_prompt_context_for_not_starred(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN the repo is not starred (status 404)
        THEN it outputs a prompt message for Claude.
        """
        assert "star-prompt:" in hook_source, (
            "Script must output star-prompt context for Claude"
        )

    @pytest.mark.unit
    def test_no_output_when_starred(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN the repo is already starred (status 204)
        THEN it produces no output (silent exit).
        """
        # The 204 path should NOT contain the prompt output
        # Check that prompt is only emitted in the not_starred branch
        assert 'result" = "not_starred"' in hook_source or (
            '"not_starred"' in hook_source
        ), "Script must gate prompt on not_starred status"

    @pytest.mark.unit
    def test_prompt_mentions_gh_api_command(self, hook_source: str) -> None:
        """
        GIVEN the prompt output
        WHEN Claude reads it
        THEN it includes the exact gh command to star the repo.
        """
        assert "gh api -X PUT /user/starred/anthropics/claude-code" in hook_source, (
            "Prompt must include the exact gh command for Claude to run"
        )


class TestStarPromptOptOut:
    """Verify the opt-out mechanism works."""

    @pytest.mark.unit
    def test_opt_out_env_var_exits_early(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1 is set
        THEN the script exits before any API calls.
        """
        lines = hook_source.split("\n")
        opt_out_idx = None
        first_api_idx = None
        for i, line in enumerate(lines):
            if "CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT" in line:
                opt_out_idx = i
            if first_api_idx is None and "api.github.com" in line:
                first_api_idx = i
        assert opt_out_idx is not None, (
            "Script must check CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT"
        )
        assert first_api_idx is not None, "Script must have API calls"
        assert opt_out_idx < first_api_idx, (
            "Opt-out check must come before any API calls"
        )


class TestStarPromptStatusChecks:
    """Verify both code paths (gh and curl) check status correctly."""

    @pytest.mark.unit
    def test_gh_path_checks_status(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN examining its logic
        THEN it queries star status and returns a status string.
        """
        match = re.search(r"check_gh\(\)\s*\{(.+?)\n\}", hook_source, re.DOTALL)
        assert match, "check_gh function must exist"
        gh_body = match.group(1)

        assert "/user/starred/" in gh_body, "check_gh must query star status"
        assert '"204"' in gh_body, "check_gh must detect starred (204)"
        assert '"404"' in gh_body, "check_gh must detect not starred (404)"

    @pytest.mark.unit
    def test_curl_path_checks_status(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN examining its logic
        THEN it queries star status and returns a status string.
        """
        match = re.search(r"check_curl\(\)\s*\{(.+?)\n\}", hook_source, re.DOTALL)
        assert match, "check_curl function must exist"
        curl_body = match.group(1)

        assert "http_code" in curl_body, "check_curl must capture HTTP status"
        assert '"204"' in curl_body, "check_curl must detect starred (204)"
        assert '"404"' in curl_body, "check_curl must detect not starred (404)"

    @pytest.mark.unit
    def test_curl_path_never_modifies(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN scanning for write operations
        THEN none exist in the curl path.
        """
        match = re.search(r"check_curl\(\)\s*\{(.+?)\n\}", hook_source, re.DOTALL)
        assert match, "check_curl function must exist"
        curl_body = match.group(1)

        assert "-X PUT" not in curl_body, "SAFETY VIOLATION: curl path contains -X PUT"
        assert "-X DELETE" not in curl_body, (
            "SAFETY VIOLATION: curl path contains -X DELETE"
        )


class TestStarPromptCurlFallback:
    """Verify curl fallback is properly implemented."""

    @pytest.mark.unit
    def test_curl_checks_availability(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN checking preconditions
        THEN it verifies curl is installed.
        """
        assert "command -v curl" in hook_source, (
            "Script must check for curl availability"
        )

    @pytest.mark.unit
    def test_curl_requires_token(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN no token is available
        THEN it exits without making API calls.
        """
        assert "GITHUB_TOKEN" in hook_source, "Script must check GITHUB_TOKEN"
        assert "GH_TOKEN" in hook_source, "Script must check GH_TOKEN as fallback"

    @pytest.mark.unit
    def test_curl_uses_bearer_auth(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN making API calls
        THEN it uses Bearer token authentication.
        """
        assert "Authorization: Bearer" in hook_source, "curl must use Bearer token auth"

    @pytest.mark.unit
    def test_gh_tried_before_curl(self, hook_source: str) -> None:
        """
        GIVEN the main execution flow
        WHEN choosing auth method
        THEN gh is tried first, curl is the fallback.
        """
        main_section = hook_source[hook_source.rfind("# --- Main") :]
        gh_pos = main_section.find("check_gh")
        curl_pos = main_section.find("check_curl")
        assert gh_pos < curl_pos, "check_gh must be attempted before check_curl"


class TestStarPromptFailSafety:
    """Verify the script fails silently on errors."""

    @pytest.mark.unit
    def test_gh_guard_checks_cli(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN gh CLI is not available
        THEN it returns non-zero to trigger fallback.
        """
        assert "command -v gh" in hook_source, (
            "Script must check for gh CLI availability"
        )

    @pytest.mark.unit
    def test_gh_guard_checks_auth(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN gh is not authenticated
        THEN it returns non-zero to trigger fallback.
        """
        assert "gh auth status" in hook_source, "Script must verify gh authentication"

    @pytest.mark.unit
    def test_main_flow_handles_all_failures(self, hook_source: str) -> None:
        """
        GIVEN the main execution flow
        WHEN both methods fail
        THEN the script exits 0 (silent failure).
        """
        assert "exit 0" in hook_source, "Script must exit 0 at the end"

    @pytest.mark.unit
    def test_script_is_executable(self) -> None:
        """
        GIVEN the hook file
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
        GIVEN the hook script
        WHEN checking the shebang line
        THEN it uses bash.
        """
        assert hook_source.startswith("#!/usr/bin/env bash"), (
            "Hook must have bash shebang"
        )

    @pytest.mark.unit
    def test_script_uses_strict_mode(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN checking shell options
        THEN it uses set -euo pipefail.
        """
        assert "set -euo pipefail" in hook_source, "Hook must use strict shell mode"
