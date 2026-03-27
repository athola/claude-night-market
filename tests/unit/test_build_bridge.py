"""Tests for build_bridge.py — OpenClaw bridge plugin builder.

Feature: Build OpenClaw bridge plugin from ClawHub export

As a night-market maintainer
I want to populate the bridge plugin from exported skills
So that OpenClaw users can install one plugin and get all skills.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_bridge import build_bridge  # noqa: E402


@pytest.fixture()
def mock_clawhub(tmp_path: Path) -> Path:
    """Create a mock ClawHub export directory."""
    clawhub = tmp_path / "clawhub"
    clawhub.mkdir()

    # Create two mock skill directories
    for slug in ["nm-pensive-bug-review", "nm-sanctum-commit-messages"]:
        skill_dir = clawhub / slug
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {slug}\ndescription: test\nversion: 1.7.0\n---\n\n# Test\n"
        )

    # Add modules to one skill
    modules = clawhub / "nm-sanctum-commit-messages" / "modules"
    modules.mkdir()
    (modules / "format.md").write_text("# Format\n")

    # Write manifest
    manifest = {
        "skills": [
            {
                "slug": "nm-pensive-bug-review",
                "source": "pensive:bug-review",
                "version": "1.7.0",
            },
            {
                "slug": "nm-sanctum-commit-messages",
                "source": "sanctum:commit-messages",
                "version": "1.7.0",
            },
        ],
        "total_exported": 2,
        "total_errors": 0,
    }
    (clawhub / "manifest.json").write_text(json.dumps(manifest))

    return clawhub


@pytest.fixture()
def mock_bridge(tmp_path: Path) -> Path:
    """Create a mock bridge plugin directory."""
    bridge = tmp_path / "bridge"
    bridge.mkdir()
    (bridge / "openclaw.plugin.json").write_text(
        json.dumps({"name": "night-market", "version": "0.0.0", "skills": ["./skills"]})
    )
    return bridge


class TestBuildBridge:
    """
    Feature: Populate bridge plugin from ClawHub export

    As a maintainer
    I want to copy exported skills into the bridge plugin
    So that OpenClaw can load them as a single plugin.
    """

    @pytest.mark.unit
    def test_copies_skills_to_bridge(
        self, mock_clawhub: Path, mock_bridge: Path
    ) -> None:
        """
        Scenario: Skills are copied from export to bridge
        Given a ClawHub export with 2 skills
        When I build the bridge
        Then both skills appear in bridge/skills/.
        """
        build_bridge(mock_clawhub, mock_bridge)

        skills_dir = mock_bridge / "skills"
        assert skills_dir.is_dir()
        assert (skills_dir / "nm-pensive-bug-review" / "SKILL.md").exists()
        assert (skills_dir / "nm-sanctum-commit-messages" / "SKILL.md").exists()

    @pytest.mark.unit
    def test_copies_modules(self, mock_clawhub: Path, mock_bridge: Path) -> None:
        """
        Scenario: Skill modules are preserved
        Given a skill with a modules/ directory
        When I build the bridge
        Then modules are copied too.
        """
        build_bridge(mock_clawhub, mock_bridge)

        modules = mock_bridge / "skills" / "nm-sanctum-commit-messages" / "modules"
        assert modules.is_dir()
        assert (modules / "format.md").exists()

    @pytest.mark.unit
    def test_updates_plugin_version(
        self, mock_clawhub: Path, mock_bridge: Path
    ) -> None:
        """
        Scenario: Plugin manifest version is updated
        Given a bridge with version 0.0.0
        When I build from export with version 1.7.0
        Then the plugin version is updated to 1.7.0.
        """
        build_bridge(mock_clawhub, mock_bridge)

        pj = json.loads((mock_bridge / "openclaw.plugin.json").read_text())
        assert pj["version"] == "1.7.0"

    @pytest.mark.unit
    def test_raises_without_manifest(self, tmp_path: Path, mock_bridge: Path) -> None:
        """
        Scenario: Missing export manifest
        Given a directory without manifest.json
        When I build the bridge
        Then it raises FileNotFoundError.
        """
        empty = tmp_path / "empty"
        empty.mkdir()

        with pytest.raises(FileNotFoundError):
            build_bridge(empty, mock_bridge)

    @pytest.mark.unit
    def test_cleans_previous_skills(
        self, mock_clawhub: Path, mock_bridge: Path
    ) -> None:
        """
        Scenario: Old skills are cleaned before copy
        Given a bridge with stale skills from a previous build
        When I rebuild
        Then only current export skills remain.
        """
        # Create a stale skill
        stale = mock_bridge / "skills" / "nm-old-stale-skill"
        stale.mkdir(parents=True)
        (stale / "SKILL.md").write_text("old")

        build_bridge(mock_clawhub, mock_bridge)

        assert not (mock_bridge / "skills" / "nm-old-stale-skill").exists()
        assert (mock_bridge / "skills" / "nm-pensive-bug-review").exists()
