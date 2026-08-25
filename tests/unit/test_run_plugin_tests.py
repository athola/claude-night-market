"""Tests for scripts/run-plugin-tests.sh threshold extraction.

The script reads coverage_threshold from [tool.nightmarket] in a
plugin's pyproject.toml using awk and passes it as --cov-fail-under
to pytest for full-suite runs.  These tests verify the awk command
produces the correct threshold value for representative pyproject.toml
configurations.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
SCRIPT = REPO_ROOT / "scripts" / "run-plugin-tests.sh"
WRAPPER = REPO_ROOT / "scripts" / "without-git-env.sh"

# The wrapper run-plugin-tests.sh must place before every test invocation.
# Committing from a linked worktree exports GIT_DIR/GIT_INDEX_FILE to hook
# subprocesses; test suites that spawn git in temp dirs then rewrite the real
# worktree index (issue #609).  Scrubbing at the invocation boundary keeps
# child git processes scoped to their own working directory.
#
# This used to be the literal `env -u GIT_DIR -u GIT_INDEX_FILE -u
# GIT_WORK_TREE`, repeated at every call site.  Naming the variables one by
# one is an allowlist against a category git populates at will: a commit from
# a linked worktree exports eight GIT_* variables, and that literal caught two
# of them.  The wrapper scrubs the prefix instead, so a variable git adds
# tomorrow is already handled, and it exists once so a fifth call site cannot
# forget a word of it.
SCRUB_WRAPPER = "scripts/without-git-env.sh"

# run-plugin-tests.sh resolves the wrapper once into this variable and every
# invocation goes through it.  The guard below asserts both halves: that the
# variable really points at the wrapper, and that nothing bypasses it.  Checking
# only the second half would pass a script whose constant pointed at `true`.
SCRUB_VAR = "$WITHOUT_GIT_ENV"

# Every GIT_* variable `git commit` exports to a hook from a linked worktree,
# as observed on git 2.43.  The point of the list is not that these eight are
# special: it is that the old three-name literal left six of them standing.
LEAKED_GIT_ENV = {
    "GIT_AUTHOR_DATE": "@1700000000 +0000",
    "GIT_AUTHOR_EMAIL": "leaked@example.com",
    "GIT_AUTHOR_NAME": "Leaked Author",
    "GIT_DIR": "/fake/.git",
    "GIT_EDITOR": ":",
    "GIT_EXEC_PATH": "/fake/libexec/git-core",
    "GIT_INDEX_FILE": "/fake/.git/index",
    "GIT_PREFIX": "some/subdir/",
    "GIT_WORK_TREE": "/fake",
}

# Awk program body: the same logic embedded in run-plugin-tests.sh.
# Reads coverage_threshold from the [tool.nightmarket] TOML section.
# Passed directly to subprocess.run (no shell quoting needed).
AWK_PROGRAM = r"""
/^\[tool\.nightmarket\]/ { in_nm=1; next }
/^\[/ { in_nm=0 }
in_nm && /^coverage_threshold[[:space:]]*=/ {
    split($0, a, "="); gsub(/[[:space:]]/, "", a[2]); print a[2]; exit
}
"""


def _run_awk(content: str, tmp_path: Path) -> str:
    """Write content to a temp pyproject.toml and run the awk command."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(content)
    result = subprocess.run(
        ["awk", AWK_PROGRAM, str(pyproject)],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class TestGitEnvScrub:
    """Feature: run-plugin-tests.sh scrubs leaked git env from test runs.

    As a developer committing from a linked worktree
    I want the pre-commit test hook to drop every GIT_* variable before
    spawning test suites
    So that tests which spawn git in temp directories cannot rewrite
    the real worktree index (issue #609: ~2,800 phantom staged
    deletions).
    """

    @pytest.mark.unit
    def test_scrub_variable_resolves_to_the_wrapper(self) -> None:
        """
        Scenario: the shared constant points at the real wrapper
        Given the run-plugin-tests.sh script on disk
        When its WITHOUT_GIT_ENV assignment is inspected
        Then it resolves to scripts/without-git-env.sh, which exists
        """
        assignment = re.search(
            rf'^WITHOUT_GIT_ENV=.*?/?{re.escape(SCRUB_WRAPPER)}"?$',
            SCRIPT.read_text(),
            re.MULTILINE,
        )
        assert assignment, (
            f"run-plugin-tests.sh must resolve {SCRUB_VAR} to {SCRUB_WRAPPER!r}; "
            "without this the bypass check below would pass a constant "
            "pointing anywhere at all."
        )
        assert WRAPPER.is_file(), f"{SCRUB_WRAPPER} is referenced but missing"
        assert os.access(WRAPPER, os.X_OK), f"{SCRUB_WRAPPER} is not executable"

    @pytest.mark.unit
    def test_every_test_invocation_scrubs_git_env(self) -> None:
        """
        Scenario: all make/pytest invocation lines go through the wrapper
        Given the run-plugin-tests.sh script on disk
        When each line that launches `make test` or `python -m pytest`
        is inspected
        Then every such line routes through the shared scrub variable

        This is the check that catches the fifth call site somebody adds in a
        hurry: a new `uv run python -m pytest` line that forgets the wrapper
        silently reintroduces issue #609, and it fails here instead.
        """
        lines = SCRIPT.read_text().splitlines()
        invocations = [
            line
            for line in lines
            if ("make test" in line or "python -m pytest" in line)
            and not line.lstrip().startswith("#")
        ]
        assert invocations, "expected test invocation lines in script"
        unscrubbed = [line for line in invocations if SCRUB_VAR not in line]
        assert not unscrubbed, (
            f"test invocations bypass the git env scrub ({SCRUB_VAR!r}): {unscrubbed}"
        )

    @pytest.mark.unit
    def test_failure_branch_shows_the_run_that_actually_failed(self) -> None:
        """
        Scenario: a plugin's quiet run fails and its output is preserved
        Given the failure branch captures the run into a temp file
        When the branch reports the failure
        Then it prints that file before removing it

        The branch re-runs the plugin verbosely to get detail, but a re-run
        is a different run. When the failure is intermittent the re-run
        passes, the captured output is deleted unread, and the only record
        of what broke is gone. Printing the captured file first means a
        transient failure still leaves evidence.
        """
        text = SCRIPT.read_text()
        # There is one failure branch per runner path (Makefile and pytest).
        # Each spans from its "Tests failed" report to the `rm -f` that
        # discards the capture. Checking only the first would let the second
        # keep discarding evidence.
        starts = [m.start() for m in re.finditer(r"Tests failed", text)]
        assert len(starts) >= 2, (
            f"expected a failure branch per runner path, found {len(starts)}"
        )

        silent = []
        for start in starts:
            end = text.index('rm -f "$temp_output"', start)
            if 'cat "$temp_output"' not in text[start:end]:
                silent.append(text[:start].count("\n") + 1)

        assert not silent, (
            f"failure branches at lines {silent} delete the captured output of "
            "the run that failed without printing it; an intermittent failure "
            "whose verbose re-run passes leaves no evidence at all"
        )

    @pytest.mark.unit
    def test_wrapper_removes_every_git_variable(self) -> None:
        """
        Scenario: the wrapper hides the whole GIT_* category from children
        Given a parent environment carrying every GIT_* variable that
        `git commit` exports to a hook in a linked worktree
        When a child process is launched behind the wrapper
        Then the child sees no GIT_* variable at all

        The old three-name literal passed a test that asked only about the
        three names it unset.  This asks the child what it can actually see,
        which is the question the leak turned on.
        """
        check = (
            "import os, sys; "
            "leaked = sorted(k for k in os.environ if k.startswith('GIT_')); "
            "print(' '.join(leaked)); "
            "sys.exit(1 if leaked else 0)"
        )
        result = subprocess.run(
            [str(WRAPPER), sys.executable, "-c", check],
            env={**os.environ, **LEAKED_GIT_ENV},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"git env leaked through the scrub wrapper: {result.stdout.strip()}"
        )

    @pytest.mark.unit
    def test_wrapper_runs_when_no_git_env_is_set(self) -> None:
        """
        Scenario: the wrapper is a no-op outside a git hook
        Given a parent environment with no GIT_* variable set
        When a command is launched behind the wrapper
        Then it runs normally and its exit status is preserved

        The wrapper runs under `set -u`, where an empty prefix expansion is
        the obvious way to abort every test run on a developer's machine.
        """
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        result = subprocess.run(
            [str(WRAPPER), sys.executable, "-c", "print('ran')"],
            env=clean_env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"wrapper failed with no GIT_* set: {result.stderr}"
        )
        assert result.stdout.strip() == "ran"

    @pytest.mark.unit
    def test_wrapper_propagates_child_exit_status(self) -> None:
        """
        Scenario: a failing suite behind the wrapper still fails the run
        Given a command that exits non-zero
        When it is launched behind the wrapper
        Then the wrapper exits with the same status

        A wrapper that swallowed the child's status would turn the test gate
        green for every plugin at once.
        """
        result = subprocess.run(
            [str(WRAPPER), sys.executable, "-c", "raise SystemExit(3)"],
            capture_output=True,
        )
        assert result.returncode == 3, (
            f"wrapper masked the child exit status: got {result.returncode}, want 3"
        )


class TestRunPluginTestsThresholdExtraction:
    """Feature: run-plugin-tests.sh reads coverage threshold from pyproject.toml.

    As a CI system
    I want the test runner to enforce the correct coverage threshold
    So that per-plugin thresholds are applied consistently without
    embedding them in pytest addopts (which would fail subset runs).
    """

    @pytest.mark.unit
    def test_reads_90_percent_threshold(self, tmp_path: Path) -> None:
        """
        Scenario: standard plugin with 90% coverage threshold
        Given a pyproject.toml with [tool.nightmarket] coverage_threshold = 90
        When the awk command extracts the threshold
        Then it returns "90"
        """
        content = textwrap.dedent("""\
            [tool.nightmarket]
            coverage_threshold = 90

            [tool.pytest.ini_options]
            addopts = ["-v", "--cov=src/pkg"]
        """)
        assert _run_awk(content, tmp_path) == "90"

    @pytest.mark.unit
    def test_reads_85_percent_threshold_for_gauntlet(self, tmp_path: Path) -> None:
        """
        Scenario: gauntlet plugin uses non-default 85% threshold
        Given a pyproject.toml with coverage_threshold = 85
        When the awk command extracts the threshold
        Then it returns "85"
        """
        content = textwrap.dedent("""\
            [tool.nightmarket]
            coverage_threshold = 85
        """)
        assert _run_awk(content, tmp_path) == "85"

    @pytest.mark.unit
    def test_returns_empty_when_section_absent(self, tmp_path: Path) -> None:
        """
        Scenario: plugin has no [tool.nightmarket] section
        Given a pyproject.toml without [tool.nightmarket]
        When the awk command runs
        Then it returns an empty string (no threshold enforced)
        """
        content = textwrap.dedent("""\
            [tool.pytest.ini_options]
            addopts = "-v --tb=short"
        """)
        assert _run_awk(content, tmp_path) == ""

    @pytest.mark.unit
    def test_ignores_other_tool_sections(self, tmp_path: Path) -> None:
        """
        Scenario: pyproject.toml has many [tool.*] sections
        Given content with [tool.ruff], [tool.mypy], and [tool.nightmarket]
        When the awk command extracts the threshold
        Then it reads only from [tool.nightmarket], ignoring others
        """
        content = textwrap.dedent("""\
            [tool.ruff]
            line-length = 88

            [tool.mypy]
            strict = true

            [tool.nightmarket]
            coverage_threshold = 90

            [tool.coverage.run]
            source = ["src"]
        """)
        assert _run_awk(content, tmp_path) == "90"

    @pytest.mark.unit
    def test_stops_at_first_match(self, tmp_path: Path) -> None:
        """
        Scenario: [tool.nightmarket] section has coverage_threshold followed by other keys
        Given a section with multiple keys
        When the awk command runs
        Then it returns the first coverage_threshold value and exits
        """
        content = textwrap.dedent("""\
            [tool.nightmarket]
            coverage_threshold = 90
            some_other_key = true
        """)
        assert _run_awk(content, tmp_path) == "90"

    @pytest.mark.unit
    def test_real_pensive_pyproject(self) -> None:
        """
        Scenario: pensive's actual pyproject.toml after migration
        Given the migrated pensive/pyproject.toml on disk
        When the awk command extracts the threshold
        Then it returns "90" (pensive uses standard 90% threshold)
        """
        pyproject = Path(__file__).parents[2] / "plugins" / "pensive" / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("pensive pyproject.toml not found")
        result = subprocess.run(
            ["awk", AWK_PROGRAM.strip(), str(pyproject)],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "90"

    @pytest.mark.unit
    def test_real_gauntlet_pyproject(self) -> None:
        """
        Scenario: gauntlet's actual pyproject.toml after migration preserves 85%
        Given the migrated gauntlet/pyproject.toml on disk
        When the awk command extracts the threshold
        Then it returns "85" (gauntlet has non-default threshold)
        """
        pyproject = (
            Path(__file__).parents[2] / "plugins" / "gauntlet" / "pyproject.toml"
        )
        if not pyproject.exists():
            pytest.skip("gauntlet pyproject.toml not found")
        result = subprocess.run(
            ["awk", AWK_PROGRAM.strip(), str(pyproject)],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "85"


def _fake_repo(tmp_path: Path) -> Path:
    """Build a throwaway repo the real runner will accept as its PROJECT_ROOT.

    The script resolves PROJECT_ROOT from its own location (``dirname $0/..``)
    and cds there, so a copy under ``tmp_path/scripts`` operates on
    ``tmp_path/plugins`` and touches nothing in the real tree. Exercising the
    script itself rather than a re-implementation of it is the point: a
    paraphrase of the dispatch logic would keep passing after the real dispatch
    broke.
    """
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("run-plugin-tests.sh", "without-git-env.sh"):
        target = scripts / name
        target.write_bytes((REPO_ROOT / "scripts" / name).read_bytes())
        target.chmod(0o755)
    (tmp_path / "plugins").mkdir()
    return tmp_path


def _add_plugin(repo: Path, name: str, *, manifest: bool = True) -> Path:
    """Create a plugin directory, with a manifest unless told otherwise."""
    plugin = repo / "plugins" / name
    plugin.mkdir(parents=True)
    if manifest:
        (plugin / "openpackage.yml").write_text(f"name: {name}\n")
    return plugin


def _run_all(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo / "scripts" / "run-plugin-tests.sh"), "--all"],
        capture_output=True,
        text=True,
        cwd=repo,
    )


class TestTestsWithoutConfigAreAFailure:
    """Feature: a plugin whose tests cannot run fails instead of being skipped.

    As a developer trusting `make test`
    I want a plugin that ships tests but no way to run them to fail the gate
    So that a suite nobody executes cannot be mistaken for a suite that passed.

    cartograph shipped 40 tests behind this hole. It had no pyproject.toml, so
    the runner's dispatch found neither a Makefile `test:` target nor a pytest
    config, printed "No test configuration", recorded a skip, and returned 0.
    `make test` stayed green for months while the plugin was tested nowhere.
    """

    @pytest.mark.unit
    def test_plugin_with_tests_but_no_config_fails(self, tmp_path: Path) -> None:
        """
        Scenario: tests present, no way to run them
        Given a plugin with a tests/ directory and no pyproject or Makefile
        When the runner is invoked
        Then it exits non-zero rather than reporting a skip

        This is the regression that hid cartograph's suite.
        """
        repo = _fake_repo(tmp_path)
        plugin = _add_plugin(repo, "broken")
        (plugin / "tests").mkdir()
        (plugin / "tests" / "test_thing.py").write_text("def test_thing(): pass\n")

        result = _run_all(repo)

        assert result.returncode != 0, (
            "A plugin with tests/ and no test configuration must fail the gate. "
            f"Runner exited 0.\n{result.stdout}"
        )
        assert "broken" in result.stdout

    @pytest.mark.unit
    def test_plugin_without_tests_is_still_a_clean_skip(self, tmp_path: Path) -> None:
        """
        Scenario: a plugin that genuinely ships no tests
        Given a plugin with no tests/ directory at all
        When the runner is invoked
        Then it exits 0 and records a skip

        The failure above must stay scoped to plugins that *have* tests. Many
        plugins are documentation and skills only, and turning those into hard
        failures would just be a broken gate in the other direction.
        """
        repo = _fake_repo(tmp_path)
        _add_plugin(repo, "docs-only")

        result = _run_all(repo)

        assert result.returncode == 0, result.stdout
        assert "Skipped" in result.stdout

    @pytest.mark.unit
    def test_non_plugin_directories_are_not_treated_as_plugins(
        self, tmp_path: Path
    ) -> None:
        """
        Scenario: a stray __pycache__ sits in plugins/
        Given plugins/__pycache__ left behind by a root-level pytest run
        When the runner is invoked
        Then it is not announced or counted as a plugin

        The bare plugins/*/ glob matched it, and the runner reported
        "Testing __pycache__...". A plugin is what carries a manifest.
        """
        repo = _fake_repo(tmp_path)
        _add_plugin(repo, "real")
        (repo / "plugins" / "__pycache__").mkdir()

        result = _run_all(repo)

        assert "__pycache__" not in result.stdout, (
            "plugins/__pycache__ is not a plugin and must not be iterated.\n"
            f"{result.stdout}"
        )
        assert "real" in result.stdout


class TestEmptyCoverageFlagUnderSetU:
    """Feature: a plugin with no coverage_threshold still runs its tests.

    bash 3.2, which is what macOS ships, treats an empty array as unset,
    so `"${cov_flag[@]}"` under `set -u` aborts the script with
    `cov_flag[@]: unbound variable` before pytest is ever invoked. Every
    plugin without a threshold -- cartograph among them -- reported
    "Tests failed" having run no tests. bash 4+ does not reproduce it,
    which is why it survived CI.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_empty_array_expansion_survives_set_u(self):
        expansions = re.findall(r"\$\{?cov_flag\[@\][^\n]{0,24}", SCRIPT.read_text())
        assert expansions, "cov_flag expansion disappeared; update this test"
        for expansion in expansions:
            assert expansion.startswith("${cov_flag[@]+"), (
                f"{expansion!r} aborts under `set -u` on bash 3.2; use the "
                '${cov_flag[@]+"${cov_flag[@]}"} guarded form'
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_guarded_form_expands_to_nothing_when_empty(self):
        script = 'set -u; cov_flag=(); set -- ${cov_flag[@]+"${cov_flag[@]}"}; echo $#'
        result = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "0"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_guarded_form_still_passes_a_set_threshold(self):
        script = (
            "set -u; cov_flag=(--cov-fail-under=85); "
            'set -- ${cov_flag[@]+"${cov_flag[@]}"}; echo "$# $1"'
        )
        result = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, check=False
        )
        assert result.stdout.strip() == "1 --cov-fail-under=85"
