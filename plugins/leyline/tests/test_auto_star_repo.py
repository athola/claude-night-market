# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,E501,PLC0415
"""Tests for auto-star-repo.sh safety guarantees.

Feature: Star Prompt on Session Start

    As a project maintainer
    I want sessions to prompt users to star athola/claude-night-market
    So that contributors can support the project voluntarily

    CRITICAL SAFETY INVARIANTS:
    - The check path must NEVER star automatically (no PUT calls)
    - The script must NEVER unstar (no DELETE calls)
    - Already-starred repos must produce no output
    - The --star flag enables starring (only called after user consent)
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


def _strip_heredocs(source: str) -> str:
    """Remove heredoc blocks (<<'PROMPT' ... PROMPT) from source."""
    return re.sub(
        r"cat <<'PROMPT'.*?^PROMPT$",
        "",
        source,
        flags=re.DOTALL | re.MULTILINE,
    )


def _extract_function(source: str, name: str) -> str | None:
    """Extract a shell function body by name."""
    match = re.search(rf"{name}\(\)\s*\{{(.+?)\n\}}", source, re.DOTALL)
    return match.group(1) if match else None


class TestCheckPathNeverStars:
    """CRITICAL: The check functions must only READ status, never write."""

    @pytest.mark.unit
    def test_check_gh_has_no_put(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN scanning for PUT operations
        THEN none exist (check_gh only reads status).
        """
        body = _extract_function(hook_source, "check_gh")
        assert body is not None, "check_gh function must exist"
        assert "-X PUT" not in body, "SAFETY: check_gh must not PUT"

    @pytest.mark.unit
    def test_check_curl_has_no_put(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN scanning for PUT operations
        THEN none exist (check_curl only reads status).
        """
        body = _extract_function(hook_source, "check_curl")
        assert body is not None, "check_curl function must exist"
        assert "-X PUT" not in body, "SAFETY: check_curl must not PUT"

    @pytest.mark.unit
    def test_no_delete_anywhere(self, hook_source: str) -> None:
        """
        GIVEN the full hook script
        WHEN scanning for DELETE operations
        THEN none exist anywhere.
        """
        assert "-X DELETE" not in hook_source, (
            "SAFETY VIOLATION: -X DELETE found in hook"
        )


class TestStarMode:
    """Verify --star flag enables starring via gh or curl."""

    @pytest.mark.unit
    def test_star_flag_is_supported(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN called with --star
        THEN it attempts to star the repo.
        """
        assert '"--star"' in hook_source, "Script must support --star flag"

    @pytest.mark.unit
    def test_do_star_gh_uses_put(self, hook_source: str) -> None:
        """
        GIVEN the do_star_gh function
        WHEN starring the repo
        THEN it uses PUT to the starred API endpoint.
        """
        body = _extract_function(hook_source, "do_star_gh")
        assert body is not None, "do_star_gh function must exist"
        assert "-X PUT" in body, "do_star_gh must PUT to star"
        assert "/user/starred/" in body, "do_star_gh must target starred API"

    @pytest.mark.unit
    def test_do_star_curl_uses_put(self, hook_source: str) -> None:
        """
        GIVEN the do_star_curl function
        WHEN starring the repo
        THEN it uses PUT with Bearer auth.
        """
        body = _extract_function(hook_source, "do_star_curl")
        assert body is not None, "do_star_curl function must exist"
        assert "-X PUT" in body, "do_star_curl must PUT to star"
        assert "Authorization: Bearer" in body, "do_star_curl must use Bearer auth"

    @pytest.mark.unit
    def test_star_mode_exits_before_check(self, hook_source: str) -> None:
        """
        GIVEN the --star code path
        WHEN starring is requested
        THEN it exits before reaching the check/prompt logic.
        """
        lines = hook_source.split("\n")
        star_exit_idx = None
        check_gh_idx = None
        for i, line in enumerate(lines):
            if '"--star"' in line:
                star_exit_idx = i
            if "check_gh()" in line and "{" in line:
                check_gh_idx = i
        assert star_exit_idx is not None
        assert check_gh_idx is not None
        assert star_exit_idx < check_gh_idx, (
            "--star path must exit before check functions"
        )


class TestTargetRepo:
    """Verify the script targets the correct repository."""

    @pytest.mark.unit
    def test_targets_athola_claude_night_market(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN checking the target repo
        THEN it targets athola/claude-night-market.
        """
        assert 'OWNER="athola"' in hook_source
        assert 'REPO="claude-night-market"' in hook_source


class TestStarPromptOutputBehavior:
    """Verify the script outputs a prompt only when not starred."""

    @pytest.mark.unit
    def test_outputs_prompt_context_for_not_starred(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN the repo is not starred
        THEN it outputs a prompt message for Claude.
        """
        assert "star-prompt:" in hook_source, (
            "Script must output star-prompt context for Claude"
        )

    @pytest.mark.unit
    def test_prompt_gated_on_not_starred(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN the repo is already starred
        THEN it produces no output.
        """
        assert '"not_starred"' in hook_source, (
            "Script must gate prompt on not_starred status"
        )

    @pytest.mark.unit
    def test_prompt_tells_claude_to_run_script(self, hook_source: str) -> None:
        """
        GIVEN the prompt output
        WHEN Claude reads it
        THEN it includes the command to star via the script.
        """
        assert "auto-star-repo.sh --star" in hook_source, (
            "Prompt must tell Claude to run the script with --star"
        )


class TestStarPromptOptOut:
    """Verify the opt-out mechanism works."""

    @pytest.mark.unit
    def test_opt_out_env_var_exits_before_checks(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1 is set
        THEN the script exits before the check_gh/check_curl calls.

        Note: opt-out is after the --star path intentionally,
        since --star is only called after explicit user consent.
        """
        lines = hook_source.split("\n")
        opt_out_idx = None
        check_gh_def_idx = None
        for i, line in enumerate(lines):
            if "CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT" in line:
                opt_out_idx = i
            if line.strip().startswith("check_gh()"):
                check_gh_def_idx = i
        assert opt_out_idx is not None, (
            "Script must check CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT"
        )
        assert check_gh_def_idx is not None, "check_gh function must exist"
        assert opt_out_idx < check_gh_def_idx, (
            "Opt-out must come before check functions"
        )


class TestStatusChecks:
    """Verify both code paths check status correctly."""

    @pytest.mark.unit
    def test_gh_path_checks_status(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN examining its logic
        THEN it detects both starred and not-starred states.
        """
        body = _extract_function(hook_source, "check_gh")
        assert body is not None, "check_gh function must exist"
        assert "/user/starred/" in body
        assert '"204"' in body, "check_gh must detect starred (204)"
        assert '"404"' in body, "check_gh must detect not starred (404)"

    @pytest.mark.unit
    def test_curl_path_checks_status(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN examining its logic
        THEN it detects both starred and not-starred states.
        """
        body = _extract_function(hook_source, "check_curl")
        assert body is not None, "check_curl function must exist"
        assert "http_code" in body
        assert '"204"' in body, "check_curl must detect starred (204)"
        assert '"404"' in body, "check_curl must detect not starred (404)"


class TestCurlFallback:
    """Verify curl fallback is properly implemented."""

    @pytest.mark.unit
    def test_curl_checks_availability(self, hook_source: str) -> None:
        assert "command -v curl" in hook_source

    @pytest.mark.unit
    def test_curl_requires_token(self, hook_source: str) -> None:
        assert "GITHUB_TOKEN" in hook_source
        assert "GH_TOKEN" in hook_source

    @pytest.mark.unit
    def test_curl_uses_bearer_auth(self, hook_source: str) -> None:
        assert "Authorization: Bearer" in hook_source

    @pytest.mark.unit
    def test_gh_tried_before_curl(self, hook_source: str) -> None:
        main_section = hook_source[hook_source.rfind("# --- Main") :]
        gh_pos = main_section.find("check_gh")
        curl_pos = main_section.find("check_curl")
        assert gh_pos < curl_pos


class TestFailSafety:
    """Verify the script fails silently on errors."""

    @pytest.mark.unit
    def test_gh_guard_checks_cli(self, hook_source: str) -> None:
        assert "command -v gh" in hook_source

    @pytest.mark.unit
    def test_gh_guard_checks_auth(self, hook_source: str) -> None:
        assert "gh auth status" in hook_source

    @pytest.mark.unit
    def test_main_flow_handles_all_failures(self, hook_source: str) -> None:
        assert "exit 0" in hook_source

    @pytest.mark.unit
    def test_script_is_executable(self) -> None:
        import os
        import stat

        mode = os.stat(HOOK_PATH).st_mode
        assert mode & stat.S_IXUSR

    @pytest.mark.unit
    def test_script_has_bash_shebang(self, hook_source: str) -> None:
        assert hook_source.startswith("#!/usr/bin/env bash")

    @pytest.mark.unit
    def test_script_uses_strict_mode(self, hook_source: str) -> None:
        assert "set -euo pipefail" in hook_source
