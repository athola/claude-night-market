"""Tests for leyline SessionStart hook: fetch-recent-discussions.sh.

Feature: Fetch Recent Discussions Hook
  As a Claude Code user on a GitHub repository
  I want recent Decisions discussions injected into my session context
  So that I have cross-session awareness of architectural decisions

Guard conditions are tested by controlling the subprocess environment.
GraphQL calls go to a fake gh put on PATH, so no test reaches GitHub.
"""

from __future__ import annotations

import json
import os
import re
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
                if entry.get("command", "").strip('"').endswith(script_name):
                    return float(entry["timeout"])
    raise AssertionError(f"{script_name} is not registered in {HOOKS_MANIFEST}")


HOOK_TIMEOUT = declared_timeout("fetch-recent-discussions.sh")


def hook_network_budget() -> float:
    """TOTAL_BUDGET as the hook declares it, so the latency follows it."""
    match = re.search(
        r"^TOTAL_BUDGET = ([0-9.]+)$", HOOK_SCRIPT.read_text(), re.MULTILINE
    )
    assert match, "TOTAL_BUDGET not found in the hook"
    return float(match.group(1))


# A real `gh api graphql` round trip costs 1.2-1.6s (see the hook's own
# header). The fake gh sleeps 40% of the hook's network budget (1.4s at
# 3.5s), inside that range, and leaves the rest for its own interpreter
# start, which is what stretches on a loaded machine. A fixed 1.6s left
# the fake's start-up and the budget racing each other.
GH_ROUND_TRIP_SECONDS = hook_network_budget() * 0.4

# The fake answers every field the hook can ask for, so whichever query
# shape the hook sends, it reads its own fields out of one response.
_FAKE_GH = """#!{python}
import json
import sys
import time

with open({log!r}, "a") as calls:
    calls.write(" ".join(sys.argv[1:3]) + "\\n")
time.sleep({latency})
decision = {{
    "number": 7,
    "title": "Pin the harness version",
    "createdAt": "2026-10-01T00:00:00Z",
    "body": "Because the CLI moved.",
}}
insight = {{
    "number": 8,
    "title": "Hooks pay in processes",
    "createdAt": "2026-10-02T00:00:00Z",
    "body": "Start-up dominates.",
}}
repository = {{
    "hasDiscussionsEnabled": True,
    "discussionCategories": {{"nodes": [
        {{"id": "DIC_decisions", "slug": "decisions"}},
        {{"id": "DIC_insights", "slug": "insights"}},
    ]}},
    "recent": {{"nodes": [
        dict(decision, category={{"slug": "decisions"}}),
        dict(insight, category={{"slug": "insights"}}),
        {{"number": 9, "title": "Off topic", "createdAt": "2026-10-03T00:00:00Z",
          "body": "", "category": {{"slug": "general"}}}},
    ]}},
    "decisions": {{"nodes": [decision]}},
    "insights": {{"nodes": [insight]}},
}}
print(json.dumps({{"data": {{"repository": repository}}}}))
"""


def fake_gh_env(tmp_path: Path, env: dict[str, str], latency: float) -> dict[str, str]:
    """Put a gh on PATH that answers both of the hook's queries after a delay."""
    shim_dir = tmp_path / "fake-gh"
    shim_dir.mkdir()
    gh = shim_dir / "gh"
    gh.write_text(
        _FAKE_GH.format(
            python=sys.executable, latency=latency, log=str(shim_dir / "calls.log")
        )
    )
    gh.chmod(0o755)
    return {**env, "PATH": f"{shim_dir}{os.pathsep}{env['PATH']}"}


def shell_gh_env(tmp_path: Path, env: dict[str, str], body: str) -> dict[str, str]:
    """Put a /bin/sh gh running *body* first on PATH in a copy of *env*."""
    shim_dir = tmp_path / "shim"
    shim_dir.mkdir(exist_ok=True)
    gh = shim_dir / "gh"
    gh.write_text(f"#!/bin/sh\n{body}\n")
    gh.chmod(0o755)
    return {**env, "PATH": f"{shim_dir}{os.pathsep}{env['PATH']}"}


