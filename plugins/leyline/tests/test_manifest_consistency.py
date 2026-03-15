# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,E501
"""Tests for manifest consistency between plugin.json and openpackage.yml.

Feature: Plugin Manifest Consistency

    As an ecosystem maintainer
    I want plugin.json and openpackage.yml to stay in sync
    So that installations and marketplace listings match
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

LEYLINE_ROOT = Path(__file__).parent.parent


@pytest.fixture
def plugin_json() -> dict:
    """Load the actual plugin.json manifest."""
    path = LEYLINE_ROOT / ".claude-plugin" / "plugin.json"
    return json.loads(path.read_text())


@pytest.fixture
def openpackage() -> dict:
    """Load the actual openpackage.yml manifest."""
    path = LEYLINE_ROOT / "openpackage.yml"
    return yaml.safe_load(path.read_text())


def _normalize_path(p: str) -> str:
    """Strip leading './' so both manifest formats compare equally."""
    return p.lstrip("./")


class TestManifestVersionSync:
    """Verify version fields stay synchronized."""

    @pytest.mark.unit
    def test_versions_match(self, plugin_json: dict, openpackage: dict) -> None:
        """
        GIVEN plugin.json and openpackage.yml
        WHEN comparing version fields
        THEN they are identical.
        """
        assert plugin_json["version"] == openpackage["version"]


class TestManifestCommandSync:
    """Verify command lists stay synchronized."""

    @pytest.mark.unit
    def test_commands_match(self, plugin_json: dict, openpackage: dict) -> None:
        """
        GIVEN both manifests
        WHEN comparing registered commands
        THEN they list the same command files.
        """
        pj_cmds = sorted(_normalize_path(c) for c in plugin_json.get("commands", []))
        op_cmds = sorted(_normalize_path(c) for c in openpackage.get("commands", []))
        assert pj_cmds == op_cmds

    @pytest.mark.unit
    def test_all_commands_exist_on_disk(self, plugin_json: dict) -> None:
        """
        GIVEN the command list in plugin.json
        WHEN checking each path
        THEN every referenced command file exists.
        """
        for cmd in plugin_json.get("commands", []):
            cmd_path = LEYLINE_ROOT / _normalize_path(cmd)
            assert cmd_path.exists(), f"Missing command: {cmd}"


class TestManifestSkillSync:
    """Verify skill lists stay synchronized."""

    @pytest.mark.unit
    def test_skills_match(self, plugin_json: dict, openpackage: dict) -> None:
        """
        GIVEN both manifests
        WHEN comparing registered skills
        THEN they list the same skill directories.
        """
        pj_skills = sorted(_normalize_path(s) for s in plugin_json.get("skills", []))
        op_skills = sorted(_normalize_path(s) for s in openpackage.get("skills", []))
        assert pj_skills == op_skills

    @pytest.mark.unit
    def test_all_skills_exist_on_disk(self, plugin_json: dict) -> None:
        """
        GIVEN the skill list in plugin.json
        WHEN checking each path
        THEN every referenced skill directory exists.
        """
        for skill in plugin_json.get("skills", []):
            skill_path = LEYLINE_ROOT / _normalize_path(skill)
            assert skill_path.is_dir(), f"Missing skill dir: {skill}"


class TestManifestMetadataSync:
    """Verify name, description, and other metadata stay synchronized."""

    @pytest.mark.unit
    def test_names_match(self, plugin_json: dict, openpackage: dict) -> None:
        """
        GIVEN both manifests
        WHEN comparing name fields
        THEN they are identical.
        """
        assert plugin_json["name"] == openpackage["name"]

    @pytest.mark.unit
    def test_descriptions_match(self, plugin_json: dict, openpackage: dict) -> None:
        """
        GIVEN both manifests
        WHEN comparing descriptions
        THEN they are identical (modulo whitespace normalization).
        """
        pj_desc = " ".join(plugin_json["description"].split())
        op_desc = " ".join(openpackage["description"].split())
        assert pj_desc == op_desc

    @pytest.mark.unit
    def test_keywords_match(self, plugin_json: dict, openpackage: dict) -> None:
        """
        GIVEN both manifests
        WHEN comparing keyword lists
        THEN they contain the same entries.
        """
        assert sorted(plugin_json.get("keywords", [])) == sorted(
            openpackage.get("keywords", [])
        )
