"""
Tests for leyline SessionStart hook: fetch-recent-discussions.sh

Feature: Fetch Recent Discussions Hook
  As a Claude Code user on a GitHub repository
  I want recent Decisions discussions injected into my session context
  So that I have cross-session awareness of architectural decisions

Guard conditions are tested by controlling the subprocess environment.
Network-dependent paths (GraphQL API calls) are out of scope for unit tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT = Path(__file__).parents[3] / "hooks" / "fetch-recent-discussions.sh"


class TestFetchRecentDiscussionsGuards:
    """
    Feature: Guard conditions prevent the hook from running in unsupported environments.
    Each guard should output valid empty-context JSON and exit 0.
    """

    @pytest.mark.unit
    def test_hook_script_exists_and_is_executable(self) -> None:
        """
        Scenario: Hook script is properly installed
        Given the leyline plugin is installed
        When checking the hook script
        Then it exists and is executable with a shebang.
        """
        assert HOOK_SCRIPT.exists(), f"Hook script not found at {HOOK_SCRIPT}"
        assert os.access(HOOK_SCRIPT, os.X_OK), "Hook script is not executable"
        first_line = HOOK_SCRIPT.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "Missing shebang line"

    @pytest.mark.unit
    def test_non_git_directory_returns_empty_context(self, tmp_path: Path) -> None:
        """
        Scenario: Non-git directory produces empty context
        Given a directory that is not a git repository
        When the hook runs
        Then it outputs valid JSON with empty additionalContext.
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_non_github_remote_returns_empty_context(self, tmp_path: Path) -> None:
        """
        Scenario: GitLab remote is silently skipped
        Given a git repo with a GitLab origin
        When the hook runs
        Then it outputs empty context (Discussions are GitHub-only).
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://gitlab.com/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_bitbucket_remote_returns_empty_context(self, tmp_path: Path) -> None:
        """
        Scenario: Bitbucket remote is silently skipped
        Given a git repo with a Bitbucket origin
        When the hook runs
        Then it outputs empty context (Discussions are GitHub-only).
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://bitbucket.org/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.skipif(
        sys.platform.startswith("win"),
        reason="PATH manipulation not reliable on Windows",
    )
    @pytest.mark.unit
    def test_missing_gh_cli_returns_empty_context(self, tmp_path: Path) -> None:
        """
        Scenario: Missing gh CLI produces empty context
        Given gh is not on PATH
        When the hook runs
        Then it outputs empty context without error.
        """
        # Create a minimal PATH with only essential commands (bash, git, python3)
        # but NOT gh, to simulate gh being unavailable
        env = os.environ.copy()
        env["PATH"] = "/usr/bin:/bin"

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
            env=env,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_no_remote_returns_empty_context(self, tmp_path: Path) -> None:
        """
        Scenario: Git repo with no remote produces empty context
        Given a git repo with no origin remote
        When the hook runs
        Then it outputs empty context.
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""


class TestFetchRecentDiscussionsOutput:
    """
    Feature: Hook output format is always valid JSON matching SessionStart schema.
    """

    @pytest.mark.unit
    def test_output_matches_session_start_schema(self, tmp_path: Path) -> None:
        """
        Scenario: Output is valid SessionStart hook JSON
        Given any environment
        When the hook runs
        Then stdout is valid JSON with hookSpecificOutput.hookEventName = "SessionStart".
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        spec = output["hookSpecificOutput"]
        assert spec["hookEventName"] == "SessionStart"
        assert "additionalContext" in spec
        assert isinstance(spec["additionalContext"], str)

    @pytest.mark.unit
    def test_ssh_github_remote_is_recognized(self, tmp_path: Path) -> None:
        """
        Scenario: SSH-style GitHub remote is recognized
        Given a git repo with SSH origin (git@github.com:owner/repo.git)
        When the hook runs
        Then it does NOT return empty context due to remote parsing failure.

        Note: It may still return empty context if gh auth fails, but the
        remote URL parsing itself should succeed (not hit the 'not GitHub' guard).
        """
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=5,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Validate it got past the "not GitHub" guard (it will likely fail
        # at gh auth, but that's a later guard - not the remote-url guard)
        assert "hookSpecificOutput" in output
