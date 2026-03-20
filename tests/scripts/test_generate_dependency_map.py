"""Tests for plugin dependency map generator.

Unit tests use synthetic temp directories to test scan functions
in isolation. Integration tests run the full script via subprocess
against the real repo.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path("scripts/generate_dependency_map.py")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Import script functions for unit testing
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from generate_dependency_map import (  # noqa: E402
    find_plugins,
    generate_map,
    scan_makefile_deps,
    scan_pyproject_deps,
    scan_python_imports,
)

# ── Fixtures ────────────────────────────────────────────


@pytest.fixture(scope="module")
def full_map_output() -> dict:
    """Run the script once, share parsed output across tests."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--stdout"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture()
def plugin_tree(tmp_path: Path) -> Path:
    """Create a minimal plugin directory tree for unit tests.

    Layout:
      plugins/
        alpha/
          .claude-plugin/plugin.json
          Makefile  (includes beta via BETA_DIR)
        beta/
          .claude-plugin/plugin.json
          Makefile  (no cross-deps)
          pyproject.toml  (depends on alpha)
        gamma/
          .claude-plugin/plugin.json
          src/gamma/core.py  (imports beta)
        not-a-plugin/
          README.md  (no plugin.json, should be ignored)
    """
    plugins = tmp_path / "plugins"
    plugins.mkdir()

    # alpha: Makefile with variable pointing to beta
    alpha = plugins / "alpha"
    alpha.mkdir()
    (alpha / ".claude-plugin").mkdir()
    (alpha / ".claude-plugin" / "plugin.json").write_text("{}")
    (alpha / "Makefile").write_text(
        "BETA_DIR := ../beta\n-include $(BETA_DIR)/config/shared.mk\n"
    )

    # beta: pyproject.toml depending on alpha
    beta = plugins / "beta"
    beta.mkdir()
    (beta / ".claude-plugin").mkdir()
    (beta / ".claude-plugin" / "plugin.json").write_text("{}")
    (beta / "Makefile").write_text(".PHONY: test\ntest:\n\techo ok\n")
    (beta / "pyproject.toml").write_text(
        '[project]\nname = "beta"\ndependencies = [\n  "alpha>=1.0",\n]\n'
    )

    # gamma: Python import of beta
    gamma = plugins / "gamma"
    gamma.mkdir()
    (gamma / ".claude-plugin").mkdir()
    (gamma / ".claude-plugin" / "plugin.json").write_text("{}")
    src = gamma / "src" / "gamma"
    src.mkdir(parents=True)
    (src / "core.py").write_text("from beta import something\n")

    # not-a-plugin: no .claude-plugin/plugin.json
    nap = plugins / "not-a-plugin"
    nap.mkdir()
    (nap / "README.md").write_text("not a plugin")

    return plugins


# ── Unit Tests: find_plugins ────────────────────────────


