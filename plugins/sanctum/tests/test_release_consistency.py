"""Filesystem-walking release-consistency tests.

These tests scan the actual on-disk plugin tree (rather than
hardcoded fixtures) so a real version drift across the
ecosystem fails CI before it ships.

Closes the gaps flagged by the /pr-review-toolkit pass on PR
#446 (release 1.9.3):

- The 15-site `find commands/ -maxdepth 1 -name '*.md'` fix
  shipped without a regression test, so a future revert would
  silently restore the 46-vs-19 sanctum drift.
- `test_pyproject_version_consistency_is_blocking` only checks
  hardcoded fixture data (`{"pensive": "1.3.7", ...}`) so it
  cannot fail when real plugin manifests drift.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# Find the repository root by walking up from this test file.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PLUGINS_DIR = _REPO_ROOT / "plugins"


def _all_plugin_dirs() -> list[Path]:
    """Return every plugin directory that has a plugin.json."""
    return sorted(
        p.parent.parent for p in _PLUGINS_DIR.glob("*/.claude-plugin/plugin.json")
    )


def _load_plugin_json(plugin_dir: Path) -> dict:
    return json.loads((plugin_dir / ".claude-plugin" / "plugin.json").read_text())


def _read_pyproject_version(plugin_dir: Path) -> str | None:
    pyproject = plugin_dir / "pyproject.toml"
    if not pyproject.exists():
        return None
    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        pyproject.read_text(),
        flags=re.MULTILINE,
    )
    return match.group(1) if match else None


class TestPluginVersionConsistency:
    """
    Feature: every plugin.json version agrees with the others
    and with its sibling pyproject.toml.

    The legacy `test_pyproject_version_consistency_is_blocking`
    in test_pr_review_workflow.py only checks a hardcoded dict;
    these tests walk the actual filesystem.
    """

    @pytest.mark.unit
    def test_all_plugin_json_versions_agree(self) -> None:
        """Scenario: all 23 plugin.json files report the same version.

        The release process bumps every plugin in lockstep. A
        single stale plugin.json indicates the version-bump
        script missed a file or a manual edit drifted.
        """
        versions = {
            plugin_dir.name: _load_plugin_json(plugin_dir)["version"]
            for plugin_dir in _all_plugin_dirs()
        }

        unique = set(versions.values())
        assert len(unique) == 1, (
            f"plugin.json version drift across the ecosystem: {versions}"
        )

    @pytest.mark.unit
    def test_pyproject_version_matches_plugin_json(self) -> None:
        """Scenario: each plugin's pyproject.toml matches its plugin.json.

        Plugins that ship a Python package have both a
        plugin.json and a pyproject.toml; the two versions must
        not drift. (Plugins without pyproject.toml are skipped.)
        """
        mismatches = []
        for plugin_dir in _all_plugin_dirs():
            pj_version = _load_plugin_json(plugin_dir)["version"]
            pyproject_version = _read_pyproject_version(plugin_dir)
            if pyproject_version is None:
                continue
            if pyproject_version != pj_version:
                mismatches.append((plugin_dir.name, pj_version, pyproject_version))

        assert not mismatches, (
            "pyproject.toml ↔ plugin.json version drift "
            f"(plugin, plugin.json, pyproject.toml): {mismatches}"
        )


class TestMakefileCommandCount:
    """
    Feature: per-plugin Makefile `make status` reports the
    same command count as plugin.json.commands.

    Regression: the `find commands/ -name '*.md'` pattern (no
    -maxdepth) counted modular command sub-files (e.g.
    sanctum's fix-pr-modules/) as separate slash commands and
    reported 46 commands for sanctum (canonical 19) and 155
    total (canonical 128).
    """

    @pytest.mark.unit
    def test_makefile_find_invocations_use_maxdepth_one(self) -> None:
        """Scenario: every `find commands/ ... *.md` uses -maxdepth 1.

        Static check: catches new Makefiles that omit the
        flag before they cause count drift.
        """
        offenders: list[tuple[Path, int, str]] = []
        find_pattern = re.compile(
            r"find\s+commands/\s+(?!.*-maxdepth\s+1).*-name\s+['\"]\*\.md['\"]"
        )
        for makefile in _PLUGINS_DIR.glob("*/Makefile"):
            for lineno, line in enumerate(makefile.read_text().splitlines(), start=1):
                if find_pattern.search(line):
                    offenders.append((makefile, lineno, line.strip()))

        assert not offenders, (
            "Makefiles counting commands/*.md without -maxdepth 1 "
            "(would over-count modular command sub-files): "
            f"{offenders}"
        )

    @pytest.mark.unit
    def test_top_level_command_md_count_matches_plugin_json(self) -> None:
        """Scenario: top-level commands/*.md count matches registered commands.

        For each plugin with a commands/ directory, the
        number of top-level *.md files must equal
        len(plugin.json.commands).
        """
        mismatches = []
        for plugin_dir in _all_plugin_dirs():
            commands_dir = plugin_dir / "commands"
            if not commands_dir.is_dir():
                continue
            top_level_md = sorted(commands_dir.glob("*.md"))
            registered = _load_plugin_json(plugin_dir).get("commands", []) or []
            if len(top_level_md) != len(registered):
                mismatches.append(
                    (
                        plugin_dir.name,
                        len(top_level_md),
                        len(registered),
                    )
                )

        assert not mismatches, (
            "Top-level commands/*.md count differs from "
            "plugin.json.commands.length (plugin, on-disk, registered): "
            f"{mismatches}"
        )
