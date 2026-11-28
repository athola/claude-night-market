"""The git pre-commit re-check catches index changes the PreToolUse gate cannot see.

The PreToolUse gate reads the index before the Bash command runs, so
``git add -A && git commit``, ``commit -a`` and ``commit <pathspec>`` are
gated against the old index (#1172 NB1). git's own pre-commit hook runs
against the index being committed, and compares it with the one the gate
let through.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import git_index_recheck
import precommit_gate
import pytest

from tests.conftest import fake_git

_HOOK = Path(git_index_recheck.__file__)
_AGENT_ENV = {"CLAUDECODE": "1"}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Build a git repo with one commit and a .gauntlet dir in gate mode."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "dev@example.com")
    _git(tmp_path, "config", "user.name", "Dev")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "a.py").write_text("x = 1\n")
    _git(tmp_path, "add", "a.py")
    _git(tmp_path, "commit", "-q", "-m", "init")
    gauntlet_dir = tmp_path / ".gauntlet"
    (gauntlet_dir / "state").mkdir(parents=True)
    (gauntlet_dir / "config.json").write_text(json.dumps({"precommit": {}}))
    return tmp_path


def _stage_hash(repo: Path) -> str:
    return precommit_gate._hash_stage_listing(_git(repo, "ls-files", "--stage"))


def _record_now(repo: Path) -> None:
    precommit_gate.record_gated_index(repo / ".gauntlet", _stage_hash(repo))


def _record_path(repo: Path) -> Path:
    return repo / ".gauntlet" / "state" / "gated_index.json"


@pytest.mark.unit
class TestRecheck:
    """recheck() refuses only an agent commit of an index the gate never saw."""

    def test_refuses_when_index_changed_after_the_gate_checked_it(
        self, repo: Path
    ) -> None:
        _record_now(repo)
        (repo / "b.py").write_text("y = 2\n")
        _git(repo, "add", "b.py")

        refusal = git_index_recheck.recheck(repo, _AGENT_ENV)

        assert refusal is not None
        assert "separate" in refusal

    def test_passes_when_index_matches_the_gated_record(self, repo: Path) -> None:
        (repo / "b.py").write_text("y = 2\n")
        _git(repo, "add", "b.py")
        _record_now(repo)

        assert git_index_recheck.recheck(repo, _AGENT_ENV) is None

    def test_record_is_consumed_by_the_check(self, repo: Path) -> None:
        _record_now(repo)

        git_index_recheck.recheck(repo, _AGENT_ENV)

        assert not _record_path(repo).exists()

    def test_passes_when_no_gate_record_exists(self, repo: Path) -> None:
        (repo / "b.py").write_text("y = 2\n")
        _git(repo, "add", "b.py")

        assert git_index_recheck.recheck(repo, _AGENT_ENV) is None

    def test_unreadable_record_refuses(self, repo: Path) -> None:
        _record_path(repo).write_text("{not json")

        assert git_index_recheck.recheck(repo, _AGENT_ENV) is not None

    def test_human_commit_outside_claude_code_is_not_checked(self, repo: Path) -> None:
        _record_now(repo)
        (repo / "b.py").write_text("y = 2\n")
        _git(repo, "add", "b.py")

        assert git_index_recheck.recheck(repo, {}) is None

    def test_mode_off_by_env_is_not_checked(self, repo: Path) -> None:
        _record_now(repo)
        (repo / "b.py").write_text("y = 2\n")
        _git(repo, "add", "b.py")
        env = {**_AGENT_ENV, "GAUNTLET_PRECOMMIT_MODE": "off"}

        assert git_index_recheck.recheck(repo, env) is None

    @pytest.mark.parametrize("mode", ["nudge", "off"])
    def test_non_gate_config_mode_is_not_checked(self, repo: Path, mode: str) -> None:
        (repo / ".gauntlet" / "config.json").write_text(
            json.dumps({"precommit": {"mode": mode}})
        )
        _record_now(repo)
        (repo / "b.py").write_text("y = 2\n")
        _git(repo, "add", "b.py")

        assert git_index_recheck.recheck(repo, _AGENT_ENV) is None

    def test_repo_without_gauntlet_dir_is_not_checked(self, tmp_path: Path) -> None:
        _git(tmp_path, "init", "-q")

        assert git_index_recheck.recheck(tmp_path, _AGENT_ENV) is None


@pytest.mark.unit
class TestGateRecordsWhatItLetThrough:
    """main() writes the record on each path that lets a gate-mode commit run."""

    def _hook_input(self) -> dict[str, object]:
        return {"tool_input": {"command": "git add -A && git commit -m x"}}

    def test_records_the_index_on_a_token_pass(self, tmp_gauntlet_dir: Path) -> None:
        with (
            patch.object(
                precommit_gate, "_get_gauntlet_dir", return_value=tmp_gauntlet_dir
            ),
            patch("precommit_gate.subprocess.run", side_effect=fake_git(["a.py"])),
        ):
            staged_hash = precommit_gate._get_staged_hash()
            precommit_gate.write_pass_token(tmp_gauntlet_dir, staged_hash)
            assert precommit_gate.main(self._hook_input()) is None

        record = json.loads(
            (tmp_gauntlet_dir / "state" / "gated_index.json").read_text()
        )
        assert record["staged_hash"] == staged_hash

    def test_records_the_clean_index_when_nothing_is_staged(
        self, tmp_gauntlet_dir: Path
    ) -> None:
        with (
            patch.object(
                precommit_gate, "_get_gauntlet_dir", return_value=tmp_gauntlet_dir
            ),
            patch("precommit_gate.subprocess.run", side_effect=fake_git([])),
        ):
            assert precommit_gate.main(self._hook_input()) is None

        assert (tmp_gauntlet_dir / "state" / "gated_index.json").exists()

    def test_nudge_mode_writes_no_record(self, tmp_gauntlet_dir: Path) -> None:
        (tmp_gauntlet_dir / "config.json").write_text(
            json.dumps({"precommit": {"mode": "nudge"}})
        )
        with (
            patch.object(
                precommit_gate, "_get_gauntlet_dir", return_value=tmp_gauntlet_dir
            ),
            patch("precommit_gate.subprocess.run", side_effect=fake_git([])),
        ):
            precommit_gate.main(self._hook_input())

        assert not (tmp_gauntlet_dir / "state" / "gated_index.json").exists()


@pytest.mark.unit
class TestInstall:
    """install() wires the re-check into git without clobbering a hook."""

    def test_writes_an_executable_pre_commit_hook(self, repo: Path) -> None:
        assert git_index_recheck.install(repo) == 0

        hook = repo / ".git" / "hooks" / "pre-commit"
        assert os.access(hook, os.X_OK)
        assert str(_HOOK) in hook.read_text()

    def test_installed_hook_refuses_add_and_commit_in_one_command(
        self, repo: Path
    ) -> None:
        git_index_recheck.install(repo)
        _record_now(repo)
        (repo / "b.py").write_text("y = 2\n")

        commit = subprocess.run(
            ["sh", "-c", "git add -A && git commit -q -m sneak"],
            cwd=repo,
            env={**os.environ, **_AGENT_ENV},
            capture_output=True,
            text=True,
        )

        assert commit.returncode != 0
        assert "gauntlet" in commit.stderr
        assert _git(repo, "log", "--oneline").count("\n") == 1

    def test_leaves_an_existing_hook_alone(self, repo: Path) -> None:
        hook = repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nmake lint\n")

        assert git_index_recheck.install(repo) == 1
        assert hook.read_text() == "#!/bin/sh\nmake lint\n"

    def test_second_install_is_a_no_op(self, repo: Path) -> None:
        git_index_recheck.install(repo)
        first = (repo / ".git" / "hooks" / "pre-commit").read_text()

        assert git_index_recheck.install(repo) == 0
        assert (repo / ".git" / "hooks" / "pre-commit").read_text() == first


@pytest.mark.unit
class TestGateDeniesWhenTheIndexCannotBeRead:
    """An unreadable index is never recorded as the gated one."""

    def test_empty_hash_denies_and_records_nothing(
        self, tmp_gauntlet_dir: Path
    ) -> None:
        with (
            patch.object(
                precommit_gate, "_get_gauntlet_dir", return_value=tmp_gauntlet_dir
            ),
            patch.object(precommit_gate, "_get_staged_hash", return_value=""),
        ):
            precommit_gate.write_pass_token(tmp_gauntlet_dir, "")
            decision = precommit_gate.main(
                {"tool_input": {"command": "git commit -m x"}}
            )

        assert decision is not None
        output = decision["hookSpecificOutput"]
        assert output["permissionDecision"] == "deny"
        assert "unable to read" in output["permissionDecisionReason"]
        assert not (tmp_gauntlet_dir / "state" / "gated_index.json").exists()