class TestFindPlugins:
    """Unit tests for plugin directory discovery."""

    def test_finds_dirs_with_plugin_json(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given dirs with plugin.json, when finding plugins,
        then return their names sorted."""
        result = find_plugins(plugin_tree)
        assert result == ["alpha", "beta", "gamma"]

    def test_ignores_dirs_without_plugin_json(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given a dir without plugin.json, when finding plugins,
        then skip it."""
        result = find_plugins(plugin_tree)
        assert "not-a-plugin" not in result

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        """Given an empty plugins dir, when finding plugins,
        then return empty list."""
        empty = tmp_path / "plugins"
        empty.mkdir()
        assert find_plugins(empty) == []


# ── Unit Tests: scan_makefile_deps ──────────────────────


class TestScanMakefileDeps:
    """Unit tests for Makefile dependency scanning."""

    def test_detects_variable_assignment(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given Makefile with BETA_DIR := ../beta,
        when scanned, then detect beta as build dep."""
        deps = scan_makefile_deps(
            plugin_tree / "alpha",
            ["alpha", "beta", "gamma"],
        )
        plugin_names = [d["plugin"] for d in deps]
        assert "beta" in plugin_names

    def test_dep_type_is_build(self, plugin_tree: Path) -> None:
        """Given a Makefile dep, when scanned,
        then type should be 'build'."""
        deps = scan_makefile_deps(
            plugin_tree / "alpha",
            ["alpha", "beta", "gamma"],
        )
        assert all(d["type"] == "build" for d in deps)

    def test_no_makefile_returns_empty(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given a plugin with no Makefile,
        when scanned, then return empty."""
        deps = scan_makefile_deps(
            plugin_tree / "gamma",
            ["alpha", "beta", "gamma"],
        )
        assert deps == []

    def test_ignores_non_plugin_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Given Makefile referencing unknown dir,
        when scanned, then ignore it."""
        p = tmp_path / "test-plugin"
        p.mkdir()
        (p / "Makefile").write_text("FOO_DIR := ../nonexistent\n")
        deps = scan_makefile_deps(p, ["alpha", "beta"])
        assert deps == []

    def test_deduplicates_same_plugin(
        self,
        tmp_path: Path,
    ) -> None:
        """Given Makefile with multiple refs to same plugin,
        when scanned, then deduplicate."""
        p = tmp_path / "test-plugin"
        p.mkdir()
        (p / "Makefile").write_text(
            "BETA_DIR := ../beta\n-include ../beta/config/other.mk\n"
        )
        deps = scan_makefile_deps(p, ["beta"])
        assert len(deps) == 1


# ── Unit Tests: scan_pyproject_deps ─────────────────────


class TestScanPyprojectDeps:
    """Unit tests for pyproject.toml dependency scanning."""

    def test_detects_dependency(self, plugin_tree: Path) -> None:
        """Given pyproject.toml with alpha dep,
        when scanned, then detect alpha as runtime dep."""
        deps = scan_pyproject_deps(
            plugin_tree / "beta",
            ["alpha", "beta", "gamma"],
        )
        plugin_names = [d["plugin"] for d in deps]
        assert "alpha" in plugin_names

    def test_dep_type_is_runtime(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given a pyproject dep, when scanned,
        then type should be 'runtime'."""
        deps = scan_pyproject_deps(
            plugin_tree / "beta",
            ["alpha", "beta", "gamma"],
        )
        assert all(d["type"] == "runtime" for d in deps)

    def test_skips_self_references(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given pyproject that mentions own name,
        when scanned, then skip self."""
        deps = scan_pyproject_deps(
            plugin_tree / "beta",
            ["alpha", "beta", "gamma"],
        )
        plugin_names = [d["plugin"] for d in deps]
        assert "beta" not in plugin_names

    def test_no_pyproject_returns_empty(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given a plugin with no pyproject.toml,
        when scanned, then return empty."""
        deps = scan_pyproject_deps(
            plugin_tree / "alpha",
            ["alpha", "beta", "gamma"],
        )
        assert deps == []


# ── Unit Tests: scan_python_imports ─────────────────────


class TestScanPythonImports:
    """Unit tests for Python import scanning."""

    def test_detects_from_import(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given Python file with 'from beta import ...',
        when scanned, then detect beta as runtime dep."""
        deps = scan_python_imports(
            plugin_tree / "gamma",
            "gamma",
            ["alpha", "beta", "gamma"],
        )
        plugin_names = [d["plugin"] for d in deps]
        assert "beta" in plugin_names

    def test_skips_self_imports(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given Python file in gamma,
        when scanned, then skip gamma imports."""
        deps = scan_python_imports(
            plugin_tree / "gamma",
            "gamma",
            ["alpha", "beta", "gamma"],
        )
        plugin_names = [d["plugin"] for d in deps]
        assert "gamma" not in plugin_names

    def test_no_src_returns_empty(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given a plugin with no src/ or scripts/,
        when scanned, then return empty."""
        deps = scan_python_imports(
            plugin_tree / "alpha",
            "alpha",
            ["alpha", "beta", "gamma"],
        )
        assert deps == []

    def test_handles_hyphenated_names(
        self,
        tmp_path: Path,
    ) -> None:
        """Given a plugin named my-plugin,
        when Python imports my_plugin, then detect it."""
        plugins = tmp_path / "plugins"
        p = plugins / "consumer"
        (p / "src" / "consumer").mkdir(parents=True)
        (p / "src" / "consumer" / "app.py").write_text("from my_plugin import util\n")
        deps = scan_python_imports(
            p,
            "consumer",
            ["consumer", "my-plugin"],
        )
        plugin_names = [d["plugin"] for d in deps]
        assert "my-plugin" in plugin_names


# ── Unit Tests: generate_map ────────────────────────────


class TestGenerateMap:
    """Unit tests for full map generation with synthetic data."""

    def test_map_has_required_keys(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given a plugin tree, when generating map,
        then output has version, generated, dependencies,
        reverse_index."""
        result = generate_map(plugin_tree)
        assert "version" in result
        assert "generated" in result
        assert "dependencies" in result
        assert "reverse_index" in result

    def test_forward_deps_track_dependents(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given beta is depended on by gamma (Python import),
        when generating map, then beta appears in dependencies
        with gamma as a dependent."""
        result = generate_map(plugin_tree)
        assert "beta" in result["dependencies"], (
            "beta should appear in dependencies since gamma depends on it"
        )
        dependents = result["dependencies"]["beta"]["dependents"]
        assert "gamma" in dependents or dependents == ["*"]

    def test_wildcard_when_all_depend(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given alpha is depended on by beta (pyproject)
        and beta is depended on by alpha (Makefile) and gamma,
        when both depend on a plugin, check wildcard logic."""
        result = generate_map(plugin_tree)
        # beta has deps from both alpha (Makefile) and gamma
        # (Python import). If all non-self plugins depend on
        # beta, it gets ["*"].
        for plugin, info in result["dependencies"].items():
            if info["dependents"] == ["*"]:
                # Verify it truly is depended on by all others
                all_others = [p for p in find_plugins(plugin_tree) if p != plugin]
                reverse_deps = [
                    p for p, deps in result["reverse_index"].items() if plugin in deps
                ]
                assert set(reverse_deps) == set(all_others)

    def test_reverse_index_excludes_empty(
        self,
        plugin_tree: Path,
    ) -> None:
        """Given some plugins with no deps,
        when generating map, then exclude them from
        reverse_index."""
        result = generate_map(plugin_tree)
        for deps in result["reverse_index"].values():
            assert len(deps) > 0


# ── Integration Tests ───────────────────────────────────


class TestDependencyMapIntegration:
    """Integration tests running the full script against the repo."""

    def test_script_runs_successfully(
        self,
        full_map_output: dict,
    ) -> None:
        """Given the script exists, when run, then exit 0
        and produce valid output."""
        assert "version" in full_map_output

    def test_output_is_valid_json(
        self,
        full_map_output: dict,
    ) -> None:
        """Given the script runs, when output captured,
        then it is valid JSON with required keys."""
        assert "version" in full_map_output
        assert "dependencies" in full_map_output
        assert "reverse_index" in full_map_output

    def test_abstract_is_universal_dependency(
        self,
        full_map_output: dict,
    ) -> None:
        """Given abstract provides Make includes to all,
        when map generated, then abstract has wildcard."""
        assert "abstract" in full_map_output["dependencies"]
        assert full_map_output["dependencies"]["abstract"]["dependents"] == ["*"]

    def test_conjure_depends_on_leyline(
        self,
        full_map_output: dict,
    ) -> None:
        """Given conjure optionally imports leyline,
        when map generated, then reverse_index shows it."""
        assert "leyline" in full_map_output["reverse_index"].get(
            "conjure",
            [],
        )

    def test_all_plugins_in_reverse_index(
        self,
        full_map_output: dict,
    ) -> None:
        """Given 17 plugins exist, when map generated,
        then all non-abstract plugins appear in reverse_index."""
        assert len(full_map_output["reverse_index"]) >= 16

    def test_output_flag_writes_file(self, tmp_path: Path) -> None:
        """Given --output flag, when run,
        then write JSON to specified path."""
        out_file = tmp_path / "deps.json"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output",
                str(out_file),
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, result.stderr
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "version" in data
