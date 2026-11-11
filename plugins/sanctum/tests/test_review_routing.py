"""Tests for review_routing.py: who should review a PR outside its author's lane.

The script reads the history of each directory a change touches. An
author with no recent commits in a directory others work in is outside
their lane there, and the people who do work there are suggested by
name. CODEOWNERS rules come first, because GitHub already requests
those reviewers.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from review_routing import lanes, main, owners_for, parse_codeowners


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _commit_as(repo: Path, name: str, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        f"change {path}",
        f"--author={name} <{name.lower()}@example.invalid>",
    )


@pytest.fixture
def team_repo(tmp_path: Path) -> tuple[Path, str]:
    """Ana owns the UI, Ben and Cy own the core, and Ana has no core commits."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "check@example.invalid")
    _git(repo, "config", "user.name", "Check")
    _commit_as(repo, "Ana", "app/ui/view.py", "v = 1\n")
    _commit_as(repo, "Ben", "app/core/logic.py", "x = 1\n")
    _commit_as(repo, "Ben", "app/core/logic.py", "x = 2\n")
    _commit_as(repo, "Cy", "app/core/rules.py", "r = 1\n")
    base = _git(repo, "rev-parse", "HEAD")
    return repo, base


class TestLanes:
    def test_author_with_history_in_the_directory_is_inside_their_lane(
        self, team_repo: tuple[Path, str]
    ) -> None:
        """GIVEN Ana has committed to app/ui before
        WHEN she changes app/ui again
        THEN no reviewer is suggested for it.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/ui/view.py", "v = 2\n")
        (lane,) = lanes(repo, base)
        assert lane.directory == "app/ui"
        assert not lane.outside
        assert lane.reviewers == []

    def test_author_new_to_a_worked_directory_gets_its_regulars_suggested(
        self, team_repo: tuple[Path, str]
    ) -> None:
        """GIVEN Ana has never committed to app/core, and Ben and Cy have
        WHEN Ana changes app/core
        THEN she is outside her lane, and Ben comes before Cy by commits.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        (lane,) = lanes(repo, base)
        assert lane.outside
        assert lane.reviewers == ["Ben", "Cy"]

    def test_a_directory_with_no_history_suggests_nobody(
        self, team_repo: tuple[Path, str]
    ) -> None:
        """GIVEN a directory nobody has committed to
        WHEN Ana adds the first file to it
        THEN it is not flagged, because there is nobody to ask.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/net/socket.py", "s = 1\n")
        (lane,) = lanes(repo, base)
        assert lane.directory == "app/net"
        assert not lane.outside

    def test_the_change_itself_does_not_count_as_history(
        self, team_repo: tuple[Path, str]
    ) -> None:
        """GIVEN Ana makes two commits to app/core in the same change
        WHEN the lane is computed against the base
        THEN her commits in the change do not put her inside the lane.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 4\n")
        (lane,) = lanes(repo, base)
        assert lane.outside

    def test_codeowners_rule_replaces_the_history_suggestion(
        self, team_repo: tuple[Path, str]
    ) -> None:
        """GIVEN CODEOWNERS assigns app/core to a team
        WHEN Ana changes app/core
        THEN the owners are reported and no history suggestion is made.
        """
        repo, base = team_repo
        (repo / ".github").mkdir()
        (repo / ".github" / "CODEOWNERS").write_text("/app/core/ @org/core\n")
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        lane = next(lane for lane in lanes(repo, base) if lane.directory == "app/core")
        assert lane.owners == ["@org/core"]
        assert lane.reviewers == []


class TestCodeowners:
    def test_last_matching_rule_wins(self) -> None:
        """GIVEN a broad rule followed by a narrower one
        WHEN a path matches both
        THEN the later rule's owners apply, as GitHub resolves them.
        """
        rules = parse_codeowners("* @all\n/app/ui/ @design\n# comment\n")
        assert owners_for("app/ui/view.py", rules) == ["@design"]
        assert owners_for("app/core/logic.py", rules) == ["@all"]

    def test_unanchored_pattern_matches_at_any_depth(self) -> None:
        """GIVEN a pattern without a leading slash
        WHEN a nested path ends in it
        THEN it matches, as a gitignore-style pattern does.
        """
        rules = parse_codeowners("*.swift @ios\n")
        assert owners_for("app/ui/View.swift", rules) == ["@ios"]
        assert owners_for("app/ui/view.py", rules) == []


