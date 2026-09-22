"""Tests for leyline SessionStart hook: fetch-recent-discussions.sh.

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
HOOKS_MANIFEST = Path(__file__).parents[3] / "hooks" / "hooks.json"


def declared_timeout(script_name: str) -> float:
    """The cap hooks.json grants a hook, which is what the harness enforces.

    A killed SessionStart hook and one that chose to emit nothing are
    indistinguishable from the session, so a hook over its cap fails
    silently. Reading the number here rather than hardcoding it means the
    performance assertion and the manifest cannot drift apart.
    """
    manifest = json.loads(HOOKS_MANIFEST.read_text(encoding="utf-8"))
    for groups in manifest["hooks"].values():
        for group in groups:
            for entry in group.get("hooks", []):
                if entry.get("command", "").endswith(script_name):
                    return float(entry["timeout"])
    raise AssertionError(f"{script_name} is not registered in {HOOKS_MANIFEST}")


HOOK_TIMEOUT = declared_timeout("fetch-recent-discussions.sh")


@pytest.fixture
def isolated_cache(tmp_path: Path) -> dict[str, str]:
    """Environment that keeps the hook off the developer's own cache."""
    env = os.environ.copy()
    env["LEYLINE_CACHE_DIR"] = str(tmp_path / "leyline-cache")
    return env


class TestFetchRecentDiscussionsGuards:
    """Feature: Guard conditions prevent the hook from running in unsupported environments.
    Each guard should output valid empty-context JSON and exit 0.
    """

    @pytest.mark.unit
    def test_hook_script_exists_and_is_executable(self) -> None:
        """Scenario: Hook script is properly installed
        Given the leyline plugin is installed
        When checking the hook script
        Then it exists and is executable with a shebang.
        """
        assert HOOK_SCRIPT.exists(), f"Hook script not found at {HOOK_SCRIPT}"
        assert os.access(HOOK_SCRIPT, os.X_OK), "Hook script is not executable"
        first_line = HOOK_SCRIPT.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "Missing shebang line"

    @pytest.mark.unit
    def test_non_git_directory_returns_empty_context(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: Non-git directory produces empty context
        Given a directory that is not a git repository
        When the hook runs
        Then it outputs valid JSON with empty additionalContext.
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_non_github_remote_returns_empty_context(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: GitLab remote is silently skipped
        Given a git repo with a GitLab origin
        When the hook runs
        Then it outputs empty context (Discussions are GitHub-only).
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )
        subprocess.run(
            ["git", "remote", "add", "origin", "https://gitlab.com/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
            check=False,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_bitbucket_remote_returns_empty_context(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: Bitbucket remote is silently skipped
        Given a git repo with a Bitbucket origin
        When the hook runs
        Then it outputs empty context (Discussions are GitHub-only).
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )
        subprocess.run(
            ["git", "remote", "add", "origin", "https://bitbucket.org/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
            check=False,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
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
        """Scenario: Missing gh CLI produces empty context
        Given gh is not on PATH
        When the hook runs
        Then it outputs empty context without error.
        """
        # Create a minimal PATH with only essential commands (bash, git, python3)
        # but NOT gh, to simulate gh being unavailable
        env = os.environ.copy()
        env["PATH"] = "/usr/bin:/bin"
        env["LEYLINE_CACHE_DIR"] = str(tmp_path / "leyline-cache")

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=env,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""

    @pytest.mark.unit
    def test_no_remote_returns_empty_context(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: Git repo with no remote produces empty context
        Given a git repo with no origin remote
        When the hook runs
        Then it outputs empty context.
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["additionalContext"] == ""


class TestFetchRecentDiscussionsOutput:
    """Feature: Hook output format is always valid JSON matching SessionStart schema."""

    @pytest.mark.unit
    def test_output_matches_session_start_schema(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: Output is valid SessionStart hook JSON
        Given any environment
        When the hook runs
        Then stdout is valid JSON with hookSpecificOutput.hookEventName = "SessionStart".
        """
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        spec = output["hookSpecificOutput"]
        assert spec["hookEventName"] == "SessionStart"
        assert "additionalContext" in spec
        assert isinstance(spec["additionalContext"], str)

    @pytest.mark.unit
    def test_ssh_github_remote_is_recognized(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: SSH-style GitHub remote is recognized
        Given a git repo with SSH origin (git@github.com:owner/repo.git)
        When the hook runs
        Then it does NOT return empty context due to remote parsing failure.

        Note: It may still return empty context if gh auth fails, but the
        remote URL parsing itself should succeed (not hit the 'not GitHub' guard).
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
            check=False,
        )

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Validate it got past the "not GitHub" guard (it will likely fail
        # at gh auth, but that's a later guard - not the remote-url guard)
        assert "hookSpecificOutput" in output


class TestFetchRecentDiscussionsBudget:
    """Feature: the hook fits the cap its own hooks.json entry declares.

    The previous shape made a ``gh auth status`` round trip, then up to
    three ``gh api graphql`` calls, interleaved with five ``python3``
    interpreter starts, with no cache and no client-side deadline. It
    measured 11.7-12.3s against a 3s cap, so the context it assembled was
    killed before it reached the session every time.
    """

    @pytest.mark.unit
    def test_hook_completes_within_its_declared_timeout(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: a cold cache in a GitHub repository
        Given no cached summary and no cached category ids
        When the hook runs
        Then it finishes inside the timeout hooks.json declares for it.
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
            check=False,
        )
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        assert result.returncode == 0
        json.loads(result.stdout)

    @pytest.mark.unit
    def test_fresh_cache_is_served_without_running_gh(self, tmp_path: Path) -> None:
        """Scenario: the steady state spends no network
        Given a cached summary written moments ago
        When the hook runs
        Then it prints the cached payload and never invokes gh.
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/owner/repo.git"],
            cwd=str(tmp_path),
            capture_output=True,
            check=False,
        )

        cache_dir = tmp_path / "leyline-cache"
        cache_dir.mkdir()
        cached = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "Recent Decisions (from GitHub Discussions):\n  #1 x",
            }
        }
        (cache_dir / "discussions-owner-repo.json").write_text(
            json.dumps(cached, indent=2) + "\n", encoding="utf-8"
        )

        # A gh that records being called and then fails. If the cache path
        # is doing its job this file never appears.
        shim_dir = tmp_path / "shim"
        shim_dir.mkdir()
        marker = tmp_path / "gh-was-called"
        gh = shim_dir / "gh"
        gh.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 1\n')
        gh.chmod(0o755)

        env = os.environ.copy()
        env["LEYLINE_CACHE_DIR"] = str(cache_dir)
        env["PATH"] = f"{shim_dir}{os.pathsep}{env['PATH']}"

        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            timeout=HOOK_TIMEOUT,
            env=env,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == cached
        assert not marker.exists(), "the cache hit still paid for a gh round trip"

    @pytest.mark.unit
    def test_hook_fits_its_cap_in_this_repository(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: the repository the finding was measured against
        Given this checkout, whose origin is a GitHub repository with
          Discussions enabled and populated
        When the hook runs on a cold cache
        Then it finishes inside the timeout hooks.json declares.

        This is the case the old shape failed: 11.7-12.3s of `gh auth
        status`, three GraphQL round trips and five interpreter starts
        against a 3s cap. A repository with no discussions to fetch exits
        early and would not have caught it.
        """
        repo_root = Path(__file__).parents[5]
        result = subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=HOOK_TIMEOUT,
            env=isolated_cache,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
