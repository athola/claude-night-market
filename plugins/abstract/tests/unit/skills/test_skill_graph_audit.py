"""Structural tests for the skill-graph-audit skill.

Feature: skill-graph-audit skill is well-formed
    As a marketplace maintainer
    I want the skill scaffold validated
    So that frontmatter, modules, and CLI hook stay consistent.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_DIR = Path(__file__).resolve().parents[3] / "skills" / "skill-graph-audit"
SKILL_MD = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "skill_graph.py"


def _load_frontmatter(md: Path) -> dict:
    text = md.read_text()
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert m, f"No frontmatter in {md}"
    data = yaml.safe_load(m.group(1))
    assert isinstance(data, dict), f"Frontmatter not a mapping in {md}"
    return data


class TestSkillScaffold:
    """Skill files conform to abstract:skill-authoring conventions."""

    @pytest.mark.unit
    def test_skill_md_exists(self) -> None:
        """Scenario: SKILL.md is present."""
        assert SKILL_MD.exists()

    @pytest.mark.unit
    def test_frontmatter_required_fields(self) -> None:
        """Scenario: name, description, version, alwaysApply present."""
        fm = _load_frontmatter(SKILL_MD)
        for key in ("name", "description", "version", "alwaysApply"):
            assert key in fm, f"Missing frontmatter field: {key}"

    @pytest.mark.unit
    def test_name_matches_directory(self) -> None:
        """Scenario: frontmatter name == directory name."""
        fm = _load_frontmatter(SKILL_MD)
        assert fm["name"] == "skill-graph-audit"

    @pytest.mark.unit
    def test_description_within_budget(self) -> None:
        """Scenario: description fits the 160-char budget."""
        fm = _load_frontmatter(SKILL_MD)
        assert len(fm["description"]) <= 160, (
            f"description is {len(fm['description'])} chars; budget is 160"
        )

    @pytest.mark.unit
    def test_description_has_use_when_trigger(self) -> None:
        """Scenario: description carries explicit activation trigger."""
        fm = _load_frontmatter(SKILL_MD)
        assert "Use when" in fm["description"], (
            "description should include 'Use when ...' trigger phrase"
        )

    @pytest.mark.unit
    def test_modules_listed_in_frontmatter_exist(self) -> None:
        """Scenario: every modules: entry resolves to a real file."""
        fm = _load_frontmatter(SKILL_MD)
        modules = fm.get("modules") or []
        for rel in modules:
            target = SKILL_DIR / rel
            assert target.exists(), f"Module {rel} does not exist"

    @pytest.mark.unit
    def test_module_files_have_frontmatter(self) -> None:
        """Scenario: each module file declares its own frontmatter."""
        for module in MODULES_DIR.glob("*.md"):
            fm = _load_frontmatter(module)
            assert "name" in fm
            assert "description" in fm


class TestScriptCli:
    """The underlying script is invocable from the project root."""

    @pytest.mark.unit
    def test_script_runs_against_marketplace(self, tmp_path: Path) -> None:
        """Scenario: script returns 0 and emits a totals header."""
        # Use a minimal fake plugins tree so this stays fast and hermetic.
        (tmp_path / "plugins" / "p" / "skills" / "s").mkdir(parents=True)
        (tmp_path / "plugins" / "p" / "skills" / "s" / "SKILL.md").write_text(
            "---\nname: s\ndescription: x\n---\nbody"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--plugins-root",
                str(tmp_path / "plugins"),
                "--top-n",
                "5",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Skills:" in result.stdout
        assert "Edges:" in result.stdout
