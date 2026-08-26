"""Guard that every plugin test suite is reachable from CI.

Until `plugin-tests.yml` existed, no workflow ran a plugin's own
`tests/` directory. `ecosystem-tests.yml` runs the root suite and
`python39-compat.yml` runs the hook subset for hook-registering plugins,
so roughly 13,900 tests were gated only by the pre-commit hook on a
contributor's machine, where a bash 3.2 bug had them reporting failure
without running at all.

The matrix is discovered at run time rather than listed, so coverage
cannot drift the way a static list would. What can still drift is the
discovery step itself, and three properties the suites depend on:

- Each job runs from the plugin directory. memory-palace and gauntlet
  resolve conftest and package imports against their own pyproject and
  fail collection when pytest runs from the repository root.
- Coverage is left on. archetypes and cartograph do not depend on
  pytest-cov, so `--no-cov` is an unrecognized argument there, and the
  plugins that do set their own thresholds.
- The path filter covers `plugins/**`. A filter narrower than the sweep
  reports success by not running, which is the failure this repository
  already documents in `test_ci_covers_ecosystem_gates.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "plugin-tests.yml"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


@pytest.fixture(scope="module")
def suite_job(workflow: dict) -> dict:
    return workflow["jobs"]["plugin-suite"]


@pytest.fixture(scope="module")
def pytest_step(suite_job: dict) -> dict:
    return next(
        step for step in suite_job["steps"] if "pytest" in str(step.get("run", ""))
    )


def _plugins_with_tests() -> set[str]:
    return {
        path.parent.name for path in REPO_ROOT.glob("plugins/*/tests") if path.is_dir()
    }


def test_the_workflow_exists() -> None:
    assert WORKFLOW.is_file(), f"{WORKFLOW} is the only gate on plugin suites"


def test_there_are_plugin_suites_to_run() -> None:
    """A green run over an empty set is the failure this file prevents."""
    assert len(_plugins_with_tests()) > 1


def test_matrix_is_discovered_not_listed(suite_job: dict) -> None:
    """A hand-written list would need its own drift gate."""
    matrix = suite_job["strategy"]["matrix"]["plugin"]
    assert "fromJSON" in str(matrix), (
        "the plugin matrix is hardcoded; either discover it or add a test "
        "deriving the list from plugins/*/tests"
    )


def test_discovery_finds_every_plugin_suite(workflow: dict) -> None:
    """The discovery glob must reach every plugin that has tests."""
    discover = workflow["jobs"]["discover"]
    listing = next(step for step in discover["steps"] if step.get("id") == "list")
    command = listing["run"]
    assert "plugins" in command and "-name tests" in command, (
        "discovery no longer enumerates plugins/*/tests"
    )
    # -maxdepth 2 from `plugins` is what reaches plugins/<name>/tests and
    # stops before a nested tests directory inside a plugin's src tree.
    assert "-maxdepth 2" in command


def test_each_suite_runs_from_its_plugin_directory(pytest_step: dict) -> None:
    working_directory = pytest_step.get("working-directory", "")
    assert "plugins/" in working_directory, (
        "the suite must run from the plugin directory; from the repo root "
        "memory-palace and gauntlet fail collection"
    )


def test_optional_dependency_extras_are_installed(pytest_step: dict) -> None:
    """`uv run` skips optional-dependencies, and two plugins keep pytest there.

    A PEP 735 `[dependency-groups] dev` is installed by default; a
    `[project.optional-dependencies] dev` is not. leyline and phantom use
    the second form, so without `--all-extras` their jobs die on "No
    module named pytest". It does not reproduce locally, where a
    repo-root `.venv` already carries pytest from an earlier run, which
    is why the first CI run is what found it.
    """
    assert "--all-extras" in pytest_step["run"]


def test_coverage_is_not_disabled(pytest_step: dict) -> None:
    assert "--no-cov" not in pytest_step["run"], (
        "archetypes and cartograph do not depend on pytest-cov, so --no-cov "
        "is an unrecognized argument and fails the run outright"
    )


@pytest.mark.parametrize("trigger", ["push", "pull_request"])
def test_path_filter_covers_every_plugin_file(workflow: dict, trigger: str) -> None:
    """A filter narrower than the sweep succeeds by not running."""
    # PyYAML reads a bare `on:` key as the boolean True.
    triggers = workflow.get("on") or workflow[True]
    paths = triggers[trigger]["paths"]
    assert "plugins/**" in paths, (
        f"{trigger} filter is {paths}; anything narrower than plugins/** "
        "lets an edit skip the suite that covers it"
    )
