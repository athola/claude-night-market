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

        GIVEN every plugin.json in the plugins tree
        WHEN I collect their version fields
        THEN exactly one unique version exists,
        AND a single stale plugin.json (bump script missed a file
        or a manual edit drifted) fails the run
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

        GIVEN a plugin that ships both plugin.json and pyproject.toml
        WHEN I compare the two version fields
        THEN they agree,
        AND plugins without pyproject.toml are skipped
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


class TestVersionBumpFanOut:
    """
    Feature: every version-bearing file the release bump
    rewrites agrees with its plugin.json.

    The bump fans out to openpackage.yml, metadata.json,
    src/<pkg>/__init__.py, the root marketplace.json, and the
    CHANGELOG release heading. TestPluginVersionConsistency
    only guards plugin.json and pyproject.toml, so a bump
    script that silently skips one of the other surfaces
    would ship a partial release undetected.
    """

    @pytest.mark.unit
    def test_openpackage_version_matches_plugin_json(self) -> None:
        """Scenario: each plugin's openpackage.yml matches its plugin.json.

        GIVEN a plugin that ships an openpackage.yml
        WHEN I compare its top-level `version:` line with plugin.json
        THEN the two versions agree
        AND plugins without the file are skipped
        """
        mismatches = []
        for plugin_dir in _all_plugin_dirs():
            openpackage = plugin_dir / "openpackage.yml"
            if not openpackage.exists():
                continue
            match = re.search(
                r"^version:\s*(\S+)",
                openpackage.read_text(),
                flags=re.MULTILINE,
            )
            op_version = match.group(1).strip("\"'") if match else None
            pj_version = _load_plugin_json(plugin_dir)["version"]
            if op_version != pj_version:
                mismatches.append((plugin_dir.name, pj_version, op_version))

        assert not mismatches, (
            "openpackage.yml ↔ plugin.json version drift "
            f"(plugin, plugin.json, openpackage.yml): {mismatches}"
        )

    @pytest.mark.unit
    def test_metadata_json_version_matches_plugin_json(self) -> None:
        """Scenario: each plugin's metadata.json matches its plugin.json.

        GIVEN a plugin whose .claude-plugin/metadata.json carries a
        version field
        WHEN I compare it with the plugin.json version
        THEN the two versions agree
        (Plugins without the file, and metadata schemas that carry no
        version field at all — e.g. tome's — are skipped.)
        """
        mismatches = []
        for plugin_dir in _all_plugin_dirs():
            metadata_path = plugin_dir / ".claude-plugin" / "metadata.json"
            if not metadata_path.exists():
                continue
            md_version = json.loads(metadata_path.read_text()).get("version")
            if md_version is None:
                continue
            pj_version = _load_plugin_json(plugin_dir)["version"]
            if md_version != pj_version:
                mismatches.append((plugin_dir.name, pj_version, md_version))

        assert not mismatches, (
            "metadata.json ↔ plugin.json version drift "
            f"(plugin, plugin.json, metadata.json): {mismatches}"
        )

    @pytest.mark.unit
    def test_package_dunder_version_matches_plugin_json(self) -> None:
        """Scenario: each src package __version__ matches its plugin.json.

        GIVEN a plugin shipping a Python package with `__version__`
        in src/<pkg>/__init__.py
        WHEN I compare that attribute with the plugin.json version
        THEN the two versions agree
        AND packages without the attribute are skipped
        """
        mismatches = []
        for plugin_dir in _all_plugin_dirs():
            pj_version = _load_plugin_json(plugin_dir)["version"]
            for init_py in plugin_dir.glob("src/*/__init__.py"):
                match = re.search(
                    r'^__version__\s*=\s*"([^"]+)"',
                    init_py.read_text(),
                    flags=re.MULTILINE,
                )
                if match is None:
                    continue
                if match.group(1) != pj_version:
                    mismatches.append((plugin_dir.name, pj_version, match.group(1)))

        assert not mismatches, (
            "src/<pkg>/__init__.py __version__ ↔ plugin.json drift "
            f"(plugin, plugin.json, __version__): {mismatches}"
        )

    @pytest.mark.unit
    def test_marketplace_versions_match_plugin_json(self) -> None:
        """Scenario: every marketplace.json entry matches its plugin.json.

        GIVEN the root .claude-plugin/marketplace.json plugin list
        WHEN I compare each entry's version with that plugin's manifest
        THEN every plugin on disk has an entry AND the versions agree
        """
        marketplace = json.loads(
            (_REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text()
        )
        market_versions = {
            entry["name"]: entry.get("version") for entry in marketplace["plugins"]
        }

        mismatches = []
        missing = []
        for plugin_dir in _all_plugin_dirs():
            pj = _load_plugin_json(plugin_dir)
            name, pj_version = pj["name"], pj["version"]
            if name not in market_versions:
                missing.append(name)
            elif market_versions[name] != pj_version:
                mismatches.append((name, pj_version, market_versions[name]))

        assert not missing, f"plugins absent from marketplace.json: {missing}"
        assert not mismatches, (
            "marketplace.json ↔ plugin.json version drift "
            f"(plugin, plugin.json, marketplace.json): {mismatches}"
        )

    @pytest.mark.unit
    def test_changelog_latest_release_heading_matches_version(self) -> None:
        """Scenario: the newest CHANGELOG release heading is the current version.

        GIVEN the CHANGELOG.md release headings beneath [Unreleased]
        WHEN I read the newest `## [x.y.z]` heading
        THEN it equals the ecosystem version from plugin.json,
        AND a bump without release notes (or vice versa) fails
        """
        changelog = (_REPO_ROOT / "CHANGELOG.md").read_text()
        headings = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, flags=re.MULTILINE)
        assert headings, "CHANGELOG.md has no versioned release headings"

        ecosystem_version = _load_plugin_json(_all_plugin_dirs()[0])["version"]
        assert headings[0] == ecosystem_version, (
            f"CHANGELOG newest release heading [{headings[0]}] does not "
            f"match ecosystem version {ecosystem_version}"
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

        GIVEN every per-plugin Makefile
        WHEN I scan its `find commands/ ... -name '*.md'` invocations
        THEN each one carries -maxdepth 1,
        AND new Makefiles that omit the flag are caught before
        they cause count drift
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

        GIVEN a plugin with a commands/ directory
        WHEN I count its top-level *.md files
        THEN the count equals len(plugin.json.commands),
        AND modular sub-files in command subdirectories are excluded
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