class TestMain:
    def test_output_names_people_and_never_their_email(
        self, team_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN an outside-lane change
        WHEN the report is printed for a PR description
        THEN it names reviewers, and no email address appears.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        assert main(["--repo", str(repo), "--base", base]) == 0
        out = capsys.readouterr().out
        assert "app/core" in out and "Ben" in out
        assert "@example.invalid" not in out

    def test_json_output_lists_each_lane(
        self, team_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN --json
        WHEN the report is printed
        THEN it parses, with one entry per touched directory.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        main(["--repo", str(repo), "--base", base, "--json"])
        report = json.loads(capsys.readouterr().out)
        assert [entry["directory"] for entry in report] == ["app/core"]

    def test_a_change_inside_every_lane_says_so(
        self, team_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a change only inside the author's lanes
        WHEN the report is printed
        THEN it states that no extra reviewer is needed.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "app/ui/view.py", "v = 2\n")
        main(["--repo", str(repo), "--base", base])
        assert "inside the author's lanes" in capsys.readouterr().out


class TestCodeownersForms:
    """The pattern forms GitHub accepts beyond the two above."""

    def test_unanchored_directory_pattern_matches_at_any_depth(self) -> None:
        """GIVEN a directory pattern without a leading slash
        WHEN a nested path sits under a directory of that name
        THEN it matches.
        """
        rules = parse_codeowners("ui/ @design\n")
        assert owners_for("app/ui/view.py", rules) == ["@design"]
        assert owners_for("app/core/logic.py", rules) == []

    def test_anchored_file_pattern_matches_only_from_the_root(self) -> None:
        """GIVEN an anchored file pattern
        WHEN the same file name sits deeper in another tree
        THEN only the rooted path matches.
        """
        rules = parse_codeowners("/app/core/logic.py @ben\n")
        assert owners_for("app/core/logic.py", rules) == ["@ben"]
        assert owners_for("vendor/app/core/logic.py", rules) == []

    def test_a_later_rule_without_owners_clears_earlier_ones(self) -> None:
        """GIVEN a catch-all owner and a later ownerless rule
        WHEN a path matches the ownerless rule
        THEN it has no owner, as GitHub reads it.
        """
        rules = parse_codeowners("* @all\n/vendor/\n")
        assert owners_for("vendor/lib.py", rules) == []


class TestMainPaths:
    """Entry-point paths the PR flow depends on."""

    def test_codeowners_routing_is_printed_for_the_who_row(
        self, team_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN CODEOWNERS covers the changed directory
        WHEN the report is printed
        THEN it says GitHub's owners will be requested.
        """
        repo, base = team_repo
        (repo / "CODEOWNERS").write_text("/app/core/ @org/core\n")
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        main(["--repo", str(repo), "--base", base])
        assert "CODEOWNERS requests @org/core" in capsys.readouterr().out

    def test_base_defaults_to_origins_head_branch(
        self, team_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN origin/HEAD points at the base commit and no --base is given
        WHEN the report runs
        THEN it measures against that branch.
        """
        repo, base = team_repo
        _git(repo, "update-ref", "refs/remotes/origin/main", base)
        _git(
            repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"
        )
        _commit_as(repo, "Ana", "app/core/logic.py", "x = 3\n")
        assert main(["--repo", str(repo)]) == 0
        assert "Ask Ben or Cy" in capsys.readouterr().out

    def test_an_unknown_base_exits_2_and_names_it(
        self, team_repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """GIVEN a base git cannot resolve
        WHEN the report runs
        THEN it exits 2 naming the base, not with a traceback.
        """
        repo, _ = team_repo
        assert main(["--repo", str(repo), "--base", "no-such-ref"]) == 2
        assert "no-such-ref" in capsys.readouterr().err

    def test_a_root_level_file_is_its_own_lane(
        self, team_repo: tuple[Path, str]
    ) -> None:
        """GIVEN a change to a file at the repository root
        WHEN lanes are computed
        THEN it is reported under the root directory.
        """
        repo, base = team_repo
        _commit_as(repo, "Ana", "README.md", "hi\n")
        assert [lane.directory for lane in lanes(repo, base)] == ["."]
