"""Tests for scripts/run-plugin-typecheck.sh plugin selection.

Feature: the pre-commit typecheck covers what a commit can break
  As a contributor committing a change to one plugin
  I want only that plugin type checked, unless the commit changes
  configuration every plugin's typecheck reads
  So that a one-plugin commit does not pay for all 23 while typecheck.yml
  still gates the full set on every pull request

The fixture plugins carry a manifest and nothing else, so the script
reports each one as "No type checking configuration" without starting
uv or make, and the Skipped summary line names exactly what it selected.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parents[2]
WRAPPER = REPO_ROOT / "scripts" / "without-git-env.sh"

needs_uv_and_make = pytest.mark.skipif(
    not (shutil.which("uv") and shutil.which("make")),
    reason="run-plugin-typecheck.sh depchecks uv and make",
)


def _git(repo: Path, *args: str) -> None:
    # Behind the wrapper so a GIT_DIR leaked by a pre-commit run cannot
    # point these commands at the real worktree (issue #609).
    subprocess.run(
        [str(WRAPPER), "git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _fake_repo(tmp_path: Path, plugins: tuple[str, ...]) -> Path:
    """A committed repo whose scripts/ copy resolves PROJECT_ROOT to it."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("run-plugin-typecheck.sh", "logging.sh"):
        target = scripts / name
        target.write_bytes((REPO_ROOT / "scripts" / name).read_bytes())
        target.chmod(0o755)
    for name in plugins:
        manifest = tmp_path / "plugins" / name / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(f'{{"name": "{name}"}}\n', encoding="utf-8")
        (manifest.parent.parent / "README.md").write_text("x\n", encoding="utf-8")
    make_dir = tmp_path / "plugins" / "abstract" / "config" / "make"
    make_dir.mkdir(parents=True)
    (make_dir / "common.mk").write_text("X := 1\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def _stage_edit(repo: Path, path: str) -> None:
    target = repo / path
    # A comment line is inert in every staged file type used here.
    target.write_text(target.read_text(encoding="utf-8") + "# edit\n", encoding="utf-8")
    _git(repo, "add", path)


def _run_changed(repo: Path) -> str:
    outcome = subprocess.run(
        [str(WRAPPER), str(repo / "scripts" / "run-plugin-typecheck.sh"), "--changed"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr
    return outcome.stdout + outcome.stderr


PLUGINS = ("abstract", "alpha", "beta")


@needs_uv_and_make
class TestChangedSelection:
    @pytest.mark.unit
    def test_typecheck_changed_checks_only_the_staged_plugin(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: a commit touches one plugin
        Given plugins abstract, alpha and beta
        When only a file in alpha is staged
        Then only alpha is selected
        """
        repo = _fake_repo(tmp_path, PLUGINS)
        _stage_edit(repo, "plugins/alpha/README.md")

        assert "Skipped (1): alpha" in _run_changed(repo)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "shared",
        [
            "pyproject.toml",
            "plugins/abstract/config/make/common.mk",
            "scripts/run-plugin-typecheck.sh",
        ],
    )
    def test_typecheck_changed_falls_back_to_all_on_shared_config(
        self, tmp_path: Path, shared: str
    ) -> None:
        """
        Scenario: a commit changes configuration every plugin reads
        Given the root pyproject.toml, a shared make include, or the
        script itself is staged
        When the script runs with --changed
        Then every plugin is selected, not only the one owning the file

        The shared make include sits inside abstract, so without the
        fallback it would select abstract alone while changing how mypy
        runs for every make-based plugin.
        """
        repo = _fake_repo(tmp_path, PLUGINS)
        _stage_edit(repo, shared)

        assert "Skipped (3): abstract alpha beta" in _run_changed(repo)

    @pytest.mark.unit
    def test_typecheck_changed_without_plugin_changes_selects_nothing(
        self, tmp_path: Path
    ) -> None:
        repo = _fake_repo(tmp_path, PLUGINS)
        (repo / "notes.txt").write_text("x\n", encoding="utf-8")
        _git(repo, "add", "notes.txt")

        assert "No plugin changes detected" in _run_changed(repo)


def _run_named(repo: Path, plugin: str) -> str:
    outcome = subprocess.run(
        [str(WRAPPER), str(repo / "scripts" / "run-plugin-typecheck.sh"), plugin],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return outcome.stdout + outcome.stderr


@needs_uv_and_make
class TestMakefileTargetProbe:
    """The probe reads make's rule database, so an included target counts.

    A name listed only in .PHONY also prints as ``typecheck:`` there, with
    no prerequisites and no recipe. Behind a catch-all it would then pass
    while checking nothing.
    """

    def _plugin_with_include(self, tmp_path: Path, included: str) -> Path:
        repo = _fake_repo(tmp_path, ("alpha",))
        plugin = repo / "plugins" / "alpha"
        (plugin / "Makefile").write_text("include extra.mk\n", encoding="utf-8")
        (plugin / "extra.mk").write_text(included, encoding="utf-8")
        return repo

    @pytest.mark.unit
    def test_target_named_only_in_phony_is_not_a_typecheck_target(
        self, tmp_path: Path
    ) -> None:
        repo = self._plugin_with_include(tmp_path, ".PHONY: typecheck\n%:\n\t@true\n")
        assert "No type checking configuration" in _run_named(repo, "alpha")

    @pytest.mark.unit
    def test_included_target_with_a_recipe_is_run(self, tmp_path: Path) -> None:
        repo = self._plugin_with_include(
            tmp_path, ".PHONY: typecheck\ntypecheck:\n\t@echo ran-typecheck\n"
        )
        assert "ran-typecheck" in _run_named(repo, "alpha")

    @pytest.mark.unit
    def test_included_target_with_only_prerequisites_is_run(
        self, tmp_path: Path
    ) -> None:
        repo = self._plugin_with_include(
            tmp_path,
            ".PHONY: typecheck types\ntypecheck: types\ntypes:\n\t@echo ran-types\n",
        )
        assert "ran-types" in _run_named(repo, "alpha")


def test_precommit_typecheck_hook_runs_changed_plugins() -> None:
    """The per-commit hook selects; typecheck.yml gates the full set on PRs."""
    config = yaml.safe_load(
        (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    hook = next(
        h
        for repo in config["repos"]
        for h in repo["hooks"]
        if h["id"] == "run-plugin-typecheck"
    )
    assert hook["entry"].endswith("--changed")
    # A root-pyproject-only commit must fire the hook, or the fallback
    # to --all can never run.
    assert re.search(hook["files"], "pyproject.toml")
    assert re.search(hook["files"], "plugins/abstract/config/make/common.mk")