def github_checkout(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=False)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
        cwd=str(path),
        capture_output=True,
        check=False,
    )


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
        When the hook runs against a gh that answers
        Then the remote parses to owner/repo and the discussions render.

        A remote that failed to parse would stop at the "not GitHub" guard
        with empty context and never reach gh.
        """
        github_checkout(tmp_path)
        env = fake_gh_env(tmp_path, isolated_cache, latency=0)

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
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "#7 Pin the harness version" in context
        cache_dir = Path(isolated_cache["LEYLINE_CACHE_DIR"])
        assert (cache_dir / "discussions-owner__repo.json").is_file()


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
        """Scenario: a cold cache and a gh that never answers
        Given no cached summary and a gh call that stalls
        When the hook runs
        Then its own deadline ends the call and it still emits JSON
        inside the timeout hooks.json declares for it.
        """
        github_checkout(tmp_path)
        env = fake_gh_env(tmp_path, isolated_cache, latency=60)

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
        assert (
            json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] == ""
        )
        assert "gh timed out" in result.stderr

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
        (cache_dir / "discussions-owner__repo.json").write_text(
            json.dumps(cached, indent=2) + "\n", encoding="utf-8"
        )

        # A gh that records being called and then fails. If the cache path
        # is doing its job this file never appears.
        marker = tmp_path / "gh-was-called"
        env = shell_gh_env(
            tmp_path,
            {**os.environ, "LEYLINE_CACHE_DIR": str(cache_dir)},
            f'touch "{marker}"\nexit 1',
        )

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
    @pytest.mark.parametrize(
        "owner,repo,other",
        [("foo", "bar-baz", "foo-bar__baz"), ("foo-bar", "baz", "foo__bar-baz")],
    )
    def test_repos_differing_only_in_where_the_hyphen_falls_do_not_share_a_cache(
        self, tmp_path: Path, owner: str, repo: str, other: str
    ) -> None:
        """Scenario: foo/bar-baz and foo-bar/baz are different repositories
        Given a fresh cache for each of them
        When the hook runs in one
        Then it serves that repository's summary, not the other's.

        GitHub logins cannot contain an underscore, so a double underscore
        between owner and repo cannot be produced by either half.
        """
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True, check=False
        )
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                f"https://github.com/{owner}/{repo}.git",
            ],
            cwd=str(tmp_path),
            capture_output=True,
            check=False,
        )
        cache_dir = tmp_path / "leyline-cache"
        cache_dir.mkdir()

        def payload(name: str) -> dict[str, dict[str, str]]:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"summary for {name}",
                }
            }

        for key in (f"{owner}__{repo}", other):
            (cache_dir / f"discussions-{key}.json").write_text(
                json.dumps(payload(key)) + "\n", encoding="utf-8"
            )

        env = shell_gh_env(
            tmp_path, {**os.environ, "LEYLINE_CACHE_DIR": str(cache_dir)}, "exit 1"
        )

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
        assert json.loads(result.stdout) == payload(f"{owner}__{repo}")

    @pytest.mark.unit
    def test_hook_fits_its_cap_with_populated_discussions(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: a repository with Discussions enabled and populated
        Given a cold cache and a gh that charges a delay on every call
        When the hook resolves the categories and fetches the discussions
        Then it spends one `gh api graphql` round trip and renders both
        sections inside the timeout hooks.json declares.

        This is the case the old shape failed: 11.7-12.3s of `gh auth
        status`, three GraphQL round trips and five interpreter starts
        against a 3s cap. A repository with no discussions to fetch exits
        early and would not have caught it. The fake gh stands in for
        GitHub, so the run neither needs the network nor varies with it.
        """
        github_checkout(tmp_path)
        env = fake_gh_env(tmp_path, isolated_cache, latency=GH_ROUND_TRIP_SECONDS)

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
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert context.startswith("Recent Decisions (from GitHub Discussions):")
        assert "#7 Pin the harness version (2026-10-01)" in context
        assert "#8 Hooks pay in processes (2026-10-02)" in context
        assert "Off topic" not in context
        calls = (tmp_path / "fake-gh" / "calls.log").read_text().splitlines()
        assert calls == ["api graphql"]

    @pytest.mark.unit
    def test_known_category_ids_fetch_only_their_discussions(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: category ids cached, summary expired
        Given a categories cache from an earlier session
        When the hook runs with round-trip-length gh calls
        Then it spends one targeted round trip and renders both sections.
        """
        github_checkout(tmp_path)
        cache_dir = Path(isolated_cache["LEYLINE_CACHE_DIR"])
        cache_dir.mkdir()
        (cache_dir / "categories-owner__repo.txt").write_text(
            "DIC_decisions|DIC_insights\n"
        )
        env = fake_gh_env(tmp_path, isolated_cache, latency=GH_ROUND_TRIP_SECONDS)

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
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "#7 Pin the harness version" in context
        assert "#8 Hooks pay in processes" in context
        calls = (tmp_path / "fake-gh" / "calls.log").read_text().splitlines()
        assert calls == ["api graphql"]


class TestFetchRecentDiscussionsEmptyAnswer:
    """Feature: an answer carrying no data is a failed lookup, not a result."""

    @pytest.mark.unit
    @pytest.mark.parametrize("answer", ['{"data": null}', '{"data": {}}', "{}"])
    def test_cold_fetch_with_no_data_caches_nothing(
        self, tmp_path: Path, isolated_cache: dict[str, str], answer: str
    ) -> None:
        """Scenario: gh exits 0 with no errors and no data
        Given a cold cache
        When gh answers without a data payload
        Then the hook emits empty context and writes neither cache,
        so the next session retries instead of inheriting '-|-' for 7 days.
        """
        github_checkout(tmp_path)
        env = shell_gh_env(tmp_path, isolated_cache, f"printf '%s\\n' '{answer}'")

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
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert context == ""
        cache_dir = Path(isolated_cache["LEYLINE_CACHE_DIR"])
        assert not (cache_dir / "categories-owner__repo.txt").exists()
        assert not (cache_dir / "discussions-owner__repo.json").exists()

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "answer",
        [
            '{"data": {"repository": null}}',
            '{"data": {"repository": {"hasDiscussionsEnabled": false}}}',
        ],
        ids=["repository-null", "discussions-disabled"],
    )
    def test_cold_fetch_without_discussions_does_not_cache_category_ids(
        self, tmp_path: Path, isolated_cache: dict[str, str], answer: str
    ) -> None:
        """Scenario: the repository is missing or has Discussions off
        Given a cold cache
        When gh answers with no repository, or one with Discussions disabled
        Then the hook emits empty context and writes no categories cache,
        so enabling Discussions is seen next session rather than in 7 days.
        """
        github_checkout(tmp_path)
        env = shell_gh_env(tmp_path, isolated_cache, f"printf '%s\\n' '{answer}'")

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
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert context == ""
        cache_dir = Path(isolated_cache["LEYLINE_CACHE_DIR"])
        assert not (cache_dir / "categories-owner__repo.txt").exists()


def cold_window() -> int:
    """COLD_WINDOW as the hook declares it, so the test cannot drift from it."""
    match = re.search(r"^COLD_WINDOW = (\d+)$", HOOK_SCRIPT.read_text(), re.MULTILINE)
    assert match, "COLD_WINDOW not found in the hook"
    return int(match.group(1))


class TestFetchRecentDiscussionsColdWindow:
    """Feature: a cold answer is cached only when it is complete."""

    @pytest.mark.unit
    def test_full_cold_window_caches_category_ids_but_not_the_summary(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: the newest COLD_WINDOW discussions fill the window
        Given a cold cache and a gh returning exactly COLD_WINDOW discussions
        When the hook runs
        Then it renders what it found and stores the category ids,
        but writes no summary cache, because older decisions may sit past
        the window and the next run asks each category directly.
        """
        github_checkout(tmp_path)
        nodes = [
            {
                "number": n,
                "title": f"Decision {n}",
                "createdAt": "2026-10-01T00:00:00Z",
                "body": "",
                "category": {"slug": "decisions" if n == 1 else "general"},
            }
            for n in range(1, cold_window() + 1)
        ]
        answer = {
            "data": {
                "repository": {
                    "hasDiscussionsEnabled": True,
                    "discussionCategories": {
                        "nodes": [{"id": "DIC_decisions", "slug": "decisions"}]
                    },
                    "recent": {"nodes": nodes},
                }
            }
        }
        answer_file = tmp_path / "answer.json"
        answer_file.write_text(json.dumps(answer))
        env = shell_gh_env(tmp_path, isolated_cache, f"cat '{answer_file}'")

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
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "#1 Decision 1" in context
        cache_dir = Path(isolated_cache["LEYLINE_CACHE_DIR"])
        assert (cache_dir / "categories-owner__repo.txt").read_text() == (
            "DIC_decisions|-\n"
        )
        assert not (cache_dir / "discussions-owner__repo.json").exists()

    @pytest.mark.unit
    def test_cold_answer_short_of_the_window_caches_the_summary(
        self, tmp_path: Path, isolated_cache: dict[str, str]
    ) -> None:
        """Scenario: fewer than COLD_WINDOW discussions exist
        Given a cold cache and a gh returning three discussions
        When the hook runs
        Then the answer is complete and the summary cache is written.
        """
        github_checkout(tmp_path)
        env = fake_gh_env(tmp_path, isolated_cache, latency=0)

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
        cache_dir = Path(isolated_cache["LEYLINE_CACHE_DIR"])
        cached = json.loads((cache_dir / "discussions-owner__repo.json").read_text())
        assert cached == json.loads(result.stdout)
