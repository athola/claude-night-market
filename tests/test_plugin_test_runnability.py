"""Guard that every plugin's tests actually run under ``make test``.

Two separate silences let ``cartograph`` ship four test files that no gate ever
executed. Each has its own test below.

**The runner skips what it cannot dispatch.**
``scripts/run-plugin-tests.sh`` looks for a Makefile with a ``test:`` target or
a ``pyproject.toml`` mentioning pytest. A plugin with neither reaches the final
branch, which prints "No test configuration", records a skip, and returns 0. A
plugin whose tests never ran is then indistinguishable from one that passed.
``archetypes`` hit this in 58ee533f; ``cartograph`` was the last plugin left.

**The repo-root config hides nested plugin tests.**
The root ``pyproject.toml`` sets ``norecursedirs = ["plugins/*"]`` so a
root-level run does not vacuum up plugin suites. A plugin that owns no pytest
config inherits that setting, because pytest walks upward for a config file and
finds the root's. ``norecursedirs`` blocks *recursion into* a directory, while a
directory named directly on the command line is always collected: a plugin whose
tests sit flat in ``tests/`` survives, and one whose tests sit in ``tests/unit/``
collects zero items and exits quietly. Layout alone decided which plugins were
tested, which is why this is pinned rather than left to luck.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

# The runner iterates ``plugins/*/``, so anything sitting there is treated as a
# plugin, including a stray ``__pycache__``. A plugin is what carries a manifest.
PLUGIN_MANIFESTS = (".claude-plugin/plugin.json", "openpackage.yml")


def _is_plugin(path: Path) -> bool:
    """True when ``path`` carries a plugin manifest."""
    return any((path / manifest).exists() for manifest in PLUGIN_MANIFESTS)


def _plugin_dirs() -> list[Path]:
    """Every real plugin directory, manifest-identified rather than globbed."""
    return sorted(p for p in PLUGINS_DIR.iterdir() if p.is_dir() and _is_plugin(p))


def _plugins_with_tests() -> list[Path]:
    return [p for p in _plugin_dirs() if (p / "tests").is_dir()]


def _has_runnable_test_config(plugin: Path) -> bool:
    """Mirror the runner's dispatch: a Makefile ``test:`` target, or pytest.

    Deliberately in lockstep with ``run_plugin_tests`` in
    ``scripts/run-plugin-tests.sh``. If the runner learns a third way to
    discover tests, this predicate has to learn it too, or the gate goes quiet
    again.
    """
    makefile = plugin / "Makefile"
    if makefile.exists() and re.search(
        r"^test:", makefile.read_text(encoding="utf-8"), re.MULTILINE
    ):
        return True

    pyproject = plugin / "pyproject.toml"
    return pyproject.exists() and "pytest" in pyproject.read_text(encoding="utf-8")


def _owns_pytest_config(plugin: Path) -> bool:
    """True when the plugin's pyproject has a real ``[tool.pytest.ini_options]``.

    Parsed, not grepped. An earlier version of this check searched the file for
    the literal table name and was satisfied by ``archetypes``, whose pyproject
    mentions the table only in a comment explaining that it has none. A
    substring match cannot tell configuration from prose.
    """
    pyproject = plugin / "pyproject.toml"
    if not pyproject.exists():
        return False
    with pyproject.open("rb") as handle:
        config = tomllib.load(handle)
    return "ini_options" in config.get("tool", {}).get("pytest", {})


def _has_nested_tests(plugin: Path) -> bool:
    """True when any test file sits below ``tests/`` rather than directly in it.

    This is the layout that ``norecursedirs`` silences for a plugin with no
    pytest config of its own.
    """
    tests_dir = plugin / "tests"
    return any(
        path.parent != tests_dir
        for path in tests_dir.rglob("test_*.py")
        if "__pycache__" not in path.parts
    )


def test_discovery_finds_the_plugins() -> None:
    """Sanity check: a bug in ``_is_plugin`` would make every gate below vacuous.

    An empty parametrize list is a silently passing test suite, which is the
    exact failure mode this module exists to prevent.
    """
    assert len(_plugins_with_tests()) > 1


def test_root_config_still_excludes_plugin_dirs() -> None:
    """Pin the premise that ``test_nested_tests_require_own_pytest_config`` rests on.

    That gate is only meaningful while the root config excludes ``plugins/*``
    from recursion. If this assertion ever fails, the root config changed and
    the reasoning below needs revisiting rather than blind trust.
    """
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        root_config = tomllib.load(handle)

    norecursedirs = root_config["tool"]["pytest"]["ini_options"]["norecursedirs"]
    assert "plugins/*" in norecursedirs


@pytest.mark.parametrize("plugin", _plugins_with_tests(), ids=lambda p: p.name)
def test_plugin_with_tests_has_runnable_config(plugin: Path) -> None:
    """A plugin with a ``tests/`` directory must be runnable by the gate."""
    assert _has_runnable_test_config(plugin), (
        f"{plugin.name} has a tests/ directory but neither a Makefile with a "
        f"'test:' target nor a pyproject.toml configuring pytest. "
        f"scripts/run-plugin-tests.sh skips it and still exits 0, so its tests "
        f"never run in any gate."
    )


def _plugins_with_nested_tests() -> list[Path]:
    """The plugins the check below actually applies to.

    Filtering here rather than skipping inside the test keeps the run free of
    five permanent skips, and pairs with the discovery assertion below. A
    runtime skip reports the same "s" whether the plugin genuinely keeps its
    tests flat or ``_has_nested_tests`` has stopped working, and this file
    exists to catch checks that go quiet.
    """
    return [p for p in _plugins_with_tests() if _has_nested_tests(p)]


def test_nested_test_discovery_is_not_empty() -> None:
    """Guard the guard: an empty list would make the check below vacuous."""
    assert _plugins_with_nested_tests(), (
        "No plugin was detected as keeping tests below tests/. Either every "
        "plugin was flattened, or _has_nested_tests stopped matching. Until "
        "this list is non-empty the pytest-config check asserts nothing."
    )


@pytest.mark.parametrize("plugin", _plugins_with_nested_tests(), ids=lambda p: p.name)
def test_nested_tests_require_own_pytest_config(plugin: Path) -> None:
    """Tests below ``tests/`` need a local pytest config to be collected at all.

    Without one, pytest resolves rootdir to the repo root, whose
    ``norecursedirs = ["plugins/*"]`` stops it descending into ``tests/unit/``.
    Collection yields zero items and the run exits without complaint.
    """
    assert _owns_pytest_config(plugin), (
        f"{plugin.name} keeps test files in subdirectories of tests/ but has no "
        f"[tool.pytest.ini_options] table, so pytest resolves rootdir to the "
        f"repo root and norecursedirs = ['plugins/*'] blocks recursion into "
        f"them. Collection returns zero tests and the run still exits 0."
    )
